"""Merchant ORM model - Personality Type Fix."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import ENUM, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.budget_alert import BudgetAlert
    from app.models.carrier_config import CarrierConfig
    from app.models.customer_profile import CustomerProfile
    from app.models.dispute import Dispute
    from app.models.faq import Faq
    from app.models.handoff_alert import HandoffAlert
    from app.models.knowledge_base import KnowledgeDocument
    from app.models.llm_configuration import LLMConfiguration
    from app.models.order import Order
    from app.models.product_pin import ProductPin, ProductPinAnalytics
    from app.models.tutorial import Tutorial
    from app.models.widget_analytics_event import WidgetAnalyticsEvent


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


class OnboardingMode(str, Enum):
    """Merchant onboarding mode (Epic 8).

    - general: General chatbot mode (no Shopify, knowledge base Q&A)
    - ecommerce: E-commerce mode (Shopify integration, product search, orders)
    """

    GENERAL = "general"
    ECOMMERCE = "ecommerce"


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
        server_default="widget",
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
    config: Mapped[dict | None] = mapped_column(
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
    custom_greeting: Mapped[str | None] = mapped_column(
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
    business_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    business_description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    business_hours: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )
    business_hours_config: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    # Bot naming configuration (Story 1.12)
    bot_name: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    # Authentication fields (Story 1.8)
    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
    )
    password_hash: Mapped[str | None] = mapped_column(
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

    # Onboarding mode (Epic 8, Story 8.1)
    onboarding_mode: Mapped[str] = mapped_column(
        String(20),
        default=OnboardingMode.GENERAL.value,
        nullable=False,
        server_default="general",
        index=True,
    )

    # Embedding provider configuration (Story 8-11)
    embedding_provider: Mapped[str] = mapped_column(
        String(20),
        default="openai",
        nullable=False,
        server_default="openai",
    )
    embedding_model: Mapped[str] = mapped_column(
        String(50),
        default="text-embedding-3-small",
        nullable=False,
        server_default="text-embedding-3-small",
    )
    embedding_dimension: Mapped[int] = mapped_column(
        Integer,
        default=1536,
        nullable=False,
        server_default="1536",
    )

    # Widget configuration (Story 5-1)
    widget_config: Mapped[dict | None] = mapped_column(
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
    product_pin_analytics: Mapped[list["ProductPinAnalytics"]] = relationship(
        "ProductPinAnalytics",
        back_populates="merchant",
        cascade="all, delete-orphan",
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
    orders: Mapped[list["Order"]] = relationship(
        "Order",
        back_populates="merchant",
        cascade="all, delete-orphan",
        order_by="Order.created_at.desc()",
    )
    customer_profiles: Mapped[list["CustomerProfile"]] = relationship(
        "CustomerProfile",
        back_populates="merchant",
        cascade="all, delete-orphan",
    )
    disputes: Mapped[list["Dispute"]] = relationship(
        "Dispute",
        back_populates="merchant",
        cascade="all, delete-orphan",
        order_by="Dispute.created_at.desc()",
    )
    carrier_configs: Mapped[list["CarrierConfig"]] = relationship(
        "CarrierConfig",
        back_populates="merchant",
        cascade="all, delete-orphan",
        order_by="CarrierConfig.priority.desc()",
    )
    knowledge_documents: Mapped[list["KnowledgeDocument"]] = relationship(
        "KnowledgeDocument",
        back_populates="merchant",
        cascade="all, delete-orphan",
        order_by="KnowledgeDocument.created_at.desc()",
    )
    widget_analytics_events: Mapped[list["WidgetAnalyticsEvent"]] = relationship(
        "WidgetAnalyticsEvent",
        back_populates="merchant",
        cascade="all, delete-orphan",
    )
    knowledge_gaps: Mapped[list["KnowledgeGap"]] = relationship(
        "KnowledgeGap",
        back_populates="merchant",
        cascade="all, delete-orphan",
        order_by="desc(KnowledgeGap.last_occurred_at)",
    )

    secret_key_hash: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    deployed_at: Mapped[datetime | None] = mapped_column(
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
        return f"<Merchant(id={self.id}, merchant_key={self.merchant_key}, status={self.status}, personality={self.personality}, onboarding_mode={self.onboarding_mode})>"
