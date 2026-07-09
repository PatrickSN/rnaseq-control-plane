from __future__ import annotations

from pathlib import Path
from typing import TypedDict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.security import hash_password
from app.models.entities import Pipeline, PipelineVersion, User
from app.services.pipeline_registry import compute_pipeline_fingerprint


class PipelineSeed(TypedDict):
    slug: str
    display_name: str
    organism: str
    description: str
    relative_path: str
    version: str
    supported_profiles: list[str]


PIPELINE_SEEDS: list[PipelineSeed] = [
    {
        "slug": "soja-iac",
        "display_name": "Soja IAC RNA-Seq",
        "organism": "Glycine max",
        "description": "Pipeline Nextflow DSL2 para RNA-Seq de soja IAC100 vs BR16.",
        "relative_path": "soja-iac",
        "version": "local-current",
        "supported_profiles": ["local", "slurm", "test"],
    },
    {
        "slug": "RNA-Seq-Arabidopsis",
        "display_name": "Arabidopsis RNA-Seq",
        "organism": "Arabidopsis thaliana",
        "description": "Pipeline Nextflow DSL2 para Arabidopsis thaliana TAIR10.",
        "relative_path": "RNA-Seq-Arabidopsis",
        "version": "local-current",
        "supported_profiles": ["local", "slurm", "test"],
    },
]


def seed_admin_user(db: Session, settings: Settings) -> None:
    existing = db.scalar(select(User).where(User.email == settings.admin_email))
    if existing is not None:
        return
    db.add(
        User(
            email=settings.admin_email,
            hashed_password=hash_password(settings.admin_password),
            full_name="Development Admin",
            role="admin",
        )
    )


def seed_pipelines(db: Session, settings: Settings) -> None:
    for seed in PIPELINE_SEEDS:
        pipeline = db.scalar(select(Pipeline).where(Pipeline.slug == seed["slug"]))
        if pipeline is None:
            pipeline = Pipeline(
                slug=seed["slug"],
                display_name=seed["display_name"],
                organism=seed["organism"],
                description=seed["description"],
            )
            db.add(pipeline)
            db.flush()

        path = (settings.pipelines_base_dir / seed["relative_path"]).resolve()
        version = db.scalar(
            select(PipelineVersion).where(
                PipelineVersion.pipeline_id == pipeline.id,
                PipelineVersion.version == seed["version"],
            )
        )
        fingerprint = compute_pipeline_fingerprint(path)
        if version is None:
            db.add(
                PipelineVersion(
                    pipeline_id=pipeline.id,
                    version=seed["version"],
                    pipeline_path=str(path),
                    main_script="main.nf",
                    params_template_path="params.yaml",
                    default_profile="local",
                    supported_profiles=seed["supported_profiles"],
                    fingerprint=fingerprint,
                    is_default=True,
                )
            )
        else:
            version.pipeline_path = str(path)
            version.fingerprint = fingerprint


def ensure_storage(settings: Settings) -> None:
    for path in [
        settings.data_root,
        settings.runs_dir,
        settings.artifacts_dir,
        settings.references_dir,
    ]:
        Path(path).mkdir(parents=True, exist_ok=True)


def init_db(db: Session, settings: Settings) -> None:
    ensure_storage(settings)
    seed_admin_user(db, settings)
    seed_pipelines(db, settings)
    db.commit()
