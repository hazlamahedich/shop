from datetime import datetime
from typing import Any, Optional, List
from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel


class PaginationMeta(BaseModel):
    """Pagination metadata."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    total: int
    page: int
    per_page: int
    total_pages: int


class ConversationListItem(BaseModel):
    """Conversation summary for list view."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id: int
    platform: str
    platform_sender_id_masked: str
    last_message: Optional[str] = None
    status: str
    sentiment: str = "neutral"  # Default for now until sentiment analysis is active
    message_count: int = 0
    updated_at: datetime
    created_at: datetime


class ConversationListResponse(BaseModel):
    """Paginated conversation list response."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    data: List[ConversationListItem]
    meta: dict  # Includes pagination and request_id


# Valid status and sentiment enum values
VALID_STATUS_VALUES = ["active", "handoff", "closed"]
VALID_SENTIMENT_VALUES = ["positive", "neutral", "negative"]


class ConversationFilterParams(BaseModel):
    """Query parameters for filtering conversations.

    Supports search and filter functionality for the conversation list.
    All fields are optional - filters are combined with AND logic.
    """

    search: Optional[str] = Field(
        None,
        description="Search term for customer ID or message content",
    )
    date_from: Optional[str] = Field(
        None,
        description="Start date filter (ISO 8601 format, e.g., 2026-02-01)",
    )
    date_to: Optional[str] = Field(
        None,
        description="End date filter (ISO 8601 format, e.g., 2026-02-28)",
    )
    status: Optional[List[str]] = Field(
        None,
        description=f"Filter by status. Valid values: {', '.join(VALID_STATUS_VALUES)}",
    )
    sentiment: Optional[List[str]] = Field(
        None,
        description=f"Filter by sentiment. Valid values: {', '.join(VALID_SENTIMENT_VALUES)}",
    )
    has_handoff: Optional[bool] = Field(
        None,
        description="Filter by handoff presence. True=has handoff, False=no handoff",
    )

    @field_validator("date_from", "date_to")
    @classmethod
    def validate_date_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate ISO 8601 date format."""
        if v is None:
            return v
        try:
            datetime.fromisoformat(v)
            return v
        except ValueError:
            raise ValueError(
                f"Invalid date format: '{v}'. Expected ISO 8601 format (e.g., 2026-02-01)"
            )

    @field_validator("status")
    @classmethod
    def validate_status_values(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate status enum values."""
        if v is None:
            return v
        invalid = [s for s in v if s not in VALID_STATUS_VALUES]
        if invalid:
            raise ValueError(
                f"Invalid status values: {invalid}. Valid values: {', '.join(VALID_STATUS_VALUES)}"
            )
        return v

    @field_validator("sentiment")
    @classmethod
    def validate_sentiment_values(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate sentiment enum values."""
        if v is None:
            return v
        invalid = [s for s in v if s not in VALID_SENTIMENT_VALUES]
        if invalid:
            raise ValueError(
                f"Invalid sentiment values: {invalid}. "
                f"Valid values: {', '.join(VALID_SENTIMENT_VALUES)}"
            )
        return v


class MessageHistoryItem(BaseModel):
    """Single message in conversation history."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id: int
    sender: str
    content: str
    created_at: datetime
    confidence_score: Optional[float] = None


class CartStateItem(BaseModel):
    """Item in cart state."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    product_id: str
    name: str
    quantity: int


class CartState(BaseModel):
    """Cart state from conversation context."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    items: List[CartStateItem] = Field(default_factory=list)


class ExtractedConstraints(BaseModel):
    """Extracted constraints from conversation."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    budget: Optional[str] = None
    size: Optional[str] = None
    category: Optional[str] = None


class ConversationContext(BaseModel):
    """Conversation context including cart and constraints."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    cart_state: Optional[CartState] = None
    extracted_constraints: Optional[ExtractedConstraints] = None


class HandoffContext(BaseModel):
    """Handoff context for conversation history."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    trigger_reason: str
    triggered_at: datetime
    urgency_level: str
    wait_time_seconds: int


class CustomerInfo(BaseModel):
    """Customer information for conversation history."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    masked_id: str
    order_count: int = 0


class ConversationHistoryData(BaseModel):
    """Conversation history response data."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    conversation_id: int
    platform_sender_id: str = Field(..., description="Customer's platform sender ID (PSID)")
    messages: List[MessageHistoryItem]
    context: ConversationContext
    handoff: HandoffContext
    customer: CustomerInfo


class ConversationHistoryMeta(BaseModel):
    """Meta information for conversation history response."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    request_id: str
    timestamp: str


class ConversationHistoryResponse(BaseModel):
    """Full conversation history response."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    data: ConversationHistoryData
    meta: ConversationHistoryMeta


# ============================================
# Story 4-9: Hybrid Mode Schemas
# ============================================


class HybridModeRequest(BaseModel):
    """Request to enable/disable hybrid mode for a conversation."""

    enabled: bool = Field(..., description="Whether to enable or disable hybrid mode")
    reason: Optional[str] = Field(
        None,
        description="Reason for change: 'merchant_responding' or 'merchant_returning'",
    )


class HybridModeState(BaseModel):
    """Hybrid mode state in conversation."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    enabled: bool
    activated_at: Optional[datetime] = None
    activated_by: Optional[str] = None
    expires_at: Optional[datetime] = None


class HybridModeResponse(BaseModel):
    """Response for hybrid mode update."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    conversation_id: int
    hybrid_mode: dict  # Contains enabled, activatedAt, activatedBy, expiresAt, remainingSeconds


class FacebookPageInfo(BaseModel):
    """Facebook page connection info for merchant."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    page_id: Optional[str] = None
    page_name: Optional[str] = None
    is_connected: bool = False
