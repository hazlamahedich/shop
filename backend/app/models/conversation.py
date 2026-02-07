"""Conversation ORM model.

Stores conversation sessions for messaging platforms (Facebook Messenger, etc.).
Supports field-level encryption for sensitive metadata (NFR-S2).
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, DateTime, Enum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.encryption import (
    encrypt_metadata,
    decrypt_metadata,
)


class Conversation(Base):
    """Conversation session model.

    Represents a messaging conversation with a customer.
    Each conversation is tied to a merchant and a platform (Facebook, Instagram, etc.).

    Sensitive metadata (user_input, voluntary_memory) is encrypted at rest (NFR-S2).
    Order references and platform IDs are kept in plaintext (business requirements).
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
    # Encrypted conversation_data for storing sensitive conversation data
    # (renamed from 'metadata' which is reserved in SQLAlchemy)
    conversation_data: Mapped[Optional[dict]] = mapped_column(
        "conversation_data",
        JSONB,
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

    # Relationship to messages - one-to-many from Conversation to Message
    # Note: Sorting handled in service layer
    messages: Mapped[list["Message"]] = relationship(
        "Message",
        back_populates="conversation",
    )

    @property
    def decrypted_metadata(self) -> Optional[dict]:
        """Get decrypted conversation metadata.

        Returns:
            Decrypted metadata dictionary with sensitive fields decrypted.

        Note:
            Automatically decrypts user_input and voluntary_memory fields.
            Order references and other non-sensitive data remain unchanged.
        """
        if self.conversation_data is None:
            return None
        return decrypt_metadata(self.conversation_data)

    def set_encrypted_metadata(self, metadata: Optional[dict]) -> None:
        """Set conversation metadata with automatic encryption.

        Args:
            metadata: Metadata dictionary potentially containing sensitive data

        Note:
            Encrypts user_input and voluntary_memory fields before storage.
            Order references and other non-sensitive data remain in plaintext.
        """
        if metadata is None:
            self.conversation_data = None
        else:
            self.conversation_data = encrypt_metadata(metadata)

    def __repr__(self) -> str:
        return (
            f"<Conversation("
            f"id={self.id}, "
            f"merchant_id={self.merchant_id}, "
            f"platform={self.platform}, "
            f"status={self.status}"
            f")>"
        )
