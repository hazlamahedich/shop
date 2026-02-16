"""add_orders_table

Revision ID: 021_add_orders_table
Revises: 020_create_handoff_alerts_table
Create Date: 2026-02-16 22:20:00.000000

Story 4-1: Natural Language Order Tracking

Creates the orders table for storing order information that can be
queried by customers using natural language through the bot.

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "021_add_orders_table"
down_revision: Union[str, None] = "020_create_handoff_alerts_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "order_number",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "merchant_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "platform_sender_id",
            sa.String(length=100),
            nullable=False,
            comment="Facebook PSID of the customer who placed the order",
        ),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "items",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="Order items as JSON array",
        ),
        sa.Column(
            "subtotal",
            sa.Numeric(precision=10, scale=2),
            nullable=False,
        ),
        sa.Column(
            "total",
            sa.Numeric(precision=10, scale=2),
            nullable=False,
        ),
        sa.Column(
            "currency_code",
            sa.String(length=3),
            nullable=False,
            server_default="USD",
        ),
        sa.Column(
            "customer_email",
            sa.String(length=255),
            nullable=True,
        ),
        sa.Column(
            "shipping_address",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="Shipping address as JSON object",
        ),
        sa.Column(
            "tracking_number",
            sa.String(length=100),
            nullable=True,
        ),
        sa.Column(
            "tracking_url",
            sa.String(length=500),
            nullable=True,
        ),
        sa.Column(
            "estimated_delivery",
            sa.DateTime(),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["merchant_id"],
            ["merchants.id"],
            name=op.f("orders_merchant_id_fkey"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("orders_pkey")),
    )
    op.create_index(
        op.f("ix_orders_order_number"),
        "orders",
        ["order_number"],
        unique=False,
    )
    op.create_index(
        op.f("ix_orders_merchant_id"),
        "orders",
        ["merchant_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_orders_platform_sender_id"),
        "orders",
        ["platform_sender_id"],
        unique=False,
    )
    op.create_index(
        "ix_orders_merchant_platform_sender",
        "orders",
        ["merchant_id", "platform_sender_id"],
        unique=False,
    )
    op.create_index(
        "ix_orders_merchant_order_number",
        "orders",
        ["merchant_id", "order_number"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_orders_merchant_order_number", table_name="orders")
    op.drop_index("ix_orders_merchant_platform_sender", table_name="orders")
    op.drop_index(op.f("ix_orders_platform_sender_id"), table_name="orders")
    op.drop_index(op.f("ix_orders_merchant_id"), table_name="orders")
    op.drop_index(op.f("ix_orders_order_number"), table_name="orders")
    op.drop_table("orders")
