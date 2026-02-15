from datetime import datetime, timezone
from typing import Annotated, Optional, List
from uuid import uuid4
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.errors import APIError, ErrorCode, ValidationError
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
)
from app.services.conversation import ConversationService
from pydantic import BaseModel

router = APIRouter()
conversation_service = ConversationService()


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
