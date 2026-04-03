"""Conversation Context ORM models.

Story 11-1: Conversation Context Memory
Models for storing conversation context with mode-aware fields.
Supports both e-commerce and general mode contexts with 24-hour expiration.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Literal

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


# Helper for timezone-aware datetime columns
def TimestampTZ() -> DateTime:
    """Create a timezone-aware DateTime column (TIMESTAMPTZ)."""
    return DateTime(timezone=True)


ModeType = Literal["ecommerce", "general"]


class ConversationContext(Base):
    """Conversation context model with mode-aware fields.

    Stores conversation context for both e-commerce and general modes.
    Context expires after 24 hours of inactivity.

    E-commerce mode tracks: products viewed, price constraints, cart items
    General mode tracks: topics discussed, documents, support issues
    """

    __tablename__ = "conversation_context"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    conversation_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    merchant_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("merchants.id", ondelete="CASCADE"),
        nullable=False,
    )
    mode: Mapped[str] = mapped_column(
        Enum(
            "ecommerce",
            "general",
            name="conversation_mode",
            create_type=False,
        ),
        nullable=False,
        index=True,
    )

    # Full context data (JSONB for flexibility)
    context_data: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # E-commerce mode fields
    viewed_products: Mapped[list[int] | None] = mapped_column(ARRAY(Integer), nullable=True)
    cart_items: Mapped[list[int] | None] = mapped_column(ARRAY(Integer), nullable=True)
    dismissed_products: Mapped[list[int] | None] = mapped_column(ARRAY(Integer), nullable=True)
    constraints: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    search_history: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)

    # General mode fields
    topics_discussed: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    documents_referenced: Mapped[list[int] | None] = mapped_column(ARRAY(Integer), nullable=True)
    support_issues: Mapped[list[dict] | None] = mapped_column(JSONB, nullable=True)
    escalation_status: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Universal fields
    preferences: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    turn_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_summarized_at: Mapped[datetime | None] = mapped_column(TimestampTZ(), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(
        TimestampTZ(),
        default=lambda: datetime.now(timezone.utc) + timedelta(hours=24),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        TimestampTZ(),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        TimestampTZ(),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_conversation_context_conversation", "conversation_id"),
        Index("ix_conversation_context_mode", "mode"),
        Index("ix_conversation_context_expires", "expires_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<ConversationContext("
            f"id={self.id}, "
            f"conversation_id={self.conversation_id}, "
            f"mode={self.mode}, "
            f"turn_count={self.turn_count}"
            f")>"
        )


class ConversationTurn(Base):
    """Individual conversation turn tracking.

    Records each turn in a conversation for analytics and context tracking.
    Stores message content, intent, sentiment, and context snapshot.
    """

    __tablename__ = "conversation_turns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    conversation_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    turn_number: Mapped[int] = mapped_column(Integer, nullable=False)
    user_message: Mapped[str | None] = mapped_column(String, nullable=True)
    bot_response: Mapped[str | None] = mapped_column(String, nullable=True)
    intent_detected: Mapped[str | None] = mapped_column(String(100), nullable=True)
    context_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    sentiment: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_conversation_turns_conversation", "conversation_id", "turn_number"),
    )

    def __repr__(self) -> str:
        return (
            f"<ConversationTurn("
            f"id={self.id}, "
            f"conversation_id={self.conversation_id}, "
            f"turn_number={self.turn_number}"
            f")>"
        )
