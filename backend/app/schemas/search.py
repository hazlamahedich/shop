"""Pydantic schemas for global search API.

Provides unified search across conversations, FAQs, and other entities.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

from app.schemas.base import BaseSchema, MinimalEnvelope, MetaData


class ConversationSearchResult(BaseSchema):
    """Search result for a conversation.

    Attributes:
        id: Conversation ID
        customer_id: Masked customer identifier
        last_message: Preview of last message
        status: Conversation status
        updated_at: Last update timestamp
    """

    id: int = Field(description="Conversation ID")
    customer_id: str = Field(
        description="Masked customer identifier", alias="platform_sender_id_masked"
    )
    last_message: Optional[str] = Field(default=None, description="Preview of last message")
    status: str = Field(description="Conversation status")
    updated_at: datetime = Field(description="Last update timestamp")


class FaqSearchResult(BaseSchema):
    """Search result for an FAQ.

    Attributes:
        id: FAQ ID
        question: FAQ question
        answer: Preview of FAQ answer
    """

    id: int = Field(description="FAQ ID")
    question: str = Field(description="FAQ question")
    answer: str = Field(description="Preview of FAQ answer (truncated)")


class GlobalSearchResults(BaseSchema):
    """Combined search results from multiple entities.

    Attributes:
        conversations: List of matching conversations
        faqs: List of matching FAQs
        total: Total number of results
    """

    conversations: List[ConversationSearchResult] = Field(
        default_factory=list, description="Matching conversations"
    )
    faqs: List[FaqSearchResult] = Field(default_factory=list, description="Matching FAQs")
    total: int = Field(description="Total number of results across all categories")


class GlobalSearchResponse(MinimalEnvelope):
    """Response envelope for global search.

    Attributes:
        data: Search results
        meta: Response metadata
    """

    data: GlobalSearchResults


__all__ = [
    "ConversationSearchResult",
    "FaqSearchResult",
    "GlobalSearchResults",
    "GlobalSearchResponse",
]
