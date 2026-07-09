from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, pipelines, runs
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.base import Base
from app.db.init_db import init_db
from app.db.session import SessionLocal, engine

configure_logging()

app = FastAPI(
    title="rnaseq-control-plane",
    version="0.1.0",
    description="Control plane for RNA-Seq Nextflow pipelines.",
)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    if settings.create_db_on_startup:
        Base.metadata.create_all(bind=engine)
        with SessionLocal() as db:
            init_db(db, settings)


@app.get("/api/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(auth.router)
app.include_router(pipelines.router)
app.include_router(runs.router)

