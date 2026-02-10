"""Add bot personality configuration to merchants table.

Story 1.10: Bot Personality Configuration

Revision ID: 011_add_bot_personality_configuration
Revises: 010_create_sessions_table
Create Date: 2025-02-10

Adds:
- personality_type ENUM type ('friendly', 'professional', 'enthusiastic')
- personality column to merchants table (defaults to 'friendly')
- custom_greeting TEXT column for optional custom greeting messages
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "011_add_bot_personality_configuration"
down_revision = "010_create_sessions_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add personality configuration columns to merchants table."""

    # Create personality_type enum type
    personality_type_enum = sa.Enum(
        "friendly",
        "professional",
        "enthusiastic",
        name="personality_type",
    )
    personality_type_enum.create(op.get_bind(), checkfirst=True)

    # Add personality column to merchants table
    # Defaults to 'friendly' for new merchants
    op.add_column(
        "merchants",
        sa.Column(
            "personality",
            sa.Enum(
                "friendly",
                "professional",
                "enthusiastic",
                name="personality_type",
                create_type=False,  # Type already created above
            ),
            nullable=False,
            server_default="friendly",
        ),
    )

    # Add custom_greeting column for optional custom greeting
    op.add_column(
        "merchants",
        sa.Column("custom_greeting", sa.Text(), nullable=True),
    )

    # Create index on personality for efficient lookups
    op.create_index(
        "ix_merchants_personality",
        "merchants",
        ["personality"],
    )


def downgrade() -> None:
    """Remove personality configuration columns from merchants table."""

    # Drop index
    op.drop_index("ix_merchants_personality", table_name="merchants")

    # Drop columns
    op.drop_column("merchants", "custom_greeting")
    op.drop_column("merchants", "personality")

    # Drop enum type
    sa.Enum(name="personality_type").drop(op.get_bind(), checkfirst=True)
