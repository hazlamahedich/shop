"""Pydantic schemas for UnifiedConversationService.

Story 5-10: Widget Full App Integration
Task 1: Create UnifiedConversationService

Defines the data structures for cross-channel message processing.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class Channel(str, Enum):
    """Supported conversation channels."""

    WIDGET = "widget"
    MESSENGER = "messenger"
    PREVIEW = "preview"


class ConversationContext(BaseModel):
    """Normalized context for any channel.

    Story 5-10 Enhancement: Added is_returning_shopper for personalized greetings.

    Provides a unified interface for message processing across
    Widget, Facebook Messenger, and Preview channels.
    """

    session_id: str = Field(description="Universal identifier (psid or widget_session_id)")
    merchant_id: int = Field(description="Merchant ID")
    channel: Channel = Field(description="Source channel")
    conversation_history: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Recent conversation messages",
    )
    platform_sender_id: Optional[str] = Field(
        None,
        description="Facebook PSID (for messenger channel)",
    )
    user_id: Optional[int] = Field(
        None,
        description="User ID (for preview channel)",
    )
    is_returning_shopper: bool = Field(
        default=False,
        description="Whether this visitor has previous sessions",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context metadata (clarification state, etc.)",
    )

    class Config:
        use_enum_values = True


class ConversationResponse(BaseModel):
    """Response from UnifiedConversationService.process_message()."""

    message: str = Field(description="Response message text")
    intent: Optional[str] = Field(None, description="Classified intent")
    confidence: Optional[float] = Field(None, description="Classification confidence")
    checkout_url: Optional[str] = Field(None, description="Checkout URL if applicable")
    fallback: bool = Field(False, description="True if using fallback response")
    fallback_url: Optional[str] = Field(None, description="Fallback URL if degraded")
    products: Optional[list[dict[str, Any]]] = Field(
        None,
        description="Product results if applicable",
    )
    cart: Optional[dict[str, Any]] = Field(None, description="Cart state if applicable")
    order: Optional[dict[str, Any]] = Field(None, description="Order info if applicable")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata",
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses."""
        return self.model_dump(exclude_none=True)


class IntentType(str, Enum):
    """Supported intent types for unified routing.

    Extends the existing IntentType from classification_schema
    with additional intents needed for unified processing.
    """

    PRODUCT_SEARCH = "product_search"
    GREETING = "greeting"
    CLARIFICATION = "clarification"
    CART_VIEW = "cart_view"
    CART_ADD = "cart_add"
    CART_REMOVE = "cart_remove"
    CHECKOUT = "checkout"
    ORDER_TRACKING = "order_tracking"
    HUMAN_HANDOFF = "human_handoff"
    FORGET_PREFERENCES = "forget_preferences"
    GENERAL = "general"
    UNKNOWN = "unknown"
