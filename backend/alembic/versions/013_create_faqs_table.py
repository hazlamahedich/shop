"""Create faqs table for FAQ items.

Story 1.11: Business Info & FAQ Configuration

Revision ID: 013_create_faqs_table
Revises: 012_add_business_info_fields
Create Date: 2026-02-10

Adds:
- faqs table with id, merchant_id, question, answer, keywords, order_index
- Foreign key constraint to merchants table with CASCADE delete
- Indexes on merchant_id and order_index
- Length constraint for answer field (max 1000 chars)
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "013_create_faqs_table"
down_revision = "012_add_business_info_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create faqs table and related constraints."""

    # Create faqs table
    op.create_table(
        "faqs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "merchant_id",
            sa.Integer(),
            sa.ForeignKey("merchants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("question", sa.String(200), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("keywords", sa.String(500), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )

    # Add length constraint for answer field (max 1000 chars)
    op.execute(
        """
        ALTER TABLE faqs
        ADD CONSTRAINT faqs_answer_length
        CHECK (LENGTH(answer) <= 1000)
        """
    )

    # Create index on merchant_id for efficient lookups
    op.create_index(
        "ix_faqs_merchant_id",
        "faqs",
        ["merchant_id"],
    )

    # Create composite index on merchant_id and order_index for ordered queries
    op.create_index(
        "ix_faqs_merchant_order",
        "faqs",
        ["merchant_id", "order_index"],
    )


def downgrade() -> None:
    """Remove faqs table and related constraints."""

    # Drop indexes
    op.drop_index("ix_faqs_merchant_order", table_name="faqs")
    op.drop_index("ix_faqs_merchant_id", table_name="faqs")

    # Drop constraint
    op.execute(
        """
        ALTER TABLE faqs
        DROP CONSTRAINT IF EXISTS faqs_answer_length
        """
    )

    # Drop table
    op.drop_table("faqs")
