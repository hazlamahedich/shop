"""add_onboarding_mode_to_merchant

Revision ID: 506c5de07ae8
Revises: b364ddab7279
Create Date: 2026-03-11 11:33:42.786707

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '506c5de07ae8'
down_revision: Union[str, None] = 'b364ddab7279'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
