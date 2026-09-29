"""initial agent tables

Revision ID: 0001_initial_agent_tables
Revises:
Create Date: 2026-09-28
"""

from typing import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial_agent_tables"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "conversations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "agent_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("conversation_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("conversation_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "tool_calls",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("agent_run_id", sa.Integer(), nullable=False),
        sa.Column("tool_name", sa.String(length=100), nullable=False),
        sa.Column("arguments", sa.JSON(), nullable=False),
        sa.Column("result", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["agent_run_id"], ["agent_runs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("tool_calls")
    op.drop_table("messages")
    op.drop_table("agent_runs")
    op.drop_table("conversations")
