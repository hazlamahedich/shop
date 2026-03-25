"""Pydantic schemas for UnifiedConversationService.

Story 5-10: Widget Full App Integration
Task 1: Create UnifiedConversationService

Defines the data structures for cross-channel message processing.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field

SourceDocumentType = Literal["pdf", "url", "text"]


class SourceCitation(BaseModel):
    """Source citation for RAG-based responses.

    Story 10-1: Source Citations Widget

    Attributes:
        document_id: ID of the source document
        title: Document title for display
        document_type: Type of document (pdf, url, text)
        relevance_score: Similarity score from RAG retrieval (0.0 to 1.0)
        url: Optional URL for web documents
        chunk_index: Optional chunk index that was used
    """

    document_id: int = Field(description="Document ID")
    title: str = Field(description="Document title")
    filename: str | None = Field(default=None, description="Source file name")
    document_type: SourceDocumentType = Field(description="Document type: pdf, url, text")
    relevance_score: float = Field(
        ge=0.0, le=1.0, description="Similarity score from RAG retrieval"
    )
    url: str | None = Field(default=None, description="URL for web documents")
    chunk_index: int | None = Field(default=None, description="Chunk index that was used")


class Channel(str, Enum):
    """Supported conversation channels."""

    WIDGET = "widget"
    MESSENGER = "messenger"
    PREVIEW = "preview"


class ConsentState(BaseModel):
    """Tracks consent state within a conversation.

    Story 6-1: Opt-In Consent Flow
    Task 3.1: Consent check integration
    Story 6-2: Added visitor_id for cross-platform deletion
    """

    prompt_shown: bool = Field(default=False, description="Whether consent prompt has been shown")
    can_store_conversation: bool = Field(
        default=False, description="Whether conversation data can be stored"
    )
    status: str = Field(
        default="pending", description="Consent status: pending, opted_in, opted_out"
    )
    visitor_id: str | None = Field(
        None, description="Visitor identifier for cross-session tracking"
    )


class ClarificationState(BaseModel):
    """Tracks clarification flow state within a conversation.

    Story 5-11: Messenger Unified Service Migration
    GAP-3: Clarification State Tracking
    """

    active: bool = Field(default=False, description="Whether clarification flow is active")
    attempt_count: int = Field(default=0, description="Number of clarification attempts")
    questions_asked: list[str] = Field(
        default_factory=list,
        description="List of constraint types asked about",
    )
    last_question: str | None = Field(None, description="Last question asked")
    last_type: str | None = Field(None, description="Last clarification type")


class HandoffState(BaseModel):
    """Tracks handoff detection state within a conversation.

    Story 5-11: Messenger Unified Service Migration
    GAP-1: Handoff Detection State Tracking
    """

    consecutive_low_confidence: int = Field(
        default=0, description="Consecutive low confidence count"
    )
    last_handoff_check: str | None = Field(None, description="ISO timestamp of last check")


class SessionShoppingState(BaseModel):
    """Tracks shopping-related state within a conversation session.

    Enables context-aware responses for:
    - Anaphoric references ("add that to cart")
    - Product mention detection
    - Personalized recommendations
    """

    last_viewed_products: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Last 5 products shown to user",
        max_length=5,
    )
    last_search_query: str | None = Field(
        None,
        description="Most recent search query",
    )
    last_search_category: str | None = Field(
        None,
        description="Most recent product category searched",
    )
    interested_product_ids: list[str] = Field(
        default_factory=list,
        description="Product IDs user has shown interest in",
    )
    last_cart_item_count: int = Field(
        default=0,
        description="Number of items in cart at last check",
    )

    def add_viewed_product(self, product: dict[str, Any]) -> None:
        """Add a product to viewed history, maintaining max 5."""
        product_id = product.get("id")
        # Remove if already exists (will be added at front)
        self.last_viewed_products = [
            p for p in self.last_viewed_products if p.get("id") != product_id
        ]
        self.last_viewed_products.insert(0, product)
        # Keep only last 5
        self.last_viewed_products = self.last_viewed_products[:5]

    def get_last_viewed_product(self) -> dict[str, Any] | None:
        """Get the most recently viewed product."""
        return self.last_viewed_products[0] if self.last_viewed_products else None

    def find_product_by_reference(
        self,
        reference: str,
    ) -> dict[str, Any] | None:
        """Find a product by reference term (first, last, by name/brand).

        Args:
            reference: Term like "first", "last", "the red one", "nike", etc.

        Returns:
            Matching product or None
        """
        if not self.last_viewed_products:
            return None

        ref_lower = reference.lower().strip()

        # Positional references
        if ref_lower in ("first", "that one", "it", "this one", "the first one"):
            return self.last_viewed_products[0]
        if ref_lower in ("second", "the second one") and len(self.last_viewed_products) > 1:
            return self.last_viewed_products[1]
        if ref_lower in ("third", "the third one") and len(self.last_viewed_products) > 2:
            return self.last_viewed_products[2]
        if ref_lower in ("last", "the last one"):
            return self.last_viewed_products[-1]

        # Search by title/brand
        for product in self.last_viewed_products:
            title = (product.get("title") or "").lower()
            if ref_lower in title:
                return product

        return None


class ConversationContext(BaseModel):
    """Normalized context for any channel.

    Story 5-10 Enhancement: Added is_returning_shopper for personalized greetings.
    Story 5-11 Enhancement: Added clarification_state, handoff_state, consent_status, hybrid_mode_enabled.

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
    platform_sender_id: str | None = Field(
        None,
        description="Facebook PSID (for messenger channel)",
    )
    user_id: int | None = Field(
        None,
        description="User ID (for preview channel)",
    )
    is_returning_shopper: bool = Field(
        default=False,
        description="Whether this visitor has previous sessions",
    )
    shopping_state: SessionShoppingState = Field(
        default_factory=SessionShoppingState,
        description="Shopping session state (viewed products, searches)",
    )
    clarification_state: ClarificationState = Field(
        default_factory=ClarificationState,
        description="Clarification flow state (GAP-3)",
    )
    handoff_state: HandoffState = Field(
        default_factory=HandoffState,
        description="Handoff detection state (GAP-1)",
    )
    consent_state: ConsentState = Field(
        default_factory=ConsentState,
        description="Consent state for conversation data (Story 6-1)",
    )
    consent_status: str | None = Field(
        None,
        description="Consent status: none, pending, granted, denied (GAP-4) - DEPRECATED: use consent_state",
    )
    pending_consent_product: dict[str, Any] | None = Field(
        None,
        description="Pending product awaiting consent (GAP-4)",
    )
    hybrid_mode_enabled: bool = Field(
        default=False,
        description="Whether hybrid mode is active (GAP-5)",
    )
    hybrid_mode_expires_at: str | None = Field(
        None,
        description="ISO timestamp when hybrid mode expires (GAP-5)",
    )
    last_activity_at: str | None = Field(
        None,
        description="ISO timestamp of last activity (GAP-7)",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context metadata (clarification state, etc.)",
    )
    conversation_data: dict[str, Any] | None = Field(
        None,
        description="Persistent conversation metadata from database (cross-device lookup state, etc.)",
    )

    class Config:
        use_enum_values = True


