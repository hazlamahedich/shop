from datetime import datetime
from typing import Optional, List
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
                f"Invalid status values: {invalid}. "
                f"Valid values: {', '.join(VALID_STATUS_VALUES)}"
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
