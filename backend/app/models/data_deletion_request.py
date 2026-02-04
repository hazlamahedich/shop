"""Data Deletion Request ORM model.

Stores GDPR/CCPA compliance data deletion requests with audit trail.
Tracks status of deletion requests within 30-day processing window.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from enum import Enum

from sqlalchemy import String, Integer, DateTime, Text, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class DeletionStatus(str, Enum):
    """Status of data deletion request."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DataDeletionRequest(Base):
    """Data deletion request model for GDPR/CCPA compliance.

    Tracks user data deletion requests with audit trail.
    Complies with 30-day processing window requirement.
    """

    __tablename__ = "data_deletion_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    platform: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    status: Mapped[DeletionStatus] = mapped_column(
        SQLEnum(DeletionStatus, name="deletion_status", create_type=False),
        default=DeletionStatus.PENDING,
        nullable=False,
    )
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    deleted_items: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    def __repr__(self) -> str:
        return (
            f"<DataDeletionRequest("
            f"id={self.id}, "
            f"customer_id={self.customer_id}, "
            f"platform={self.platform}, "
            f"status={self.status}"
            f")>"
        )
