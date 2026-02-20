"""Shopify Integration ORM model.

Stores merchant's Shopify store connection details including encrypted access tokens.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, Boolean, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ShopifyIntegration(Base):
    """Shopify store integration model.

    Represents a merchant's connected Shopify store with OAuth credentials.
    Stores encrypted Admin API and Storefront API tokens.
    """

    __tablename__ = "shopify_integrations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    merchant_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("merchants.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    shop_domain: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )
    shop_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    storefront_token_encrypted: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    admin_token_encrypted: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    scopes: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        Enum(
            "pending",
            "active",
            "error",
            name="shopify_status",
            create_type=False,
        ),
        default="pending",
        nullable=True,
    )
    storefront_api_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )
    admin_api_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )
    webhook_subscribed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )
    webhook_topic_subscriptions: Mapped[Optional[list]] = mapped_column(
        JSONB,
        nullable=True,
    )
    last_webhook_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
    )
    last_webhook_verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
    )
    connected_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
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
            f"<ShopifyIntegration("
            f"id={self.id}, "
            f"merchant_id={self.merchant_id}, "
            f"shop_domain={self.shop_domain}, "
            f"status={self.status}"
            f")>"
        )
