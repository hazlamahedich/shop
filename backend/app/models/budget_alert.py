"""Budget Alert ORM model.

Tracks budget threshold notifications for merchants.
Supports in-app notifications for 80% and 100% budget thresholds.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.merchant import Merchant


class BudgetAlert(Base):
    """Budget alert notification model.

    Stores alerts when merchants hit budget thresholds (80% or 100%).
    Supports in-app notifications with read/unread status.
    """

    __tablename__ = "budget_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    merchant_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("merchants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    threshold: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    is_read: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    merchant: Mapped[Merchant] = relationship(
        "Merchant",
        back_populates="budget_alerts",
    )

    def __repr__(self) -> str:
        return (
            f"<BudgetAlert(id={self.id}, merchant_id={self.merchant_id}, "
            f"threshold={self.threshold}%, is_read={self.is_read})>"
        )
