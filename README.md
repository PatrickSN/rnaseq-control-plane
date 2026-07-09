# rnaseq-control-plane

Web + CLI control plane for running, monitoring, and exploring RNA-Seq Nextflow
pipelines without modifying the scientific pipeline repositories.

Supported pipeline targets in this MVP:

- `~/pipelines/soja-iac`
- `~/pipelines/RNA-Seq-Arabidopsis`

## Monorepo layout

```text
apps/api              FastAPI API, SQLAlchemy models, runner, parser
apps/web              Next.js + TypeScript UI
apps/cli              Typer CLI
packages/contracts    Shared Pydantic schemas and TypeScript interfaces
infra/docker          Optional Docker Compose stack for future/dev use
storage               Repository placeholder only; server data belongs in DATA_ROOT
docs                  Architecture and roadmap
```

## Target environment

The project is developed and executed on a Linux server with micromamba. The
Python backend, CLI, runner, tests, and Node.js build tools should run inside
the `rnaseq-control` environment. Do not create a local `.venv` as the default
workflow and do not install project dependencies globally.

Expected server directories:

```bash
PROJECT_ROOT=~/projetos/rnaseq-control-plane
DATA_ROOT=~/dados/rnaseq-control
PIPELINES_ROOT=~/pipelines
RUNS_ROOT=~/dados/rnaseq-control/runs
ARTIFACTS_ROOT=~/dados/rnaseq-control/artifacts
REFERENCES_ROOT=~/dados/rnaseq-control/references
```

Keep the control-plane dependencies separate from heavy scientific pipeline
environments such as `envs/rnaseq-tools.yml` and `envs/r-analysis.yml`.

## Environment setup

```bash
cd ~/projetos/rnaseq-control-plane
micromamba create -f environment.yml
micromamba activate rnaseq-control
pip install -e ./packages/contracts -e './apps/api[dev]' -e ./apps/cli
npm install
cp .env.example .env
```

Edit `.env` for the real server hostname, PostgreSQL credentials, secrets, and
pipeline/data directories before starting services. The API and Alembic load the
project-root `.env` without overriding variables already exported by the shell.

Check the runtime tools:

```bash
micromamba run -n rnaseq-control python --version
micromamba run -n rnaseq-control nextflow -version
micromamba run -n rnaseq-control node --version
```

## Database

Create the PostgreSQL database and user on the server, then set
`RNASEQ_DATABASE_URL` in `.env`.

Run migrations from the API directory:

```bash
cd ~/projetos/rnaseq-control-plane/apps/api
micromamba run -n rnaseq-control alembic upgrade head
```

Default development login after startup seed:

- email: `admin@example.com`
- password: value from `RNASEQ_ADMIN_PASSWORD`

## API

Start the API on all server interfaces so it can be reached remotely:

```bash
micromamba activate rnaseq-control
cd ~/projetos/rnaseq-control-plane/apps/api
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

FastAPI serves OpenAPI at `http://<server-host>:8000/openapi.json`. To export a
copy into contracts:

```bash
cd ~/projetos/rnaseq-control-plane
micromamba run -n rnaseq-control python apps/api/scripts/export_openapi.py
```

## Web

If the API and Web UI use the same hostname, the browser client infers
`http://<current-host>:8000`. Export `NEXT_PUBLIC_API_URL` before starting the
Web UI only when the API is served from a different hostname or port.

```bash
cd ~/projetos/rnaseq-control-plane
micromamba run -n rnaseq-control npm run web:dev
```

Open `http://<server-host>:3000/login`.

## CLI

```bash
cd ~/projetos/rnaseq-control-plane
export RNASEQ_API_URL=http://<server-host>:8000
micromamba run -n rnaseq-control rnaseq auth login --email admin@example.com --password '<password>'
micromamba run -n rnaseq-control rnaseq pipelines list
micromamba run -n rnaseq-control rnaseq runs create --pipeline soja-iac --params-file ~/pipelines/soja-iac/params.yaml
micromamba run -n rnaseq-control rnaseq runs list --json
```

CLI commands are human-readable by default and support `--json` where automation
needs scriptable output.

## Runner

The real runner executes Nextflow with an argument list, not an interpolated
shell string. A run records the pipeline path and fingerprint, generated
parameters, profile, executor, command, work directory, output directory, logs,
Nextflow session ID, trace, reports, and indexed artifacts.

Real local Nextflow execution requires `RNASEQ_RUNNER_MODE=local`, Java,
Nextflow, and pipeline-specific environments available on the Linux server.
Use `RNASEQ_RUNNER_MODE=fake` for deterministic API/web/CLI validation without
running scientific tools.

## Docker Compose

Docker Compose files remain under `infra/docker` for optional development or
future packaging, but Docker is not required for the MVP server workflow.

## Quality checks

```bash
cd ~/projetos/rnaseq-control-plane
micromamba run -n rnaseq-control pytest
micromamba run -n rnaseq-control ruff check apps/api packages/contracts apps/cli
micromamba run -n rnaseq-control mypy apps/api packages/contracts apps/cli
micromamba run -n rnaseq-control npm run contracts:build
micromamba run -n rnaseq-control npm run typecheck
micromamba run -n rnaseq-control npm run web:build
```

Use fake-runner tests for product validation and run real Nextflow smoke checks
only on a server configured with the target pipelines and their scientific
environments.
