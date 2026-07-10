from __future__ import annotations

import importlib
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select


def test_create_run_with_fake_runner(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RNASEQ_DATABASE_URL", f"sqlite+pysqlite:///{tmp_path / 'test.sqlite3'}")
    monkeypatch.setenv("RNASEQ_STORAGE_DIR", str(tmp_path / "storage"))
    monkeypatch.setenv("RNASEQ_PIPELINES_BASE_DIR", str(tmp_path / "pipelines"))
    monkeypatch.setenv("RNASEQ_RUNNER_MODE", "fake")
    monkeypatch.setenv("RNASEQ_ADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("RNASEQ_ADMIN_PASSWORD", "admin12345")

    config = importlib.import_module("app.core.config")
    config.get_settings.cache_clear()
    session_module = importlib.import_module("app.db.session")
    importlib.reload(session_module)
    main_module = importlib.import_module("app.main")
    importlib.reload(main_module)

    from app.db.session import SessionLocal
    from app.models.entities import AuditEvent, Run, RunArtifact, RunParameter, RunTask

    with TestClient(main_module.app) as client:
        root = client.get("/")
        assert root.status_code == 200
        assert root.json()["docs"] == "/docs"
        assert client.get("/favicon.ico").status_code == 204

        login = client.post(
            "/api/auth/login",
            json={"email": "admin@example.com", "password": "admin12345"},
        )
        assert login.status_code == 200
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        pipelines = client.get("/api/pipelines", headers=headers)
        assert pipelines.status_code == 200
        pipeline_id = pipelines.json()[0]["id"]

        response = client.post(
            "/api/runs",
            headers=headers,
            json={
                "pipeline_id": pipeline_id,
                "name": "integration fake run",
                "profile": "local",
                "executor": "local",
                "params": {"samplesheet": "samplesheet.csv"},
                "input_paths": {},
            },
        )
        assert response.status_code == 201
        run_id = response.json()["id"]

    with SessionLocal() as db:
        run = db.get(Run, run_id)
        assert run is not None
        assert run.status == "succeeded"
        assert db.scalar(select(RunParameter).where(RunParameter.run_id == run_id)) is not None
        assert db.scalar(select(RunTask).where(RunTask.run_id == run_id)) is not None
        assert db.scalar(select(RunArtifact).where(RunArtifact.run_id == run_id)) is not None
        assert db.scalar(select(AuditEvent).where(AuditEvent.run_id == run_id)) is not None
