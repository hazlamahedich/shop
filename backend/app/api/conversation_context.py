"""Conversation Context API endpoints.

Story 11-1: Conversation Context Memory
Provides endpoints for:
- Getting conversation context
- Updating conversation context
- Triggering context summarization
"""

from __future__ import annotations

from typing import Any

import structlog
from fastapi import APIRouter, Depends, Header, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.helpers import create_meta, get_merchant_id
from app.core.csrf import get_csrf_protection
from app.core.database import get_db
from app.core.errors import APIError, ErrorCode
from app.core.security import get_redis_client
from app.models.conversation_context import ConversationContext
from app.schemas.conversation_context import (
    ContextSummaryResponse,
    ContextUpdateResponse,
    ConversationContextResponse,
    ConversationContextUpdate,
)
from app.services.conversation_context import ConversationContextService

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.get(
    "/conversations/{conversation_id}/context",
    response_model=ContextUpdateResponse,
)
async def get_conversation_context(
    conversation_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_csrf_token: str = Header(..., alias="X-CSRF-Token"),
) -> ContextUpdateResponse:
    """
    Get conversation context.

    Retrieves the current conversation context including mode-aware
    information (products viewed for ecommerce, topics discussed for general).

    Args:
        conversation_id: Conversation ID to retrieve context for
        request: FastAPI request with merchant authentication
        db: Database session
        x_csrf_token: CSRF token from X-CSRF-Token header

    Returns:
        ContextUpdateResponse with conversation context

    Raises:
        APIError: If conversation not found or context expired
        APIError: If CSRF token validation fails
    """
    # Validate CSRF token
    csrf = get_csrf_protection()
    if not csrf.validate_token(request, x_csrf_token):
        raise APIError(
            ErrorCode.VALIDATION_ERROR,
            "Invalid or missing CSRF token",
            details={"required_header": "X-CSRF-Token"},
        )

    merchant_id = get_merchant_id(request)

    # Verify conversation belongs to merchant
    await _verify_conversation_belongs_to_merchant(conversation_id, merchant_id, db)

    # Get context service
    redis_client = get_redis_client()
    context_service = ConversationContextService(db=db, redis_client=redis_client)

    # Retrieve context
    context = await context_service.get_context(conversation_id)

    if not context:
        raise APIError(
            ErrorCode.CONTEXT_NOT_FOUND,
            f"Context not found for conversation {conversation_id}",
        )

    logger.info(
        "context_retrieved",
        conversation_id=conversation_id,
        merchant_id=merchant_id,
        mode=context.get("mode"),
    )

    # Build response
    response_data = ConversationContextResponse(
        id=conversation_id,
        conversation_id=conversation_id,
        merchant_id=merchant_id,
        mode=context.get("mode", "ecommerce"),
        turn_count=context.get("turn_count", 0),
        viewed_products=context.get("viewed_products"),
        cart_items=context.get("cart_items"),
        constraints=context.get("constraints"),
        search_history=context.get("search_history"),
        topics_discussed=context.get("topics_discussed"),
        documents_referenced=context.get("documents_referenced"),
        support_issues=context.get("support_issues"),
        escalation_status=context.get("escalation_status"),
        preferences=context.get("preferences"),
        last_summarized_at=context.get("last_summarized_at"),
        expires_at=context.get("expires_at"),
        created_at=context.get("created_at"),
        updated_at=context.get("updated_at"),
    )

    return ContextUpdateResponse(
        data=response_data,
        meta=create_meta().model_dump(),
    )


