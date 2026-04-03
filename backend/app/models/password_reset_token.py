"""Password Reset Token ORM model.

Stores temporary tokens for password reset flow.
Tokens expire after 1 hour and can only be used once.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.merchant import Merchant


class PasswordResetToken(Base):
    """Password reset token model.

    Stores secure tokens for password reset flow.
    Each token is valid for 1 hour and can only be used once.
    """

    __tablename__ = "password_reset_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    merchant_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("merchants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )
    used_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_password_reset_tokens_merchant_token", "merchant_id", "token"),
    )

    merchant: Mapped["Merchant"] = relationship(
        "Merchant",
        backref="password_reset_tokens",
    )

    def __repr__(self) -> str:
        return (
            f"<PasswordResetToken("
            f"id={self.id}, "
            f"merchant_id={self.merchant_id}, "
            f"expires_at={self.expires_at}, "
            f"used={self.used_at is not None}"
            f")>"
        )

    def is_valid(self) -> bool:
        """Check if token is valid (not expired and not used).

        Returns:
            True if token is valid, False otherwise
        """
        if self.used_at is not None:
            return False
        if datetime.now(timezone.utc) > self.expires_at:
            return False
        return True
