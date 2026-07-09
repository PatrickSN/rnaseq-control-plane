from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


def _bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    project_root: Path
    database_url: str
    jwt_secret: str
    jwt_expire_minutes: int
    admin_email: str
    admin_password: str
    pipelines_base_dir: Path
    storage_dir: Path
    runner_mode: str
    create_db_on_startup: bool
    cors_origins: list[str]


@lru_cache
def get_settings() -> Settings:
    project_root = Path(__file__).resolve().parents[4]
    pipelines_base = Path(os.getenv("RNASEQ_PIPELINES_BASE_DIR", ".."))
    storage = Path(os.getenv("RNASEQ_STORAGE_DIR", "storage"))
    cors = os.getenv("RNASEQ_CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
    return Settings(
        project_root=project_root,
        database_url=os.getenv(
            "RNASEQ_DATABASE_URL",
            f"sqlite+pysqlite:///{project_root / 'storage' / 'rnaseq-dev.sqlite3'}",
        ),
        jwt_secret=os.getenv("RNASEQ_JWT_SECRET", "dev-only-change-me"),
        jwt_expire_minutes=int(os.getenv("RNASEQ_JWT_EXPIRE_MINUTES", "1440")),
        admin_email=os.getenv("RNASEQ_ADMIN_EMAIL", "admin@example.com"),
        admin_password=os.getenv("RNASEQ_ADMIN_PASSWORD", "admin123"),
        pipelines_base_dir=(
            pipelines_base if pipelines_base.is_absolute() else project_root / pipelines_base
        ).resolve(),
        storage_dir=(storage if storage.is_absolute() else project_root / storage).resolve(),
        runner_mode=os.getenv("RNASEQ_RUNNER_MODE", "local"),
        create_db_on_startup=_bool_env("RNASEQ_CREATE_DB_ON_STARTUP", True),
        cors_origins=[item.strip() for item in cors.split(",") if item.strip()],
    )

