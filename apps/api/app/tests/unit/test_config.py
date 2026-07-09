from __future__ import annotations

from app.core.config import get_settings


def test_settings_resolve_server_data_directories(monkeypatch, tmp_path) -> None:
    for name in [
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
    ]:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("RNASEQ_DATA_ROOT", str(tmp_path / "data"))

    get_settings.cache_clear()
    settings = get_settings()

    assert settings.data_root == (tmp_path / "data").resolve()
    assert settings.storage_dir == settings.data_root
    assert settings.runs_dir == (tmp_path / "data" / "runs").resolve()
    assert settings.artifacts_dir == (tmp_path / "data" / "artifacts").resolve()
    assert settings.references_dir == (tmp_path / "data" / "references").resolve()
    assert settings.database_url == f"sqlite+pysqlite:///{tmp_path / 'data' / 'rnaseq-dev.sqlite3'}"

    get_settings.cache_clear()
