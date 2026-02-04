"""Message ORM model.

Stores individual messages within conversations.
Supports field-level encryption for sensitive content (NFR-S2).
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, Text, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.encryption import (
    encrypt_conversation_content,
    decrypt_conversation_content,
    encrypt_metadata,
    decrypt_metadata,
)


class Message(Base):
    """Message model.

    Represents an individual message within a conversation.
    Can be from customer or bot, with support for various message types.

    Customer message content is encrypted at rest (NFR-S2).
    Bot responses are stored in plaintext (non-sensitive).
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

    @property
    def decrypted_content(self) -> str:
        """Get decrypted message content.

        Returns:
            Decrypted content for customer messages,
            plaintext for bot messages.

        Note:
            This property automatically decrypts customer message content.
            Bot messages are returned as-is (non-sensitive).
        """
        if self.sender == "customer":
            return decrypt_conversation_content(self.content)
        return self.content

    def set_encrypted_content(self, content: str, sender: Optional[str] = None) -> None:
        """Set message content with automatic encryption.

        Args:
            content: Plain text message content
            sender: Message sender ('customer' or 'bot').
                    If None, uses current sender value.

        Note:
            Customer messages are encrypted before storage.
            Bot messages are stored in plaintext.
        """
        msg_sender = sender if sender is not None else self.sender

        if msg_sender == "customer":
            self.content = encrypt_conversation_content(content)
        else:
            # Bot responses are stored in plaintext
            self.content = content

    @property
    def decrypted_metadata(self) -> Optional[dict]:
        """Get decrypted message metadata.

        Returns:
            Decrypted metadata dictionary with sensitive fields decrypted.

        Note:
            Automatically decrypts user_input and voluntary_memory fields.
        """
        if self.message_metadata is None:
            return None
        return decrypt_metadata(self.message_metadata)

    def set_encrypted_metadata(self, metadata: Optional[dict]) -> None:
        """Set message metadata with automatic encryption.

        Args:
            metadata: Metadata dictionary potentially containing sensitive data

        Note:
            Encrypts user_input and voluntary_memory fields before storage.
        """
        if metadata is None:
            self.message_metadata = None
        else:
            self.message_metadata = encrypt_metadata(metadata)

    def __repr__(self) -> str:
        return (
            f"<Message("
            f"id={self.id}, "
            f"conversation_id={self.conversation_id}, "
            f"sender={self.sender}, "
            f"type={self.message_type}"
            f")>"
        )
