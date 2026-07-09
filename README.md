# rnaseq-control-plane

Web + CLI control plane for running, monitoring, and exploring RNA-Seq Nextflow pipelines without modifying the scientific pipeline repositories.

Supported pipeline targets in this MVP:

- `../soja-iac`
- `../RNA-Seq-Arabidopsis`

## Monorepo layout

```text
apps/api              FastAPI API, SQLAlchemy models, runner, parser
apps/web              Next.js + TypeScript UI
apps/cli              Typer CLI
packages/contracts    Shared Pydantic schemas and TypeScript interfaces
infra/docker          Development Docker Compose
storage               Local run state and captured logs
docs                  Architecture and roadmap
```

## Development prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL 16 for normal development
- Docker Compose for the provided dev stack
- Nextflow, Java, and Conda/Mamba only when executing real pipelines with `RNASEQ_RUNNER_MODE=local`

The Docker Compose stack defaults to `RNASEQ_RUNNER_MODE=fake` so the API, web, auth, database, parser, and UI can be exercised without installing Nextflow inside the API container.

## API

```powershell
cd rnaseq-control-plane
py -3 -m venv .venv
.\.venv\Scripts\pip install -e .\packages\contracts -e .\apps\api[dev]
$env:RNASEQ_RUNNER_MODE="fake"
.\.venv\Scripts\uvicorn app.main:app --app-dir apps/api --reload
```

Default development login:

- email: `admin@example.com`
- password: `admin123`

FastAPI serves OpenAPI at `http://localhost:8000/openapi.json`. To export a copy into contracts:

```powershell
$env:PYTHONPATH="apps/api;packages/contracts"
.\.venv\Scripts\python apps/api/scripts/export_openapi.py
```

## Web

```powershell
cd rnaseq-control-plane
npm install
npm run web:dev
```

Open `http://localhost:3000/login`.

## CLI

```powershell
cd rnaseq-control-plane
.\.venv\Scripts\pip install -e .\packages\contracts -e .\apps\cli
$env:RNASEQ_API_URL="http://localhost:8000"
rnaseq auth login --email admin@example.com --password admin123
rnaseq pipelines list
rnaseq runs create --pipeline soja-iac --params-file ..\soja-iac\params.yaml
rnaseq runs list
```

## Docker Compose

```powershell
cd rnaseq-control-plane\infra\docker
docker compose up --build
```

Services:

- API: `http://localhost:8000`
- Web: `http://localhost:3000`
- PostgreSQL: `localhost:5432`

To attempt real local Nextflow execution instead of fake runs, set `RNASEQ_RUNNER_MODE=local` and ensure the API runtime can see `nextflow`, Java, Conda/Mamba environments, and the pipeline paths. The scientific pipelines are mounted read-only by Compose and are not modified by this product.

## Quality checks

```powershell
cd rnaseq-control-plane
$env:PYTHONPATH="apps/api;packages/contracts"
pytest
ruff check apps/api packages/contracts apps/cli
mypy apps/api packages/contracts apps/cli
npm run contracts:build
npm run typecheck
npm run web:build
```

This environment may not have Docker or Nextflow installed. In that case, use `RNASEQ_RUNNER_MODE=fake` for API integration tests and run real pipeline smoke checks on a host configured for Nextflow.

