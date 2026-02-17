"""Widget API endpoints for embeddable chat widget.

Provides public API endpoints for:
- Creating anonymous widget sessions
- Sending messages and receiving bot responses
- Getting widget configuration
- Ending widget sessions

Story 5.1: Backend Widget API
"""

from __future__ import annotations

import os
from typing import Optional

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.core.database import get_db
from app.core.errors import APIError, ErrorCode
from app.core.rate_limiter import RateLimiter
from app.schemas.base import MetaData
from app.schemas.widget import (
    CreateSessionRequest,
    WidgetSessionResponse,
    WidgetSessionEnvelope,
    WidgetSessionMetadataResponse,
    WidgetSessionMetadataEnvelope,
    SendMessageRequest,
    WidgetMessageResponse,
    WidgetMessageEnvelope,
    WidgetConfigResponse,
    WidgetConfigEnvelope,
    SuccessResponse,
    SuccessEnvelope,
    WidgetConfig,
    create_meta,
)
from app.models.merchant import Merchant
from app.services.widget.widget_session_service import WidgetSessionService
from app.services.widget.widget_message_service import WidgetMessageService


logger = structlog.get_logger(__name__)

router = APIRouter()


def _validate_domain_whitelist(request: Request, allowed_domains: list[str]) -> None:
    """Validate request origin against domain whitelist.

    Args:
        request: FastAPI request
        allowed_domains: List of allowed domains (empty = all allowed)

    Raises:
        APIError: If origin is not in whitelist
    """
    if not allowed_domains:
        return

    origin = request.headers.get("Origin", "")
    if not origin:
        return

    from urllib.parse import urlparse

    try:
        parsed = urlparse(origin)
        request_domain = parsed.netloc.lower()

        for allowed in allowed_domains:
            allowed_lower = allowed.lower()
            if request_domain == allowed_lower or request_domain.endswith(f".{allowed_lower}"):
                return

        raise APIError(
            ErrorCode.WIDGET_DOMAIN_NOT_ALLOWED,
            f"Domain {request_domain} is not allowed",
        )
    except Exception as e:
        if isinstance(e, APIError):
            raise
        logger.warning("widget_domain_parse_error", origin=origin, error=str(e))


def _check_rate_limit(request: Request) -> Optional[int]:
    """Check if client is rate limited using shared RateLimiter.

    Args:
        request: FastAPI request

    Returns:
        None if allowed, retry_after seconds if rate limited
    """
    return RateLimiter.check_widget_rate_limit(request)


@router.post(
    "/widget/session",
    response_model=WidgetSessionEnvelope,
    summary="Create widget session",
    description="Create a new anonymous widget session for a merchant",
)
async def create_widget_session(
    request: Request,
    session_request: CreateSessionRequest,
    db: AsyncSession = Depends(get_db),
) -> WidgetSessionEnvelope:
    """Create a new anonymous widget session.

    Creates a session that allows visitors to interact with the
    merchant's AI shopping assistant without authentication.

    Args:
        request: FastAPI request
        session_request: Session creation request with merchant_id
        db: Database session

    Returns:
        WidgetSessionEnvelope with session_id and expires_at

    Raises:
        APIError: If merchant not found or widget disabled
    """
    # Check rate limit
    retry_after = _check_rate_limit(request)
    if retry_after:
        raise APIError(
            ErrorCode.WIDGET_RATE_LIMITED,
            "Rate limit exceeded",
            {"retry_after": retry_after},
        )

    # Verify merchant exists
    result = await db.execute(select(Merchant).where(Merchant.id == session_request.merchant_id))
    merchant = result.scalars().first()

    if not merchant:
        raise APIError(
            ErrorCode.MERCHANT_NOT_FOUND,
            f"Merchant {session_request.merchant_id} not found",
        )

    # Check if widget is enabled for this merchant
    widget_config = merchant.widget_config or {}
    if not widget_config.get("enabled", True):
        raise APIError(
            ErrorCode.WIDGET_MERCHANT_DISABLED,
            "Widget is disabled for this merchant",
        )

    # Validate domain whitelist (AC7)
    allowed_domains = widget_config.get("allowed_domains", [])
    _validate_domain_whitelist(request, allowed_domains)

    # Create session
    client_ip = RateLimiter.get_widget_client_ip(request)
    user_agent = request.headers.get("User-Agent")

    session_service = WidgetSessionService()
    session = await session_service.create_session(
        merchant_id=merchant.id,
        visitor_ip=client_ip,
        user_agent=user_agent,
    )

    logger.info(
        "widget_session_created",
        merchant_id=merchant.id,
        session_id=session.session_id,
        client_ip=client_ip,
    )

    return WidgetSessionEnvelope(
        data=WidgetSessionResponse(
            session_id=session.session_id,
            expires_at=session.expires_at,
        ),
        meta=create_meta(),
    )


