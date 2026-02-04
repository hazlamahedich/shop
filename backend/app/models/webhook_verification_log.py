"""Webhook Verification Log ORM model.

Stores webhook verification test results for troubleshooting and audit.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class WebhookVerificationLog(Base):
    """Webhook verification test log model.

    Records all webhook verification attempts including status checks,
    test webhooks, and re-subscriptions for troubleshooting purposes.
    """

    __tablename__ = "webhook_verification_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    merchant_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("merchants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Test details
    platform: Mapped[str] = mapped_column(
        Enum(
            "facebook",
            "shopify",
            name="verification_platform",
            create_type=False,
        ),
        nullable=False,
        index=True,
    )
    test_type: Mapped[str] = mapped_column(
        Enum(
            "status_check",
            "test_webhook",
            "resubscribe",
            name="test_type",
            create_type=False,
        ),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        Enum(
            "pending",
            "success",
            "failed",
            name="verification_status",
            create_type=False,
        ),
        default="pending",
        nullable=False,
    )

    # Results
    error_message: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    error_code: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    diagnostic_data: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
    )

    # Timing
    started_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
    )
    duration_ms: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<WebhookVerificationLog("
            f"id={self.id}, "
            f"merchant_id={self.merchant_id}, "
            f"platform={self.platform}, "
            f"test_type={self.test_type}, "
            f"status={self.status}"
            f")>"
        )
