"""FAQ ORM model.

Story 1.11: Business Info & FAQ Configuration
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Faq(Base):
    """FAQ (Frequently Asked Question) model.

    Represents a single FAQ item for a merchant.
    Used by the bot to automatically answer common customer questions.
    """

    __tablename__ = "faqs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    merchant_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("merchants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    answer: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    keywords: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    order_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    merchant: Mapped["Merchant"] = relationship(
        "Merchant",
        back_populates="faqs",
    )

    def __repr__(self) -> str:
        return f"<Faq(id={self.id}, question={self.question[:30]}..., merchant_id={self.merchant_id})>"
