"""Handoff Alert API endpoints.

Story 4-6: Handoff Notifications
Story 4-7: Handoff Queue with Urgency

Provides endpoints for:
- Listing handoff alerts with pagination and urgency filtering
- Queue view for active handoffs sorted by urgency/wait time
- Getting unread count for dashboard badge
- Marking individual alerts as read
- Marking all alerts as read
"""

from __future__ import annotations

from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import case, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.config import settings
from app.core.database import get_db
from app.core.errors import APIError, ErrorCode
from app.models.handoff_alert import HandoffAlert
from app.schemas.base import BaseSchema
from app.schemas.handoff import UrgencyLevel

router = APIRouter()

VALID_URGENCY_VALUES = ["high", "medium", "low"]
VALID_VIEW_VALUES = ["notifications", "queue"]
VALID_SORT_BY_VALUES = ["created_desc", "urgency_desc"]


class HandoffAlertResponse(BaseSchema):
    """Response schema for a single handoff alert."""

    id: int
    conversation_id: int
    platform_sender_id: str | None = Field(
        default=None, description="Customer's platform sender ID (PSID)"
    )
    urgency_level: str = Field(description="Urgency level: high, medium, or low")
    customer_name: str | None = Field(default=None, description="Customer display name")
    customer_id: str | None = Field(default=None, description="Customer platform ID")
    conversation_preview: str | None = Field(default=None, description="Last 3 messages")
    wait_time_seconds: int = Field(description="Time since handoff in seconds")
    is_read: bool = Field(description="Whether alert has been read")
    is_offline: bool = Field(
        default=False, description="Whether handoff was triggered outside business hours"
    )
    created_at: str = Field(description="ISO 8601 timestamp")
    handoff_reason: str | None = Field(
        default=None, description="Reason for handoff: keyword, low_confidence, clarification_loop"
    )


class HandoffAlertListMeta(BaseSchema):
    """Metadata for paginated handoff alert list response."""

    total: int = Field(description="Total number of alerts matching filter")
    page: int = Field(description="Current page number")
    limit: int = Field(description="Items per page")
    unread_count: int = Field(description="Total unread alerts for merchant")
    total_waiting: int | None = Field(
        default=None,
        description="Total active handoffs waiting (only for queue view)",
    )


class HandoffAlertListResponse(BaseSchema):
    """Paginated list response for handoff alerts."""

    data: list[HandoffAlertResponse]
    meta: HandoffAlertListMeta


class UnreadCountResponse(BaseSchema):
    """Response for unread count endpoint."""

    unread_count: int = Field(description="Number of unread handoff alerts")


class MarkReadResponse(BaseSchema):
    """Response for mark as read endpoint."""

    success: bool
    alert_id: int


class MarkAllReadResponse(BaseSchema):
    """Response for mark all as read endpoint."""

    success: bool
    updated_count: int


def _get_merchant_id(request: Request) -> int:
    """Extract merchant ID from request state or headers.

    Args:
        request: FastAPI request object

    Returns:
        Merchant ID

    Raises:
        APIError: If authentication fails
    """
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


def _alert_to_response(alert: HandoffAlert) -> HandoffAlertResponse:
    """Convert HandoffAlert model to response schema.

    Args:
        alert: HandoffAlert model instance

    Returns:
        HandoffAlertResponse schema
    """
    handoff_reason = None
    platform_sender_id = None
    if alert.conversation:
        handoff_reason = alert.conversation.handoff_reason
        platform_sender_id = alert.conversation.platform_sender_id

    return HandoffAlertResponse(
        id=alert.id,
        conversation_id=alert.conversation_id,
        platform_sender_id=platform_sender_id,
        urgency_level=alert.urgency_level,
        customer_name=alert.customer_name,
        customer_id=alert.customer_id,
        conversation_preview=alert.conversation_preview,
        wait_time_seconds=alert.wait_time_seconds,
        is_read=alert.is_read,
        is_offline=getattr(alert, "is_offline", False),
        created_at=alert.created_at.isoformat() if alert.created_at else "",
        handoff_reason=handoff_reason,
    )


