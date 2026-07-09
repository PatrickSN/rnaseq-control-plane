from __future__ import annotations

from app.core.config import ensure_sqlite_database_parent, get_settings, normalize_database_url


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
    assert (tmp_path / "data").is_dir()

    get_settings.cache_clear()


def test_ensure_sqlite_database_parent_creates_parent(tmp_path) -> None:
    database_path = tmp_path / "missing" / "rnaseq.sqlite3"

    ensure_sqlite_database_parent(f"sqlite+pysqlite:///{database_path}")

    assert database_path.parent.is_dir()


def test_relative_sqlite_database_url_is_resolved_from_project_root(tmp_path) -> None:
    normalized = normalize_database_url(
        "sqlite+pysqlite:///../../storage/rnaseq-dev.sqlite3",
        tmp_path / "project" / "apps" / "api",
    )

    assert normalized.startswith("sqlite+pysqlite:///")
    assert ".." not in normalized
    assert normalized.endswith("/storage/rnaseq-dev.sqlite3")


def test_ensure_sqlite_database_parent_ignores_non_sqlite(tmp_path) -> None:
    marker = tmp_path / "db-host.example:5432"

    ensure_sqlite_database_parent("postgresql+psycopg://rnaseq:secret@db-host.example:5432/rnaseq")

    assert not marker.exists()
