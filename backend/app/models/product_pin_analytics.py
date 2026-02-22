"""Product Pin Analytics ORM model.

Tracks engagement metrics for pinned products to help merchants
understand which featured items perform best.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ProductPinAnalytics(Base):
    """Analytics for pinned product engagement.

    Tracks views and cart additions for pinned products,
    enabling merchants to measure the effectiveness of their
    featured product selections.

    Attributes:
        id: Unique identifier
        merchant_id: Foreign key to merchants table
        product_id: Shopify product ID
        views_count: Number of times the pinned product was shown
        cart_adds_count: Number of times the product was added to cart
        last_viewed_at: Timestamp of most recent view
        last_cart_add_at: Timestamp of most recent cart addition
    """

    __tablename__ = "product_pin_analytics"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=lambda: uuid4(),
    )
    merchant_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("merchants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    views_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    cart_adds_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    last_viewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_cart_add_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    merchant: Mapped["Merchant"] = relationship(
        "Merchant",
        back_populates="product_pin_analytics",
    )

    def __repr__(self) -> str:
        return (
            f"<ProductPinAnalytics(id={self.id}, merchant_id={self.merchant_id}, "
            f"product_id={self.product_id}, views={self.views_count}, "
            f"cart_adds={self.cart_adds_count})>"
        )
