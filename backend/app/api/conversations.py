from typing import Annotated, Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.errors import APIError, ErrorCode, ValidationError
from app.schemas.conversation import (
    ConversationListResponse,
    ConversationFilterParams,
    VALID_STATUS_VALUES,
    VALID_SENTIMENT_VALUES,
)
from app.services.conversation import ConversationService

router = APIRouter()
conversation_service = ConversationService()


@router.get("", response_model=ConversationListResponse)
async def list_conversations(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("updated_at", description="Sort column"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
    search: Optional[str] = Query(None, description="Search term for customer ID or message content"),
    date_from: Optional[str] = Query(None, description="Start date filter (ISO 8601)"),
    date_to: Optional[str] = Query(None, description="End date filter (ISO 8601)"),
    status: Optional[List[str]] = Query(None, description=f"Filter by status: {', '.join(VALID_STATUS_VALUES)}"),
    sentiment: Optional[List[str]] = Query(None, description=f"Filter by sentiment: {', '.join(VALID_SENTIMENT_VALUES)}"),
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
    if not hasattr(request.state, "merchant_id") or not request.state.merchant_id:
        # Fallback if middleware fails or is missing (though 401 is usually handled there)
        raise APIError(
            ErrorCode.AUTH_FAILED,
            "Authentication required",
        )

    merchant_id = request.state.merchant_id

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
    """
    List conversations for the authenticated merchant.

    Supports search and filtering by:
    - Search term: customer ID or bot message content
    - Date range: conversation created_at date range
    - Status: active, handoff, closed (multi-select)
    - Sentiment: positive, neutral, negative (multi-select)
    - Handoff: has/doesn't have handoff status

    Returns a paginated list of conversations.
    """
    # 1. Verify Authentication
    # Note: Authentication logic/middleware must populate request.state.merchant_id
    if not hasattr(request.state, "merchant_id") or not request.state.merchant_id:
        # Fallback if middleware fails or is missing (though 401 is usually handled there)
        raise APIError(
            ErrorCode.AUTH_FAILED,
            "Authentication required",
        )

    merchant_id = request.state.merchant_id

    # 2. Validate Params
    valid_sort_columns = ["updated_at", "status", "created_at"]
    if sort_by not in valid_sort_columns:
        raise ValidationError(
            "Invalid sort column",
            fields={"sort_by": f"Must be one of: {', '.join(valid_sort_columns)}"},
        )

    # Validate date formats if provided
    if date_from:
        try:
            datetime.fromisoformat(date_from)
        except ValueError:
            raise APIError(
                ErrorCode.INVALID_DATE_FORMAT,
                f"Invalid date format for date_from: '{date_from}'. Expected ISO 8601 format (e.g., 2026-02-01)",
            )

    if date_to:
        try:
            datetime.fromisoformat(date_to)
        except ValueError:
            raise APIError(
                ErrorCode.INVALID_DATE_FORMAT,
                f"Invalid date format for date_to: '{date_to}'. Expected ISO 8601 format (e.g., 2026-02-28)",
            )

    # Validate status values if provided
    if status:
        invalid_status = [s for s in status if s not in VALID_STATUS_VALUES]
        if invalid_status:
            raise APIError(
                ErrorCode.INVALID_STATUS_VALUE,
                f"Invalid status values: {invalid_status}. Valid values: {', '.join(VALID_STATUS_VALUES)}",
            )

    # Validate sentiment values if provided
    if sentiment:
        invalid_sentiment = [s for s in sentiment if s not in VALID_SENTIMENT_VALUES]
        if invalid_sentiment:
            raise APIError(
                ErrorCode.INVALID_SENTIMENT_VALUE,
                f"Invalid sentiment values: {invalid_sentiment}. Valid values: {', '.join(VALID_SENTIMENT_VALUES)}",
            )

    # 3. Call Service with filter parameters
    conversations, total = await conversation_service.get_conversations(
        db=db,
        merchant_id=merchant_id,
        page=page,
        per_page=per_page,
        sort_by=sort_by,
        sort_order=sort_order,
        search=search,
        date_from=date_from,
        date_to=date_to,
        status=status,
        sentiment=sentiment,
        has_handoff=has_handoff,
    )

    # 4. Construct Response
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
