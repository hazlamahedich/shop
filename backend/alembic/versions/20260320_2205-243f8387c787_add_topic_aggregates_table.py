"""add_topic_aggregates_table

Revision ID: 243f8387c787
Revises: a1b2c3d4e5f6
Create Date: 2026-03-20 22:05:40.034552

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "243f8387c787"
down_revision: str | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "topic_aggregates",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("merchant_id", sa.Integer(), nullable=False),
        sa.Column("topic_name", sa.String(255), nullable=False),
        sa.Column("query_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("trend", sa.String(20), nullable=True),
        sa.Column("period_days", sa.Integer(), nullable=False),
        sa.Column("period_start", sa.DateTime(), nullable=False),
        sa.Column("period_end", sa.DateTime(), nullable=False),
        sa.Column("computed_at", sa.DateTime(), server_default=sa.text("NOW()"), nullable=False),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "merchant_id",
            "topic_name",
            "period_days",
            name="uq_topic_aggregates_merchant_topic_period",
        ),
    )
    op.create_index(
        "idx_topic_aggregates_merchant", "topic_aggregates", ["merchant_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index("idx_topic_aggregates_merchant", table_name="topic_aggregates")
    op.drop_table("topic_aggregates")
