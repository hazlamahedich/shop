"""add_rag_query_logs_table

Revision ID: a1b2c3d4e5f6
Revises: message_feedback
Create Date: 2026-03-20 14:35:06.673889

Story 10-7: Knowledge Effectiveness Widget

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "message_feedback"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "rag_query_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("merchant_id", sa.Integer(), nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("matched", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("sources", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("rag_query_logs_pkey")),
    )
    op.create_index(
        op.f("ix_rag_query_logs_merchant_id"), "rag_query_logs", ["merchant_id"], unique=False
    )
    op.create_index(
        "idx_rag_logs_merchant_date", "rag_query_logs", ["merchant_id", "created_at"], unique=False
    )


def downgrade() -> None:
    op.drop_index("idx_rag_logs_merchant_date", table_name="rag_query_logs")
    op.drop_index(op.f("ix_rag_query_logs_merchant_id"), table_name="rag_query_logs")
    op.drop_table("rag_query_logs")
