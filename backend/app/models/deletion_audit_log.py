"""Deletion Audit Log ORM model.

Story 6-2: Request Data Deletion
Story 6-5: 30-Day Retention Enforcement
Story 6-6: GDPR Deletion Processing

Persistent audit trail for data deletion requests (GDPR/CCPA compliance).
Tracks all immediate "forget preferences" deletions for compliance auditing.
Enhanced to track retention policy deletions (automated cleanup).
Enhanced for GDPR/CCPA 30-day compliance window tracking.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from sqlalchemy import String, Integer, DateTime, Text, Index, Enum as SQLEnum, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class DeletionTrigger(str, Enum):
    """Trigger type for data deletion."""

    MANUAL = "manual"  # User-requested deletion
    AUTO = "auto"  # Automated retention policy deletion


class DeletionRequestType(str, Enum):
    """Type of GDPR/CCPA deletion request."""

    MANUAL = "manual"  # "forget my preferences"
    GDPR_FORMAL = "gdpr_formal"  # Formal GDPR request via form/email
    CCPA_REQUEST = "ccpa_request"  # CCPA deletion request


class DeletionAuditLog(Base):
    """Persistent audit trail for data deletion requests.

    Story 6-2: Tracks immediate "forget preferences" deletions.
    Story 6-5: Enhanced to track automated retention policy deletions.
    Story 6-6: Enhanced for GDPR/CCPA 30-day compliance window tracking.

    Stores:
    - session_id: Widget session ID or PSID
    - visitor_id: Cross-platform identifier (optional)
    - customer_id: Customer ID for GDPR-level tracking (Story 6-6)
    - merchant_id: Merchant ID
    - deleted_counts: Number of conversations, messages, and Redis keys deleted
    - retention_period_days: Retention period for automated deletions (Story 6-5)
    - deletion_trigger: Whether deletion was manual or automated (Story 6-5)
    - request_type: GDPR/CCPA request type (Story 6-6)
    - request_timestamp: When GDPR request was received (Story 6-6)
    - processing_deadline: 30-day deadline from request (Story 6-6)
    - completion_date: When GDPR deletion was actually completed (Story 6-6)
    - confirmation_email_sent: Whether confirmation email was sent (Story 6-6)
    - email_sent_at: When confirmation email was sent (Story 6-6)
    - Timestamps and error tracking for compliance

    Attributes:
        id: Primary key
        session_id: Widget session ID or PSID that requested deletion
        visitor_id: Optional visitor identifier for cross-platform tracking
        customer_id: Customer ID for GDPR-level tracking (optional, for GDPR requests)
        merchant_id: Merchant ID
        retention_period_days: Retention period in days (null for manual deletions)
        deletion_trigger: Whether deletion was manual or automated
        request_type: Type of GDPR/CCPA request (manual, gdpr_formal, ccpa_request)
        request_timestamp: When GDPR request was received
        processing_deadline: 30-day deadline from request
        completion_date: When deletion was actually completed
        confirmation_email_sent: Whether confirmation email was sent
        email_sent_at: When confirmation email was sent
        requested_at: When deletion was requested
        completed_at: When deletion completed (or failed)
        conversations_deleted: Count of conversations deleted
        messages_deleted: Count of messages deleted
        redis_keys_cleared: Count of Redis keys cleared
        failed_redis_keys: JSON list of Redis keys that failed to delete
        error_message: Error message if deletion failed
    """

    __tablename__ = "deletion_audit_log"

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
    customer_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="Customer ID for GDPR-level tracking (optional)",
    )
    customer_email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Queued email address for confirmation email (deleted after sending)",
    )
    merchant_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )
    retention_period_days: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Retention period in days for automated deletions (null for manual)",
    )
    deletion_trigger: Mapped[str] = mapped_column(
        SQLEnum(
            DeletionTrigger,
            name="deletion_trigger",
            create_type=False,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        default=DeletionTrigger.MANUAL.value,
        nullable=False,
        comment="Whether deletion was manual (user-requested) or automated (retention policy)",
    )
    request_type: Mapped[Optional[str]] = mapped_column(
        SQLEnum(
            DeletionRequestType,
            name="deletion_request_type",
            create_type=False,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=True,
        default=DeletionRequestType.MANUAL.value,
        comment="Type of GDPR/CCPA deletion request",
    )
    request_timestamp: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When GDPR request was received",
    )
    processing_deadline: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="30-day deadline from request",
    )
    completion_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When GDPR deletion was actually completed",
    )
    confirmation_email_sent: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether confirmation email was sent",
    )
    email_sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When confirmation email was sent",
    )
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    conversations_deleted: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    messages_deleted: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    redis_keys_cleared: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    failed_redis_keys: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="JSON array of Redis keys that failed to delete for retry",
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    __table_args__ = (
        Index("ix_deletion_audit_log_merchant_requested", "merchant_id", "requested_at"),
        Index("ix_deletion_audit_log_gdpr_compliance", "processing_deadline", "completion_date"),
    )

    def __repr__(self) -> str:
        parts = [
            f"<DeletionAuditLog(",
            f"id={self.id}, ",
            f"session_id={self.session_id[:16]}..., ",
            f"merchant_id={self.merchant_id}, ",
        ]
        if self.customer_id:
            parts.append(f"customer_id={self.customer_id}, ")
        parts.extend(
            [
                f"conversations={self.conversations_deleted}, ",
                f"messages={self.messages_deleted}, ",
                f"trigger={self.deletion_trigger}",
            ]
        )
        if self.request_type:
            parts.append(f", request_type={self.request_type}")
        parts.append(")>")
        return "".join(parts)

    def mark_completed(
        self,
        conversations: int,
        messages: int,
        redis_keys: int,
        failed_redis_keys: Optional[list[str]] = None,
    ) -> None:
        """Mark deletion as completed with counts.

        Args:
            conversations: Number of conversations deleted
            messages: Number of messages deleted
            redis_keys: Number of Redis keys cleared
            failed_redis_keys: List of Redis keys that failed to delete
        """
        self.completed_at = datetime.now(timezone.utc)
        self.conversations_deleted = conversations
        self.messages_deleted = messages
        self.redis_keys_cleared = redis_keys
        if failed_redis_keys:
            import json

            self.failed_redis_keys = json.dumps(failed_redis_keys)

    def mark_failed(self, error_message: str) -> None:
        """Mark deletion as failed.

        Args:
            error_message: Error description
        """
        self.completed_at = datetime.now(timezone.utc)
        self.error_message = error_message
