"""FAQ ORM model.

Story 1.11: Business Info & FAQ Configuration
Story 10-2: Added icon field for FAQ quick buttons.
"""

from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Faq(Base):
    """FAQ (Frequently Asked Question) model.

    Story 1.11: Business Info & FAQ Configuration
    Story 10-2: Added icon field for FAQ quick buttons.
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
    keywords: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    icon: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    order_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    merchant: Mapped["Merchant"] = relationship(
        "Merchant",
        back_populates="faqs",
    )
    interaction_logs: Mapped[list["FaqInteractionLog"]] = relationship(
        "FaqInteractionLog",
        back_populates="faq",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<Faq(id={self.id}, question={self.question[:30]}..., merchant_id={self.merchant_id})>"
        )