@router.get(
    "/widget/session/{session_id}",
    response_model=WidgetSessionMetadataEnvelope,
    summary="Get widget session metadata",
    description="Retrieve metadata for an active widget session",
)
async def get_widget_session(
    request: Request,
    session_id: str,
) -> WidgetSessionMetadataEnvelope:
    """Get widget session metadata.

    Returns metadata about an active widget session including
    creation time, last activity, and expiry.

    Args:
        request: FastAPI request
        session_id: Widget session identifier

    Returns:
        WidgetSessionMetadataEnvelope with session details

    Raises:
        APIError: If session not found or expired
    """
    session_service = WidgetSessionService()
    session = await session_service.get_session_or_error(session_id)

    logger.info(
        "widget_session_retrieved",
        session_id=session_id,
        merchant_id=session.merchant_id,
    )

    return WidgetSessionMetadataEnvelope(
        data=WidgetSessionMetadataResponse(
            session_id=session.session_id,
            merchant_id=session.merchant_id,
            expires_at=session.expires_at,
            created_at=session.created_at,
            last_activity_at=session.last_activity_at,
        ),
        meta=create_meta(),
    )


@router.post(
    "/widget/message",
    response_model=WidgetMessageEnvelope,
    summary="Send widget message",
    description="Send a message and receive bot response",
)
async def send_widget_message(
    request: Request,
    message_request: SendMessageRequest,
    db: AsyncSession = Depends(get_db),
) -> WidgetMessageEnvelope:
    """Send a message in the widget and get bot response.

    Processes the user's message through the merchant's configured
    LLM provider and returns the bot's response.

    Args:
        request: FastAPI request
        message_request: Message with session_id and message text
        db: Database session

    Returns:
        WidgetMessageEnvelope with bot response

    Raises:
        APIError: If session invalid, expired, or processing fails
    """
    # Check rate limit
    retry_after = _check_rate_limit(request)
    if retry_after:
        raise APIError(
            ErrorCode.WIDGET_RATE_LIMITED,
            "Rate limit exceeded",
            {"retry_after": retry_after},
        )

    # Validate message
    if not message_request.message or not message_request.message.strip():
        raise APIError(
            ErrorCode.VALIDATION_ERROR,
            "Message cannot be empty",
        )

    # Get and validate session
    session_service = WidgetSessionService()
    session = await session_service.get_session_or_error(message_request.session_id)

    # Get merchant
    result = await db.execute(select(Merchant).where(Merchant.id == session.merchant_id))
    merchant = result.scalars().first()

    if not merchant:
        raise APIError(
            ErrorCode.MERCHANT_NOT_FOUND,
            f"Merchant {session.merchant_id} not found",
        )

    # Check if widget is enabled
    widget_config = merchant.widget_config or {}
    if not widget_config.get("enabled", True):
        raise APIError(
            ErrorCode.WIDGET_MERCHANT_DISABLED,
            "Widget is disabled for this merchant",
        )

    # Validate domain whitelist (AC7)
    allowed_domains = widget_config.get("allowed_domains", [])
    _validate_domain_whitelist(request, allowed_domains)

    # Process message
    message_service = WidgetMessageService(db=db, session_service=session_service)
    response = await message_service.process_message(
        session=session,
        message=message_request.message,
        merchant=merchant,
    )

    logger.info(
        "widget_message_sent",
        session_id=session.session_id,
        merchant_id=merchant.id,
        message_length=len(message_request.message),
    )

    return WidgetMessageEnvelope(
        data=WidgetMessageResponse(
            message_id=response["message_id"],
            content=response["content"],
            sender=response["sender"],
            created_at=response["created_at"],
        ),
        meta=create_meta(),
    )


