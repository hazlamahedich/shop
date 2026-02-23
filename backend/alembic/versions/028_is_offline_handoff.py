"""Add is_offline column to handoff_alerts table.

Revision ID: 028_add_is_offline_to_handoff_alerts
Revises: 027_add_merchant_sender
Create Date: 2026-02-23

Story 4-12: Business Hours Handling Enhancement
- Adds is_offline flag to track after-hours handoffs
- Enables "After Hours" badge in HandoffQueue UI
- Allows filtering by offline status
"""

from alembic import op
import sqlalchemy as sa

revision = "028_is_offline_handoff"
down_revision = "add_merchant_sender"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "handoff_alerts",
        sa.Column("is_offline", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.create_index(
        "ix_handoff_alerts_is_offline",
        "handoff_alerts",
        ["is_offline"],
    )


def downgrade() -> None:
    op.drop_index("ix_handoff_alerts_is_offline", "handoff_alerts")
    op.drop_column("handoff_alerts", "is_offline")