@router.get("", response_model=HandoffAlertListResponse)
async def list_handoff_alerts(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    urgency: str | None = Query(
        None, description=f"Filter by urgency: {', '.join(VALID_URGENCY_VALUES)}"
    ),
    view: str = Query(
        "notifications",
        description=f"View mode: {', '.join(VALID_VIEW_VALUES)}",
    ),
    sort_by: str = Query(
        "created_desc",
        description=f"Sort order: {', '.join(VALID_SORT_BY_VALUES)}",
    ),
) -> HandoffAlertListResponse:
    """List handoff alerts for the authenticated merchant.

    Story 4-6: Notifications view (default) - shows all alerts, sorted by created_at DESC
    Story 4-7: Queue view - shows active handoffs only, sorted by urgency then wait time

    Supports filtering by urgency level and pagination.

    Args:
        request: FastAPI request
        db: Database session
        page: Page number (1-indexed)
        limit: Items per page
        urgency: Optional urgency filter
        view: 'notifications' (all) or 'queue' (active handoffs only)
        sort_by: 'created_desc' or 'urgency_desc'

    Returns:
        Paginated list of handoff alerts with metadata
    """
    merchant_id = _get_merchant_id(request)

    if urgency and urgency not in VALID_URGENCY_VALUES:
        raise APIError(
            ErrorCode.VALIDATION_ERROR,
            f"Invalid urgency value. Must be one of: {', '.join(VALID_URGENCY_VALUES)}",
        )

    if view not in VALID_VIEW_VALUES:
        raise APIError(
            ErrorCode.VALIDATION_ERROR,
            f"Invalid view value. Must be one of: {', '.join(VALID_VIEW_VALUES)}",
        )

    if sort_by not in VALID_SORT_BY_VALUES:
        raise APIError(
            ErrorCode.VALIDATION_ERROR,
            f"Invalid sort_by value. Must be one of: {', '.join(VALID_SORT_BY_VALUES)}",
        )

    base_query = (
        select(HandoffAlert)
        .options(joinedload(HandoffAlert.conversation))
        .where(HandoffAlert.merchant_id == merchant_id)
    )

    if urgency:
        base_query = base_query.where(HandoffAlert.urgency_level == urgency)

    if view == "queue":
        from app.models.conversation import Conversation

        base_query = base_query.join(Conversation).where(Conversation.status == "handoff")

    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    unread_query = select(func.count()).where(
        HandoffAlert.merchant_id == merchant_id,
        HandoffAlert.is_read.is_(False),
    )
    unread_result = await db.execute(unread_query)
    unread_count = unread_result.scalar() or 0

    total_waiting: int | None = None
    if view == "queue":
        from app.models.conversation import Conversation

        waiting_query = (
            select(func.count())
            .select_from(HandoffAlert)
            .join(Conversation)
            .where(
                HandoffAlert.merchant_id == merchant_id,
                Conversation.status == "handoff",
            )
        )
        if urgency:
            waiting_query = waiting_query.where(HandoffAlert.urgency_level == urgency)
        waiting_result = await db.execute(waiting_query)
        total_waiting = waiting_result.scalar() or 0

    offset = (page - 1) * limit

    if view == "queue" and sort_by == "urgency_desc":
        urgency_order = case(
            (HandoffAlert.urgency_level == "high", 3),
            (HandoffAlert.urgency_level == "medium", 2),
            (HandoffAlert.urgency_level == "low", 1),
            else_=0,
        )
        alerts_query = (
            base_query.order_by(urgency_order.desc())
            .order_by(HandoffAlert.wait_time_seconds.desc())
            .offset(offset)
            .limit(limit)
        )
    else:
        alerts_query = (
            base_query.order_by(HandoffAlert.created_at.desc()).offset(offset).limit(limit)
        )

    result = await db.execute(alerts_query)
    alerts = result.scalars().unique().all()

    return HandoffAlertListResponse(
        data=[_alert_to_response(alert) for alert in alerts],
        meta=HandoffAlertListMeta(
            total=total,
            page=page,
            limit=limit,
            unread_count=unread_count,
            total_waiting=total_waiting,
        ),
    )


@router.get("/unread-count", response_model=UnreadCountResponse)
async def get_unread_count(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UnreadCountResponse:
    """Get count of unread handoff alerts for dashboard badge.

    Args:
        request: FastAPI request
        db: Database session

    Returns:
        Unread count for the authenticated merchant
    """
    merchant_id = _get_merchant_id(request)

    query = select(func.count()).where(
        HandoffAlert.merchant_id == merchant_id,
        HandoffAlert.is_read.is_(False),
    )

    result = await db.execute(query)
    unread_count = result.scalar() or 0

    return UnreadCountResponse(unread_count=unread_count)


@router.post("/{alert_id}/read", response_model=MarkReadResponse)
async def mark_alert_as_read(
    alert_id: int,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MarkReadResponse:
    """Mark a single handoff alert as read.

    Args:
        alert_id: ID of the alert to mark as read
        request: FastAPI request
        db: Database session

    Returns:
        Success status and alert ID

    Raises:
        APIError: If alert not found or not owned by merchant
    """
    merchant_id = _get_merchant_id(request)

    query = select(HandoffAlert).where(
        HandoffAlert.id == alert_id,
        HandoffAlert.merchant_id == merchant_id,
    )

    result = await db.execute(query)
    alert = result.scalars().first()

    if not alert:
        raise APIError(
            ErrorCode.NOT_FOUND,
            f"Handoff alert {alert_id} not found",
        )

    alert.is_read = True
    await db.commit()

    return MarkReadResponse(success=True, alert_id=alert_id)


@router.post("/mark-all-read", response_model=MarkAllReadResponse)
async def mark_all_alerts_as_read(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MarkAllReadResponse:
    """Mark all handoff alerts as read for the authenticated merchant.

    Args:
        request: FastAPI request
        db: Database session

    Returns:
        Success status and number of alerts updated
    """
    merchant_id = _get_merchant_id(request)

    stmt = (
        update(HandoffAlert)
        .where(
            HandoffAlert.merchant_id == merchant_id,
            HandoffAlert.is_read.is_(False),
        )
        .values(is_read=True)
    )

    result = await db.execute(stmt)
    await db.commit()

    updated_count = result.rowcount or 0

    return MarkAllReadResponse(success=True, updated_count=updated_count)
