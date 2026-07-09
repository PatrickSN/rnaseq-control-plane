from __future__ import annotations

import os
from collections.abc import Generator

import pytest

os.environ["RNASEQ_ENV_FILE"] = ""

_SETTINGS_ENV_NAMES = [
    "RNASEQ_DATABASE_URL",
    "RNASEQ_DATA_ROOT",
    "DATA_ROOT",
    "RNASEQ_STORAGE_DIR",
    "RNASEQ_RUNS_DIR",
    "RUNS_ROOT",
    "RNASEQ_ARTIFACTS_ROOT",
    "ARTIFACTS_ROOT",
    "RNASEQ_REFERENCES_ROOT",
    "REFERENCES_ROOT",
    "RNASEQ_PIPELINES_BASE_DIR",
    "PIPELINES_ROOT",
    "RNASEQ_RUNNER_MODE",
]


@pytest.fixture(autouse=True)
def isolate_settings_env_file(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    from app.core.config import get_settings

    monkeypatch.setenv("RNASEQ_ENV_FILE", "")
    for name in _SETTINGS_ENV_NAMES:
        monkeypatch.delenv(name, raising=False)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()