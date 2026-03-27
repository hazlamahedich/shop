"""add_merchant_id_to_feedback

Revision ID: dfd9eb30064f
Revises: bcdcbceb4989
Create Date: 2026-03-27 23:04:23.440440

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "dfd9eb30064f"
down_revision: Union[str, None] = "bcdcbceb4989"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "message_feedback",
        sa.Column("merchant_id", sa.Integer(), nullable=True),
    )
    op.create_index(
        "ix_message_feedback_merchant_id",
        "message_feedback",
        ["merchant_id"],
    )
    op.create_foreign_key(
        "fk_message_feedback_merchant_id",
        "message_feedback",
        "merchants",
        ["merchant_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_message_feedback_merchant_id",
        "message_feedback",
        type_="foreignkey",
    )
    op.drop_index(
        "ix_message_feedback_merchant_id",
        table_name="message_feedback",
    )
    op.drop_column("message_feedback", "merchant_id")
