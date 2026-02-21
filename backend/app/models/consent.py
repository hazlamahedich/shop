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

from sqlalchemy import String, Integer, DateTime, Boolean, Index, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ConsentType:
    """Constants for consent types."""

    CART = "cart"
    DATA_COLLECTION = "data_collection"
    MARKETING = "marketing"


class Consent(Base):
    """User consent model for GDPR compliance.

    Tracks explicit consent from users for various operations.
    Consent is required before cart operations and data collection.

    Attributes:
        id: Primary key
        session_id: Widget session ID or PSID
        merchant_id: Merchant ID
        consent_type: Type of consent (cart, data_collection, marketing)
        granted: Whether consent was granted
        granted_at: Timestamp when consent was granted
        revoked_at: Timestamp when consent was revoked (if applicable)
        ip_address: Optional IP address for audit trail
        user_agent: Optional user agent for audit trail
    """

    __tablename__ = "consents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
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

    __table_args__ = (
        Index("ix_consents_session_type", "session_id", "consent_type"),
        Index("ix_consents_merchant_type", "merchant_id", "consent_type"),
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
    ) -> "Consent":
        """Create a new consent record.

        Args:
            session_id: Widget session ID or PSID
            merchant_id: Merchant ID
            consent_type: Type of consent

        Returns:
            New Consent instance (not yet granted)
        """
        return cls(
            session_id=session_id,
            merchant_id=merchant_id,
            consent_type=consent_type,
            granted=False,
        )
