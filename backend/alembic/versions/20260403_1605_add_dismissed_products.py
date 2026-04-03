"""add dismissed_products to conversation_context

Revision ID: 033_add_dismissed_products
Revises: 032_add_password_reset_tokens
Create Date: 2026-04-03 16:05:00.000000

Story 11-6: Contextual Product Recommendations
Adds dismissed_products ARRAY(Integer) column to track products dismissed by user.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY

revision: str = "033_add_dismissed_products"
down_revision: Union[str, None] = "032_add_password_reset_tokens"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "conversation_context",
        sa.Column("dismissed_products", ARRAY(sa.Integer()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("conversation_context", "dismissed_products")
