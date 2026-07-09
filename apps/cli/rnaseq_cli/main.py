from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Any, cast

import typer
import yaml
from rich.console import Console
from rich.table import Table

from rnaseq_cli.client import request, save_config

app = typer.Typer(help="Control RNA-Seq Nextflow runs.")
auth_app = typer.Typer(help="Authentication commands.")
pipelines_app = typer.Typer(help="Pipeline commands.")
runs_app = typer.Typer(help="Run commands.")
app.add_typer(auth_app, name="auth")
app.add_typer(pipelines_app, name="pipelines")
app.add_typer(runs_app, name="runs")
console = Console()


def emit_json(payload: Any) -> None:
    console.print(json.dumps(payload, indent=2, ensure_ascii=False))


@auth_app.command("login")
def auth_login(
    email: Annotated[str, typer.Option()],
    password: Annotated[str, typer.Option(hide_input=True)],
) -> None:
    token = cast(
        dict[str, Any],
        request("POST", "/api/auth/login", json={"email": email, "password": password}),
    )
    save_config({"token": token["access_token"]})
    console.print("Authenticated.")


@pipelines_app.command("list")
def pipelines_list(json_output: Annotated[bool, typer.Option("--json")] = False) -> None:
    pipelines = cast(list[dict[str, Any]], request("GET", "/api/pipelines"))
    if json_output:
        emit_json(pipelines)
        return
    table = Table("Slug", "Name", "Organism", "Default version")
    for pipeline in pipelines:
        default = next((v for v in pipeline["versions"] if v["is_default"]), None)
        table.add_row(
            pipeline["slug"],
            pipeline["display_name"],
            pipeline["organism"],
            default["version"] if default else "-",
        )
    console.print(table)


def read_yaml(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    return loaded if isinstance(loaded, dict) else {}


def resolve_pipeline(identifier: str) -> dict[str, Any]:
    pipelines = cast(list[dict[str, Any]], request("GET", "/api/pipelines"))
    for pipeline in pipelines:
        if pipeline["id"] == identifier or pipeline["slug"] == identifier:
            return pipeline
    raise RuntimeError(f"Pipeline not found: {identifier}")


@runs_app.command("create")
def runs_create(
    pipeline: Annotated[str, typer.Option(help="Pipeline slug or UUID.")],
    params_file: Annotated[
        Path | None,
        typer.Option("--params-file", exists=True, readable=True),
    ] = None,
    name: Annotated[str | None, typer.Option()] = None,
    profile: Annotated[str, typer.Option()] = "local",
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    selected = resolve_pipeline(pipeline)
    payload = {
        "pipeline_id": selected["id"],
        "name": name,
        "profile": profile,
        "executor": "local",
        "params": read_yaml(params_file),
        "input_paths": {},
    }
    run = cast(dict[str, Any], request("POST", "/api/runs", json=payload))
    if json_output:
        emit_json(run)
    else:
        console.print(f"Run created: {run['id']} status={run['status']}")


@runs_app.command("list")
def runs_list(json_output: Annotated[bool, typer.Option("--json")] = False) -> None:
    runs = cast(list[dict[str, Any]], request("GET", "/api/runs"))
    if json_output:
        emit_json(runs)
        return
    table = Table("ID", "Name", "Status", "Profile", "Session")
    for run in runs:
        table.add_row(
            run["id"],
            run["name"] or "-",
            run["status"],
            run["profile"],
            run["session_id"] or "-",
        )
    console.print(table)


@runs_app.command("show")
def runs_show(
    run_id: str,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    run = cast(dict[str, Any], request("GET", f"/api/runs/{run_id}"))
    if json_output:
        emit_json(run)
        return
    console.print(f"[bold]{run['id']}[/bold]")
    console.print(f"status: {run['status']}")
    console.print(f"pipeline: {run['pipeline_id']}")
    console.print(f"session: {run['session_id'] or '-'}")
    console.print(f"output: {run['output_dir']}")


@runs_app.command("resume")
def runs_resume(
    run_id: str,
    params_file: Annotated[
        Path | None,
        typer.Option("--params-file", exists=True, readable=True),
    ] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    run = cast(
        dict[str, Any],
        request(
            "POST",
            f"/api/runs/{run_id}/resume",
            json={"params_override": read_yaml(params_file)},
        ),
    )
    if json_output:
        emit_json(run)
    else:
        console.print(f"Resumed as: {run['id']} status={run['status']}")
