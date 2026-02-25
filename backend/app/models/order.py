"""Order ORM model for order tracking (Story 4-1).

Stores order information for customer order tracking queries.
Orders are populated by Shopify webhooks (Story 4-2) or mock data for testing.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class OrderStatus(str, Enum):
    """Order status values matching ECommerceProvider.

    Kept in sync with backend/app/services/ecommerce/base.py::OrderStatus.
    """

    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class Order(Base):
    """Order model for customer order tracking.

    Represents an order placed by a customer through the bot.
    Orders can be queried by platform_sender_id (customer) or order_number.

    Story 4-2 will populate this table from Shopify webhooks.
    Story 4-1 uses mock orders for testing.
    """

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    merchant_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("merchants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    platform_sender_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Facebook PSID of the customer who placed the order",
    )
    is_test: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
        comment="True if order is from test webhook (no real customer PSID)",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=OrderStatus.PENDING.value,
    )
    items: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Order items as JSON array",
    )
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )
    total: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )
    currency_code: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
    )
    customer_email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    shipping_address: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Shipping address as JSON object",
    )
    tracking_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    tracking_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    estimated_delivery: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )
    shopify_order_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        unique=True,
        index=True,
        comment="Shopify GID (gid://shopify/Order/123)",
    )
    shopify_order_key: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Human-readable order number (#1001)",
    )
    fulfillment_status: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="Shopify fulfillment status (null, fulfilled, partial, restocked)",
    )
    shopify_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        comment="Last update timestamp from Shopify (for out-of-order handling)",
    )

    # Payment breakdown fields (Story 4-13)
    discount_codes: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Discount codes applied to order as JSON array",
    )
    total_discount: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Total discount amount",
    )
    total_tax: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Total tax amount",
    )
    total_shipping: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Total shipping cost",
    )
    tax_lines: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Tax breakdown as JSON array",
    )
    payment_method: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Payment method used (e.g., credit_card, paypal)",
    )
    payment_details: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Masked payment details as JSON",
    )

    # COGS tracking fields (Story 4-13)
    cogs_total: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Total cost of goods sold",
    )
    cogs_fetched_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        comment="When COGS was last fetched from Shopify",
    )

    # Customer identity fields (Story 4-13)
    customer_phone: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Customer phone number",
    )
    customer_first_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Customer first name",
    )
    customer_last_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Customer last name",
    )

    # Geographic fields for analytics (Story 4-13)
    shipping_city: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Shipping city for analytics",
    )
    shipping_province: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Shipping province/state for analytics",
    )
    shipping_country: Mapped[str | None] = mapped_column(
        String(2),
        nullable=True,
        index=True,
        comment="Shipping country code (ISO 3166-1 alpha-2)",
    )
    shipping_postal_code: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="Shipping postal code",
    )

    # Cancellation fields (Story 4-13)
    cancel_reason: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Reason for order cancellation",
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        comment="When order was cancelled",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    __table_args__ = (
        Index(
            "ix_orders_merchant_platform_sender",
            "merchant_id",
            "platform_sender_id",
        ),
        Index(
            "ix_orders_merchant_order_number",
            "merchant_id",
            "order_number",
        ),
    )

    merchant: Mapped[Merchant] = relationship(
        "Merchant",
        back_populates="orders",
    )
    disputes: Mapped[list["Dispute"]] = relationship(
        "Dispute",
        back_populates="order",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<Order("
            f"id={self.id}, "
            f"order_number={self.order_number}, "
            f"merchant_id={self.merchant_id}, "
            f"status={self.status}"
            f")>"
        )