class ConversationResponse(BaseModel):
    """Response from UnifiedConversationService.process_message().

    Story 9-4: Added quick_replies for quick reply buttons.
    Story 10-1: Added sources for RAG-based response citations.
    Story 10-3: Added suggested_replies for follow-up question suggestions.
    """

    message: str = Field(description="Response message text")
    message_id: int | None = Field(
        None, description="Database ID of the bot message"
    )
    intent: str | None = Field(None, description="Classified intent")
    confidence: float | None = Field(None, description="Classification confidence")
    checkout_url: str | None = Field(None, description="Checkout URL if applicable")
    fallback: bool = Field(False, description="True if using fallback response")
    fallback_url: str | None = Field(None, description="Fallback URL if degraded")
    products: list[dict[str, Any]] | None = Field(
        None,
        description="Product results if applicable",
    )
    cart: dict[str, Any] | None = Field(None, description="Cart state if applicable")
    order: dict[str, Any] | None = Field(None, description="Order info if applicable")
    quick_replies: list[dict[str, Any]] | None = Field(
        None,
        description="Quick reply buttons for user response (Story 9-4)",
    )
    sources: list[dict[str, Any]] | None = Field(
        None,
        description="RAG source citations for knowledge-based responses (Story 10-1)",
    )
    suggested_replies: list[str] | None = Field(
        default=None,
        description="Server-generated follow-up question suggestions (Story 10-3)",
    )
    contact_options: list[dict[str, Any]] | None = Field(
        None,
        description="Contact options for escalation (Story 10-5)",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata",
    )

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
    PRODUCT_INQUIRY = "product_inquiry"
    PRODUCT_COMPARISON = "product_comparison"
    GREETING = "greeting"
    CLARIFICATION = "clarification"
    CART_VIEW = "cart_view"
    CART_ADD = "cart_add"
    CART_REMOVE = "cart_remove"
    CART_CLEAR = "cart_clear"
    ADD_LAST_VIEWED = "add_last_viewed"
    CHECKOUT = "checkout"
    ORDER_TRACKING = "order_tracking"
    HUMAN_HANDOFF = "human_handoff"
    FORGET_PREFERENCES = "forget_preferences"
    CHECK_CONSENT_STATUS = "check_consent_status"
    GENERAL = "general"
    UNKNOWN = "unknown"
