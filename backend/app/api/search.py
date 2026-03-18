"""Global Search API endpoint.

Provides unified search across conversations, FAQs, and other entities.
"""

from __future__ import annotations

from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.helpers import create_meta, get_merchant_id
from app.core.database import get_db
from app.models.conversation import Conversation
from app.models.faq import Faq
from app.models.message import Message
from app.schemas.search import (
    ConversationSearchResult,
    FaqSearchResult,
    GlobalSearchResponse,
    GlobalSearchResults,
)

logger = structlog.get_logger(__name__)

router = APIRouter()

MAX_RESULTS_PER_CATEGORY = 5


@router.get(
    "/search",
    response_model=GlobalSearchResponse,
)
async def global_search(
    request: Request,
    db: AsyncSession = Depends(get_db),
    q: Annotated[str, Query(min_length=2, max_length=100, description="Search query")] = "",
) -> GlobalSearchResponse:
    """Global search across conversations, FAQs, and other entities.

    Args:
        request: FastAPI request with merchant authentication
        db: Database session
        q: Search query string (min 2 chars)

    Returns:
        GlobalSearchResponse with grouped results

    Raises:
        APIError: If authentication fails
    """
    merchant_id = get_merchant_id(request)
    search_term = f"%{q}%"

    # Search conversations by customer ID or bot message content
    # Note: We search bot messages (plaintext) not customer messages (encrypted)
    message_content_match = (
        select(Message.id)
        .where(Message.conversation_id == Conversation.id)
        .where(Message.sender == "bot")
        .where(Message.content.ilike(search_term))
        .exists()
    )

    conversation_results = await db.execute(
        select(Conversation)
        .where(Conversation.merchant_id == merchant_id)
        .where(
            or_(
                Conversation.platform_sender_id.ilike(search_term),
                message_content_match,
            )
        )
        .options(selectinload(Conversation.messages))
        .order_by(Conversation.updated_at.desc())
        .limit(MAX_RESULTS_PER_CATEGORY)
    )
    conversations = conversation_results.scalars().all()

    # Search FAQs
    faq_results = await db.execute(
        select(Faq)
        .where(Faq.merchant_id == merchant_id)
        .where(
            or_(
                Faq.question.ilike(search_term),
                Faq.answer.ilike(search_term),
                Faq.keywords.ilike(search_term),
            )
        )
        .order_by(Faq.order_index)
        .limit(MAX_RESULTS_PER_CATEGORY)
    )
    faqs = faq_results.scalars().all()

    # Format results
    conversation_results = [
        ConversationSearchResult(
            id=c.id,
            platform_sender_id_masked=_mask_customer_id(c.platform_sender_id),
            last_message=_get_last_bot_message(c) if c.messages else None,
            status=c.status or "active",
            updated_at=c.updated_at,
        )
        for c in conversations
    ]

    faq_results = [
        FaqSearchResult(
            id=f.id,
            question=f.question,
            answer=_truncate_text(f.answer, 100),
        )
        for f in faqs
    ]

    total = len(conversation_results) + len(faq_results)

    logger.info(
        "global_search_completed",
        merchant_id=merchant_id,
        query=q,
        total_results=total,
        conversations=len(conversation_results),
        faqs=len(faq_results),
    )

    return GlobalSearchResponse(
        data=GlobalSearchResults(
            conversations=conversation_results,
            faqs=faq_results,
            total=total,
        ),
        meta=create_meta(),
    )


def _get_last_bot_message(conversation: Conversation) -> str | None:
    """Get the last bot message content from a conversation.

    Args:
        conversation: Conversation with loaded messages

    Returns:
        Last bot message content or None
    """
    if not conversation.messages:
        return None

    bot_messages = [m for m in conversation.messages if m.sender == "bot"]
    if not bot_messages:
        return None

    sorted_messages = sorted(bot_messages, key=lambda m: m.created_at, reverse=True)
    content = sorted_messages[0].content
    return _truncate_text(content, 100) if content else None


def _mask_customer_id(customer_id: str) -> str:
    """Mask customer ID for privacy.

    Args:
        customer_id: Full customer ID

    Returns:
        Masked customer ID (e.g., "abc***xyz")
    """
    if len(customer_id) <= 6:
        return "***"
    return f"{customer_id[:3]}***{customer_id[-3:]}"


def _truncate_text(text: str, max_length: int) -> str:
    """Truncate text to max length with ellipsis.

    Args:
        text: Text to truncate
        max_length: Maximum length

    Returns:
        Truncated text with ellipsis if needed
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."
