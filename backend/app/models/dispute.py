"""Dispute ORM model for Story 4-13.

Stores Shopify chargeback/dispute information for merchant alerts.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class DisputeStatus(str, Enum):
    """Dispute status values from Shopify."""

    OPEN = "open"
    WON = "won"
    LOST = "lost"
    PENDING = "pending"


class DisputeReason(str, Enum):
    """Dispute reason codes from Shopify."""

    CHARGEBACK = "chargeback"
    INQUIRY = "inquiry"


class Dispute(Base):
    """Dispute model for chargeback tracking.

    Stores Shopify dispute/chargeback information received via webhooks.
    Triggers merchant notifications for chargeback alerts.
    """

    __tablename__ = "disputes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    merchant_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("merchants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    order_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    shopify_dispute_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
        comment="Shopify dispute GID",
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
    )
    reason: Mapped[str] = mapped_column(
        String(50),
        nullable=True,
        comment="Dispute reason (chargeback, inquiry)",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=DisputeStatus.OPEN.value,
    )
    evidence_due_by: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        comment="Deadline for submitting evidence",
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

    merchant: Mapped[Merchant] = relationship(
        "Merchant",
        back_populates="disputes",
    )
    order: Mapped[Order | None] = relationship(
        "Order",
        back_populates="disputes",
    )

    def __repr__(self) -> str:
        return (
            f"<Dispute("
            f"id={self.id}, "
            f"shopify_dispute_id={self.shopify_dispute_id}, "
            f"merchant_id={self.merchant_id}, "
            f"amount={self.amount} {self.currency}, "
            f"status={self.status}"
            f")>"
        )
