# Architecture

## Summary

`rnaseq-control-plane` is a product layer around existing Nextflow RNA-Seq pipelines. The control plane persists users, pipeline metadata, runs, parameters, tasks, artifacts, logs, and audit events. It does not alter `soja-iac` or `RNA-Seq-Arabidopsis`.

## Components

- `apps/api`: FastAPI service with SQLAlchemy 2 models, Alembic migration, JWT auth, local background runner, and parser.
- `apps/web`: Next.js UI for login, pipeline catalog, run wizard, and run detail.
- `apps/cli`: Typer CLI for automation and shell/HPC workflows.
- `packages/contracts`: Pydantic schemas and TypeScript interfaces shared across surfaces.
- `infra/docker`: PostgreSQL + API + web development stack.

## Data model

The initial relational model contains:

- `User`: auth identity with role `admin` or `user`.
- `Pipeline`: logical pipeline such as `soja-iac`.
- `PipelineVersion`: versioned path/fingerprint/profile metadata.
- `Run`: execution state and provenance.
- `RunParameter`: serialized generated run parameters.
- `RunTask`: rows parsed from `nextflow_trace.txt`.
- `RunArtifact`: logs, Nextflow reports, trace, DAG, timeline, and essential result TSVs.
- `AuditEvent`: security and run lifecycle events.

## Run lifecycle

1. Authenticated user posts `RunCreate`.
2. API selects default `PipelineVersion`.
3. API creates a `Run` in `queued` state and stores user parameters.
4. Background runner writes `params.generated.yaml` with `outdir` forced to `storage/runs/{run_id}/results`.
5. Runner executes `nextflow run` with explicit report, trace, timeline, DAG, log, and work directory arguments.
6. Runner persists stdout, stderr, `.nextflow.log`, exit code, and detected session ID.
7. Parser indexes `nextflow_trace.txt` into `RunTask` and known outputs into `RunArtifact`.

## Execution modes

- `fake`: writes deterministic logs, trace, reports, and result TSVs for API/web/CLI development.
- `local`: invokes `nextflow` from the API runtime PATH.
- `slurm`: modeled in contracts and profiles, not implemented as a distinct runner in the MVP.

## Provenance

Every run stores:

- pipeline path and fingerprint;
- generated params path;
- original user params and input paths;
- executor/profile;
- exact command list;
- output and work directories;
- session ID when detected;
- logs and indexed artifacts.

## Boundaries

The control plane may read pipeline files and execute `main.nf`. It must not edit pipeline source, module code, R scripts, environment files, or sample sheets in this first delivery.

