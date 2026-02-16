"""Merchant ORM model - Personality Type Fix."""

from datetime import datetime
from typing import Optional
from enum import Enum

from sqlalchemy import String, Integer, DateTime, Text, Boolean
from sqlalchemy.dialects.postgresql import JSONB, ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class PersonalityType(str, Enum):
    """Personality types for bot responses (Story 1.10)."""

    FRIENDLY = "friendly"
    PROFESSIONAL = "professional"
    ENTHUSIASTIC = "enthusiastic"


class StoreProvider(str, Enum):
    """E-commerce store provider types (Sprint Change Proposal 2026-02-13).

    Indicates which e-commerce platform (if any) the merchant has connected.
    """

    NONE = "none"  # No store connected - Facebook-only mode
    SHOPIFY = "shopify"  # Shopify store connected
    WOOCOMMERCE = "woocommerce"  # Future: WooCommerce integration
    BIGCOMMERCE = "bigcommerce"  # Future: BigCommerce integration


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
            "pending",
            "active",
            "failed",
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
    # Bot personality configuration (Story 1.10)
    personality: Mapped[PersonalityType] = mapped_column(
        ENUM(
            PersonalityType,
            name="personality_type",
            create_type=False,
            values_callable=lambda x: [e.value for e in PersonalityType],
        ),
        default=PersonalityType.FRIENDLY,
        nullable=False,
    )
    custom_greeting: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    # Greeting configuration (Story 1.14)
    use_custom_greeting: Mapped[bool] = mapped_column(
        Boolean,  # type: ignore
        default=False,
        nullable=False,
        server_default="false",
    )

    # Business information (Story 1.11)
    business_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    business_description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    business_hours: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
    )
    business_hours_config: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
    )

    # Bot naming configuration (Story 1.12)
    bot_name: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )

    # Authentication fields (Story 1.8)
    email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
    )
    password_hash: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    # E-commerce store provider (Sprint Change Proposal 2026-02-13)
    store_provider: Mapped[str] = mapped_column(
        String(20),
        default=StoreProvider.NONE.value,
        nullable=False,
        server_default="none",
        index=True,  # Index for common query pattern
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
    faqs: Mapped[list["Faq"]] = relationship(
        "Faq",
        back_populates="merchant",
        cascade="all, delete-orphan",
        order_by="Faq.order_index",
    )
    product_pins: Mapped[list["ProductPin"]] = relationship(
        "ProductPin",
        back_populates="merchant",
        cascade="all, delete-orphan",
        order_by="ProductPin.pinned_order",
    )
    budget_alerts: Mapped[list["BudgetAlert"]] = relationship(
        "BudgetAlert",
        back_populates="merchant",
        cascade="all, delete-orphan",
        order_by="BudgetAlert.created_at.desc()",
    )
    handoff_alerts: Mapped[list["HandoffAlert"]] = relationship(
        "HandoffAlert",
        back_populates="merchant",
        cascade="all, delete-orphan",
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
        return f"<Merchant(id={self.id}, merchant_key={self.merchant_key}, status={self.status}, personality={self.personality})>"
