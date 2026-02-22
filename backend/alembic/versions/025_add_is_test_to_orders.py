"""add_is_test_to_orders

Revision ID: 025_add_is_test_to_orders
Revises: 024_shopify_nullable_storefront_token
Create Date: 2026-02-21 10:00:00.000000

Story 5-10: Widget Full App Integration

Adds is_test field to orders table to filter out test webhook orders
from user-facing features (order tracking, context prompts, etc.).

Test orders are those where platform_sender_id is "unknown" or None,
indicating no real customer PSID was resolved during webhook processing.

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "025_add_is_test_to_orders"
down_revision: Union[str, None] = "024_nullable_storefront_tkn"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "orders",
        sa.Column(
            "is_test",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
            comment="True if order is from test webhook (no real customer PSID)",
        ),
    )
    op.create_index(
        op.f("ix_orders_is_test"),
        "orders",
        ["is_test"],
        unique=False,
    )

    op.execute("UPDATE orders SET is_test = true WHERE platform_sender_id = 'unknown'")


def downgrade() -> None:
    op.drop_index(op.f("ix_orders_is_test"), table_name="orders")
    op.drop_column("orders", "is_test")
