"""Add widget_analytics_events table

Revision ID: widget_analytics_events
Revises: embedding_jsonb
Create Date: 2026-03-17

Story 9-10: Analytics & Performance Monitoring
- Creates widget_analytics_events table for storing widget engagement events
- Supports GDPR compliance with 30-day retention policy
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

revision: str = "widget_analytics_events"
down_revision: str | None = "embedding_jsonb"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "widget_analytics_events",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "merchant_id",
            sa.Integer(),
            sa.ForeignKey("merchants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "session_id",
            sa.String(100),
            nullable=False,
        ),
        sa.Column(
            "event_type",
            sa.String(50),
            nullable=False,
        ),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "metadata",
            JSONB,
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # Index for efficient querying by merchant and time range
    op.create_index(
        "ix_widget_analytics_events_merchant_timestamp",
        "widget_analytics_events",
        ["merchant_id", "timestamp"],
    )

    # Index for event type filtering
    op.create_index(
        "ix_widget_analytics_events_type",
        "widget_analytics_events",
        ["event_type"],
    )

    # Index for session-based queries
    op.create_index(
        "ix_widget_analytics_events_session",
        "widget_analytics_events",
        ["session_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_widget_analytics_events_session", table_name="widget_analytics_events")
    op.drop_index("ix_widget_analytics_events_type", table_name="widget_analytics_events")
    op.drop_index(
        "ix_widget_analytics_events_merchant_timestamp", table_name="widget_analytics_events"
    )
    op.drop_table("widget_analytics_events")
