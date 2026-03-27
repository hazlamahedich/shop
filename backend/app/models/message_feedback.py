"""Message feedback ORM model.

Stores user feedback (thumbs up/down) on bot messages.
Enables merchants to identify helpful responses and areas for improvement.
"""

from __future__ import annotations

import enum
from datetime import UTC, datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class FeedbackRating(str, enum.Enum):
    """Feedback rating values."""

    POSITIVE = "positive"
    NEGATIVE = "negative"


class MessageFeedback(Base):
    """Message feedback model.

    Represents user feedback on a bot message (thumbs up/down).
    One rating per message per session (upsert on re-click).

    No PII stored - session IDs are anonymous UUIDs.
    """

    __tablename__ = "message_feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    message_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    widget_message_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    merchant_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("merchants.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    conversation_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    rating: Mapped[FeedbackRating] = mapped_column(
        Enum(FeedbackRating, name="feedback_rating", create_type=False),
        nullable=False,
    )
    comment: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    session_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    message: Mapped[object] = relationship(
        "Message",
        backref="feedback",
    )
    conversation: Mapped[object] = relationship(
        "Conversation",
        backref="feedback",
    )
    merchant: Mapped[object] = relationship(
        "Merchant",
        backref="feedback",
    )

    __table_args__ = (
        UniqueConstraint(
            "session_id",
            "message_id",
            "widget_message_id",
            name="uq_message_feedback_message_session",
        ),
        Index("ix_message_feedback_created", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<MessageFeedback("
            f"id={self.id}, "
            f"message_id={self.message_id}, "
            f"rating={self.rating.value}, "
            f"session_id={self.session_id[:8]}..."
            f")>"
        )
