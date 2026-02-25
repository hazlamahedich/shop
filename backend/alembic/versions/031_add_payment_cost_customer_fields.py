"""add_payment_cost_customer_fields

Revision ID: 031_add_payment_cost_customer_fields
Revises: 030_fix_business_hours_keys
Create Date: 2026-02-25 10:00:00.000000

Story 4-13: Shopify Payment/Cost Data Enhancement

Adds payment breakdown, customer identity, geographic, and COGS fields
to orders table, plus creates new customer_profiles table.

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


revision: str = "031_payment_cost_customer"
down_revision: Union[str, None] = "030_fix_business_hours_keys"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add payment breakdown columns to orders
    op.add_column(
        "orders",
        sa.Column(
            "discount_codes",
            JSONB,
            nullable=True,
            comment="Discount codes applied to order as JSON array",
        ),
    )
    op.add_column(
        "orders",
        sa.Column(
            "total_discount",
            sa.Numeric(10, 2),
            nullable=True,
            comment="Total discount amount",
        ),
    )
    op.add_column(
        "orders",
        sa.Column(
            "total_tax",
            sa.Numeric(10, 2),
            nullable=True,
            comment="Total tax amount",
        ),
    )
    op.add_column(
        "orders",
        sa.Column(
            "total_shipping",
            sa.Numeric(10, 2),
            nullable=True,
            comment="Total shipping cost",
        ),
    )
    op.add_column(
        "orders",
        sa.Column(
            "tax_lines",
            JSONB,
            nullable=True,
            comment="Tax breakdown as JSON array",
        ),
    )
    op.add_column(
        "orders",
        sa.Column(
            "payment_method",
            sa.String(50),
            nullable=True,
            comment="Payment method used (e.g., credit_card, paypal)",
        ),
    )
    op.add_column(
        "orders",
        sa.Column(
            "payment_details",
            JSONB,
            nullable=True,
            comment="Masked payment details as JSON",
        ),
    )

    # Add COGS tracking columns
    op.add_column(
        "orders",
        sa.Column(
            "cogs_total",
            sa.Numeric(10, 2),
            nullable=True,
            comment="Total cost of goods sold",
        ),
    )
    op.add_column(
        "orders",
        sa.Column(
            "cogs_fetched_at",
            sa.DateTime(),
            nullable=True,
            comment="When COGS was last fetched from Shopify",
        ),
    )

    # Add customer identity columns
    op.add_column(
        "orders",
        sa.Column(
            "customer_phone",
            sa.String(50),
            nullable=True,
            comment="Customer phone number",
        ),
    )
    op.add_column(
        "orders",
        sa.Column(
            "customer_first_name",
            sa.String(100),
            nullable=True,
            comment="Customer first name",
        ),
    )
    op.add_column(
        "orders",
        sa.Column(
            "customer_last_name",
            sa.String(100),
            nullable=True,
            comment="Customer last name",
        ),
    )

    # Add geographic columns for analytics
    op.add_column(
        "orders",
        sa.Column(
            "shipping_city",
            sa.String(100),
            nullable=True,
            comment="Shipping city for analytics",
        ),
    )
    op.add_column(
        "orders",
        sa.Column(
            "shipping_province",
            sa.String(100),
            nullable=True,
            comment="Shipping province/state for analytics",
        ),
    )
    op.add_column(
        "orders",
        sa.Column(
            "shipping_country",
            sa.String(2),
            nullable=True,
            comment="Shipping country code (ISO 3166-1 alpha-2)",
        ),
    )
    op.add_column(
        "orders",
        sa.Column(
            "shipping_postal_code",
            sa.String(20),
            nullable=True,
            comment="Shipping postal code",
        ),
    )

    # Add index on shipping_country for geographic analytics
    op.create_index(
        op.f("ix_orders_shipping_country"),
        "orders",
        ["shipping_country"],
        unique=False,
    )

    # Add cancelled order fields
    op.add_column(
        "orders",
        sa.Column(
            "cancel_reason",
            sa.String(255),
            nullable=True,
            comment="Reason for order cancellation",
        ),
    )
    op.add_column(
        "orders",
        sa.Column(
            "cancelled_at",
            sa.DateTime(),
            nullable=True,
            comment="When order was cancelled",
        ),
    )

    # Create customer_profiles table
    op.create_table(
        "customer_profiles",
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
            "email",
            sa.String(255),
            nullable=False,
        ),
        sa.Column(
            "phone",
            sa.String(50),
            nullable=True,
        ),
        sa.Column(
            "first_name",
            sa.String(100),
            nullable=True,
        ),
        sa.Column(
            "last_name",
            sa.String(100),
            nullable=True,
        ),
        sa.Column(
            "total_orders",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "total_spent",
            sa.Numeric(12, 2),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "first_order_at",
            sa.DateTime(),
            nullable=True,
        ),
        sa.Column(
            "last_order_at",
            sa.DateTime(),
            nullable=True,
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

    # Create indexes for customer_profiles
    op.create_index(
        op.f("ix_customer_profiles_email"),
        "customer_profiles",
        ["email"],
        unique=False,
    )
    op.create_index(
        op.f("ix_customer_profiles_merchant"),
        "customer_profiles",
        ["merchant_id"],
        unique=False,
    )
    op.create_index(
        "ix_customer_profiles_merchant_email",
        "customer_profiles",
        ["merchant_id", "email"],
        unique=True,
    )


def downgrade() -> None:
    # Drop customer_profiles table
    op.drop_index("ix_customer_profiles_merchant_email", table_name="customer_profiles")
    op.drop_index(op.f("ix_customer_profiles_merchant"), table_name="customer_profiles")
    op.drop_index(op.f("ix_customer_profiles_email"), table_name="customer_profiles")
    op.drop_table("customer_profiles")

    # Drop order columns
    op.drop_index(op.f("ix_orders_shipping_country"), table_name="orders")
    op.drop_column("orders", "cancelled_at")
    op.drop_column("orders", "cancel_reason")
    op.drop_column("orders", "shipping_postal_code")
    op.drop_column("orders", "shipping_country")
    op.drop_column("orders", "shipping_province")
    op.drop_column("orders", "shipping_city")
    op.drop_column("orders", "customer_last_name")
    op.drop_column("orders", "customer_first_name")
    op.drop_column("orders", "customer_phone")
    op.drop_column("orders", "cogs_fetched_at")
    op.drop_column("orders", "cogs_total")
    op.drop_column("orders", "payment_details")
    op.drop_column("orders", "payment_method")
    op.drop_column("orders", "tax_lines")
    op.drop_column("orders", "total_shipping")
    op.drop_column("orders", "total_tax")
    op.drop_column("orders", "total_discount")
    op.drop_column("orders", "discount_codes")
