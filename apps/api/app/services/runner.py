from __future__ import annotations

import os
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy.orm import Session, sessionmaker

from app.models.entities import Run
from app.services.parser import index_run_outputs

SESSION_PATTERNS = [
    re.compile(r"Session UUID:\s*([A-Za-z0-9-]+)"),
    re.compile(r"session\s+id[:\s]+([A-Za-z0-9-]+)", re.IGNORECASE),
]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def write_generated_params(params_path: Path, params: dict[str, Any], output_dir: Path) -> None:
    params_path.parent.mkdir(parents=True, exist_ok=True)
    merged = {**params, "outdir": str(output_dir)}
    with params_path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(merged, handle, sort_keys=True, allow_unicode=True)


def extract_session_id(*paths: Path) -> str | None:
    for path in paths:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SESSION_PATTERNS:
            match = pattern.search(text)
            if match:
                return match.group(1)
    return None


def build_nextflow_command(run: Run, resume: bool = False) -> list[str]:
    output_dir = Path(run.output_dir)
    run_dir = output_dir.parent
    command = [
        "nextflow",
        "run",
        str(Path(run.pipeline_path) / "main.nf"),
        "-profile",
        run.profile,
        "-params-file",
        run.params_path,
        "-with-report",
        str(output_dir / "nextflow_report.html"),
        "-with-trace",
        str(output_dir / "nextflow_trace.txt"),
        "-with-timeline",
        str(output_dir / "nextflow_timeline.html"),
        "-with-dag",
        str(output_dir / "nextflow_dag.html"),
        "-log",
        str(run_dir / ".nextflow.log"),
        "-work-dir",
        run.work_dir,
        "-ansi-log",
        "false",
    ]
    if resume:
        command.append("-resume")
    return command


class LocalNextflowRunner:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self.session_factory = session_factory

    def start(self, run_id: str, resume: bool = False) -> None:
        with self.session_factory() as db:
            run = db.get(Run, run_id)
            if run is None:
                return
            self._run(db, run, resume=resume)

    def _run(self, db: Session, run: Run, resume: bool = False) -> None:
        output_dir = Path(run.output_dir)
        run_dir = output_dir.parent
        output_dir.mkdir(parents=True, exist_ok=True)
        Path(run.work_dir).mkdir(parents=True, exist_ok=True)
        write_generated_params(Path(run.params_path), run.inputs.get("params", {}), output_dir)

        command = build_nextflow_command(run, resume=resume)
        run.command = command
        run.status = "running"
        run.started_at = utc_now()
        db.commit()

        stdout_path = run_dir / "stdout.log"
        stderr_path = run_dir / "stderr.log"
        nextflow_log_path = run_dir / ".nextflow.log"

        if shutil.which("nextflow") is None:
            run.status = "failed"
            run.exit_code = 127
            run.error_message = "nextflow executable not found in PATH"
            run.finished_at = utc_now()
            db.commit()
            return

        with stdout_path.open("w", encoding="utf-8") as stdout, stderr_path.open(
            "w", encoding="utf-8"
        ) as stderr:
            process = subprocess.Popen(
                command,
                cwd=run.pipeline_path,
                stdout=stdout,
                stderr=stderr,
                text=True,
                env={**os.environ, "NXF_ANSI_LOG": "false"},
            )
            exit_code = process.wait()

        run.exit_code = exit_code
        run.session_id = extract_session_id(nextflow_log_path, stdout_path, stderr_path)
        run.finished_at = utc_now()
        if exit_code == 0:
            try:
                index_run_outputs(db, run)
                run.status = "succeeded"
            except Exception as exc:  # noqa: BLE001 - preserve run and raw logs.
                run.status = "parsing_failed"
                run.error_message = f"Parser failed after successful process: {exc}"
        else:
            run.status = "failed"
            run.error_message = f"nextflow exited with code {exit_code}"
            try:
                index_run_outputs(db, run)
            except Exception:
                pass
        db.commit()


class FakeRunner(LocalNextflowRunner):
    def _run(self, db: Session, run: Run, resume: bool = False) -> None:
        output_dir = Path(run.output_dir)
        run_dir = output_dir.parent
        output_dir.mkdir(parents=True, exist_ok=True)
        Path(run.work_dir).mkdir(parents=True, exist_ok=True)
        write_generated_params(Path(run.params_path), run.inputs.get("params", {}), output_dir)
        run.command = build_nextflow_command(run, resume=resume)
        run.status = "running"
        run.started_at = utc_now()
        db.commit()

        (run_dir / "stdout.log").write_text("Fake runner completed\nSession UUID: fake-session\n")
        (run_dir / "stderr.log").write_text("")
        (run_dir / ".nextflow.log").write_text("Session UUID: fake-session\n")
        (output_dir / "nextflow_trace.txt").write_text(
            "task_id\thash\tname\tstatus\texit\trealtime\t%cpu\trss\n"
            "1\tab/cd\tDESEQ2\tCOMPLETED\t0\t1m\t12.0%\t1 GB\n",
            encoding="utf-8",
        )
        for name in ["nextflow_report.html", "nextflow_timeline.html", "nextflow_dag.html"]:
            (output_dir / name).write_text("<html><body>fake</body></html>", encoding="utf-8")

        required = {
            "deseq2/deseq2_results_all.tsv": "gene\tlog2FoldChange\tpadj\nGeneA\t1.2\t0.01\n",
            "deseq2/deseq2_results_sig.tsv": "gene\tlog2FoldChange\tpadj\nGeneA\t1.2\t0.01\n",
            "counts/sample_metadata.tsv": "sample\tcondition\nS1\tcontrol\n",
            "enrichment/go_bp_results.tsv": "term\tpadj\nGO:1\t0.02\n",
            "enrichment/kegg_results.tsv": "pathway\tpadj\nath00010\t0.03\n",
            "splicing/splicing_significant.tsv": "event\tfdr\nSE1\t0.01\n",
            "wgcna/wgcna_modules.tsv": "gene\tmodule\nGeneA\tblue\n",
            "integration/key_candidates.tsv": "gene\tscore\nGeneA\t10\n",
        }
        for relative, content in required.items():
            path = output_dir / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")

        run.session_id = "fake-session"
        run.exit_code = 0
        run.finished_at = utc_now()
        index_run_outputs(db, run)
        run.status = "succeeded"
        db.commit()

