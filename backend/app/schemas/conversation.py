from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field
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
