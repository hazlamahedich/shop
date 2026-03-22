"""Add faq_interaction_logs table

Story 10-10: FAQ Usage Widget

Revision ID: 20260322_1218_faq_interaction_logs
Revises: add_response_type_to_costs
Create Date: 2026-03-22 12:18:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260322_1218_faq_interaction_logs"
down_revision: Union[str, None] = "add_response_type_to_costs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create faq_interaction_logs table."""
    op.create_table(
        "faq_interaction_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("faq_id", sa.Integer(), nullable=False),
        sa.Column("merchant_id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.String(length=100), nullable=False),
        sa.Column("clicked_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("had_followup", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("followup_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["faq_id"], ["faqs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("ix_faq_interaction_logs_faq_id", "faq_interaction_logs", ["faq_id"])
    op.create_index("ix_faq_interaction_logs_merchant_id", "faq_interaction_logs", ["merchant_id"])
    op.create_index("ix_faq_interaction_logs_session_id", "faq_interaction_logs", ["session_id"])
    op.create_index("ix_faq_interaction_logs_clicked_at", "faq_interaction_logs", ["clicked_at"])
    op.create_index(
        "ix_faq_interaction_logs_merchant_clicked",
        "faq_interaction_logs",
        ["merchant_id", "clicked_at"],
    )
    op.create_index(
        "ix_faq_interaction_logs_faq_merchant", "faq_interaction_logs", ["faq_id", "merchant_id"]
    )


def downgrade() -> None:
    """Drop faq_interaction_logs table."""
    op.drop_index("ix_faq_interaction_logs_faq_merchant", table_name="faq_interaction_logs")
    op.drop_index("ix_faq_interaction_logs_merchant_clicked", table_name="faq_interaction_logs")
    op.drop_index("ix_faq_interaction_logs_clicked_at", table_name="faq_interaction_logs")
    op.drop_index("ix_faq_interaction_logs_session_id", table_name="faq_interaction_logs")
    op.drop_index("ix_faq_interaction_logs_merchant_id", table_name="faq_interaction_logs")
    op.drop_index("ix_faq_interaction_logs_faq_id", table_name="faq_interaction_logs")
    op.drop_table("faq_interaction_logs")
