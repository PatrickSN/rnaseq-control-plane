# AGENTS.md

## Objective

Build and maintain a product layer for RNA-Seq Nextflow execution, monitoring, provenance, and artifact exploration for `soja-iac` and `RNA-Seq-Arabidopsis`.

## Operating principles

- Do not modify the scientific pipelines in the MVP.
- Treat pipeline directories as versioned external artifacts.
- Persist enough provenance to reproduce a run: pipeline path, fingerprint, params, profile, executor, command, work directory, output directory, logs, session ID, and artifacts.
- Keep `local` and `slurm` modeled, while only `local` execution is implemented in the MVP.
- Prefer typed contracts and explicit validation over implicit payload shapes.
- Keep comments sparse and focused on operational context.

## Main agent

The main agent coordinates changes across API, web, CLI, contracts, infra, tests, and docs. It should preserve the product boundary between control plane and scientific pipelines.

## Backend agent

Owns FastAPI routes, SQLAlchemy models, Alembic migrations, auth, audit events, runner orchestration, log capture, and parser indexing.

Acceptance checks:

- API returns stable Pydantic response models.
- `POST /api/runs` persists run, parameters, audit event, logs, tasks, and artifacts in fake-runner tests.
- Real runner failure preserves stdout, stderr, `.nextflow.log` where available.

## Frontend agent

Owns Next.js screens for login, pipelines, new-run wizard, and run detail. The UI must handle missing logs/artifacts without crashing.

## CLI agent

Owns Typer commands under `rnaseq`. CLI output should be scriptable with `--json` and human-readable by default.

## Bioinformatics agent

Owns pipeline metadata, params/artifact contracts, trace parsing, and species-specific assumptions. It must not rewrite `main.nf`, modules, R scripts, or pipeline configs without explicit approval.

## DevOps/QA agent

Owns Docker Compose, reproducible local setup, tests, and smoke validation boundaries. It should clearly separate fake-runner validation from real Nextflow validation.

