"""add_knowledge_gaps_table

Revision ID: kg_20260327_001
Revises: 9580e911f8fb
Create Date: 2026-03-27 09:10:00

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "kg_20260327_001"
down_revision = "9580e911f8fb"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "knowledge_gaps",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "merchant_id",
            sa.Integer(),
            sa.ForeignKey("merchants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "conversation_id",
            sa.Integer(),
            sa.ForeignKey("conversations.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("question_hash", sa.Text(), nullable=False),
        sa.Column("gap_types", JSONB(), nullable=False, server_default="[]"),
        sa.Column("occurrence_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "first_occurred_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "last_occurred_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("resolved", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("resolved_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("resolved_by_type", sa.Text(), nullable=True),
        sa.Column("resolved_by_id", sa.Integer(), nullable=True),
        sa.Column("sample_response", sa.Text(), nullable=True),
        sa.Column("metadata", JSONB(), nullable=True),
    )

    op.create_index(
        "idx_knowledge_gaps_merchant_resolved",
        "knowledge_gaps",
        ["merchant_id", "resolved"],
    )
    op.create_index(
        "idx_knowledge_gaps_merchant_hash",
        "knowledge_gaps",
        ["merchant_id", "question_hash"],
    )
    op.create_index(
        op.f("ix_knowledge_gaps_merchant_id"),
        "knowledge_gaps",
        ["merchant_id"],
    )
    op.create_index(
        op.f("ix_knowledge_gaps_question_hash"),
        "knowledge_gaps",
        ["question_hash"],
    )


def downgrade():
    op.drop_index(op.f("ix_knowledge_gaps_question_hash"), table_name="knowledge_gaps")
    op.drop_index(op.f("ix_knowledge_gaps_merchant_id"), table_name="knowledge_gaps")
    op.drop_index("idx_knowledge_gaps_merchant_hash", table_name="knowledge_gaps")
    op.drop_index("idx_knowledge_gaps_merchant_resolved", table_name="knowledge_gaps")
    op.drop_table("knowledge_gaps")
