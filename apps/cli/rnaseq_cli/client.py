from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import httpx

CONFIG_PATH = Path.home() / ".rnaseq-control-plane" / "config.json"


def api_url() -> str:
    return os.getenv("RNASEQ_API_URL", "http://localhost:8000").rstrip("/")


def load_config() -> dict[str, Any]:
    if not CONFIG_PATH.is_file():
        return {}
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def save_config(config: dict[str, Any]) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(config, indent=2), encoding="utf-8")


def token() -> str | None:
    return os.getenv("RNASEQ_TOKEN") or load_config().get("token")


def headers() -> dict[str, str]:
    current = token()
    return {"Authorization": f"Bearer {current}"} if current else {}


def request(method: str, path: str, **kwargs: Any) -> Any:
    url = f"{api_url()}{path}"
    with httpx.Client(timeout=30) as client:
        response = client.request(method, url, headers=headers(), **kwargs)
    if response.status_code >= 400:
        detail = response.text
        try:
            detail = response.json().get("detail", detail)
        except ValueError:
            pass
        raise RuntimeError(f"{response.status_code} {detail}")
    if not response.content:
        return None
    return response.json()

