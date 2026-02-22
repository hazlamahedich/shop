from datetime import datetime, timezone, timedelta
from typing import Annotated, Optional, List, Literal
from uuid import uuid4

import structlog
from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.database import get_db
from app.core.errors import APIError, ErrorCode, ValidationError
from app.models.conversation import Conversation
from app.schemas.base import MinimalEnvelope, MetaData
from app.schemas.conversation import (
    ConversationListResponse,
    ConversationFilterParams,
    ConversationHistoryResponse,
    ConversationHistoryData,
    ConversationHistoryMeta,
    ConversationContext,
    HandoffContext,
    CustomerInfo,
    VALID_STATUS_VALUES,
    VALID_SENTIMENT_VALUES,
    HybridModeRequest,
    HybridModeResponse,
    FacebookPageInfo,
)
from app.services.conversation import ConversationService

router = APIRouter()
conversation_service = ConversationService()
logger = structlog.get_logger(__name__)


class ActiveCountResponse(BaseModel):
    activeCount: int


@router.get("", response_model=ConversationListResponse)
async def list_conversations(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("updated_at", description="Sort column"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
    search: Optional[str] = Query(
        None, description="Search term for customer ID or message content"
    ),
    date_from: Optional[str] = Query(None, description="Start date filter (ISO 8601)"),
    date_to: Optional[str] = Query(None, description="End date filter (ISO 8601)"),
    status: Optional[List[str]] = Query(
        None, description=f"Filter by status: {', '.join(VALID_STATUS_VALUES)}"
    ),
    sentiment: Optional[List[str]] = Query(
        None, description=f"Filter by sentiment: {', '.join(VALID_SENTIMENT_VALUES)}"
    ),
    has_handoff: Optional[bool] = Query(None, description="Filter by handoff presence"),
) -> ConversationListResponse:
    """
    List conversations for the authenticated merchant.

    Supports search and filtering by:
    - Search term: customer ID or bot message content
    - Date range: conversation created_at date range
    - Status: active, handoff, closed (multi-select)
    - Sentiment: positive, neutral, negative (multi-select)
    - Handoff: has/doesn't have handoff status

    Returns a paginated list of conversations.

    Raises:
        APIError: If authentication fails or validation fails
    """
    # 1. Verify Authentication
    # Note: Authentication logic/middleware must populate request.state.merchant_id
    # For testing/manual verification, fallback to merchant_id 1 if header is present or DEBUG is on
    merchant_id = getattr(request.state, "merchant_id", None)
    if not merchant_id:
        # Check X-Merchant-Id header in DEBUG mode for easier testing
        if settings()["DEBUG"]:
            merchant_id_header = request.headers.get("X-Merchant-Id")
            if merchant_id_header:
                merchant_id = int(merchant_id_header)
            else:
                merchant_id = 1  # Default for dev/test
        else:
            raise APIError(
                ErrorCode.AUTH_FAILED,
                "Authentication required",
            )

    # 2. Validate and Parse Filter Parameters using Pydantic model
    # This leverages ConversationFilterParams validators for status, sentiment, and dates
    try:
        filter_params = ConversationFilterParams(
            search=search,
            date_from=date_from,
            date_to=date_to,
            status=status,
            sentiment=sentiment,
            has_handoff=has_handoff,
        )
    except ValueError as e:
        # Pydantic validation errors
        raise ValidationError(str(e))

    # 3. Validate sort column (separate from filter params)
    valid_sort_columns = ["updated_at", "status", "created_at"]
    if sort_by not in valid_sort_columns:
        raise ValidationError(
            "Invalid sort column",
            fields={"sort_by": f"Must be one of: {', '.join(valid_sort_columns)}"},
        )

    # 4. Call Service with validated filter parameters
    conversations, total = await conversation_service.get_conversations(
        db=db,
        merchant_id=merchant_id,
        page=page,
        per_page=per_page,
        sort_by=sort_by,
        sort_order=sort_order,
        search=filter_params.search,
        date_from=filter_params.date_from,
        date_to=filter_params.date_to,
        status=filter_params.status,
        sentiment=filter_params.sentiment,
        has_handoff=filter_params.has_handoff,
    )

    # 5. Construct Response
    total_pages = (total + per_page - 1) // per_page

    return ConversationListResponse(
        data=conversations,
        meta={
            "pagination": {
                "total": total,
                "page": page,
                "perPage": per_page,
                "totalPages": total_pages,
            },
            # request_id handled by middleware usually, but can be added here if needed in body
        },
    )


@router.get("/active-count", response_model=ActiveCountResponse)
async def get_active_conversation_count(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ActiveCountResponse:
    """
    Get count of active conversations for the authenticated merchant.

    Active conversations are those where status='active' (not in handoff or closed).
    Used for displaying a badge on the Conversations navigation item.

    Returns:
        Count of active conversations
    """
    merchant_id = getattr(request.state, "merchant_id", None)
    if not merchant_id:
        if settings()["DEBUG"]:
            merchant_id_header = request.headers.get("X-Merchant-Id")
            if merchant_id_header:
                merchant_id = int(merchant_id_header)
            else:
                merchant_id = 1
        else:
            raise APIError(
                ErrorCode.AUTH_FAILED,
                "Authentication required",
            )

    active_count = await conversation_service.get_active_count(db, merchant_id)
    return ActiveCountResponse(activeCount=active_count)


@router.get("/{conversation_id}/history", response_model=ConversationHistoryResponse)
async def get_conversation_history(
    request: Request,
    conversation_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ConversationHistoryResponse:
    """
    Get full conversation history with context for a handoff conversation.

    Returns:
        Conversation history with messages, bot context, handoff info, and customer info.

    Raises:
        APIError: If authentication fails or conversation not found
    """
    merchant_id = getattr(request.state, "merchant_id", None)
    if not merchant_id:
        if settings()["DEBUG"]:
            merchant_id_header = request.headers.get("X-Merchant-Id")
            if merchant_id_header:
                merchant_id = int(merchant_id_header)
            else:
                merchant_id = 1
        else:
            raise APIError(
                ErrorCode.AUTH_FAILED,
                "Authentication required",
            )

    history_data = await conversation_service.get_conversation_history(
        db=db,
        conversation_id=conversation_id,
        merchant_id=merchant_id,
    )

    if not history_data:
        raise APIError(
            ErrorCode.CONVERSATION_NOT_FOUND,
            "Conversation not found or access denied",
        )

    context = ConversationContext(
        cart_state=history_data["context"]["cart_state"],
        extracted_constraints=history_data["context"]["extracted_constraints"],
    )

    handoff = HandoffContext(
        trigger_reason=history_data["handoff"]["trigger_reason"],
        triggered_at=history_data["handoff"]["triggered_at"],
        urgency_level=history_data["handoff"]["urgency_level"],
        wait_time_seconds=history_data["handoff"]["wait_time_seconds"],
    )

    customer = CustomerInfo(
        masked_id=history_data["customer"]["masked_id"],
        order_count=history_data["customer"]["order_count"],
    )

    data = ConversationHistoryData(
        conversation_id=history_data["conversation_id"],
        platform_sender_id=history_data["platform_sender_id"],
        platform=history_data["platform"],
        messages=history_data["messages"],
        context=context,
        handoff=handoff,
        customer=customer,
    )

    meta = ConversationHistoryMeta(
        request_id=str(uuid4()),
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

    return ConversationHistoryResponse(data=data, meta=meta)


@router.patch(
    "/{conversation_id}/hybrid-mode",
    response_model=MinimalEnvelope,
)
async def set_hybrid_mode(
    request: Request,
    conversation_id: int,
    hybrid_mode_request: HybridModeRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """
    Enable or disable hybrid mode for a conversation.

    Hybrid mode allows merchants to take control of a conversation from the bot.
    When enabled, the bot will only respond to @bot mentions.

    Story 4-10: When disabling hybrid mode:
    - Status transitions from "handoff" to "active"
    - handoff_status resets to "none"
    - Welcome message sent to shopper (if within 24h window)

    Args:
        conversation_id: ID of the conversation
        hybrid_mode_request: Request body with 'enabled' and optional 'reason'

    Returns:
        Updated hybrid mode state with remaining time and status

    Raises:
        APIError: If authentication fails or conversation not found
    """
    from app.models.conversation import Conversation
    from app.models.facebook_integration import FacebookIntegration
    from app.core.security import decrypt_access_token
    from app.services.handoff.return_to_bot_service import ReturnToBotService
    from app.services.messenger.send_service import MessengerSendService

    logger = structlog.get_logger(__name__)

    merchant_id = getattr(request.state, "merchant_id", None)
    if not merchant_id:
        if settings()["DEBUG"]:
            merchant_id_header = request.headers.get("X-Merchant-Id")
            if merchant_id_header:
                merchant_id = int(merchant_id_header)
            else:
                merchant_id = 1
        else:
            raise APIError(
                ErrorCode.AUTH_FAILED,
                "Authentication required",
            )

    fb_result = await db.execute(
        select(FacebookIntegration).where(FacebookIntegration.merchant_id == merchant_id)
    )
    fb_integration = fb_result.scalars().first()

    if not fb_integration:
        raise APIError(
            ErrorCode.NO_FACEBOOK_PAGE_CONNECTION,
            "Merchant has not connected a Facebook page",
        )

    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.merchant_id == merchant_id,
        )
    )
    conversation = result.scalars().first()

    if not conversation:
        raise APIError(
            ErrorCode.CONVERSATION_NOT_FOUND,
            "Conversation not found or access denied",
        )

    now = datetime.now(timezone.utc)
    conversation_data = conversation.conversation_data or {}
    expires_at: datetime | None = None
    previous_status = conversation.status

    if hybrid_mode_request.enabled:
        expires_at = now + timedelta(hours=2)
        conversation_data["hybrid_mode"] = {
            "enabled": True,
            "activated_at": now.isoformat(),
            "activated_by": "merchant",
            "expires_at": expires_at.isoformat(),
        }
        remaining_seconds = 7200
    else:
        conversation_data["hybrid_mode"] = {
            "enabled": False,
            "activated_at": None,
            "activated_by": None,
            "expires_at": None,
        }
        remaining_seconds = 0

        # CRITICAL: Cannot auto-reopen closed conversations
        if conversation.status == "closed":
            raise APIError(
                ErrorCode.INVALID_STATUS_TRANSITION,
                "Cannot reopen closed conversation via return-to-bot",
            )

        if conversation.status == "handoff":
            conversation.status = "active"
            logger.info(
                "handoff_resolved",
                conversation_id=conversation_id,
                previous_status=previous_status,
                new_status="active",
                merchant_id=merchant_id,
            )

        # Reset handoff_status for all non-"none" states (pending, active, resolved)
        if conversation.handoff_status in ("pending", "active", "resolved"):
            previous_handoff_status = conversation.handoff_status
            conversation.handoff_status = "none"
            logger.info(
                "handoff_status_reset",
                conversation_id=conversation_id,
                previous_handoff_status=previous_handoff_status,
                handoff_status="none",
            )

        if fb_integration.access_token_encrypted:
            try:
                access_token = decrypt_access_token(fb_integration.access_token_encrypted)
                return_service = ReturnToBotService(db)
                fb_service = MessengerSendService(access_token=access_token)
                welcome_result = await return_service.send_welcome_message(conversation, fb_service)
                logger.info(
                    "return_to_bot_welcome",
                    conversation_id=conversation_id,
                    sent=welcome_result.get("sent"),
                    reason=welcome_result.get("reason"),
                )
            except Exception as e:
                logger.error(
                    "return_to_bot_welcome_failed",
                    conversation_id=conversation_id,
                    error=str(e),
                )

    conversation.conversation_data = conversation_data
    await db.commit()
    await db.refresh(conversation)

    response_data = {
        "conversationId": conversation_id,
        "hybridMode": {
            "enabled": hybrid_mode_request.enabled,
            "activatedAt": now.isoformat() if hybrid_mode_request.enabled else None,
            "activatedBy": "merchant" if hybrid_mode_request.enabled else None,
            "expiresAt": expires_at.isoformat() if expires_at else None,
            "remainingSeconds": remaining_seconds,
        },
        "conversationStatus": conversation.status,
        "handoffStatus": conversation.handoff_status or "none",
    }

    return {
        "data": response_data,
        "meta": {
            "requestId": str(uuid4()),
            "timestamp": now.isoformat(),
        },
    }


class HandoffContextResponse(BaseModel):
    """Response schema for handoff context."""

    isWithinBusinessHours: bool
    businessHoursConfigured: bool
    formattedBusinessHours: str | None = None
    expectedResponseTime: str | None = None


class HandoffContextEnvelope(MinimalEnvelope):
    """Envelope for handoff context response."""

    data: HandoffContextResponse


class HandoffNotificationRequest(BaseModel):
    """Request schema for handoff notification."""

    urgencyLevel: Literal["high", "medium", "low"] = "medium"
    currentTime: str | None = None


class HandoffNotificationResponse(BaseModel):
    """Response schema for handoff notification."""

    queued: bool
    scheduledFor: str | None = None
    sentImmediately: bool = False
    businessHoursConfigured: bool
    isWithinBusinessHours: bool
    urgencyLevel: str
    queueId: str | None = None


class HandoffNotificationEnvelope(MinimalEnvelope):
    """Envelope for handoff notification response."""

    data: HandoffNotificationResponse


class NotificationQueueStatusResponse(BaseModel):
    """Response schema for notification queue status."""

    queued: bool
    scheduledFor: str | None = None
    queueId: str | None = None


class NotificationQueueStatusEnvelope(MinimalEnvelope):
    """Envelope for notification queue status response."""

    data: NotificationQueueStatusResponse


def _get_merchant_id(request: Request) -> int:
    """Extract merchant ID from request state or headers."""
    merchant_id = getattr(request.state, "merchant_id", None)
    if not merchant_id:
        if settings()["DEBUG"]:
            merchant_id_header = request.headers.get("X-Merchant-Id")
            if merchant_id_header:
                return int(merchant_id_header)
            return 1
        raise APIError(
            ErrorCode.AUTH_FAILED,
            "Authentication required",
        )
    return merchant_id


@router.get(
    "/{conversation_id}/handoff-context",
    response_model=HandoffContextEnvelope,
)
async def get_handoff_context(
    request: Request,
    conversation_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    currentTime: str | None = Query(None, description="Time to check (ISO 8601)"),
) -> HandoffContextEnvelope:
    """Get business hours context for handoff message.

    Story 4-12: Business Hours Handling
    AC1: Business Hours in Handoff Message
    AC2: Expected Response Time

    Returns whether the merchant is within business hours and
    the expected response time if outside business hours.

    Args:
        request: FastAPI request
        conversation_id: Conversation ID
        db: Database session
        currentTime: Optional time override for testing

    Returns:
        HandoffContextEnvelope with business hours context
    """
    from app.models.merchant import Merchant
    from app.services.handoff.business_hours_handoff_service import (
        BusinessHoursHandoffService,
    )

    merchant_id = _get_merchant_id(request)

    result = await db.execute(select(Merchant).where(Merchant.id == merchant_id))
    merchant = result.scalars().first()

    if not merchant:
        raise APIError(
            ErrorCode.MERCHANT_NOT_FOUND,
            "Merchant not found",
        )

    conv_result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.merchant_id == merchant_id,
        )
    )
    conversation = conv_result.scalars().first()

    if not conversation:
        raise APIError(
            ErrorCode.CONVERSATION_NOT_FOUND,
            "Conversation not found or access denied",
        )

    check_time = None
    if currentTime:
        try:
            check_time = datetime.fromisoformat(currentTime.replace("Z", "+00:00"))
        except ValueError:
            pass

    if check_time is None:
        check_time = datetime.now(timezone.utc)

    business_hours_config = merchant.business_hours_config
    business_hours_configured = bool(business_hours_config and business_hours_config.get("hours"))

    handoff_service = BusinessHoursHandoffService()
    context = handoff_service.get_handoff_message_context(business_hours_config, check_time)

    return HandoffContextEnvelope(
        data=HandoffContextResponse(
            isWithinBusinessHours=not context.is_offline,
            businessHoursConfigured=business_hours_configured,
            formattedBusinessHours=context.business_hours_str if context.is_offline else None,
            expectedResponseTime=context.expected_response_time if context.is_offline else None,
        ),
        meta=MetaData(
            request_id=str(uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
        ),
    )


@router.post(
    "/{conversation_id}/handoff-notification",
    response_model=HandoffNotificationEnvelope,
)
async def create_handoff_notification(
    request: Request,
    conversation_id: int,
    notification_request: HandoffNotificationRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> HandoffNotificationEnvelope:
    """Create or queue a handoff notification.

    Story 4-12: Business Hours Handling
    AC3: Notification Queue Behavior

    If outside business hours, queues the notification for the next
    business hour opening. Otherwise, sends immediately.

    Args:
        request: FastAPI request
        conversation_id: Conversation ID
        notification_request: Notification request with urgency level
        db: Database session

    Returns:
        HandoffNotificationEnvelope with queue status
    """
    from app.models.merchant import Merchant
    from app.services.handoff.business_hours_handoff_service import (
        BusinessHoursHandoffService,
    )

    merchant_id = _get_merchant_id(request)

    result = await db.execute(select(Merchant).where(Merchant.id == merchant_id))
    merchant = result.scalars().first()

    if not merchant:
        raise APIError(
            ErrorCode.MERCHANT_NOT_FOUND,
            "Merchant not found",
        )

    conv_result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.merchant_id == merchant_id,
        )
    )
    conversation = conv_result.scalars().first()

    if not conversation:
        raise APIError(
            ErrorCode.CONVERSATION_NOT_FOUND,
            "Conversation not found or access denied",
        )

    check_time = None
    if notification_request.currentTime:
        try:
            check_time = datetime.fromisoformat(
                notification_request.currentTime.replace("Z", "+00:00")
            )
        except ValueError:
            pass

    if check_time is None:
        check_time = datetime.now(timezone.utc)

    business_hours_config = merchant.business_hours_config
    business_hours_configured = bool(business_hours_config and business_hours_config.get("hours"))

    handoff_service = BusinessHoursHandoffService()
    context = handoff_service.get_handoff_message_context(business_hours_config, check_time)

    queue_id = str(uuid4())

    if context.is_offline and context.next_business_hour:
        scheduled_for = context.next_business_hour.isoformat()
        queued = True
        sent_immediately = False

        logger.info(
            "handoff_notification_queued",
            conversation_id=conversation_id,
            merchant_id=merchant_id,
            scheduled_for=scheduled_for,
            urgency_level=notification_request.urgencyLevel,
        )
    else:
        scheduled_for = None
        queued = False
        sent_immediately = True

        logger.info(
            "handoff_notification_sent_immediately",
            conversation_id=conversation_id,
            merchant_id=merchant_id,
            urgency_level=notification_request.urgencyLevel,
        )

    return HandoffNotificationEnvelope(
        data=HandoffNotificationResponse(
            queued=queued,
            scheduledFor=scheduled_for,
            sentImmediately=sent_immediately,
            businessHoursConfigured=business_hours_configured,
            isWithinBusinessHours=not context.is_offline,
            urgencyLevel=notification_request.urgencyLevel,
            queueId=queue_id if queued else None,
        ),
        meta=MetaData(
            request_id=str(uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
        ),
    )


@router.get(
    "/{conversation_id}/notification-queue-status",
    response_model=NotificationQueueStatusEnvelope,
)
async def get_notification_queue_status(
    request: Request,
    conversation_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> NotificationQueueStatusEnvelope:
    """Get notification queue status for a conversation.

    Story 4-12: Business Hours Handling
    AC3: Notification Queue Behavior

    Returns whether a notification is queued for this conversation.

    Args:
        request: FastAPI request
        conversation_id: Conversation ID
        db: Database session

    Returns:
        NotificationQueueStatusEnvelope with queue status
    """
    merchant_id = _get_merchant_id(request)

    conv_result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.merchant_id == merchant_id,
        )
    )
    conversation = conv_result.scalars().first()

    if not conversation:
        raise APIError(
            ErrorCode.CONVERSATION_NOT_FOUND,
            "Conversation not found or access denied",
        )

    conversation_data = conversation.conversation_data or {}
    queue_info = conversation_data.get("notification_queue", {})

    return NotificationQueueStatusEnvelope(
        data=NotificationQueueStatusResponse(
            queued=queue_info.get("queued", False),
            scheduledFor=queue_info.get("scheduledFor"),
            queueId=queue_info.get("queueId"),
        ),
        meta=MetaData(
            request_id=str(uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
        ),
    )


class MerchantReplyRequest(BaseModel):
    """Request schema for merchant reply."""

    content: str = Field(..., min_length=1, max_length=5000, description="Reply message content")


class MerchantReplyData(BaseModel):
    """Response data schema for merchant reply."""

    id: int
    content: str
    sender: str = "merchant"
    createdAt: str
    platform: str


class MerchantReplyResponse(BaseModel):
    """Response schema for merchant reply."""

    message: MerchantReplyData


class MerchantReplyEnvelope(MinimalEnvelope):
    """Envelope for merchant reply response."""

    data: MerchantReplyResponse


@router.post(
    "/{conversation_id}/reply",
    response_model=MerchantReplyEnvelope,
)
async def merchant_reply(
    request: Request,
    conversation_id: int,
    reply_request: MerchantReplyRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MerchantReplyEnvelope:
    """Send a merchant reply to a conversation.

    Platform-specific behavior:
    - Messenger: Sends via Facebook Send API to the customer
    - Widget: Stores message and broadcasts to active widget via SSE
    - Preview: Returns 400 error (preview conversations are read-only)

    Args:
        request: FastAPI request
        conversation_id: Conversation ID to reply to
        reply_request: Request body with message content
        db: Database session

    Returns:
        MerchantReplyEnvelope with the sent message details

    Raises:
        APIError: If authentication fails, conversation not found,
                  or reply fails (e.g., preview is read-only)
    """
    from app.services.conversation.merchant_reply_service import MerchantReplyService

    logger.info(
        "merchant_reply_request",
        conversation_id=conversation_id,
        content_length=len(reply_request.content),
    )

    merchant_id = _get_merchant_id(request)

    reply_service = MerchantReplyService(db)

    # Set SSE manager if available (for widget broadcasts)
    from app.api.widget_events import sse_manager

    if sse_manager:
        reply_service.set_sse_manager(sse_manager)

    result = await reply_service.send_reply(
        conversation_id=conversation_id,
        merchant_id=merchant_id,
        content=reply_request.content,
    )

    message_data = result.get("message", {})

    return MerchantReplyEnvelope(
        data=MerchantReplyResponse(
            message=MerchantReplyData(
                id=message_data.get("id"),
                content=message_data.get("content"),
                sender="merchant",
                createdAt=message_data.get("createdAt"),
                platform=result.get("platform"),
            ),
        ),
        meta=MetaData(
            request_id=str(uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
        ),
    )
