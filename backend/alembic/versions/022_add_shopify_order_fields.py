"""add_shopify_order_fields

Revision ID: 022_add_shopify_order_fields
Revises: 021_add_orders_table
Create Date: 2026-02-17 12:00:00.000000

Story 4-2: Shopify Webhook Integration

Adds Shopify-specific fields to the orders table for storing webhook data:
- shopify_order_id: Shopify GID for deduplication
- shopify_order_key: Human-readable order number
- fulfillment_status: Shopify fulfillment status
- shopify_updated_at: For out-of-order webhook handling

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "022_add_shopify_order_fields"
down_revision: Union[str, None] = "021_add_orders_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "orders",
        sa.Column(
            "shopify_order_id",
            sa.String(length=100),
            nullable=True,
            comment="Shopify GID (gid://shopify/Order/123)",
        ),
    )
    op.add_column(
        "orders",
        sa.Column(
            "shopify_order_key",
            sa.String(length=50),
            nullable=True,
            comment="Human-readable order number (#1001)",
        ),
    )
    op.add_column(
        "orders",
        sa.Column(
            "fulfillment_status",
            sa.String(length=20),
            nullable=True,
            comment="Shopify fulfillment status (null, fulfilled, partial, restocked)",
        ),
    )
    op.add_column(
        "orders",
        sa.Column(
            "shopify_updated_at",
            sa.DateTime(),
            nullable=True,
            comment="Last update timestamp from Shopify (for out-of-order handling)",
        ),
    )
    op.create_index(
        op.f("ix_orders_shopify_order_id"),
        "orders",
        ["shopify_order_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_orders_shopify_order_id"), table_name="orders")
    op.drop_column("orders", "shopify_updated_at")
    op.drop_column("orders", "fulfillment_status")
    op.drop_column("orders", "shopify_order_key")
    op.drop_column("orders", "shopify_order_id")
