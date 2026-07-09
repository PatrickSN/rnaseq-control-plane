from __future__ import annotations

from pathlib import Path

from app.services.parser import ESSENTIAL_RESULT_ARTIFACTS, parse_trace_file


def test_parse_trace_file_fixture() -> None:
    trace = Path(__file__).parents[1] / "fixtures" / "parser_run" / "nextflow_trace.txt"
    rows = parse_trace_file(trace)
    assert len(rows) == 2
    assert rows[0]["name"] == "FASTQC_RAW (S1)"
    assert rows[0]["status"] == "COMPLETED"
    assert rows[1]["exit"] == "0"


def test_essential_artifact_contract_contains_required_tables() -> None:
    paths = {spec.relative_path for spec in ESSENTIAL_RESULT_ARTIFACTS}
    assert "deseq2/deseq2_results_all.tsv" in paths
    assert "integration/key_candidates.tsv" in paths

