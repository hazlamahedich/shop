"""Pydantic schemas for bot preview mode (Story 1.13).

Preview mode allows merchants to test their bot configuration in a sandbox
environment before exposing it to real customers.

Error codes: 4300-4399 (Bot Preview Mode)
"""

from __future__ import annotations

from typing import Any, Optional
from pydantic import Field, field_validator
from datetime import datetime

from app.schemas.base import BaseSchema, MinimalEnvelope, MetaData


# Sample conversation starters for preview mode
STARTER_PROMPTS = [
    "What products do you have under $50?",
    "What are your business hours?",
    "Show me running shoes",
    "I need help with my order",
    "Tell me about your return policy",
]


class PreviewMessageRequest(BaseSchema):
    """Request schema for sending a message in preview mode.

    Uses camelCase aliases for API compatibility with frontend.
    """

    message: str = Field(min_length=1, max_length=1000, description="Message text to send to bot")
    preview_session_id: str = Field(description="Preview session identifier")

    @field_validator("message")
    @classmethod
    def validate_message_length(cls, v: str) -> str:
        """Validate message length is within acceptable limits."""
        if len(v.strip()) == 0:
            raise ValueError("Message cannot be empty or whitespace only")
        if len(v) > 1000:
            raise ValueError("Message cannot exceed 1000 characters")
        return v.strip()


class PreviewMessageResponse(BaseSchema):
    """Response schema for bot response in preview mode.

    Includes bot response text, confidence score, and metadata
    for debugging and transparency.
    """

    response: str = Field(description="Bot's response text")
    confidence: int = Field(ge=0, le=100, description="Confidence score (0-100)")
    confidence_level: str = Field(description="Confidence level: high, medium, or low")
    metadata: PreviewMessageMetadata = Field(description="Additional metadata about the response")
    products: Optional[list[dict]] = Field(
        default=None,
        description="Products returned from search queries",
    )
    cart: Optional[dict] = Field(
        default=None,
        description="Cart state if cart operation was performed",
    )


class PreviewMessageMetadata(BaseSchema):
    """Metadata for preview message response.

    Provides technical details about the bot's response
    for debugging and transparency.
    """

    intent: Optional[str] = Field(None, description="Detected intent classification")
    faq_matched: bool = Field(description="Whether an FAQ was matched")
    products_found: int = Field(default=0, description="Number of products found in search")
    llm_provider: Optional[str] = Field(None, description="LLM provider used for response")


class PreviewSessionResponse(BaseSchema):
    """Response schema for preview session initialization.

    Returns session info and sample conversation starters.
    """

    preview_session_id: str = Field(description="Unique preview session identifier")
    merchant_id: int = Field(description="Merchant ID")
    created_at: str = Field(description="Session creation timestamp (ISO-8601)")
    starter_prompts: list[str] = Field(
        default_factory=lambda: STARTER_PROMPTS, description="Sample conversation starter prompts"
    )


class PreviewResetResponse(BaseSchema):
    """Response schema for preview session reset."""

    cleared: bool = Field(description="Whether the conversation was cleared")
    message: str = Field(description="Status message")


class PreviewMessageEnvelope(MinimalEnvelope):
    """Minimal envelope for preview message response."""

    data: PreviewMessageResponse


class PreviewSessionEnvelope(MinimalEnvelope):
    """Minimal envelope for preview session response."""

    data: PreviewSessionResponse


class PreviewResetEnvelope(MinimalEnvelope):
    """Minimal envelope for preview reset response."""

    data: PreviewResetResponse


__all__ = [
    "MinimalEnvelope",
    "MetaData",
    "PreviewMessageRequest",
    "PreviewMessageResponse",
    "PreviewMessageMetadata",
    "PreviewSessionResponse",
    "PreviewResetResponse",
    "PreviewMessageEnvelope",
    "PreviewSessionEnvelope",
    "PreviewResetEnvelope",
    "STARTER_PROMPTS",
]
