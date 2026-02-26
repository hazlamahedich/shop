"""Consent ORM model for user consent tracking.

Story 5-10 Task 18: Consent Management Middleware

Tracks user consent for various operations:
- Cart management (adding items, checkout)
- Data collection (conversation history)
- Marketing communications

Implements GDPR/compliance requirements for explicit consent.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, Integer, DateTime, Boolean, Index, Text, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column
import enum

from app.core.database import Base


class ConsentSource(str, enum.Enum):
    """Source channel for consent collection."""

    MESSENGER = "messenger"
    WIDGET = "widget"
    PREVIEW = "preview"


class ConsentType:
    """Constants for consent types."""

    CART = "cart"
    DATA_COLLECTION = "data_collection"
    MARKETING = "marketing"
    CONVERSATION = "conversation"


class Consent(Base):
    """User consent model for GDPR compliance.

    Tracks explicit consent from users for various operations.
    Consent is required before cart operations and data collection.

    Story 6-1 Enhancement: Added visitor_id for privacy-friendly consent persistence.
    Consent is looked up by visitor_id (primary) or session_id (fallback).

    Attributes:
        id: Primary key
        session_id: Widget session ID or PSID
        visitor_id: Visitor identifier for cross-session consent tracking (localStorage)
        merchant_id: Merchant ID
        consent_type: Type of consent (cart, data_collection, marketing, conversation)
        granted: Whether consent was granted
        granted_at: Timestamp when consent was granted
        revoked_at: Timestamp when consent was revoked (if applicable)
        ip_address: Optional IP address for audit trail
        user_agent: Optional user agent for audit trail
        source_channel: Source channel for consent (messenger, widget, preview)
        consent_message_shown: Whether consent prompt was shown to user
    """

    __tablename__ = "consents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    visitor_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    merchant_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )
    consent_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    granted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    granted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    revoked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),
        nullable=True,
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    source_channel: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )
    consent_message_shown: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    __table_args__ = (
        Index("ix_consents_session_type", "session_id", "consent_type"),
        Index("ix_consents_merchant_type", "merchant_id", "consent_type"),
        Index("ix_consents_visitor_merchant", "visitor_id", "merchant_id"),
    )

    def __repr__(self) -> str:
        return f"<Consent(id={self.id}, session={self.session_id[:8]}..., type={self.consent_type}, granted={self.granted})>"

    def grant(self, ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> None:
        """Grant consent.

        Args:
            ip_address: Optional IP address for audit
            user_agent: Optional user agent for audit
        """
        self.granted = True
        self.granted_at = datetime.now(timezone.utc)
        self.revoked_at = None
        if ip_address:
            self.ip_address = ip_address
        if user_agent:
            self.user_agent = user_agent

    def revoke(self) -> None:
        """Revoke consent."""
        self.granted = False
        self.revoked_at = datetime.now(timezone.utc)

    def is_valid(self) -> bool:
        """Check if consent is currently valid.

        Returns:
            True if consent is granted and not revoked
        """
        return self.granted and self.revoked_at is None

    @classmethod
    def create(
        cls,
        session_id: str,
        merchant_id: int,
        consent_type: str,
        source_channel: Optional[str] = None,
        visitor_id: Optional[str] = None,
    ) -> "Consent":
        """Create a new consent record.

        Args:
            session_id: Widget session ID or PSID
            merchant_id: Merchant ID
            consent_type: Type of consent
            source_channel: Source channel for consent (messenger, widget, preview)
            visitor_id: Optional visitor identifier for cross-session tracking

        Returns:
            New Consent instance (not yet granted)
        """
        return cls(
            session_id=session_id,
            merchant_id=merchant_id,
            consent_type=consent_type,
            granted=False,
            source_channel=source_channel,
            consent_message_shown=False,
            visitor_id=visitor_id,
        )

    def mark_message_shown(self) -> None:
        """Mark that consent prompt message has been shown to user."""
        self.consent_message_shown = True
