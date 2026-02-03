"""Conversation ORM model.

Stores conversation sessions for messaging platforms (Facebook Messenger, etc.).
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, DateTime, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Conversation(Base):
    """Conversation session model.

    Represents a messaging conversation with a customer.
    Each conversation is tied to a merchant and a platform (Facebook, Instagram, etc.).
    """

    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    merchant_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("merchants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    platform: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )
    platform_sender_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        Enum(
            "active",
            "handoff",
            "closed",
            name="conversation_status",
            create_type=False,
        ),
        default="active",
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

    def __repr__(self) -> str:
        return (
            f"<Conversation("
            f"id={self.id}, "
            f"merchant_id={self.merchant_id}, "
            f"platform={self.platform}, "
            f"status={self.status}"
            f")>"
        )
