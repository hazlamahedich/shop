"""Merchant ORM model.

Represents a merchant account that has deployed the bot.
Each merchant has a unique merchant_key and stores deployment configuration.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, Boolean, DateTime, JSON
from sqlalchemy.dialects.postgresql import JSONB, ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Merchant(Base):
    """Merchant account model.

    Represents a deployed bot instance for a merchant.
    Stores deployment configuration and status.
    """

    __tablename__ = "merchants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    merchant_key: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )
    platform: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    # Use PostgreSQL ENUM to properly map to the database type
    status: Mapped[str] = mapped_column(
        ENUM(
            "pending", "active", "failed",
            name="merchant_status",
            create_type=False,  # Type already exists from migration
        ),
        default="pending",
        nullable=True,
    )
    config: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
    )

    # Relationships
    llm_configuration: Mapped[Optional["LLMConfiguration"]] = relationship(
        "LLMConfiguration",
        back_populates="merchant",
        uselist=False,  # One-to-one relationship
    )
    tutorial: Mapped[Optional["Tutorial"]] = relationship(
        "Tutorial",
        back_populates="merchant",
        uselist=False,  # One-to-one relationship
        passive_deletes="all",  # Let DB handle cascade deletes
    )

    secret_key_hash: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    deployed_at: Mapped[Optional[datetime]] = mapped_column(
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
        return f"<Merchant(id={self.id}, merchant_key={self.merchant_key}, status={self.status})>"
