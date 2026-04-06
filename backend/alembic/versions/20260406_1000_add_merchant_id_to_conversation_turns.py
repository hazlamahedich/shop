"""add merchant_id to conversation_turns

Revision ID: 035_merchant_id_conversation_turns
Revises: 034_add_uq_conversation_turns_conv_turn
Create Date: 2026-04-06 10:00:00.000000

Add merchant_id column to conversation_turns table for direct data isolation
queries without JOINing through conversations table.
Backpopulates merchant_id from conversations.merchant_id.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "035_merchant_id_conversation_turns"
down_revision: Union[str, None] = "034_add_uq_conversation_turns_conv_turn"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "conversation_turns",
        sa.Column("merchant_id", sa.Integer(), nullable=True),
    )

    op.execute(
        """
        UPDATE conversation_turns ct
        SET merchant_id = c.merchant_id
        FROM conversations c
        WHERE ct.conversation_id = c.id
        """
    )

    op.alter_column("conversation_turns", "merchant_id", nullable=False)

    op.create_foreign_key(
        "fk_conversation_turns_merchant_id",
        "conversation_turns",
        "merchants",
        ["merchant_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.create_index(
        "ix_conversation_turns_merchant",
        "conversation_turns",
        ["merchant_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_conversation_turns_merchant", table_name="conversation_turns")
    op.drop_constraint(
        "fk_conversation_turns_merchant_id",
        "conversation_turns",
        type_="foreignkey",
    )
    op.drop_column("conversation_turns", "merchant_id")
