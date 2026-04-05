"""add unique constraint on conversation_turns(conversation_id, turn_number)

Revision ID: 034_add_uq_conversation_turns_conv_turn
Revises: 033_add_dismissed_products
Create Date: 2026-04-05 19:23:00.000000

Story 11-12a: Conversation Turn Tracking Pipeline
Adds unique constraint to prevent duplicate turn records per conversation.
"""

from typing import Sequence, Union

from alembic import op

revision: str = "034_add_uq_conversation_turns_conv_turn"
down_revision: Union[str, None] = "033_add_dismissed_products"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_conversation_turns_conv_turn",
        "conversation_turns",
        ["conversation_id", "turn_number"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_conversation_turns_conv_turn",
        "conversation_turns",
        type_="unique",
    )
