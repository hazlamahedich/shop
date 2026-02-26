"""Deletion Audit Log ORM model.

Story 6-2: Request Data Deletion

Persistent audit trail for data deletion requests (GDPR/CCPA compliance).
Tracks all immediate "forget preferences" deletions for compliance auditing.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, Integer, DateTime, Text, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class DeletionAuditLog(Base):
    """Persistent audit trail for data deletion requests.

    Story 6-2: Tracks immediate "forget preferences" deletions.

    Stores:
    - session_id: Widget session ID or PSID
    - visitor_id: Cross-platform identifier (optional)
    - merchant_id: Merchant ID
    - deleted_counts: Number of conversations, messages, and Redis keys deleted
    - Timestamps and error tracking for compliance

    Attributes:
        id: Primary key
        session_id: Widget session ID or PSID that requested deletion
        visitor_id: Optional visitor identifier for cross-platform tracking
        merchant_id: Merchant ID
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
    merchant_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
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
    )

    def __repr__(self) -> str:
        return (
            f"<DeletionAuditLog("
            f"id={self.id}, "
            f"session_id={self.session_id[:16]}..., "
            f"merchant_id={self.merchant_id}, "
            f"conversations={self.conversations_deleted}, "
            f"messages={self.messages_deleted}"
            f")>"
        )

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
