from __future__ import annotations

import csv
import hashlib
import mimetypes
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.models.entities import Run, RunArtifact, RunTask


@dataclass(frozen=True)
class ArtifactSpec:
    relative_path: str
    kind: str
    label: str


NEXTFLOW_ARTIFACTS = [
    ArtifactSpec("nextflow_report.html", "nextflow_report", "Nextflow report"),
    ArtifactSpec("nextflow_timeline.html", "nextflow_timeline", "Nextflow timeline"),
    ArtifactSpec("nextflow_dag.html", "nextflow_dag", "Nextflow DAG"),
    ArtifactSpec("nextflow_trace.txt", "nextflow_trace", "Nextflow trace"),
]

ESSENTIAL_RESULT_ARTIFACTS = [
    ArtifactSpec("deseq2/deseq2_results_all.tsv", "result_table", "DESeq2 all results"),
    ArtifactSpec("deseq2/deseq2_results_sig.tsv", "result_table", "DESeq2 significant results"),
    ArtifactSpec("counts/sample_metadata.tsv", "result_table", "Sample metadata"),
    ArtifactSpec("enrichment/go_bp_results.tsv", "result_table", "GO BP enrichment"),
    ArtifactSpec("enrichment/kegg_results.tsv", "result_table", "KEGG enrichment"),
    ArtifactSpec("splicing/splicing_significant.tsv", "result_table", "Significant splicing"),
    ArtifactSpec("wgcna/wgcna_modules.tsv", "result_table", "WGCNA modules"),
    ArtifactSpec("integration/key_candidates.tsv", "result_table", "Key candidates"),
]


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_int(raw: str | None) -> int | None:
    if raw in (None, "", "-"):
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def normalize_trace_row(row: dict[str, str]) -> dict[str, Any]:
    return {key.strip().lower().replace("%", "percent"): value for key, value in row.items()}


def parse_trace_file(trace_path: Path) -> list[dict[str, Any]]:
    if not trace_path.is_file():
        return []
    with trace_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return [normalize_trace_row(row) for row in reader]


def task_from_trace(run_id: str, row: dict[str, Any]) -> RunTask:
    name = row.get("name") or row.get("process") or "unknown"
    return RunTask(
        run_id=run_id,
        task_id=row.get("task_id") or row.get("task id"),
        hash=row.get("hash"),
        name=name,
        process=row.get("process"),
        status=row.get("status"),
        exit_code=parse_int(row.get("exit") or row.get("exit_code")),
        submit=row.get("submit"),
        start=row.get("start"),
        complete=row.get("complete"),
        duration=row.get("duration"),
        realtime=row.get("realtime"),
        cpu_percent=row.get("cpupercent") or row.get("pcpu"),
        memory=row.get("rss") or row.get("vmem"),
        raw=row,
    )


def artifact_from_path(run_id: str, output_dir: Path, spec: ArtifactSpec) -> RunArtifact | None:
    path = output_dir / spec.relative_path
    if not path.is_file():
        return None
    mime_type, _ = mimetypes.guess_type(path.name)
    stat = path.stat()
    return RunArtifact(
        run_id=run_id,
        kind=spec.kind,
        label=spec.label,
        path=str(path),
        relative_path=spec.relative_path,
        mime_type=mime_type,
        size_bytes=stat.st_size,
        sha256=file_sha256(path),
    )


def index_run_outputs(db: Session, run: Run) -> None:
    output_dir = Path(run.output_dir)
    db.execute(delete(RunTask).where(RunTask.run_id == run.id))
    db.execute(delete(RunArtifact).where(RunArtifact.run_id == run.id))

    trace_path = output_dir / "nextflow_trace.txt"
    for row in parse_trace_file(trace_path):
        db.add(task_from_trace(run.id, row))

    for spec in [*NEXTFLOW_ARTIFACTS, *ESSENTIAL_RESULT_ARTIFACTS]:
        artifact = artifact_from_path(run.id, output_dir, spec)
        if artifact is not None:
            db.add(artifact)

    run_artifact_logs(db, run)
    db.flush()


def run_artifact_logs(db: Session, run: Run) -> None:
    candidates = [
        (Path(run.params_path), "params", "Generated params"),
        (Path(run.output_dir).parent / "stdout.log", "stdout_log", "stdout"),
        (Path(run.output_dir).parent / "stderr.log", "stderr_log", "stderr"),
        (Path(run.output_dir).parent / ".nextflow.log", "nextflow_log", ".nextflow.log"),
    ]
    for path, kind, label in candidates:
        if not path.is_file():
            continue
        db.add(
            RunArtifact(
                run_id=run.id,
                kind=kind,
                label=label,
                path=str(path),
                relative_path=path.name,
                mime_type=mimetypes.guess_type(path.name)[0],
                size_bytes=path.stat().st_size,
                sha256=file_sha256(path),
            )
        )

