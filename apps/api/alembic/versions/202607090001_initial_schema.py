from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "202607090001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("hashed_password", sa.String(length=256), nullable=False),
        sa.Column("full_name", sa.String(length=160), nullable=True),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "pipelines",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.Column("display_name", sa.String(length=160), nullable=False),
        sa.Column("organism", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_pipelines_slug", "pipelines", ["slug"], unique=True)

    op.create_table(
        "pipeline_versions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "pipeline_id",
            sa.String(length=36),
            sa.ForeignKey("pipelines.id"),
            nullable=False,
        ),
        sa.Column("version", sa.String(length=80), nullable=False),
        sa.Column("pipeline_path", sa.Text(), nullable=False),
        sa.Column("main_script", sa.String(length=120), nullable=False),
        sa.Column("params_template_path", sa.String(length=160), nullable=False),
        sa.Column("default_profile", sa.String(length=32), nullable=False),
        sa.Column("supported_profiles", sa.JSON(), nullable=False),
        sa.Column("fingerprint", sa.String(length=64), nullable=True),
        sa.Column("is_default", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("pipeline_id", "version", name="uq_pipeline_version"),
    )

    op.create_table(
        "runs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "pipeline_id",
            sa.String(length=36),
            sa.ForeignKey("pipelines.id"),
            nullable=False,
        ),
        sa.Column(
            "pipeline_version_id",
            sa.String(length=36),
            sa.ForeignKey("pipeline_versions.id"),
            nullable=False,
        ),
        sa.Column(
            "resumed_from_run_id",
            sa.String(length=36),
            sa.ForeignKey("runs.id"),
            nullable=True,
        ),
        sa.Column("name", sa.String(length=160), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("profile", sa.String(length=32), nullable=False),
        sa.Column("executor", sa.String(length=32), nullable=False),
        sa.Column("pipeline_path", sa.Text(), nullable=False),
        sa.Column("pipeline_fingerprint", sa.String(length=64), nullable=True),
        sa.Column("work_dir", sa.Text(), nullable=False),
        sa.Column("output_dir", sa.Text(), nullable=False),
        sa.Column("params_path", sa.Text(), nullable=False),
        sa.Column("command", sa.JSON(), nullable=False),
        sa.Column("session_id", sa.String(length=120), nullable=True),
        sa.Column("exit_code", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("environment", sa.JSON(), nullable=False),
        sa.Column("inputs", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_runs_status", "runs", ["status"])
    op.create_index("ix_runs_session_id", "runs", ["session_id"])

    op.create_table(
        "run_parameters",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("run_id", sa.String(length=36), sa.ForeignKey("runs.id"), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("value", sa.JSON(), nullable=True),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "run_tasks",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("run_id", sa.String(length=36), sa.ForeignKey("runs.id"), nullable=False),
        sa.Column("task_id", sa.String(length=80), nullable=True),
        sa.Column("hash", sa.String(length=80), nullable=True),
        sa.Column("name", sa.String(length=260), nullable=False),
        sa.Column("process", sa.String(length=160), nullable=True),
        sa.Column("status", sa.String(length=80), nullable=True),
        sa.Column("exit_code", sa.Integer(), nullable=True),
        sa.Column("submit", sa.String(length=80), nullable=True),
        sa.Column("start", sa.String(length=80), nullable=True),
        sa.Column("complete", sa.String(length=80), nullable=True),
        sa.Column("duration", sa.String(length=80), nullable=True),
        sa.Column("realtime", sa.String(length=80), nullable=True),
        sa.Column("cpu_percent", sa.String(length=80), nullable=True),
        sa.Column("memory", sa.String(length=80), nullable=True),
        sa.Column("raw", sa.JSON(), nullable=False),
    )
    op.create_index("ix_run_tasks_run_id", "run_tasks", ["run_id"])

    op.create_table(
        "run_artifacts",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("run_id", sa.String(length=36), sa.ForeignKey("runs.id"), nullable=False),
        sa.Column("kind", sa.String(length=80), nullable=False),
        sa.Column("label", sa.String(length=160), nullable=False),
        sa.Column("path", sa.Text(), nullable=False),
        sa.Column("relative_path", sa.Text(), nullable=False),
        sa.Column("mime_type", sa.String(length=160), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=True),
        sa.Column("sha256", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_run_artifacts_run_id", "run_artifacts", ["run_id"])

    op.create_table(
        "audit_events",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("run_id", sa.String(length=36), sa.ForeignKey("runs.id"), nullable=True),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("entity_type", sa.String(length=80), nullable=False),
        sa.Column("entity_id", sa.String(length=80), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("audit_events")
    op.drop_index("ix_run_artifacts_run_id", table_name="run_artifacts")
    op.drop_table("run_artifacts")
    op.drop_index("ix_run_tasks_run_id", table_name="run_tasks")
    op.drop_table("run_tasks")
    op.drop_table("run_parameters")
    op.drop_index("ix_runs_session_id", table_name="runs")
    op.drop_index("ix_runs_status", table_name="runs")
    op.drop_table("runs")
    op.drop_table("pipeline_versions")
    op.drop_index("ix_pipelines_slug", table_name="pipelines")
    op.drop_table("pipelines")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
