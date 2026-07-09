from __future__ import annotations

from typing import Annotated, TypeAlias

from fastapi import APIRouter, Depends
from rnaseq_contracts import PipelineRead
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.entities import Pipeline, User

router = APIRouter(prefix="/api/pipelines", tags=["pipelines"])
DbSession: TypeAlias = Annotated[Session, Depends(get_db)]
CurrentUser: TypeAlias = Annotated[User, Depends(get_current_user)]


@router.get("", response_model=list[PipelineRead])
def list_pipelines(
    db: DbSession,
    _: CurrentUser,
) -> list[Pipeline]:
    return list(
        db.scalars(
            select(Pipeline)
            .options(selectinload(Pipeline.versions))
            .where(Pipeline.is_active.is_(True))
            .order_by(Pipeline.display_name)
        )
    )
