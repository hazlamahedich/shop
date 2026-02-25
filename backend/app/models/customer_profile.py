"""Customer Profile ORM model for Story 4-13.

Stores aggregated customer data for cross-device recognition and
personalized experiences.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class CustomerProfile(Base):
    """Customer profile model for cross-device recognition.

    Aggregates customer data across multiple orders and devices.
    Email is the primary identifier with phone as secondary.
    """

    __tablename__ = "customer_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    merchant_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("merchants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    phone: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    first_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    last_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    total_orders: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    total_spent: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0"),
    )
    first_order_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )
    last_order_at: Mapped[datetime | None] = mapped_column(
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
            "ix_customer_profiles_merchant_email",
            "merchant_id",
            "email",
            unique=True,
        ),
    )

    merchant: Mapped[Merchant] = relationship(
        "Merchant",
        back_populates="customer_profiles",
    )

    def __repr__(self) -> str:
        return (
            f"<CustomerProfile("
            f"id={self.id}, "
            f"merchant_id={self.merchant_id}, "
            f"email={self.email}, "
            f"total_orders={self.total_orders}"
            f")>"
        )
