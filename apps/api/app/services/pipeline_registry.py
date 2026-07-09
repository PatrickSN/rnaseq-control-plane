from __future__ import annotations

import hashlib
from pathlib import Path


FINGERPRINT_FILES = ("main.nf", "nextflow.config", "params.yaml")


def compute_pipeline_fingerprint(pipeline_path: Path) -> str | None:
    if not pipeline_path.exists():
        return None

    digest = hashlib.sha256()
    touched = False
    for relative in FINGERPRINT_FILES:
        path = pipeline_path / relative
        if path.is_file():
            touched = True
            digest.update(relative.encode("utf-8"))
            digest.update(path.read_bytes())
    return digest.hexdigest() if touched else None

