"""Onboarding ORM model.

Stores prerequisite checklist completion state for merchants.
Migrated from localStorage in Story 1.2.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class PrerequisiteChecklist(Base):
    """Prerequisite checklist model.

    Stores the completion state of onboarding prerequisites.
    Created in Story 1.1 and used for migration in Story 1.2.
    """

    __tablename__ = "prerequisite_checklists"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    merchant_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("merchants.id"),
        nullable=False,
    )
    has_cloud_account: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    has_facebook_account: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    has_shopify_access: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    has_llm_provider_choice: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
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
        return f"<PrerequisiteChecklist(id={self.id}, merchant_id={self.merchant_id})>"

    @property
    def is_complete(self) -> bool:
        """Check if all prerequisites are complete."""
        return all([
            self.has_cloud_account,
            self.has_facebook_account,
            self.has_shopify_access,
            self.has_llm_provider_choice,
        ])

    def update_completed_at(self) -> None:
        """Update completed_at timestamp if all prerequisites are complete.

        This should be called after updating any of the prerequisite flags.
        """
        if self.is_complete and self.completed_at is None:
            self.completed_at = datetime.utcnow()
