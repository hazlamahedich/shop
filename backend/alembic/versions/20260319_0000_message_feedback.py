"""Add message_feedback table

Revision ID: message_feedback
Revises: c724bdeb1564
Create Date: 2026-03-19

Story 10-4: Feedback Rating Widget
- Creates message_feedback table for storing user feedback on bot messages
- Supports thumbs up/down ratings with optional comments
- One rating per message per session (upsert on re-click)
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "message_feedback"
down_revision: str | None = "c724bdeb1564"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE feedback_rating AS ENUM ('positive', 'negative');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.create_table(
        "message_feedback",
        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
        ),
        sa.Column(
            "message_id",
            sa.Integer(),
            sa.ForeignKey("messages.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "conversation_id",
            sa.Integer(),
            sa.ForeignKey("conversations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "rating",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "comment",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "session_id",
            sa.String(100),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.create_unique_constraint(
        "uq_message_feedback_message_session",
        "message_feedback",
        ["message_id", "session_id"],
    )

    op.create_index(
        "ix_message_feedback_message_id",
        "message_feedback",
        ["message_id"],
    )

    op.create_index(
        "ix_message_feedback_conversation_id",
        "message_feedback",
        ["conversation_id"],
    )

    op.create_index(
        "ix_message_feedback_session_id",
        "message_feedback",
        ["session_id"],
    )

    op.create_index(
        "ix_message_feedback_created",
        "message_feedback",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_message_feedback_created", table_name="message_feedback")
    op.drop_index("ix_message_feedback_session_id", table_name="message_feedback")
    op.drop_index("ix_message_feedback_conversation_id", table_name="message_feedback")
    op.drop_index("ix_message_feedback_message_id", table_name="message_feedback")
    op.drop_constraint("uq_message_feedback_message_session", "message_feedback")
    op.drop_table("message_feedback")
    op.execute("DROP TYPE IF EXISTS feedback_rating")
