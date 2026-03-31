"""Conversation Context Pydantic schemas.

Story 11-1: Conversation Context Memory
API schemas with snake_case → camelCase conversion.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from pydantic.alias_generators import to_camel


class ConversationContextResponse(BaseModel):
    """Conversation context response with mode-aware fields."""

    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, from_attributes=True
    )

    id: int
    conversation_id: int
    merchant_id: int
    mode: Literal["ecommerce", "general"]
    turn_count: int
    expires_at: datetime
    created_at: datetime
    updated_at: datetime

    # E-commerce fields
    viewed_products: list[int] | None = None
    cart_items: list[int] | None = None
    constraints: dict | None = None
    search_history: list[str] | None = None

    # General mode fields
    topics_discussed: list[str] | None = None
    documents_referenced: list[int] | None = None
    support_issues: list[dict] | None = None
    escalation_status: str | None = None

    # Universal fields
    preferences: dict | None = None
    last_summarized_at: datetime | None = None


class ConversationContextUpdate(BaseModel):
    """Request to update conversation context."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    message: str = Field(..., description="User message to extract context from")
    mode: Literal["ecommerce", "general"] = Field(
        ..., description="Merchant mode (ecommerce or general)"
    )


class ContextSummary(BaseModel):
    """Context summary for token efficiency."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    summary: str = Field(..., description="Summarized context")
    key_points: list[str] = Field(
        ..., description="Key points extracted from conversation"
    )
    active_constraints: dict = Field(..., description="Active constraints/conversations")
    original_turns: int | None = Field(None, description="Number of turns summarized")
    summarized_at: datetime | None = Field(None, description="When summarization occurred")


class ConversationTurnResponse(BaseModel):
    """Conversation turn response."""

    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, from_attributes=True
    )

    id: int
    conversation_id: int
    turn_number: int
    user_message: str | None
    bot_response: str | None
    intent_detected: str | None
    context_snapshot: dict | None
    sentiment: str | None
    created_at: datetime


class ContextUpdateResponse(BaseModel):
    """Response after context update."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    data: ConversationContextResponse
    meta: dict


class ContextSummaryResponse(BaseModel):
    """Response after context summarization."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    data: ContextSummary
    meta: dict
