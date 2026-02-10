"""Add business info fields to merchants table.

Story 1.11: Business Info & FAQ Configuration

Revision ID: 012_add_business_info_fields
Revises: 011_add_bot_personality_configuration
Create Date: 2026-02-10

Adds:
- business_name VARCHAR(100) - Business name
- business_description TEXT - Business description (max 500 chars with constraint)
- business_hours VARCHAR(200) - Business hours
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "012_add_business_info_fields"
down_revision = "011_add_bot_personality_configuration"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add business info columns to merchants table."""

    # Add business_name column (max 100 chars)
    op.add_column(
        "merchants",
        sa.Column(
            "business_name",
            sa.String(100),
            nullable=True,
        ),
    )

    # Add business_description column (TEXT with length constraint)
    op.add_column(
        "merchants",
        sa.Column("business_description", sa.Text(), nullable=True),
    )

    # Add length constraint for business_description (max 500 chars)
    op.execute(
        """
        ALTER TABLE merchants
        ADD CONSTRAINT merchants_business_description_length
        CHECK (LENGTH(business_description) <= 500)
        """
    )

    # Add business_hours column (max 200 chars)
    op.add_column(
        "merchants",
        sa.Column(
            "business_hours",
            sa.String(200),
            nullable=True,
        ),
    )

    # Create index on business_name for efficient lookups
    op.create_index(
        "ix_merchants_business_name",
        "merchants",
        ["business_name"],
    )


def downgrade() -> None:
    """Remove business info columns from merchants table."""

    # Drop index
    op.drop_index("ix_merchants_business_name", table_name="merchants")

    # Drop constraint
    op.execute(
        """
        ALTER TABLE merchants
        DROP CONSTRAINT IF EXISTS merchants_business_description_length
        """
    )

    # Drop columns
    op.drop_column("merchants", "business_hours")
    op.drop_column("merchants", "business_description")
    op.drop_column("merchants", "business_name")
