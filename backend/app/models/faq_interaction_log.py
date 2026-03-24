"""FAQ Interaction Log model for tracking FAQ clicks and conversions.

Story 10-10: FAQ Usage Widget
"""

from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class FaqInteractionLog(Base):
    """Model for tracking FAQ interactions.

    Story 10-10: FAQ Usage Widget

    Tracks when users click on FAQs in the widget, and whether they
    sent a follow-up message (indicating the answer didn't fully resolve
    their question).

    Attributes:
        id: Primary key
        faq_id: Foreign key to the FAQ
        merchant_id: Foreign key to the merchant (for efficient querying)
        session_id: Widget session ID (to track follow-up messages)
        clicked_at: Timestamp when the FAQ was clicked
        had_followup: Whether the user sent a message after clicking
        followup_at: Timestamp of the follow-up message (if any)
    """

    __tablename__ = "faq_interaction_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    faq_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("faqs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    merchant_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("merchants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    clicked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
        index=True,
    )
    had_followup: Mapped[bool] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    followup_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    __table_args__ = (
        Index("ix_faq_interaction_logs_merchant_clicked", "merchant_id", "clicked_at"),
        Index("ix_faq_interaction_logs_faq_merchant", "faq_id", "merchant_id"),
    )

    faq: Mapped["Faq"] = relationship(
        "Faq",
        back_populates="interaction_logs",
    )

    def __repr__(self) -> str:
        return (
            f"<FaqInteractionLog(id={self.id}, faq_id={self.faq_id}, "
            f"session_id={self.session_id[:8]}..., had_followup={self.had_followup})>"
        )
