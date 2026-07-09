from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, cast

import httpx

CONFIG_PATH = Path.home() / ".rnaseq-control-plane" / "config.json"


def api_url() -> str:
    configured = os.getenv("RNASEQ_API_URL")
    if not configured:
        raise RuntimeError("Set RNASEQ_API_URL, for example http://<server-host>:8000")
    return configured.rstrip("/")


def load_config() -> dict[str, Any]:
    if not CONFIG_PATH.is_file():
        return {}
    return cast(dict[str, Any], json.loads(CONFIG_PATH.read_text(encoding="utf-8")))


def save_config(config: dict[str, Any]) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(config, indent=2), encoding="utf-8")


def token() -> str | None:
    configured = os.getenv("RNASEQ_TOKEN")
    if configured:
        return configured
    saved = load_config().get("token")
    return saved if isinstance(saved, str) else None


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
