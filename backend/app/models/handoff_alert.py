"""Handoff Alert ORM model.

Story 4-6: Handoff Notifications

Stores handoff alert notifications for merchants.
Supports dashboard badge and notification dropdown.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.conversation import Conversation
    from app.models.merchant import Merchant


class HandoffAlert(Base):
    """Handoff alert notification model.

    Stores alerts when conversations need human attention.
    Supports dashboard badge notifications with read/unread status.
    """

    __tablename__ = "handoff_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    merchant_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("merchants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    conversation_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    urgency_level: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )
    customer_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    customer_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    conversation_preview: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    wait_time_seconds: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    is_read: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    merchant: Mapped[Merchant] = relationship(
        "Merchant",
        back_populates="handoff_alerts",
    )
    conversation: Mapped[Conversation] = relationship(
        "Conversation",
        back_populates="handoff_alert",
        uselist=False,
    )

    def __repr__(self) -> str:
        return (
            f"<HandoffAlert(id={self.id}, merchant_id={self.merchant_id}, "
            f"conversation_id={self.conversation_id}, urgency={self.urgency_level}, "
            f"is_read={self.is_read})>"
        )
