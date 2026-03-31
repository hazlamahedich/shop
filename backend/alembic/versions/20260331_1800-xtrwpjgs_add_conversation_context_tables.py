"""add_conversation_context_tables

Revision ID: xtrwpjgs
Revises: dfd9eb30064f
Create Date: 2026-03-31 18:00:00.000000

Story 11-1: Conversation Context Memory
Add conversation_context and conversation_turns tables for
tracking conversation context with mode-aware fields and 24h expiration.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "xtrwpjgs"
down_revision: Union[str, None] = "dfd9eb30064f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create conversation_context and conversation_turns tables."""

    # Create conversation_mode enum type
    conversation_mode_enum = postgresql.ENUM(
        "ecommerce",
        "general",
        name="conversation_mode",
        create_type=True,
    )

    # Create conversation_context table
    op.create_table(
        "conversation_context",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "conversation_id",
            sa.Integer(),
            sa.ForeignKey("conversations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "merchant_id",
            sa.Integer(),
            sa.ForeignKey("merchants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("mode", conversation_mode_enum, nullable=False),
        sa.Column("context_data", postgresql.JSONB(), nullable=False),
        # E-commerce fields
        sa.Column("viewed_products", postgresql.ARRAY(sa.Integer()), nullable=True),
        sa.Column("cart_items", postgresql.ARRAY(sa.Integer()), nullable=True),
        sa.Column("constraints", postgresql.JSONB(), nullable=True),
        sa.Column("search_history", postgresql.ARRAY(sa.String()), nullable=True),
        # General mode fields
        sa.Column("topics_discussed", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column(
            "documents_referenced", postgresql.ARRAY(sa.Integer()), nullable=True
        ),
        sa.Column("support_issues", postgresql.JSONB(), nullable=True),
        sa.Column("escalation_status", sa.String(length=50), nullable=True),
        # Universal fields
        sa.Column("preferences", postgresql.JSONB(), nullable=True),
        sa.Column("turn_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_summarized_at", sa.DateTime(), nullable=True),
        sa.Column(
            "expires_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("NOW() + INTERVAL '24 hours'"),
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for performance
    op.create_index(
        "ix_conversation_context_conversation",
        "conversation_context",
        ["conversation_id"],
    )
    op.create_index("ix_conversation_context_mode", "conversation_context", ["mode"])
    op.create_index(
        "ix_conversation_context_expires", "conversation_context", ["expires_at"]
    )

    # Create conversation_turns table
    op.create_table(
        "conversation_turns",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "conversation_id",
            sa.Integer(),
            sa.ForeignKey("conversations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("turn_number", sa.Integer(), nullable=False),
        sa.Column("user_message", sa.String(), nullable=True),
        sa.Column("bot_response", sa.String(), nullable=True),
        sa.Column("intent_detected", sa.String(length=100), nullable=True),
        sa.Column("context_snapshot", postgresql.JSONB(), nullable=True),
        sa.Column("sentiment", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create composite index for turn lookup
    op.create_index(
        "ix_conversation_turns_conversation",
        "conversation_turns",
        ["conversation_id", "turn_number"],
    )


def downgrade() -> None:
    """Drop conversation_context and conversation_turns tables."""

    op.drop_index(
        "ix_conversation_turns_conversation", table_name="conversation_turns"
    )
    op.drop_table("conversation_turns")

    op.drop_index("ix_conversation_context_expires", table_name="conversation_context")
    op.drop_index("ix_conversation_context_mode", table_name="conversation_context")
    op.drop_index(
        "ix_conversation_context_conversation", table_name="conversation_context"
    )
    op.drop_table("conversation_context")

    # Drop enum type
    op.execute("DROP TYPE IF EXISTS conversation_mode")
