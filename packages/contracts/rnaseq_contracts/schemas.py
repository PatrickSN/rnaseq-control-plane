from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"
    PARSING_FAILED = "parsing_failed"


class ProfileName(StrEnum):
    LOCAL = "local"
    SLURM = "slurm"
    TEST = "test"


class ExecutorKind(StrEnum):
    LOCAL = "local"
    SLURM = "slurm"


class ArtifactKind(StrEnum):
    NEXTFLOW_REPORT = "nextflow_report"
    NEXTFLOW_TIMELINE = "nextflow_timeline"
    NEXTFLOW_DAG = "nextflow_dag"
    NEXTFLOW_TRACE = "nextflow_trace"
    NEXTFLOW_LOG = "nextflow_log"
    STDOUT_LOG = "stdout_log"
    STDERR_LOG = "stderr_log"
    PARAMS = "params"
    RESULT_TABLE = "result_table"


class RoleName(StrEnum):
    ADMIN = "admin"
    USER = "user"


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str | None = None


class AuthLogin(BaseModel):
    email: EmailStr
    password: str


class TokenRead(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    full_name: str | None
    role: RoleName
    is_active: bool
    created_at: datetime


class PipelineVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    pipeline_id: UUID
    version: str
    pipeline_path: str
    main_script: str
    params_template_path: str
    default_profile: ProfileName
    supported_profiles: list[ProfileName]
    fingerprint: str | None
    is_default: bool
    created_at: datetime


class PipelineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    slug: str
    display_name: str
    organism: str
    description: str | None
    is_active: bool
    versions: list[PipelineVersionRead] = Field(default_factory=list)


class RunCreate(BaseModel):
    pipeline_id: UUID
    pipeline_version_id: UUID | None = None
    name: str | None = Field(default=None, max_length=160)
    profile: ProfileName = ProfileName.LOCAL
    executor: ExecutorKind = ExecutorKind.LOCAL
    params: dict[str, Any] = Field(default_factory=dict)
    input_paths: dict[str, str] = Field(default_factory=dict)


class RunResumeRequest(BaseModel):
    params_override: dict[str, Any] = Field(default_factory=dict)


class RunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    pipeline_id: UUID
    pipeline_version_id: UUID
    resumed_from_run_id: UUID | None
    name: str | None
    status: RunStatus
    profile: ProfileName
    executor: ExecutorKind
    pipeline_path: str
    pipeline_fingerprint: str | None
    work_dir: str
    output_dir: str
    params_path: str
    command: list[str]
    session_id: str | None
    exit_code: int | None
    error_message: str | None
    environment: dict[str, Any]
    inputs: dict[str, Any]
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None


class RunTaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    run_id: UUID
    task_id: str | None
    hash: str | None
    name: str
    process: str | None
    status: str | None
    exit_code: int | None
    submit: str | None
    start: str | None
    complete: str | None
    duration: str | None
    realtime: str | None
    cpu_percent: str | None
    memory: str | None
    raw: dict[str, Any]


class ArtifactRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    run_id: UUID
    kind: ArtifactKind
    label: str
    path: str
    relative_path: str
    mime_type: str | None
    size_bytes: int | None
    sha256: str | None
    created_at: datetime


class LogRead(BaseModel):
    run_id: UUID
    log_type: str
    content: str

