"""Carrier configuration model for custom shipping carriers (Epic 6).

Allows merchants to configure custom shipping carriers with their own
tracking URL templates and optional tracking number patterns.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class CarrierConfig(Base):
    """Custom carrier configuration for a merchant.

    Merchants can add custom carriers that aren't in Shopify's supported list
    or the built-in pattern detection. This allows tracking links for local
    carriers (e.g., LBC, J&T in Philippines).
    """

    __tablename__ = "carrier_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    merchant_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("merchants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    carrier_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Display name of the carrier (e.g., 'LBC Express')",
    )
    tracking_url_template: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="URL template with {tracking_number} placeholder",
    )
    tracking_number_pattern: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="Optional regex pattern to auto-detect this carrier",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether this carrier config is active",
    )
    priority: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=50,
        comment="Detection priority (higher = checked first, 1-100)",
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

    merchant: Mapped[Merchant] = relationship(
        "Merchant",
        back_populates="carrier_configs",
    )

    def __repr__(self) -> str:
        return (
            f"<CarrierConfig("
            f"id={self.id}, "
            f"merchant_id={self.merchant_id}, "
            f"carrier_name={self.carrier_name}, "
            f"is_active={self.is_active}"
            f")>"
        )
