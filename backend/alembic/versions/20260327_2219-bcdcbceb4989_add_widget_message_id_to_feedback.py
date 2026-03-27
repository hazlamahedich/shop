"""add_widget_message_id_to_feedback

Revision ID: bcdcbceb4989
Revises: kg_20260327_001
Create Date: 2026-03-27 22:19:22.188090

Supports feedback for non-persisted widget messages (UUID IDs).
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "bcdcbceb4989"
down_revision: Union[str, None] = "kg_20260327_001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "message_feedback",
        sa.Column("widget_message_id", sa.String(100), nullable=True),
    )
    op.create_index(
        "ix_message_feedback_widget_message_id",
        "message_feedback",
        ["widget_message_id"],
    )
    op.alter_column(
        "message_feedback",
        "message_id",
        existing_type=sa.Integer(),
        nullable=True,
    )
    op.alter_column(
        "message_feedback",
        "conversation_id",
        existing_type=sa.Integer(),
        nullable=True,
    )
    op.drop_constraint(
        "uq_message_feedback_message_session",
        "message_feedback",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_message_feedback_message_session",
        "message_feedback",
        ["session_id", "message_id", "widget_message_id"],
        postgresql_nulls_not_distinct=True,
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_message_feedback_message_session",
        "message_feedback",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_message_feedback_message_session",
        "message_feedback",
        ["message_id", "session_id"],
    )
    op.alter_column(
        "message_feedback",
        "conversation_id",
        existing_type=sa.Integer(),
        nullable=False,
    )
    op.alter_column(
        "message_feedback",
        "message_id",
        existing_type=sa.Integer(),
        nullable=False,
    )
    op.drop_index(
        "ix_message_feedback_widget_message_id",
        table_name="message_feedback",
    )
    op.drop_column("message_feedback", "widget_message_id")