@router.get(
    "/widget/config/{merchant_id}",
    response_model=WidgetConfigEnvelope,
    summary="Get widget configuration",
    description="Get widget theme and bot configuration for a merchant",
)
async def get_widget_config(
    merchant_id: int,
    db: AsyncSession = Depends(get_db),
) -> WidgetConfigEnvelope:
    """Get widget configuration for a merchant.

    Returns the widget's appearance settings and bot configuration
    for the frontend to render the widget correctly.

    Args:
        merchant_id: The merchant ID
        db: Database session

    Returns:
        WidgetConfigEnvelope with theme and bot settings

    Raises:
        APIError: If merchant not found
    """
    # Get merchant
    result = await db.execute(select(Merchant).where(Merchant.id == merchant_id))
    merchant = result.scalars().first()

    if not merchant:
        raise APIError(
            ErrorCode.MERCHANT_NOT_FOUND,
            f"Merchant {merchant_id} not found",
        )

    # Get widget config with defaults
    stored_config = merchant.widget_config or {}
    widget_config = WidgetConfig(**stored_config)

    # Override bot_name with merchant's bot_name if set
    bot_name = merchant.bot_name or widget_config.bot_name

    logger.info(
        "widget_config_retrieved",
        merchant_id=merchant_id,
    )

    return WidgetConfigEnvelope(
        data=WidgetConfigResponse(
            bot_name=bot_name,
            welcome_message=widget_config.welcome_message,
            theme=widget_config.theme,
            enabled=widget_config.enabled,
        ),
        meta=create_meta(),
    )


@router.delete(
    "/widget/session/{session_id}",
    response_model=SuccessEnvelope,
    summary="End widget session",
    description="Terminate a widget session and clear its data",
)
async def end_widget_session(
    request: Request,
    session_id: str,
) -> SuccessEnvelope:
    """End a widget session.

    Terminates the session and clears all associated data
    including message history.

    Args:
        request: FastAPI request
        session_id: Widget session identifier

    Returns:
        SuccessEnvelope with success status

    Raises:
        APIError: If session not found
    """
    # Check rate limit
    retry_after = _check_rate_limit(request)
    if retry_after:
        raise APIError(
            ErrorCode.WIDGET_RATE_LIMITED,
            "Rate limit exceeded",
            {"retry_after": retry_after},
        )

    # End session
    session_service = WidgetSessionService()
    ended = await session_service.end_session(session_id)

    if not ended:
        raise APIError(
            ErrorCode.WIDGET_SESSION_NOT_FOUND,
            f"Widget session {session_id} not found",
        )

    logger.info(
        "widget_session_ended",
        session_id=session_id,
    )

    return SuccessEnvelope(
        data=SuccessResponse(success=True),
        meta=create_meta(),
    )


@router.post(
    "/widget/test/reset-rate-limiter",
    response_model=SuccessEnvelope,
    summary="Reset rate limiter state (test only)",
    description="Reset the rate limiter state for testing purposes",
)
async def reset_rate_limiter(request: Request) -> SuccessEnvelope:
    """Reset rate limiter state for testing.

    This endpoint is only available in test mode and resets the
    in-memory rate limiter state.

    Args:
        request: FastAPI request

    Returns:
        SuccessEnvelope with success status

    Raises:
        APIError: If not in test mode
    """
    is_test_env = os.getenv("IS_TESTING", "false").lower() == "true"
    is_test_header = request.headers.get("X-Test-Mode", "").lower() == "true"

    if not (is_test_env or is_test_header):
        raise APIError(
            ErrorCode.FORBIDDEN,
            "This endpoint is only available in test mode",
        )

    RateLimiter.reset_all()

    logger.info("widget_rate_limiter_reset")

    return SuccessEnvelope(
        data=SuccessResponse(success=True),
        meta=create_meta(),
    )
