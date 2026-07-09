from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.entities import Pipeline, User
from rnaseq_contracts import PipelineRead

router = APIRouter(prefix="/api/pipelines", tags=["pipelines"])


@router.get("", response_model=list[PipelineRead])
def list_pipelines(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[Pipeline]:
    return list(
        db.scalars(
            select(Pipeline)
            .options(selectinload(Pipeline.versions))
            .where(Pipeline.is_active.is_(True))
            .order_by(Pipeline.display_name)
        )
    )

