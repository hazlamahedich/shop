"""remove_platform_column

Revision ID: 9580e911f8fb
Revises: 46d19402406c
Create Date: 2026-03-26 21:16:09.943156

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9580e911f8fb'
down_revision: Union[str, None] = '46d19402406c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
