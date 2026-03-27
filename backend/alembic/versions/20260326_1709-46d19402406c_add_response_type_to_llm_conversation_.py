"""add_response_type_to_llm_conversation_costs

Revision ID: 46d19402406c
Revises: 1b8bcc56b7b4
Create Date: 2026-03-26 17:09:48.615734

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "46d19402406c"
down_revision: Union[str, None] = "1b8bcc56b7b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "llm_conversation_costs",
        sa.Column("response_type", sa.String(20), nullable=True, server_default="unknown"),
    )


def downgrade() -> None:
    op.drop_column("llm_conversation_costs", "response_type")
