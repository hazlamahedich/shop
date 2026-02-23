"""Add handoff resolution fields for auto-close timer.

Revision ID: 029_resolution_fields
Revises: 028_is_offline_handoff
Create Date: 2026-02-23

Story: Handoff Resolution Flow Enhancement
- Adds fields for tracking handoff resolution
- Supports 24-hour auto-close timer
- Supports 7-day reopen window
- Supports customer satisfaction tracking
"""

from alembic import op
import sqlalchemy as sa

revision = "029_resolution_fields"
down_revision = "028_is_offline_handoff"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add resolution tracking columns to conversations
    op.add_column(
        "conversations",
        sa.Column("handoff_resolved_at", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "conversations",
        sa.Column("handoff_resolution_type", sa.String(20), nullable=True),
    )
    op.add_column(
        "conversations",
        sa.Column("handoff_reopened_count", sa.Integer(), server_default="0", nullable=True),
    )
    op.add_column(
        "conversations",
        sa.Column("last_customer_message_at", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "conversations",
        sa.Column("last_merchant_message_at", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "conversations",
        sa.Column("customer_satisfied", sa.Boolean(), nullable=True),
    )

    # Add indexes for efficient querying
    op.create_index(
        "ix_conversations_handoff_resolved_at",
        "conversations",
        ["handoff_resolved_at"],
    )
    op.create_index(
        "ix_conversations_last_customer_message_at",
        "conversations",
        ["last_customer_message_at"],
    )

    # Add new values to handoff_status enum
    op.execute("""
        ALTER TYPE handoff_status ADD VALUE IF NOT EXISTS 'reopened';
    """)
    op.execute("""
        ALTER TYPE handoff_status ADD VALUE IF NOT EXISTS 'escalated';
    """)

    # Add resolution fields to handoff_alerts
    op.add_column(
        "handoff_alerts",
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "handoff_alerts",
        sa.Column("resolution_type", sa.String(20), nullable=True),
    )
    op.add_column(
        "handoff_alerts",
        sa.Column("reopen_count", sa.Integer(), server_default="0", nullable=True),
    )

    op.create_index(
        "ix_handoff_alerts_resolved_at",
        "handoff_alerts",
        ["resolved_at"],
    )


def downgrade() -> None:
    # Remove handoff_alerts columns
    op.drop_index("ix_handoff_alerts_resolved_at", "handoff_alerts")
    op.drop_column("handoff_alerts", "reopen_count")
    op.drop_column("handoff_alerts", "resolution_type")
    op.drop_column("handoff_alerts", "resolved_at")

    # Note: Cannot remove enum values in PostgreSQL
    # They would need to be recreated, which is risky in production

    # Remove conversations columns
    op.drop_index("ix_conversations_last_customer_message_at", "conversations")
    op.drop_index("ix_conversations_handoff_resolved_at", "conversations")
    op.drop_column("conversations", "customer_satisfied")
    op.drop_column("conversations", "last_merchant_message_at")
    op.drop_column("conversations", "last_customer_message_at")
    op.drop_column("conversations", "handoff_reopened_count")
    op.drop_column("conversations", "handoff_resolution_type")
    op.drop_column("conversations", "handoff_resolved_at")
