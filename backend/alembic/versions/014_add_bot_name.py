"""Add bot_name field to merchants table.

Story 1.12: Bot Naming

Revision ID: 014_add_bot_name
Revises: 013_create_faqs_table
Create Date: 2026-02-11

Adds:
- bot_name VARCHAR(50) - Custom bot name that appears in all bot messages
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "014_add_bot_name"
down_revision = "013_create_faqs_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add bot_name column to merchants table."""

    # Add bot_name column (max 50 chars)
    op.add_column(
        "merchants",
        sa.Column(
            "bot_name",
            sa.String(50),
            nullable=True,
        ),
    )

    # Create index on bot_name for efficient lookups
    op.create_index(
        "ix_merchants_bot_name",
        "merchants",
        ["bot_name"],
    )


def downgrade() -> None:
    """Remove bot_name column from merchants table."""

    # Drop index
    op.drop_index("ix_merchants_bot_name", table_name="merchants")

    # Drop column
    op.drop_column("merchants", "bot_name")
