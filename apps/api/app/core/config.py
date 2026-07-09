from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from sqlalchemy.engine import make_url


def _bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.lower() in {"1", "true", "yes", "on"}


def _load_env_file(path: Path) -> None:
    if not path.is_file():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'\"")
        if key and key not in os.environ:
            os.environ[key] = value


@dataclass(frozen=True)
class Settings:
    project_root: Path
    data_root: Path
    database_url: str
    jwt_secret: str
    jwt_expire_minutes: int
    admin_email: str
    admin_password: str
    pipelines_base_dir: Path
    storage_dir: Path
    runs_dir: Path
    artifacts_dir: Path
    references_dir: Path
    runner_mode: str
    create_db_on_startup: bool
    cors_origins: list[str]


def _first_env(*names: str) -> str | None:
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return None


def _resolve_path(raw: str | Path, base: Path | None = None) -> Path:
    path = Path(raw).expanduser()
    if not path.is_absolute() and base is not None:
        path = base / path
    return path.resolve()


def _env_file_path(project_root: Path) -> Path | None:
    raw = os.getenv("RNASEQ_ENV_FILE")
    if raw is None:
        return project_root / ".env"
    if not raw.strip():
        return None
    return _resolve_path(raw, project_root)


def normalize_database_url(database_url: str, base_dir: Path) -> str:
    url = make_url(database_url)
    if not url.drivername.startswith("sqlite") or not url.database or url.database == ":memory:":
        return database_url

    database_path = Path(url.database).expanduser()
    if not database_path.is_absolute():
        database_path = base_dir / database_path
    database_path = database_path.resolve()
    return str(url.set(database=str(database_path)))


def ensure_sqlite_database_parent(database_url: str) -> None:
    url = make_url(database_url)
    if not url.drivername.startswith("sqlite") or not url.database or url.database == ":memory:":
        return
    Path(url.database).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    detected_root = Path(__file__).resolve().parents[4]
    env_file = _env_file_path(detected_root)
    if env_file is not None:
        _load_env_file(env_file)
    project_root = _resolve_path(_first_env("RNASEQ_PROJECT_ROOT", "PROJECT_ROOT") or detected_root)
    data_root = _resolve_path(
        _first_env("RNASEQ_DATA_ROOT", "DATA_ROOT", "RNASEQ_STORAGE_DIR")
        or "~/dados/rnaseq-control"
    )
    pipelines_base = _resolve_path(
        _first_env("RNASEQ_PIPELINES_BASE_DIR", "PIPELINES_ROOT") or "~/pipelines",
        project_root,
    )
    runs_dir = _resolve_path(_first_env("RNASEQ_RUNS_DIR", "RUNS_ROOT") or data_root / "runs")
    artifacts_dir = _resolve_path(
        _first_env("RNASEQ_ARTIFACTS_ROOT", "ARTIFACTS_ROOT") or data_root / "artifacts"
    )
    references_dir = _resolve_path(
        _first_env("RNASEQ_REFERENCES_ROOT", "REFERENCES_ROOT") or data_root / "references"
    )
    cors = os.getenv("RNASEQ_CORS_ORIGINS", "*")
    database_url = normalize_database_url(
        os.getenv(
            "RNASEQ_DATABASE_URL",
            f"sqlite+pysqlite:///{data_root / 'rnaseq-dev.sqlite3'}",
        ),
        project_root,
    )
    ensure_sqlite_database_parent(database_url)
    return Settings(
        project_root=project_root,
        data_root=data_root,
        database_url=database_url,
        jwt_secret=os.getenv("RNASEQ_JWT_SECRET", "dev-only-change-me"),
        jwt_expire_minutes=int(os.getenv("RNASEQ_JWT_EXPIRE_MINUTES", "1440")),
        admin_email=os.getenv("RNASEQ_ADMIN_EMAIL", "admin@example.com"),
        admin_password=os.getenv("RNASEQ_ADMIN_PASSWORD", "admin123"),
        pipelines_base_dir=pipelines_base,
        storage_dir=data_root,
        runs_dir=runs_dir,
        artifacts_dir=artifacts_dir,
        references_dir=references_dir,
        runner_mode=os.getenv("RNASEQ_RUNNER_MODE", "local"),
        create_db_on_startup=_bool_env("RNASEQ_CREATE_DB_ON_STARTUP", True),
        cors_origins=[item.strip() for item in cors.split(",") if item.strip()],
    )
