from __future__ import annotations

from pathlib import Path
from typing import Annotated, Literal, TypeAlias

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from rnaseq_contracts import (
    ArtifactRead,
    LogRead,
    RunCreate,
    RunRead,
    RunResumeRequest,
    RunTaskRead,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.db.session import SessionLocal, get_db
from app.models.entities import (
    AuditEvent,
    PipelineVersion,
    Run,
    RunArtifact,
    RunParameter,
    RunTask,
    User,
)
from app.services.runner import FakeRunner, LocalNextflowRunner, build_nextflow_command

router = APIRouter(prefix="/api/runs", tags=["runs"])
DbSession: TypeAlias = Annotated[Session, Depends(get_db)]
CurrentUser: TypeAlias = Annotated[User, Depends(get_current_user)]


def runner() -> LocalNextflowRunner:
    settings = get_settings()
    if settings.runner_mode == "fake":
        return FakeRunner(SessionLocal)
    return LocalNextflowRunner(SessionLocal)


def choose_pipeline_version(db: Session, payload: RunCreate) -> PipelineVersion:
    query = select(PipelineVersion).where(PipelineVersion.pipeline_id == str(payload.pipeline_id))
    if payload.pipeline_version_id:
        query = query.where(PipelineVersion.id == str(payload.pipeline_version_id))
    else:
        query = query.where(PipelineVersion.is_default.is_(True))
    version = db.scalar(query)
    if version is None:
        raise HTTPException(status_code=404, detail="Pipeline version not found")
    return version


def create_run_model(
    db: Session,
    payload: RunCreate,
    current_user: User,
    resumed_from: Run | None = None,
) -> Run:
    settings = get_settings()
    if payload.executor != "local":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only local executor is implemented in the MVP",
        )
    version = choose_pipeline_version(db, payload)
    if payload.profile not in version.supported_profiles:
        raise HTTPException(status_code=422, detail=f"Unsupported profile: {payload.profile}")

    run = Run(
        user_id=current_user.id,
        pipeline_id=version.pipeline_id,
        pipeline_version_id=version.id,
        resumed_from_run_id=resumed_from.id if resumed_from else None,
        name=payload.name,
        status="queued",
        profile=str(payload.profile),
        executor=str(payload.executor),
        pipeline_path=version.pipeline_path,
        pipeline_fingerprint=version.fingerprint,
        work_dir="",
        output_dir="",
        params_path="",
        command=[],
        environment={"runner_mode": settings.runner_mode},
        inputs={"params": payload.params, "input_paths": payload.input_paths},
    )
    db.add(run)
    db.flush()

    run_root = settings.runs_dir / run.id
    run.output_dir = str(run_root / "results")
    run.work_dir = str(run_root / "work")
    run.params_path = str(run_root / "params.generated.yaml")
    run.command = build_nextflow_command(run, resume=resumed_from is not None)

    for name, value in payload.params.items():
        db.add(RunParameter(run_id=run.id, name=name, value=value, source="user"))

    db.add(
        AuditEvent(
            user_id=current_user.id,
            run_id=run.id,
            action="run.resume" if resumed_from else "run.create",
            entity_type="run",
            entity_id=run.id,
            payload={"pipeline_version_id": version.id, "profile": str(payload.profile)},
        )
    )
    db.commit()
    db.refresh(run)
    return run


@router.post("", response_model=RunRead, status_code=status.HTTP_201_CREATED)
def create_run(
    payload: RunCreate,
    background_tasks: BackgroundTasks,
    db: DbSession,
    current_user: CurrentUser,
) -> Run:
    run = create_run_model(db, payload, current_user)
    background_tasks.add_task(runner().start, run.id, False)
    return run


@router.get("", response_model=list[RunRead])
def list_runs(
    db: DbSession,
    current_user: CurrentUser,
) -> list[Run]:
    query = select(Run).order_by(Run.created_at.desc())
    if current_user.role != "admin":
        query = query.where(Run.user_id == current_user.id)
    return list(db.scalars(query))


@router.get("/{run_id}", response_model=RunRead)
def get_run(
    run_id: str,
    db: DbSession,
    current_user: CurrentUser,
) -> Run:
    run = db.get(Run, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    if current_user.role != "admin" and run.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    return run


@router.post("/{run_id}/resume", response_model=RunRead, status_code=status.HTTP_201_CREATED)
def resume_run(
    run_id: str,
    payload: RunResumeRequest,
    background_tasks: BackgroundTasks,
    db: DbSession,
    current_user: CurrentUser,
) -> Run:
    original = get_run(run_id, db, current_user)
    params = dict(original.inputs.get("params", {}))
    params.update(payload.params_override)
    resumed_payload = RunCreate(
        pipeline_id=original.pipeline_id,
        pipeline_version_id=original.pipeline_version_id,
        name=f"Resume {original.name or original.id}",
        profile=original.profile,
        executor=original.executor,
        params=params,
        input_paths=original.inputs.get("input_paths", {}),
    )
    resumed = create_run_model(db, resumed_payload, current_user, resumed_from=original)
    background_tasks.add_task(runner().start, resumed.id, True)
    return resumed


@router.get("/{run_id}/tasks", response_model=list[RunTaskRead])
def list_tasks(
    run_id: str,
    db: DbSession,
    current_user: CurrentUser,
) -> list[RunTask]:
    get_run(run_id, db, current_user)
    return list(db.scalars(select(RunTask).where(RunTask.run_id == run_id).order_by(RunTask.name)))


@router.get("/{run_id}/artifacts", response_model=list[ArtifactRead])
def list_artifacts(
    run_id: str,
    db: DbSession,
    current_user: CurrentUser,
) -> list[RunArtifact]:
    get_run(run_id, db, current_user)
    return list(
        db.scalars(
            select(RunArtifact).where(RunArtifact.run_id == run_id).order_by(RunArtifact.label)
        )
    )


@router.get("/{run_id}/logs/{log_type}", response_model=LogRead)
def get_log(
    run_id: str,
    log_type: Literal["stdout", "stderr", "nextflow"],
    db: DbSession,
    current_user: CurrentUser,
) -> LogRead:
    run = get_run(run_id, db, current_user)
    base = Path(run.output_dir).parent
    filenames = {
        "stdout": "stdout.log",
        "stderr": "stderr.log",
        "nextflow": ".nextflow.log",
    }
    path = base / filenames[log_type]
    content = path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""
    return LogRead(run_id=run.id, log_type=log_type, content=content)
