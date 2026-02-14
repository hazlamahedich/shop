"""add_business_hours_config

Revision ID: d8b872fa2427
Revises: 018_create_budget_alerts_table
Create Date: 2026-02-14 09:30:17.146400

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "d8b872fa2427"
down_revision: Union[str, None] = "018_create_budget_alerts_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "merchants",
        sa.Column("business_hours_config", postgresql.JSONB(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("merchants", "business_hours_config")
