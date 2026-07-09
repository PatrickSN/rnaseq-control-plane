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

