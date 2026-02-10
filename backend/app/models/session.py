"""Session ORM model for JWT revocation support.

Implements session management for merchant authentication:
- Session rotation on login (prevents fixation attacks)
- Session revocation on logout
- Token hash storage for validation
- Indexes for merchant_id and token_hash

AC 2: Session Management
- JWT expires after 24 hours of inactivity
- Sliding expiration extends session on activity
- Automatic token refresh at 50% of session lifetime

AC 6: Database
- sessions table with columns: id, merchant_id, token_hash, created_at, expires_at, revoked
- Index on merchant_id for session lookup
- Index on token_hash for validation
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4

from sqlalchemy import String, Integer, DateTime, Boolean, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Session(Base):
    """Merchant session model for JWT revocation support.

    Supports:
    - Session rotation (prevent fixation attacks)
    - Session revocation (logout)
    - Multiple concurrent sessions per merchant
    - Token validation via hash lookup

    Attributes:
        id: Primary key
        merchant_id: Foreign key to merchants table
        token_hash: SHA-256 hash of JWT token (for validation)
        created_at: Session creation timestamp
        expires_at: Session expiration timestamp
        revoked: Whether session has been revoked
    """

    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    merchant_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )
    token_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.utcnow(),
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )
    revoked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
    )

    # Define composite indexes for common queries
    __table_args__ = (
        Index("ix_sessions_merchant_revoked", "merchant_id", "revoked"),
        Index("ix_sessions_expires", "expires_at"),
    )

    def __repr__(self) -> str:
        return f"<Session(id={self.id}, merchant_id={self.merchant_id}, revoked={self.revoked})>"

    def is_valid(self) -> bool:
        """Check if session is valid (not revoked and not expired).

        Returns:
            True if session is valid
        """
        if self.revoked:
            return False

        if datetime.utcnow() > self.expires_at:
            return False

        return True

    def revoke(self) -> None:
        """Mark session as revoked."""
        self.revoked = True

    @classmethod
    def create(cls, merchant_id: int, token_hash: str, hours: int = 24) -> "Session":
        """Create a new session.

        Args:
            merchant_id: Merchant identifier
            token_hash: Hashed JWT token
            hours: Session lifetime in hours (default: 24)

        Returns:
            New Session instance
        """
        now = datetime.utcnow()
        expires_at = now + timedelta(hours=hours)

        return cls(
            merchant_id=merchant_id,
            token_hash=token_hash,
            created_at=now,
            expires_at=expires_at,
            revoked=False,
        )

    @classmethod
    def generate_session_id(cls) -> str:
        """Generate unique session identifier.

        Returns:
            UUID string
        """
        return str(uuid4())
