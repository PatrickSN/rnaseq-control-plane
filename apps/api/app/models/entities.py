from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base


def new_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(256), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(160))
    role: Mapped[str] = mapped_column(String(32), default="user", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    runs: Mapped[list[Run]] = relationship(back_populates="user")


class Pipeline(Base):
    __tablename__ = "pipelines"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(160), nullable=False)
    organism: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    versions: Mapped[list[PipelineVersion]] = relationship(
        back_populates="pipeline", cascade="all, delete-orphan"
    )


class PipelineVersion(Base):
    __tablename__ = "pipeline_versions"
    __table_args__ = (UniqueConstraint("pipeline_id", "version", name="uq_pipeline_version"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    pipeline_id: Mapped[str] = mapped_column(ForeignKey("pipelines.id"), nullable=False)
    version: Mapped[str] = mapped_column(String(80), nullable=False)
    pipeline_path: Mapped[str] = mapped_column(Text, nullable=False)
    main_script: Mapped[str] = mapped_column(String(120), default="main.nf", nullable=False)
    params_template_path: Mapped[str] = mapped_column(String(160), default="params.yaml")
    default_profile: Mapped[str] = mapped_column(String(32), default="local", nullable=False)
    supported_profiles: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    fingerprint: Mapped[str | None] = mapped_column(String(64))
    is_default: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    pipeline: Mapped[Pipeline] = relationship(back_populates="versions")
    runs: Mapped[list[Run]] = relationship(back_populates="pipeline_version")


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    pipeline_id: Mapped[str] = mapped_column(ForeignKey("pipelines.id"), nullable=False)
    pipeline_version_id: Mapped[str] = mapped_column(ForeignKey("pipeline_versions.id"), nullable=False)
    resumed_from_run_id: Mapped[str | None] = mapped_column(ForeignKey("runs.id"))
    name: Mapped[str | None] = mapped_column(String(160))
    status: Mapped[str] = mapped_column(String(32), default="queued", index=True, nullable=False)
    profile: Mapped[str] = mapped_column(String(32), default="local", nullable=False)
    executor: Mapped[str] = mapped_column(String(32), default="local", nullable=False)
    pipeline_path: Mapped[str] = mapped_column(Text, nullable=False)
    pipeline_fingerprint: Mapped[str | None] = mapped_column(String(64))
    work_dir: Mapped[str] = mapped_column(Text, nullable=False)
    output_dir: Mapped[str] = mapped_column(Text, nullable=False)
    params_path: Mapped[str] = mapped_column(Text, nullable=False)
    command: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    session_id: Mapped[str | None] = mapped_column(String(120), index=True)
    exit_code: Mapped[int | None] = mapped_column(Integer)
    error_message: Mapped[str | None] = mapped_column(Text)
    environment: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    inputs: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship(back_populates="runs")
    pipeline_version: Mapped[PipelineVersion] = relationship(back_populates="runs")
    parameters: Mapped[list[RunParameter]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )
    tasks: Mapped[list[RunTask]] = relationship(back_populates="run", cascade="all, delete-orphan")
    artifacts: Mapped[list[RunArtifact]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )


class RunParameter(Base):
    __tablename__ = "run_parameters"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    value: Mapped[Any] = mapped_column(JSON, nullable=True)
    source: Mapped[str] = mapped_column(String(32), default="user", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    run: Mapped[Run] = relationship(back_populates="parameters")


class RunTask(Base):
    __tablename__ = "run_tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id"), nullable=False, index=True)
    task_id: Mapped[str | None] = mapped_column(String(80))
    hash: Mapped[str | None] = mapped_column(String(80))
    name: Mapped[str] = mapped_column(String(260), nullable=False)
    process: Mapped[str | None] = mapped_column(String(160))
    status: Mapped[str | None] = mapped_column(String(80))
    exit_code: Mapped[int | None] = mapped_column(Integer)
    submit: Mapped[str | None] = mapped_column(String(80))
    start: Mapped[str | None] = mapped_column(String(80))
    complete: Mapped[str | None] = mapped_column(String(80))
    duration: Mapped[str | None] = mapped_column(String(80))
    realtime: Mapped[str | None] = mapped_column(String(80))
    cpu_percent: Mapped[str | None] = mapped_column(String(80))
    memory: Mapped[str | None] = mapped_column(String(80))
    raw: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    run: Mapped[Run] = relationship(back_populates="tasks")


class RunArtifact(Base):
    __tablename__ = "run_artifacts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id"), nullable=False, index=True)
    kind: Mapped[str] = mapped_column(String(80), nullable=False)
    label: Mapped[str] = mapped_column(String(160), nullable=False)
    path: Mapped[str] = mapped_column(Text, nullable=False)
    relative_path: Mapped[str] = mapped_column(Text, nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(160))
    size_bytes: Mapped[int | None] = mapped_column(Integer)
    sha256: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    run: Mapped[Run] = relationship(back_populates="artifacts")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    run_id: Mapped[str | None] = mapped_column(ForeignKey("runs.id"))
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_id: Mapped[str | None] = mapped_column(String(80))
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

