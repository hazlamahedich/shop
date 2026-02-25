"""add_disputes_table

Revision ID: 032_add_disputes_table
Revises: 031_payment_cost_customer
Create Date: 2026-02-25 11:00:00.000000

Story 4-13: Shopify Payment/Cost Data Enhancement

Creates disputes table for chargeback/dispute tracking.

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "032_add_disputes_table"
down_revision: Union[str, None] = "031_payment_cost_customer"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "disputes",
        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
        ),
        sa.Column(
            "merchant_id",
            sa.Integer(),
            sa.ForeignKey("merchants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "order_id",
            sa.Integer(),
            sa.ForeignKey("orders.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "shopify_dispute_id",
            sa.String(100),
            nullable=False,
            comment="Shopify dispute GID",
        ),
        sa.Column(
            "amount",
            sa.Numeric(12, 2),
            nullable=False,
        ),
        sa.Column(
            "currency",
            sa.String(3),
            nullable=False,
            server_default="USD",
        ),
        sa.Column(
            "reason",
            sa.String(50),
            nullable=True,
            comment="Dispute reason (chargeback, inquiry)",
        ),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="open",
        ),
        sa.Column(
            "evidence_due_by",
            sa.DateTime(),
            nullable=True,
            comment="Deadline for submitting evidence",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )

    op.create_index(
        op.f("ix_disputes_merchant_id"),
        "disputes",
        ["merchant_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_disputes_order_id"),
        "disputes",
        ["order_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_disputes_shopify_dispute_id"),
        "disputes",
        ["shopify_dispute_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_disputes_shopify_dispute_id"), table_name="disputes")
    op.drop_index(op.f("ix_disputes_order_id"), table_name="disputes")
    op.drop_index(op.f("ix_disputes_merchant_id"), table_name="disputes")
    op.drop_table("disputes")
