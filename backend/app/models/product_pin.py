"""Product Pin ORM model.

Story 1.15: Product Highlight Pins

Stores merchant's pinned products for prioritized bot recommendations.
Pinned products get 2x relevance boost in recommendations.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy import String, Integer, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ProductPin(Base):
    """Product Pin model for merchant-pinned products.

    Story 1.15 AC 1, 2, 4: Pin Products List Management,
    Pin and Unpin Products, Integration with Bot Recommendation Engine.

    Stores which products a merchant wants to prioritize in bot
    recommendations. Pinned products receive a 2x relevance boost
    and appear first in recommendation results.

    Attributes:
        id: Unique identifier for this pin record
        merchant_id: Foreign key to merchants table
        product_id: Shopify product ID (string)
        product_title: Denormalized product title for search
        product_image_url: Product image URL for display
        pinned_at: Timestamp when product was pinned (automatic)
        pinned_order: Merchant-defined priority order (1-10)

    Relationships:
        merchant: Back reference to merchant who owns these pins
    """

    __tablename__ = "product_pins"

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
    product_title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    product_image_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    pinned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    pinned_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # Relationships
    merchant: Mapped["Merchant"] = relationship(
        "Merchant",
        back_populates="product_pins",
    )

    def __repr__(self) -> str:
        return (
            f"<ProductPin(id={self.id}, merchant_id={self.merchant_id}, "
            f"product_id={self.product_id}, pinned_order={self.pinned_order})>"
        )
