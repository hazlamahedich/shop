"""Widget Analytics Event Model

Story 9-10: Analytics & Performance Monitoring

Stores analytics events from widget usage.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.merchant import Merchant


class WidgetAnalyticsEvent(Base):
    """Analytics event from widget usage."""

    __tablename__ = "widget_analytics_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id: Mapped[int] = mapped_column(Integer, ForeignKey("merchants.id"), nullable=False)
    session_id: Mapped[str] = mapped_column(String(100), nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    event_metadata: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    merchant: Mapped[Merchant | None] = relationship(back_populates="widget_analytics_events")

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "merchant_id": self.merchant_id,
            "session_id": self.session_id,
            "event_type": self.event_type,
            "metadata": dict(self.event_metadata) if self.event_metadata else {},
            "timestamp": self.timestamp.isoformat(),
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self) -> str:
        return f"WidgetAnalyticsEvent(event_type={self.event_type}, merchant_id={self.merchant_id}, session_id={self.session_id})"
