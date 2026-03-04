"""Data Export Audit Log Model

Audit trail for merchant data exports (GDPR compliance).
Based on DeletionAuditLog pattern from Story 6-2.
"""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Integer, DateTime, Text, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.core.database import Base


class DataExportAuditLog(Base):
    """Audit trail for merchant data exports (GDPR compliance)."""

    __tablename__ = "data_export_audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    merchant_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    conversations_exported: Mapped[int] = mapped_column(Integer, default=0)
    messages_exported: Mapped[int] = mapped_column(Integer, default=0)
    opted_out_excluded: Mapped[int] = mapped_column(
        Integer, default=0, comment="Number of opted-out conversations excluded (GDPR compliance)"
    )

    file_size_bytes: Mapped[Optional[int]] = mapped_column(Integer)
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    __table_args__ = (Index("ix_export_audit_merchant_requested", "merchant_id", "requested_at"),)

    def mark_completed(self, conversations: int, messages: int, excluded: int, size: int) -> None:
        """Mark export as completed with counts."""
        self.completed_at = datetime.now(timezone.utc)
        self.conversations_exported = conversations
        self.messages_exported = messages
        self.opted_out_excluded = excluded
        self.file_size_bytes = size
