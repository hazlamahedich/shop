"""Tutorial ORM model.

Stores tutorial progress per merchant including current step,
completed steps, timestamps, and skip status.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Tutorial(Base):
    """Tutorial progress model.

    Stores tutorial progress for each merchant including:
    - Current step number
    - Completed steps list
    - Start and completion timestamps
    - Skip status
    - Tutorial version for future updates
    """

    __tablename__ = "tutorials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    merchant_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("merchants.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Relationship to Merchant for proper ORM ordering
    merchant: Mapped["Merchant"] = relationship(
        "Merchant",
        back_populates="tutorial",
    )

    # Tutorial state
    current_step: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )
    completed_steps: Mapped[list[str]] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
    )
    skipped: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Tutorial metadata
    tutorial_version: Mapped[str] = mapped_column(
        String(10),
        default="1.0",
        nullable=False,
    )
    steps_total: Mapped[int] = mapped_column(
        Integer,
        default=4,
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
            f"<Tutorial(id={self.id}, merchant_id={self.merchant_id}, "
            f"current_step={self.current_step}, skipped={self.skipped})>"
        )
