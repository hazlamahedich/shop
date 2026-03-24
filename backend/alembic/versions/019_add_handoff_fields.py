"""Add handoff fields to conversations table.

Revision ID: 019_add_handoff_fields
Revises: d8b872fa2427
Create Date: 2026-02-14

Adds:
- handoff_status enum: none, pending, active, resolved (separate from status)
- handoff_triggered_at: timestamp when handoff was triggered
- handoff_reason: reason for handoff trigger
- consecutive_low_confidence_count: counter for confidence tracking
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "019_add_handoff_fields"
down_revision: str | None = "018_create_budget_alerts_table"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add handoff fields to conversations table."""
    handoff_status_enum = postgresql.ENUM(
        "none",
        "pending",
        "active",
        "resolved",
        name="handoff_status",
        create_type=True,
    )
    handoff_status_enum.create(op.get_bind())

    op.add_column(
        "conversations",
        sa.Column(
            "handoff_status",
            handoff_status_enum,
            nullable=True,
            server_default="none",
        ),
    )

    op.add_column(
        "conversations",
        sa.Column(
            "handoff_triggered_at",
            sa.DateTime(),
            nullable=True,
        ),
    )

    op.add_column(
        "conversations",
        sa.Column(
            "handoff_reason",
            sa.String(50),
            nullable=True,
        ),
    )

    op.add_column(
        "conversations",
        sa.Column(
            "consecutive_low_confidence_count",
            sa.Integer(),
            nullable=True,
            server_default="0",
        ),
    )

    op.create_index(
        "ix_conversations_handoff_status",
        "conversations",
        ["handoff_status"],
    )


def downgrade() -> None:
    """Remove handoff fields from conversations table."""
    op.drop_index("ix_conversations_handoff_status", table_name="conversations")

    op.drop_column("conversations", "consecutive_low_confidence_count")
    op.drop_column("conversations", "handoff_reason")
    op.drop_column("conversations", "handoff_triggered_at")
    op.drop_column("conversations", "handoff_status")

    handoff_status_enum = postgresql.ENUM(name="handoff_status")
    handoff_status_enum.drop(op.get_bind())
