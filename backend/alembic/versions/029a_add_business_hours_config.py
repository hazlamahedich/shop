"""Add business_hours_config JSONB column to merchants table.

Revision ID: 029a_add_business_hours_config
Revises: 029_resolution_fields
Create Date: 2026-02-23

Adds:
- business_hours_config JSONB column to merchants table
"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

# revision identifiers, used by Alembic.
revision = "029a_add_business_hours_config"
down_revision = "029_resolution_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add business_hours_config JSONB column to merchants table."""
    op.add_column(
        "merchants",
        sa.Column(
            "business_hours_config",
            JSONB,
            nullable=True,
        ),
    )


def downgrade() -> None:
    """Remove business_hours_config column from merchants table."""
    op.drop_column("merchants", "business_hours_config")
