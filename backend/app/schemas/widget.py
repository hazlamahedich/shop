"""Widget schemas for embeddable chat widget API.

Provides request/response schemas for widget session management,
messaging, and configuration endpoints.

Story 5.1: Backend Widget API
Story 5.5: Theme Customization System
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Optional, Any
from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema, MinimalEnvelope, MetaData


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
    """

    enabled: bool = Field(default=True)
    bot_name: str = Field(default="Shopping Assistant", max_length=50)
    welcome_message: str = Field(
        default="Hi! How can I help you today?",
        max_length=500,
    )
    theme: WidgetTheme = Field(default_factory=WidgetTheme)
    allowed_domains: list[str] = Field(default_factory=list)
    rate_limit: Optional[int] = Field(default=None, ge=1, le=1000)


class WidgetSessionData(BaseSchema):
    """Widget session data stored in Redis.

    Story 5-10 Enhancement: Added visitor_id and is_returning_shopper.

    Attributes:
        session_id: Unique session identifier (UUID)
        merchant_id: Associated merchant ID
        created_at: Session creation timestamp
        last_activity_at: Last activity timestamp
        expires_at: Session expiry timestamp
        visitor_ip: Optional visitor IP for analytics
        user_agent: Optional user agent for analytics
        visitor_id: Optional visitor identifier for returning shopper detection
        is_returning_shopper: Whether this visitor has previous sessions
    """

    session_id: str
    merchant_id: int
    created_at: datetime
    last_activity_at: datetime
    expires_at: datetime
    visitor_ip: Optional[str] = None
    user_agent: Optional[str] = None
    visitor_id: Optional[str] = None
    is_returning_shopper: bool = False


class CreateSessionRequest(BaseSchema):
    """Request to create a new widget session.

    Story 5-10 Enhancement: Added visitor_id for returning shopper detection.

    Attributes:
        merchant_id: The merchant ID to create session for
        visitor_id: Optional visitor identifier for returning shopper detection
    """

    merchant_id: int
    visitor_id: Optional[str] = Field(
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


class SendMessageRequest(BaseSchema):
    """Request to send a message in widget.

    Attributes:
        session_id: Active session identifier
        message: User message text
    """

    session_id: str
    message: str = Field(min_length=1, max_length=4000)


class WidgetMessageResponse(BaseSchema):
    """Response for widget message.

    Attributes:
        message_id: Unique message identifier
        content: Bot response content
        sender: Message sender (always 'bot')
        created_at: Message timestamp
    """

    message_id: str
    content: str
    sender: str = "bot"
    created_at: datetime
    products: Optional[list[dict[str, Any]]] = None
    cart: Optional[dict[str, Any]] = None
    checkout_url: Optional[str] = None


class WidgetMessageEnvelope(MinimalEnvelope):
    """Envelope for message response."""

    data: WidgetMessageResponse


class WidgetConfigResponse(BaseSchema):
    """Response for widget configuration.

    Story 5-10 Enhancement: Added personality and business_hours for frontend context.

    Attributes:
        bot_name: Display name for the bot
        welcome_message: Initial greeting message
        theme: Visual theme configuration
        enabled: Whether widget is enabled
        personality: Bot personality type (friendly, professional, enthusiastic)
        business_hours: Business hours string for display (e.g., "Mon-Fri 9am-5pm")
    """

    bot_name: str
    welcome_message: str
    theme: WidgetTheme
    enabled: bool
    personality: Optional[str] = Field(default=None, description="Bot personality type")
    business_hours: Optional[str] = Field(default=None, description="Business hours for display")


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
