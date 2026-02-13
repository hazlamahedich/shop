"""Create budget_alerts table for budget notifications.

Story 3.8: Budget Alert Notifications

Revision ID: 018_create_budget_alerts_table
Revises: 017_create_product_pins_table
Create Date: 2026-02-13

Adds:
- budget_alerts table with id, merchant_id, threshold, message, created_at, is_read
- Foreign key constraint to merchants table with CASCADE delete
- Index on (merchant_id, is_read) for efficient queries
- Index on (merchant_id, created_at) for chronological queries
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "018_create_budget_alerts_table"
down_revision = "017_create_product_pins_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create budget_alerts table and related constraints."""

    op.create_table(
        "budget_alerts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "merchant_id",
            sa.Integer(),
            sa.ForeignKey("merchants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "threshold",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "is_read",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
    )

    op.create_index(
        "ix_budget_alerts_merchant_unread",
        "budget_alerts",
        ["merchant_id", "is_read"],
    )

    op.create_index(
        "ix_budget_alerts_merchant_created",
        "budget_alerts",
        ["merchant_id", "created_at"],
    )


def downgrade() -> None:
    """Remove budget_alerts table and related constraints."""

    op.drop_index("ix_budget_alerts_merchant_created", table_name="budget_alerts")
    op.drop_index("ix_budget_alerts_merchant_unread", table_name="budget_alerts")
    op.drop_table("budget_alerts")
