"""Widget schemas for embeddable chat widget API.

Provides request/response schemas for widget session management,
messaging, and configuration endpoints.

Story 5.1: Backend Widget API
Story 5.5: Theme Customization System
Story 9-6: Proactive Engagement Triggers
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Literal

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema, MetaData, MinimalEnvelope


class QuickReply(BaseSchema):
    """Quick reply button for bot messages.

    Story 9-4: Quick Reply Buttons

    Attributes:
        id: Unique identifier for the quick reply
        text: Display text for the button
        icon: Optional icon/emoji to display before text
        payload: Optional payload to send when clicked (defaults to text)
    """

    id: str = Field(description="Unique identifier")
    text: str = Field(max_length=50, description="Button display text")
    icon: str | None = Field(default=None, max_length=10, description="Optional icon/emoji")
    payload: str | None = Field(default=None, max_length=100, description="Optional payload string")


SourceDocumentType = Literal["pdf", "url", "text"]


class SourceCitation(BaseSchema):
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

    document_id: int = Field(alias="documentId", description="Document ID")
    title: str = Field(description="Document title")
    filename: str | None = Field(default=None, description="Source file name")
    document_type: SourceDocumentType = Field(
        alias="documentType", description="Document type: pdf, url, text"
    )
    relevance_score: float = Field(
        alias="relevanceScore", ge=0.0, le=1.0, description="Relevance score"
    )
    url: str | None = Field(default=None, description="Source URL")
    chunk_index: int | None = Field(default=None, alias="chunkIndex", description="Chunk index")
    metadata: dict[str, Any] | None = Field(default=None, description="Additional metadata")


class VoiceInputConfig(BaseSchema):
    """Voice input configuration for widget.

    Story 9-5: Voice Input Interface

    Attributes:
        enabled: Whether voice input is enabled
        language: BCP 47 language tag (e.g., 'en-US')
        continuous: Whether to continuously listen
        interim_results: Whether to show interim results
    """

    enabled: bool = Field(default=True, description="Whether voice input is enabled")
    language: str = Field(default="en-US", max_length=10, description="BCP 47 language tag")
    continuous: bool = Field(default=False, description="Continuous listening mode")
    interim_results: bool = Field(default=True, description="Show interim results")


TriggerType = Literal[
    "exit_intent", "time_on_page", "scroll_depth", "cart_abandonment", "product_view"
]


class ProactiveTriggerActionSchema(BaseSchema):
    """Action button for proactive engagement modal.

    Story 9-6: Proactive Engagement Triggers

    Attributes:
        text: Button display text
        pre_populated_message: Optional message to pre-fill in chat input
    """

    text: str = Field(min_length=1, max_length=100, description="Button display text")
    pre_populated_message: str | None = Field(
        default=None, max_length=500, description="Message to pre-fill in chat input"
    )


class ProactiveTriggerSchema(BaseSchema):
    """Configuration for a single proactive trigger.

    Story 9-6: Proactive Engagement Triggers

    Attributes:
        type: Trigger type (exit_intent, time_on_page, scroll_depth, cart_abandonment, product_view)
        enabled: Whether this trigger is enabled
        threshold: Threshold value (varies by type: seconds for time_on_page, percent for scroll_depth, count for product_view)
        message: Message to display when trigger fires
        actions: Action buttons to show in the modal
        cooldown: Cooldown period in minutes (1-1440)
    """

    type: TriggerType = Field(description="Trigger type")
    enabled: bool = Field(default=True, description="Whether this trigger is enabled")
    threshold: int | None = Field(
        default=None, ge=1, le=100, description="Threshold value (varies by type)"
    )
    message: str = Field(min_length=1, max_length=500, description="Message to display")
    actions: list[ProactiveTriggerActionSchema] = Field(
        default_factory=list, description="Action buttons"
    )
    cooldown: int = Field(
        ge=1, le=1440, default=30, description="Cooldown in minutes (1 min - 24 hours)"
    )


class ProactiveEngagementConfigSchema(BaseSchema):
    """Configuration for proactive engagement feature.

    Story 9-6: Proactive Engagement Triggers

    Attributes:
        enabled: Whether proactive engagement is enabled
        triggers: List of trigger configurations
    """

    enabled: bool = Field(default=True, description="Whether proactive engagement is enabled")
    triggers: list[ProactiveTriggerSchema] = Field(
        default_factory=list, description="List of trigger configurations"
    )


class WidgetTheme(BaseSchema):
    """Theme configuration for widget appearance.

    Attributes:
        primary_color: Primary brand color (hex)
        background_color: Widget background color (hex)
        text_color: Text color (hex)
        bot_bubble_color: Bot message bubble color (hex)
        user_bubble_color: User message bubble color (hex)
        position: Widget position on page
        border_radius: Border radius in pixels (0-24)
        width: Widget width in pixels (280-600)
        height: Widget height in pixels (400-900)
        font_family: CSS font-family value
        font_size: Base font size in pixels (12-20)
    """

    primary_color: str = Field(default="#6366f1", pattern=r"^#[0-9a-fA-F]{6}$")
    background_color: str = Field(default="#ffffff", pattern=r"^#[0-9a-fA-F]{6}$")
    text_color: str = Field(default="#1f2937", pattern=r"^#[0-9a-fA-F]{6}$")
    bot_bubble_color: str = Field(default="#f3f4f6", pattern=r"^#[0-9a-fA-F]{6}$")
    user_bubble_color: str = Field(default="#6366f1", pattern=r"^#[0-9a-fA-F]{6}$")
    position: str = Field(default="bottom-right", pattern=r"^(bottom-right|bottom-left)$")
    border_radius: int = Field(default=16, ge=0, le=24)
    width: int = Field(default=380, ge=280, le=600)
    height: int = Field(default=600, ge=400, le=900)
    font_family: str = Field(default="Inter, sans-serif", max_length=200)
    font_size: int = Field(default=14, ge=12, le=20)

    @field_validator("font_family")
    @classmethod
    def sanitize_font_family(cls, v: str) -> str:
        return re.sub(r'[<>"\']', "", v)


class WidgetConfig(BaseSchema):
    """Widget configuration for a merchant.

    Attributes:
        enabled: Whether widget is enabled
        bot_name: Display name for the bot
        welcome_message: Initial greeting message
        theme: Visual theme configuration
        allowed_domains: Optional domain whitelist for CORS
        rate_limit: Optional per-merchant rate limit (requests per minute)
        feedback_enabled: Whether feedback rating collection is enabled (Story 10-4)
    """

    enabled: bool = Field(default=True)
    bot_name: str = Field(default="Mantisbot", max_length=50)
    welcome_message: str = Field(
        default="Hi! How can I help you today?",
        max_length=500,
    )
    theme: WidgetTheme = Field(default_factory=WidgetTheme)
    allowed_domains: list[str] = Field(default_factory=list)
    rate_limit: int | None = Field(default=None, ge=1, le=1000)
    feedback_enabled: bool = Field(
        default=True, description="Whether feedback rating collection is enabled"
    )
    contact_options: list[ContactOptionSchema] | None = Field(
        default=None, description="Contact options for escalation (Story 10-5)"
    )


class WidgetSessionData(BaseSchema):
    """Widget session data stored in Redis.

    Story 5-10 Enhancement: Added visitor_id and is_returning_shopper.
    Story 6-2 Enhancement: Added metadata for session state persistence.

    Attributes:
        session_id: Unique session identifier (UUID)
        merchant_id: Associated merchant ID
        created_at: Session creation timestamp
        last_activity_at: Last activity timestamp
        expires_at: Session expiry timestamp
        visitor_ip: Optional visitor IP for analytics
        user_agent: Optional user agent for analytics
        visitor_id: Optional visitor identifier for cross-session tracking
        is_returning_shopper: Whether this visitor has previous sessions
        metadata: Optional metadata for session state (pending lookups, etc.)
    """

    session_id: str
    merchant_id: int
    created_at: datetime
    last_activity_at: datetime
    expires_at: datetime
    visitor_ip: str | None = None
    user_agent: str | None = None
    visitor_id: str | None = None
    is_returning_shopper: bool = False
    metadata: dict[str, Any] | None = None
    customer_name: str | None = None


class CreateSessionRequest(BaseSchema):
    """Request to create a new widget session.

    Story 5-10 Enhancement: Added visitor_id for returning shopper detection.

    Attributes:
        merchant_id: The merchant ID to create session for
        visitor_id: Optional visitor identifier for returning shopper detection
    """

    merchant_id: int
    visitor_id: str | None = Field(
        default=None, description="Visitor ID for returning shopper detection"
    )


class WidgetSessionResponse(BaseSchema):
    """Response for session creation.

    Attributes:
        session_id: Unique session identifier
        expires_at: Session expiry timestamp
    """

    session_id: str
    expires_at: datetime


class WidgetSessionMetadataResponse(BaseSchema):
    """Response for session metadata retrieval.

    Attributes:
        session_id: Unique session identifier
        merchant_id: Associated merchant ID
        expires_at: Session expiry timestamp
        created_at: Session creation timestamp
        last_activity_at: Last activity timestamp
    """

    session_id: str
    merchant_id: int
    expires_at: datetime
    created_at: datetime
    last_activity_at: datetime


class WidgetSessionEnvelope(MinimalEnvelope):
    """Envelope for session response."""

    data: WidgetSessionResponse


class WidgetSessionMetadataEnvelope(MinimalEnvelope):
    """Envelope for session metadata response."""

    data: WidgetSessionMetadataResponse


class WidgetVisitorSessionResponse(BaseSchema):
    """Response for visitor-based session lookup."""

    session_id: str | None = None


class WidgetVisitorSessionEnvelope(MinimalEnvelope):
    """Envelope for visitor session lookup response."""

    data: WidgetVisitorSessionResponse


class SendMessageRequest(BaseSchema):
    """Request to send a message in widget.

    Attributes:
        session_id: Active session identifier
        message: User message text
        streaming: Whether to stream response via WebSocket (default: false for fallback to HTTP)
    """

    session_id: str
    message: str = Field(min_length=1, max_length=4000)
    streaming: str | None = Field(default="false", description="Stream via WebSocket if available")


class ContactOptionSchema(BaseSchema):
    """Contact option for escalation.

    Story 10-5: Contact Card Widget

    Attributes:
        type: Contact type (phone, email, custom)
        label: Display label for the option
        value: Phone number, email address, or custom URL
        icon: Optional icon identifier
    """

    type: str = Field(description="Contact type: phone, email, custom")
    label: str = Field(description="Display label")
    value: str = Field(description="Phone number, email address, or custom URL")
    icon: str | None = Field(default=None, description="Optional icon identifier")


class WidgetMessageResponse(BaseSchema):
    """Response for widget message.

    Story 6-1: Added consent_prompt_required for opt-in consent flow.
    Story 9-4: Added quick_replies for quick reply buttons.
    Story 10-1: Added sources for RAG-based response citations.

    Attributes:
        message_id: Unique message identifier
        content: Bot response content
        sender: Message sender (always 'bot')
        created_at: Message timestamp
        consent_prompt_required: Whether to show consent prompt (Story 6-1)
        quick_replies: Optional quick reply buttons (Story 9-4)
        sources: Optional RAG source citations (Story 10-1)
    """

    message_id: str = Field(alias="messageId")
    content: str
    sender: str = "bot"
    created_at: datetime = Field(alias="createdAt")
    products: list[dict[str, Any]] | None = None
    cart: dict[str, Any] | None = None
    checkout_url: str | None = Field(default=None, alias="checkoutUrl")
    consent_prompt_required: bool | None = Field(
        default=None, description="Whether to show consent prompt (Story 6-1)"
    )
    quick_replies: list[QuickReply] | None = Field(
        default=None, description="Quick reply buttons for user response (Story 9-4)"
    )
    sources: list[SourceCitation] | None = Field(
        default=None, description="RAG source citations (Story 10-1)"
    )
    suggested_replies: list[str] | None = Field(
        default=None,
        alias="suggestedReplies",
        description="Follow-up question suggestions (Story 10-3)",
    )
    feedback_enabled: bool | None = Field(
        default=None,
        alias="feedbackEnabled",
        description="Whether feedback rating collection is enabled (Story 10-4)",
    )
    user_rating: str | None = Field(
        default=None,
        alias="userRating",
        description="User's previous rating if any (Story 10-4)",
    )
    contact_options: list[ContactOptionSchema] | None = Field(
        default=None,
        alias="contactOptions",
        description="Contact options for escalation (Story 10-5)",
    )
    customer_name: str | None = Field(default=None, alias="customerName")


class WidgetMessageEnvelope(MinimalEnvelope):
    """Envelope for message response."""

    data: WidgetMessageResponse


class FAQQuickButtonsConfigResponse(BaseSchema):
    """FAQ quick buttons configuration response.

    Story 10-2: AC5 Merchant Configuration UI

    Attributes:
        enabled: Whether FAQ quick buttons are enabled
        faq_ids: List of FAQ IDs to show as quick buttons (max 5)
    """

    enabled: bool = Field(default=True, description="Whether FAQ quick buttons are enabled")
    faq_ids: list[int] = Field(
        default_factory=list,
        max_length=5,
        description="List of FAQ IDs to show as quick buttons (max 5)",
    )


class WidgetConfigResponse(BaseSchema):
    """Response for widget configuration.

    Story 5-10 Enhancement: Added personality and business_hours for frontend context.
    Story 9-5: Added voice_input_config for voice input interface.
    Story 9-6: Added proactive_engagement_config for proactive engagement triggers.
    Story 10-2: Added onboarding_mode and faq_quick_buttons for FAQ quick buttons.
    Story 10-4: Added feedback_enabled for feedback rating collection.

    Attributes:
        bot_name: Display name for the bot
        welcome_message: Initial greeting message
        theme: Visual theme configuration
        enabled: Whether widget is enabled
        personality: Bot personality type (friendly, professional, enthusiastic)
        business_hours: Business hours string for display (e.g., "Mon-Fri 9am-5pm")
        shop_domain: Shopify shop domain for checkout URL construction
        voice_input_config: Voice input configuration (Story 9-5)
        proactive_engagement_config: Proactive engagement configuration (Story 9-6)
        onboarding_mode: Merchant's onboarding mode ('general' or 'ecommerce')
        faq_quick_buttons: FAQ quick buttons configuration (Story 10-2)
        feedback_enabled: Whether feedback rating collection is enabled (Story 10-4)
    """

    bot_name: str
    welcome_message: str
    theme: WidgetTheme
    enabled: bool
    personality: str | None = Field(default=None, description="Bot personality type")
    business_hours: str | None = Field(default=None, description="Business hours for display")
    shop_domain: str | None = Field(
        default=None, description="Shopify shop domain for checkout URL"
    )
    voice_input_config: VoiceInputConfig | None = Field(
        default=None, description="Voice input configuration (Story 9-5)"
    )
    proactive_engagement_config: ProactiveEngagementConfigSchema | None = Field(
        default=None, description="Proactive engagement configuration (Story 9-6)"
    )
    onboarding_mode: str | None = Field(
        default=None, description="Merchant's onboarding mode ('general' or 'ecommerce')"
    )
    faq_quick_buttons: FAQQuickButtonsConfigResponse | None = Field(
        default=None, description="FAQ quick buttons configuration (Story 10-2)"
    )
    feedback_enabled: bool = Field(
        default=True, description="Whether feedback rating collection is enabled (Story 10-4)"
    )
    business_name: str | None = Field(default=None, alias="businessName")
    contact_options: list[ContactOptionSchema] | None = Field(
        default=None,
        alias="contactOptions",
        description="Contact options for escalation (Story 10-5)",
    )


class WidgetConfigEnvelope(MinimalEnvelope):
    """Envelope for config response."""

    data: WidgetConfigResponse


class SuccessResponse(BaseSchema):
    """Generic success response.

    Attributes:
        success: Always True for success
    """

    success: bool = True


class SuccessEnvelope(MinimalEnvelope):
    """Envelope for success response."""

    data: SuccessResponse


class FAQQuickButtonResponse(BaseSchema):
    """FAQ quick button response schema.

    Story 10-2: FAQ Quick Buttons Widget

    Attributes:
        id: FAQ ID
        question: FAQ question text
        icon: Optional icon/emoji
    """

    id: int = Field(description="FAQ ID")
    question: str = Field(description="FAQ question text")
    icon: str | None = Field(default=None, description="Optional icon/emoji")


class FAQQuickButtonsListResponse(BaseSchema):
    """Response for FAQ quick buttons list.

    Story 10-2: FAQ Quick Buttons Widget

    Attributes:
        buttons: List of FAQ quick buttons
    """

    buttons: list[FAQQuickButtonResponse] = Field(
        default_factory=list, description="List of FAQ quick buttons"
    )


class FAQQuickButtonsEnvelope(MinimalEnvelope):
    """Envelope for FAQ quick buttons response.

    Story 10-2: FAQ Quick Buttons Widget
    """

    data: FAQQuickButtonsListResponse


class WidgetMessageHistoryItem(BaseSchema):
    """Single message in widget history.

    Attributes:
        role: Message role ('user' or 'bot')
        content: Message content
        timestamp: Message timestamp
        user_rating: User's feedback rating (if any)
    """

    message_id: str | None = Field(default=None, alias="messageId")
    role: str
    content: str
    timestamp: str
    customer_name: str | None = Field(default=None, alias="customerName")
    user_rating: str | None = Field(default=None, alias="userRating")
    products: list[dict[str, Any]] | None = None
    cart: dict[str, Any] | None = None
    checkout_url: str | None = Field(default=None, alias="checkoutUrl")
    quick_replies: list[QuickReply] | None = Field(default=None, alias="quickReplies")
    sources: list[SourceCitation] | None = None
    suggested_replies: list[str] | None = Field(default=None, alias="suggestedReplies")
    contact_options: list[ContactOptionSchema] | None = Field(default=None, alias="contactOptions")


class WidgetMessageHistoryResponse(BaseSchema):
    """Response for widget message history.

    Attributes:
        messages: List of message history items
        expired: Whether the history has expired
        expires_at: When the history will expire (ISO timestamp)
    """

    messages: list[WidgetMessageHistoryItem]
    expired: bool
    expires_at: str | None = None


class WidgetMessageHistoryEnvelope(MinimalEnvelope):
    """Envelope for message history response."""

    data: WidgetMessageHistoryResponse


def create_meta() -> MetaData:
    """Create metadata for API response.

    Returns:
        MetaData object with request_id and timestamp
    """
    from uuid import uuid4

    return MetaData(
        request_id=str(uuid4()),
        timestamp=datetime.now().replace(microsecond=0).isoformat() + "Z",
    )
