"""Add use_custom_greeting field to merchants table.

Story 1.14: Smart Greeting Templates

Revision ID: 015_add_use_custom_greeting
Revises: 014_add_bot_name
Create Date: 2026-02-11

Adds:
- use_custom_greeting BOOLEAN - Flag to enable/disable custom greeting templates
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "015_add_use_custom_greeting"
down_revision = "014_add_bot_name"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add use_custom_greeting column to merchants table."""

    # Add use_custom_greeting column (boolean, defaults to False)
    op.add_column(
        "merchants",
        sa.Column(
            "use_custom_greeting",
            sa.Boolean(),
            nullable=False,
            server_default="False",
        ),
    )

    # Create index on use_custom_greeting for efficient lookups
    op.create_index(
        "ix_merchants_use_custom_greeting",
        "merchants",
        ["use_custom_greeting"],
    )


def downgrade() -> None:
    """Remove use_custom_greeting column from merchants table."""

    # Drop index
    op.drop_index("ix_merchants_use_custom_greeting", table_name="merchants")

    # Drop column
    op.drop_column("merchants", "use_custom_greeting")
