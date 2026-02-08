"""Cost tracking API endpoints.

Provides endpoints for:
- Getting conversation cost details
- Getting cost summaries with date filtering
- Real-time cost tracking
"""

from __future__ import annotations

from typing import Annotated, Optional
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.errors import APIError, ErrorCode, ValidationError
from app.schemas.cost_tracking import (
    CostListResponse,
)
from app.services.cost_tracking import CostTrackingService


router = APIRouter(prefix="/api/costs", tags=["costs"])
cost_service = CostTrackingService()


@router.get(
    "/conversation/{conversation_id}",
    response_model=CostListResponse,
)
async def get_conversation_costs(
    request: Request,
    conversation_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CostListResponse:
    """
    Get cost breakdown for a specific conversation.

    Returns detailed cost information including:
    - Total cost, tokens, request count
    - Per-request breakdown with timestamps
    - Provider and model information
    - Processing times

    Args:
        request: FastAPI request with merchant authentication
        conversation_id: Conversation identifier
        db: Database session

    Returns:
        Conversation cost response with detailed breakdown

    Raises:
        APIError: If authentication fails or cost data not found
    """
    # 1. Verify Authentication
    merchant_id = _get_merchant_id(request)

    # 2. Get conversation costs
    try:
        cost_data = await cost_service.get_conversation_costs(
            db=db,
            merchant_id=merchant_id,
            conversation_id=conversation_id,
        )
    except ValueError as e:
        raise APIError(
            ErrorCode.LLM_COST_NOT_FOUND,
            str(e),
        )

    # 3. Return response
    return CostListResponse(
        data=cost_data,
        meta={
            "requestId": f"cost-{conversation_id}",
        },
    )


@router.get(
    "/summary",
    response_model=CostListResponse,
)
async def get_cost_summary(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    date_from: Optional[str] = Query(
        None,
        description="Start date filter (ISO 8601 format, e.g., 2026-02-01)",
    ),
    date_to: Optional[str] = Query(
        None,
        description="End date filter (ISO 8601 format, e.g., 2026-02-28)",
    ),
) -> CostListResponse:
    """
    Get cost summary for the authenticated merchant.

    Returns aggregated cost data including:
    - Total cost, tokens, request count
    - Top conversations by cost
    - Cost breakdown by provider
    - Daily breakdown (if date range > 1 day)

    Args:
        request: FastAPI request with merchant authentication
        db: Database session
        date_from: Start date filter (ISO 8601 string)
        date_to: End date filter (ISO 8601 string)

    Returns:
        Cost summary response with aggregated data

    Raises:
        APIError: If authentication fails or date format is invalid
    """
    # 1. Verify Authentication
    merchant_id = _get_merchant_id(request)

    # 2. Validate date format
    if date_from or date_to:
        try:
            if date_from:
                # Just validate format, don't convert
                from datetime import datetime

                datetime.fromisoformat(date_from)
            if date_to:
                from datetime import datetime

                datetime.fromisoformat(date_to)
        except ValueError as e:
            raise ValidationError(
                f"Invalid date format: {str(e)}. " "Expected ISO 8601 format (e.g., 2026-02-01)"
            )

    # 3. Get cost summary
    summary = await cost_service.get_cost_summary(
        db=db,
        merchant_id=merchant_id,
        date_from=date_from,
        date_to=date_to,
    )

    # 4. Return response
    return CostListResponse(
        data=summary,
        meta={
            "requestId": "cost-summary",
        },
    )


def _get_merchant_id(request: Request) -> int:
    """Get merchant ID from request state with fallback for testing.

    Args:
        request: FastAPI request

    Returns:
        Merchant ID

    Raises:
        APIError: If authentication fails
    """
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
    return merchant_id
