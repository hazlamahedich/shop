"""Widget schemas for embeddable chat widget API.

Provides request/response schemas for widget session management,
messaging, and configuration endpoints.

Story 5.1: Backend Widget API
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseSchema, MinimalEnvelope, MetaData


class WidgetTheme(BaseSchema):
    """Theme configuration for widget appearance.

    Attributes:
        primary_color: Primary brand color (hex)
        background_color: Widget background color (hex)
        text_color: Text color (hex)
        position: Widget position on page
        border_radius: Border radius in pixels
    """

    primary_color: str = Field(default="#6366f1", pattern=r"^#[0-9a-fA-F]{6}$")
    background_color: str = Field(default="#ffffff", pattern=r"^#[0-9a-fA-F]{6}$")
    text_color: str = Field(default="#1f2937", pattern=r"^#[0-9a-fA-F]{6}$")
    position: str = Field(default="bottom-right", pattern=r"^(bottom-right|bottom-left)$")
    border_radius: int = Field(default=16, ge=0, le=32)


class WidgetConfig(BaseSchema):
    """Widget configuration for a merchant.

    Attributes:
        enabled: Whether widget is enabled
        bot_name: Display name for the bot
        welcome_message: Initial greeting message
        theme: Visual theme configuration
        allowed_domains: Optional domain whitelist for CORS
    """

    enabled: bool = Field(default=True)
    bot_name: str = Field(default="Shopping Assistant", max_length=50)
    welcome_message: str = Field(
        default="Hi! How can I help you today?",
        max_length=500,
    )
    theme: WidgetTheme = Field(default_factory=WidgetTheme)
    allowed_domains: list[str] = Field(default_factory=list)


class WidgetSessionData(BaseSchema):
    """Widget session data stored in Redis.

    Attributes:
        session_id: Unique session identifier (UUID)
        merchant_id: Associated merchant ID
        created_at: Session creation timestamp
        last_activity_at: Last activity timestamp
        expires_at: Session expiry timestamp
        visitor_ip: Optional visitor IP for analytics
        user_agent: Optional user agent for analytics
    """

    session_id: str
    merchant_id: int
    created_at: datetime
    last_activity_at: datetime
    expires_at: datetime
    visitor_ip: Optional[str] = None
    user_agent: Optional[str] = None


class CreateSessionRequest(BaseSchema):
    """Request to create a new widget session.

    Attributes:
        merchant_id: The merchant ID to create session for
    """

    merchant_id: int


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


class WidgetMessageEnvelope(MinimalEnvelope):
    """Envelope for message response."""

    data: WidgetMessageResponse


class WidgetConfigResponse(BaseSchema):
    """Response for widget configuration.

    Attributes:
        bot_name: Display name for the bot
        welcome_message: Initial greeting message
        theme: Visual theme configuration
        enabled: Whether widget is enabled
    """

    bot_name: str
    welcome_message: str
    theme: WidgetTheme
    enabled: bool


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
