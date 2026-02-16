"""Create handoff_alerts table for handoff notifications.

Story 4-6: Handoff Notifications

Revision ID: 020_create_handoff_alerts_table
Revises: 019_add_handoff_fields
Create Date: 2026-02-14

Adds:
- handoff_alerts table with id, merchant_id, conversation_id, urgency_level,
  customer_name, customer_id, conversation_preview, wait_time_seconds,
  is_read, created_at
- Foreign key constraint to merchants table with CASCADE delete
- Foreign key constraint to conversations table with CASCADE delete
- Index on (merchant_id, is_read) for efficient queries
- Index on (merchant_id, created_at) for chronological queries
- Index on (conversation_id) for conversation-level queries
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "020_create_handoff_alerts_table"
down_revision: Union[str, None] = "019_add_handoff_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create handoff_alerts table and related constraints."""

    op.create_table(
        "handoff_alerts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "merchant_id",
            sa.Integer(),
            sa.ForeignKey("merchants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "conversation_id",
            sa.Integer(),
            sa.ForeignKey("conversations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "urgency_level",
            sa.String(10),
            nullable=False,
        ),
        sa.Column(
            "customer_name",
            sa.String(255),
            nullable=True,
        ),
        sa.Column(
            "customer_id",
            sa.String(100),
            nullable=True,
        ),
        sa.Column(
            "conversation_preview",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "wait_time_seconds",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "is_read",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )

    op.create_index(
        "ix_handoff_alerts_merchant_unread",
        "handoff_alerts",
        ["merchant_id", "is_read"],
    )

    op.create_index(
        "ix_handoff_alerts_merchant_created",
        "handoff_alerts",
        ["merchant_id", "created_at"],
    )

    op.create_index(
        "ix_handoff_alerts_conversation",
        "handoff_alerts",
        ["conversation_id"],
    )


def downgrade() -> None:
    """Remove handoff_alerts table and related constraints."""

    op.drop_index("ix_handoff_alerts_conversation", table_name="handoff_alerts")
    op.drop_index("ix_handoff_alerts_merchant_created", table_name="handoff_alerts")
    op.drop_index("ix_handoff_alerts_merchant_unread", table_name="handoff_alerts")
    op.drop_table("handoff_alerts")
