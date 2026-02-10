"""Pydantic schemas for Facebook Messenger webhooks and responses.

Defines request/response schemas for webhook processing with
camelCase API compatibility.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


def to_camel(value: str) -> str:
    """Convert snake_case to camelCase for API compatibility.

    Args:
        value: snake_case string

    Returns:
        camelCase string
    """
    components = value.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


class FacebookMessaging(BaseModel):
    """Facebook messaging entry from webhook."""

    sender_id: str = Field(alias="id", description="PSID of sender")
    message_text: Optional[str] = Field(None, alias="text", description="Message text content")

    class Config:
        alias_generator = to_camel
        populate_by_name = True


class FacebookEntry(BaseModel):
    """Facebook webhook entry."""

    id: str = Field(description="Page ID")
    time: int = Field(description="Timestamp")
    messaging: list[dict[str, Any]] = Field(description="Messaging events")

    class Config:
        alias_generator = to_camel
        populate_by_name = True


class FacebookWebhookPayload(BaseModel):
    """Facebook Messenger webhook payload."""

    object: str = Field(description="Webhook object type (should be 'page')")
    entry: list[FacebookEntry] = Field(description="Webhook entries")

    @property
    def sender_id(self) -> str:
        """Extract sender PSID from first message."""
        if self.entry and self.entry[0].messaging:
            return self.entry[0].messaging[0].get("sender", {}).get("id", "")
        return ""

    @property
    def message_text(self) -> Optional[str]:
        """Extract message text from first message."""
        if self.entry and self.entry[0].messaging:
            message = self.entry[0].messaging[0].get("message", {})
            return message.get("text")
        return None

    @property
    def postback_payload(self) -> Optional[str]:
        """Extract postback payload from button tap."""
        if self.entry and self.entry[0].messaging:
            postback = self.entry[0].messaging[0].get("postback", {})
            return postback.get("payload")
        return None

    @property
    def page_id(self) -> str:
        """Extract Facebook Page ID from webhook entry (Story 1.10)."""
        if self.entry:
            return self.entry[0].id
        return ""

    class Config:
        alias_generator = to_camel
        populate_by_name = True


class MessengerResponse(BaseModel):
    """Response message for Facebook Messenger."""

    text: str = Field(description="Response text")
    recipient_id: str = Field(alias="recipientId", description="PSID of recipient")

    class Config:
        alias_generator = to_camel
        populate_by_name = True


class ClarificationState(BaseModel):
    """State of clarification flow for handling ambiguous user requests."""

    active: bool = Field(False, description="Is clarification flow active?")
    attempt_count: int = Field(0, description="Number of clarification attempts")
    questions_asked: list[str] = Field(
        default_factory=list, description="Constraints asked about"
    )
    last_question: Optional[str] = Field(None, description="Last question asked")
    original_intent: Optional[dict[str, Any]] = Field(
        None, description="Original intent being clarified"
    )
    started_at: Optional[str] = Field(None, description="When clarification started")

    class Config:
        alias_generator = to_camel
        populate_by_name = True


class ConversationContext(BaseModel):
    """Conversation context for message processing."""

    psid: str = Field(description="Facebook Page-Scoped ID")
    created_at: Optional[str] = Field(None, description="Session creation timestamp")
    last_message_at: Optional[str] = Field(None, description="Last message timestamp")
    message_count: int = Field(0, description="Number of messages in session")
    previous_intents: list[str] = Field(default_factory=list, description="Previous intent classifications")
    extracted_entities: dict[str, Any] = Field(default_factory=dict, description="Extracted entities from conversation")
    conversation_state: str = Field("active", description="Current conversation state")
    clarification: Optional[ClarificationState] = Field(None, description="Clarification flow state")

    class Config:
        alias_generator = to_camel
        populate_by_name = True
