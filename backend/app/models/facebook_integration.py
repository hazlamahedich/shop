"""Facebook Integration ORM model.

Stores merchant's Facebook Page connection details including encrypted access token.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, Boolean, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class FacebookIntegration(Base):
    """Facebook Page integration model.

    Represents a merchant's connected Facebook Page with OAuth credentials.
    Stores encrypted access token and page metadata.
    """

    __tablename__ = "facebook_integrations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    merchant_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("merchants.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    page_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    page_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    page_picture_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    access_token_encrypted: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    scopes: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        Enum(
            "pending",
            "active",
            "error",
            name="facebook_status",
            create_type=False,
        ),
        default="pending",
        nullable=True,
    )
    webhook_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )
    last_webhook_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
    )
    connected_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
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
            f"<FacebookIntegration("
            f"id={self.id}, "
            f"merchant_id={self.merchant_id}, "
            f"page_id={self.page_id}, "
            f"status={self.status}"
            f")>"
        )