@router.put(
    "/conversations/{conversation_id}/context",
    response_model=ContextUpdateResponse,
)
async def update_conversation_context(
    conversation_id: int,
    request: Request,
    update: ConversationContextUpdate,
    db: AsyncSession = Depends(get_db),
    x_csrf_token: str = Header(..., alias="X-CSRF-Token"),
) -> ContextUpdateResponse:
    """
    Update conversation context.

    Extracts relevant context from the user message and updates
    the conversation context using mode-aware extraction.

    Args:
        conversation_id: Conversation ID to update context for
        request: FastAPI request with merchant authentication
        update: Context update with message and mode
        db: Database session
        x_csrf_token: CSRF token from X-CSRF-Token header

    Returns:
        ContextUpdateResponse with updated context

    Raises:
        APIError: If conversation not found
        APIError: If CSRF token validation fails
    """
    # Validate CSRF token
    csrf = get_csrf_protection()
    if not csrf.validate_token(request, x_csrf_token):
        raise APIError(
            ErrorCode.VALIDATION_ERROR,
            "Invalid or missing CSRF token",
            details={"required_header": "X-CSRF-Token"},
        )

    merchant_id = get_merchant_id(request)

    # Verify conversation belongs to merchant
    await _verify_conversation_belongs_to_merchant(conversation_id, merchant_id, db)

    # Get context service
    redis_client = get_redis_client()
    context_service = ConversationContextService(db=db, redis_client=redis_client)

    # Update context
    updated_context = await context_service.update_context(
        conversation_id=conversation_id,
        merchant_id=merchant_id,
        message=update.message,
        mode=update.mode,
    )

    logger.info(
        "context_updated",
        conversation_id=conversation_id,
        merchant_id=merchant_id,
        mode=update.mode,
        turn_count=updated_context.get("turn_count", 0),
    )

    # Build response
    response_data = ConversationContextResponse(
        id=conversation_id,
        conversation_id=conversation_id,
        merchant_id=merchant_id,
        mode=updated_context.get("mode", "ecommerce"),
        turn_count=updated_context.get("turn_count", 0),
        viewed_products=updated_context.get("viewed_products"),
        cart_items=updated_context.get("cart_items"),
        constraints=updated_context.get("constraints"),
        search_history=updated_context.get("search_history"),
        topics_discussed=updated_context.get("topics_discussed"),
        documents_referenced=updated_context.get("documents_referenced"),
        support_issues=updated_context.get("support_issues"),
        escalation_status=updated_context.get("escalation_status"),
        preferences=updated_context.get("preferences"),
        last_summarized_at=updated_context.get("last_summarized_at"),
        expires_at=updated_context.get("expires_at"),
        created_at=updated_context.get("created_at"),
        updated_at=updated_context.get("updated_at"),
    )

    return ContextUpdateResponse(
        data=response_data,
        meta=create_meta().model_dump(),
    )


@router.post(
    "/conversations/{conversation_id}/context/summary",
    response_model=ContextSummaryResponse,
    status_code=status.HTTP_200_OK,
)
async def summarize_conversation_context(
    conversation_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_csrf_token: str = Header(..., alias="X-CSRF-Token"),
) -> ContextSummaryResponse:
    """
    Trigger context summarization.

    Generates an LLM-based summary of the conversation context
    for token efficiency. Can be triggered manually or automatically
    every 5 turns / when context exceeds 1KB.

    Args:
        conversation_id: Conversation ID to summarize
        request: FastAPI request with merchant authentication
        db: Database session
        x_csrf_token: CSRF token from X-CSRF-Token header

    Returns:
        ContextSummaryResponse with summary data

    Raises:
        APIError: If conversation not found or context missing
        APIError: If CSRF token validation fails
    """
    # Validate CSRF token
    csrf = get_csrf_protection()
    if not csrf.validate_token(request, x_csrf_token):
        raise APIError(
            ErrorCode.VALIDATION_ERROR,
            "Invalid or missing CSRF token",
            details={"required_header": "X-CSRF-Token"},
        )

    merchant_id = get_merchant_id(request)

    # Verify conversation belongs to merchant
    await _verify_conversation_belongs_to_merchant(conversation_id, merchant_id, db)

    # Get context service
    redis_client = get_redis_client()
    context_service = ConversationContextService(db=db, redis_client=redis_client)

    # Get current context
    context = await context_service.get_context(conversation_id)

    if not context:
        raise APIError(
            ErrorCode.CONTEXT_NOT_FOUND,
            f"Context not found for conversation {conversation_id}",
        )

    # Generate summary
    summary = await context_service.summarize_context(
        conversation_id=conversation_id,
        context=context,
    )

    logger.info(
        "context_summarized",
        conversation_id=conversation_id,
        merchant_id=merchant_id,
        original_turns=summary.get("original_turns", 0),
        key_points_count=len(summary.get("key_points", [])),
    )

    from app.schemas.conversation_context import ContextSummary

    # Build response
    summary_data = ContextSummary(
        summary=summary.get("summary", ""),
        key_points=summary.get("key_points", []),
        active_constraints=summary.get("active_constraints", {}),
        original_turns=summary.get("original_turns"),
        summarized_at=summary.get("summarized_at"),
    )

    return ContextSummaryResponse(
        data=summary_data,
        meta=create_meta().model_dump(),
    )


async def _verify_conversation_belongs_to_merchant(
    conversation_id: int,
    merchant_id: int,
    db: AsyncSession,
) -> None:
    """Verify that a conversation belongs to a merchant.

    Args:
        conversation_id: Conversation ID to verify
        merchant_id: Merchant ID to check against
        db: Database session

    Raises:
        APIError: If conversation not found or doesn't belong to merchant
    """
    from app.models.conversation import Conversation

    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.merchant_id == merchant_id,
        )
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise APIError(
            ErrorCode.CONVERSATION_NOT_FOUND,
            f"Conversation {conversation_id} not found for merchant {merchant_id}",
        )
