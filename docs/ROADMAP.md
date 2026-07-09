# Roadmap

## MVP

- Monorepo scaffold with API, web, CLI, contracts, Docker Compose, tests, and docs.
- PostgreSQL-backed model for users, pipelines, versions, runs, parameters, tasks, artifacts, and audit events.
- Login/register/JWT auth with development admin seed.
- Local background runner that executes `nextflow run` and captures logs/provenance.
- Fake runner for deterministic development and tests.
- Parser for `nextflow_trace.txt`, Nextflow HTML reports, and essential result TSV artifacts.
- Pipeline catalog, new-run wizard, and run detail UI.
- CLI commands for auth, pipelines list, runs create/list/show/resume.

## v1

- Worker service for long-running jobs and process supervision.
- Run cancellation and retry policies.
- Samplesheet upload and validation.
- Result readers for DESeq2, enrichment, splicing, WGCNA, and integration tables.
- Role-based authorization on runs and pipeline management.
- More complete OpenAPI-generated TypeScript client.
- Real local-run smoke fixture on a machine with Nextflow and Conda/Mamba.

## v2

- Slurm submission strategy with scheduler-aware state tracking.
- Pipeline version publishing from Git tags or commit SHAs.
- Artifact browser with secure downloads.
- Run-to-run parameter and result comparison.
- Storage backends beyond local filesystem.
- Optional Apptainer/Singularity support for HPC environments.

