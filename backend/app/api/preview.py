"""Bot preview mode API endpoints (Story 1.13).

Provides endpoints for merchants to test their bot configuration
in a sandbox environment before exposing it to real customers.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.core.database import get_db
from app.core.errors import APIError, ErrorCode
from app.api.helpers import create_meta, get_merchant_id, verify_merchant_exists
from app.schemas.preview import (
    PreviewMessageRequest,
    PreviewSessionResponse,
    PreviewResetResponse,
    PreviewMessageEnvelope,
    PreviewSessionEnvelope,
    PreviewResetEnvelope,
)
from app.services.preview.preview_service import PreviewService


# Maximum age for preview sessions before cleanup (1 hour)
PREVIEW_SESSION_MAX_AGE_SECONDS = 3600


logger = structlog.get_logger(__name__)

router = APIRouter()


@router.post(
    "/preview/conversation",
    response_model=PreviewSessionEnvelope,
)
async def create_preview_conversation(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> PreviewSessionEnvelope:
    """
    Create a new preview conversation session.

    Initializes a sandbox environment where merchants can test their
    bot configuration without affecting real conversations or incurring
    LLM costs.

    NOTE: CSRF protection is provided by CSRFMiddleware (see main.py:164).
    All POST requests automatically require valid CSRF tokens unless the path
    is in BYPASS_PATHS. The /api/v1/preview/conversation path is NOT in
    the bypass list, so it is protected by default.

    NOTE: Authentication in DEBUG mode uses X-Merchant-Id header for
    convenience. In production, proper JWT authentication should be used.

    Args:
        request: FastAPI request with merchant authentication
        db: Database session

    Returns:
        PreviewSessionEnvelope with session info and starter prompts

    Raises:
        APIError: If authentication fails or merchant not found
    """
    merchant_id = get_merchant_id(request)
    merchant = await verify_merchant_exists(merchant_id, db)

    preview_service = PreviewService(db=db)
    session_data = preview_service.create_session(merchant)

    logger.info(
        "preview_conversation_created",
        merchant_id=merchant_id,
        session_id=session_data["preview_session_id"],
    )

    return PreviewSessionEnvelope(
        data=PreviewSessionResponse(**session_data),
        meta=create_meta(),
    )


@router.post(
    "/preview/message",
    response_model=PreviewMessageEnvelope,
)
async def send_preview_message(
    request: Request,
    message_request: PreviewMessageRequest,
    db: AsyncSession = Depends(get_db),
) -> PreviewMessageEnvelope:
    """
    Send a message in preview mode and get bot response.

    Processes a merchant's test message through the bot configuration
    and returns the bot's response with confidence scoring.

    NOTE: CSRF protection is provided by CSRFMiddleware (see main.py:164).
    All POST requests automatically require valid CSRF tokens unless the path
    is in BYPASS_PATHS. The /api/v1/preview/message path is NOT in
    the bypass list, so it is protected by default.

    NOTE: Authentication in DEBUG mode uses X-Merchant-Id header for
    convenience. In production, proper JWT authentication should be used.

    Args:
        request: FastAPI request with merchant authentication
        message_request: Message with preview session ID
        db: Database session

    Returns:
        PreviewMessageEnvelope with bot response and confidence metadata

    Raises:
        APIError: If session not found, message invalid, or generation fails
    """
    merchant_id = get_merchant_id(request)
    merchant = await verify_merchant_exists(merchant_id, db)

    # Validate message format
    if not message_request.message or not message_request.message.strip():
        raise APIError(
            ErrorCode.VALIDATION_ERROR,
            "Message cannot be empty",
        )

    preview_service = PreviewService(db=db)

    # Verify session exists
    session = preview_service.get_session(message_request.preview_session_id)
    if not session:
        raise APIError(
            ErrorCode.NOT_FOUND,
            f"Preview session {message_request.preview_session_id} not found or has expired",
        )

    try:
        # Send message and get bot response
        response = await preview_service.send_message(
            session_id=message_request.preview_session_id,
            message=message_request.message,
            merchant=merchant,
        )

        logger.info(
            "preview_message_sent",
            merchant_id=merchant_id,
            session_id=message_request.preview_session_id,
            confidence=response.confidence,
        )

        return PreviewMessageEnvelope(
            data=response,
            meta=create_meta(),
        )

    except ValueError as e:
        # Session not found error
        raise APIError(
            ErrorCode.NOT_FOUND,
            str(e),
        )
    except APIError:
        # Re-raise APIError as-is
        raise
    except Exception as e:
        logger.error(
            "preview_message_failed",
            merchant_id=merchant_id,
            session_id=message_request.preview_session_id,
            error=str(e),
            error_type=type(e).__name__,
        )
        raise APIError(
            ErrorCode.LLM_PROVIDER_ERROR,
            f"Failed to generate bot response: {str(e)}",
        )


@router.delete(
    "/preview/conversation/{preview_session_id}",
    response_model=PreviewResetEnvelope,
)
async def reset_preview_conversation(
    request: Request,
    preview_session_id: str,
    db: AsyncSession = Depends(get_db),
) -> PreviewResetEnvelope:
    """
    Reset or delete a preview conversation.

    Clears all messages from the current preview session, allowing
    the merchant to start fresh with a new test conversation.

    NOTE: CSRF protection is provided by CSRFMiddleware (see main.py:164).
    All DELETE requests automatically require valid CSRF tokens unless the path
    is in BYPASS_PATHS. The /api/v1/preview/conversation path is NOT in
    the bypass list, so it is protected by default.

    NOTE: Authentication in DEBUG mode uses X-Merchant-Id header for
    convenience. In production, proper JWT authentication should be used.

    Args:
        request: FastAPI request with merchant authentication
        preview_session_id: The preview session ID to reset
        db: Database session

    Returns:
        PreviewResetEnvelope with reset status

    Raises:
        APIError: If session not found or reset fails
    """
    merchant_id = get_merchant_id(request)
    # Verify merchant exists but don't need the merchant object for reset
    await verify_merchant_exists(merchant_id, db)

    preview_service = PreviewService(db=db)

    # Try to reset the session (clears messages)
    reset_success = preview_service.reset_session(preview_session_id)

    if not reset_success:
        # If reset fails, the session might not exist
        raise APIError(
            ErrorCode.NOT_FOUND,
            f"Preview session {preview_session_id} not found",
        )

    logger.info(
        "preview_conversation_reset",
        merchant_id=merchant_id,
        session_id=preview_session_id,
    )

    return PreviewResetEnvelope(
        data=PreviewResetResponse(
            cleared=True,
            message="Preview conversation reset successfully",
        ),
        meta=create_meta(),
    )


@router.post(
    "/preview/cleanup",
    response_model=dict,
)
async def cleanup_old_preview_sessions(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Clean up old preview sessions from memory.

    This endpoint removes preview sessions that have exceeded the maximum age
    to prevent memory leaks. Can be called periodically by a background task.

    NOTE: This endpoint is authenticated to prevent abuse.

    Args:
        request: FastAPI request with merchant authentication
        db: Database session

    Returns:
        Dictionary with cleanup results
    """
    # Verify authentication but don't need merchant object
    merchant_id = get_merchant_id(request)
    await verify_merchant_exists(merchant_id, db)

    preview_service = PreviewService(db=db)
    removed_count = preview_service.cleanup_old_sessions(
        max_age_seconds=PREVIEW_SESSION_MAX_AGE_SECONDS
    )

    logger.info(
        "preview_sessions_cleanup_completed",
        merchant_id=merchant_id,
        removed_count=removed_count,
    )

    return {
        "removed_count": removed_count,
        "message": f"Cleaned up {removed_count} old preview session(s)"
    }
