"""Deployment log ORM model.

Stores log entries for deployment processes.
Used for tracking deployment progress and troubleshooting.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class DeploymentLog(Base):
    """Deployment log entry model.

    Stores individual log messages from deployment processes.
    Supports tracking progress, errors, and troubleshooting.
    """

    __tablename__ = "deployment_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    deployment_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        index=True,
    )
    merchant_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("merchants.id"),
        nullable=False,
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        index=True,
        nullable=False,
    )
    level: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )
    step: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<DeploymentLog(id={self.id}, deployment_id={self.deployment_id}, level={self.level})>"
