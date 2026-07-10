from __future__ import annotations

from sqlalchemy import select

from app.core.config import get_settings
from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.models.entities import Pipeline


def main() -> None:
    settings = get_settings()
    with SessionLocal() as db:
        init_db(db, settings)
        pipelines = list(db.scalars(select(Pipeline).order_by(Pipeline.slug)))

    print(f"Seeded {len(pipelines)} pipelines:")
    for pipeline in pipelines:
        print(f"- {pipeline.slug}: {pipeline.display_name}")


if __name__ == "__main__":
    main()

