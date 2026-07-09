from __future__ import annotations

from uuid import uuid4

import pytest
from pydantic import ValidationError
from rnaseq_contracts import ExecutorKind, ProfileName, RunCreate, RunStatus, UserCreate


def test_run_create_defaults() -> None:
    payload = RunCreate(pipeline_id=uuid4())
    assert payload.profile == ProfileName.LOCAL
    assert payload.executor == ExecutorKind.LOCAL
    assert payload.params == {}


def test_user_password_min_length() -> None:
    with pytest.raises(ValidationError):
        UserCreate(email="user@example.com", password="short")


def test_run_status_values_are_stable() -> None:
    assert {status.value for status in RunStatus} >= {"queued", "running", "succeeded", "failed"}

