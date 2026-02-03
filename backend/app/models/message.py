"""Message ORM model.

Stores individual messages within conversations.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, Text, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Message(Base):
    """Message model.

    Represents an individual message within a conversation.
    Can be from customer or bot, with support for various message types.
    """

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    conversation_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sender: Mapped[str] = mapped_column(
        Enum("customer", "bot", name="message_sender"),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    message_type: Mapped[str] = mapped_column(
        Enum(
            "text",
            "attachment",
            "postback",
            name="message_type",
            create_type=False,
        ),
        default="text",
        nullable=False,
    )
    message_metadata: Mapped[Optional[dict]] = mapped_column(
        "message_metadata",
        JSONB,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )

    def __repr__(self) -> str:
        return (
            f"<Message("
            f"id={self.id}, "
            f"conversation_id={self.conversation_id}, "
            f"sender={self.sender}, "
            f"type={self.message_type}"
            f")>"
        )
