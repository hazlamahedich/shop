"""Order ORM model for order tracking (Story 4-1).

Stores order information for customer order tracking queries.
Orders are populated by Shopify webhooks (Story 4-2) or mock data for testing.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Optional

from sqlalchemy import String, Integer, DateTime, ForeignKey, Numeric, Index
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
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=OrderStatus.PENDING.value,
    )
    items: Mapped[Optional[dict[str, Any]]] = mapped_column(
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
    customer_email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    shipping_address: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Shipping address as JSON object",
    )
    tracking_number: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    tracking_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    estimated_delivery: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
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

    merchant: Mapped["Merchant"] = relationship(
        "Merchant",
        back_populates="orders",
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
