# PROJECT_MEMORY.md

## Runtime target

This project is not meant to be executed on the developer's local workstation.
The software is developed and executed on a Linux server using micromamba.

Primary environment:

- Target operating system: Linux server.
- Environment manager: micromamba.
- Environment name: `rnaseq-control`.
- Suggested project directory: `~/projetos/Eulalio/rnaseq-control-plane`.
- Backend, CLI, runner, and Python services must run inside the micromamba environment `rnaseq-control`.

## Command policy

When creating Python/backend/CLI/runner commands, prefer:

```bash
micromamba activate rnaseq-control
```

For isolated commands, prefer:

```bash
micromamba run -n rnaseq-control <command>
```

Examples:

```bash
micromamba run -n rnaseq-control pytest
micromamba run -n rnaseq-control alembic upgrade head
micromamba run -n rnaseq-control uvicorn app.main:app --host 0.0.0.0 --port 8000
micromamba run -n rnaseq-control rnaseq pipelines list
```

## API operation notes

The FastAPI service should be started from the API app directory on the Linux
server:

```bash
cd ~/projetos/Eulalio/rnaseq-control-plane/apps/api
micromamba run -n rnaseq-control uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Expected unauthenticated endpoints:

- `GET /` returns service discovery links for health, docs, and OpenAPI.
- `GET /api/health` returns the API health payload.
- `GET /docs` opens FastAPI Swagger UI.

Protected API endpoints such as `GET /api/pipelines` and `GET /api/runs` require
a bearer token. Authenticate first:

```bash
curl -s -X POST http://127.0.0.1:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"<password>"}'
```

Then call protected endpoints with:

```bash
curl -s http://127.0.0.1:8000/api/pipelines \
  -H "Authorization: Bearer <access_token>"
```

The response `{"detail":"Missing bearer token"}` means the route is protected
and the request did not include the `Authorization` header.

## Pipeline registration

In the MVP, pipelines are not added from the web UI. The system seeds the two
known pipeline records from `apps/api/app/db/init_db.py`:

- `soja-iac`
- `RNA-Seq-Arabidopsis`

The seed uses `RNASEQ_PIPELINES_BASE_DIR` or `PIPELINES_ROOT` as the parent
directory. On the target server, this should normally be:

```bash
RNASEQ_PIPELINES_BASE_DIR=~/pipelines
```

The expected pipeline directories are:

```bash
~/pipelines/soja-iac
~/pipelines/RNA-Seq-Arabidopsis
```

If the Pipelines screen is empty after migrations, rerun the seed explicitly:

```bash
cd ~/projetos/Eulalio/rnaseq-control-plane/apps/api
micromamba run -n rnaseq-control python scripts/seed_initial_data.py
```

Then verify through the protected API:

```bash
curl -s http://127.0.0.1:8000/api/pipelines \
  -H "Authorization: Bearer <access_token>"
```

If this returns `[]`, check that the API process and the seed command are using
the same `RNASEQ_DATABASE_URL`.

## Negative assumptions

Agents and contributors must not assume:

- Windows, PowerShell, or paths such as `C:\` or `L:\`.
- A local workstation development runtime.
- A local `.venv` as the default workflow.
- Global system package installation.
- Docker as a mandatory initial requirement.

Docker Compose may exist for optional development or future packaging, but it is
not the baseline requirement for the MVP server workflow.

## Path policy

Use Linux server paths in docs, commands, and examples:

- Project: `~/projetos/Eulalio/rnaseq-control-plane`
- Data: `~/dados/rnaseq-control`
- Pipelines: `~/pipelines`
- Runs: `~/dados/rnaseq-control/runs`
- Artifacts: `~/dados/rnaseq-control/artifacts`
- References: `~/dados/rnaseq-control/references`

