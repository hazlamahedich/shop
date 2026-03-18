"""add_icon_to_faqs

Revision ID: c724bdeb1564
Revises: 74f75004679c
Create Date: 2026-03-18 14:04:44.739062

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c724bdeb1564'
down_revision: Union[str, None] = '74f75004679c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
