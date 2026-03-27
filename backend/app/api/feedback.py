"""Feedback API endpoints for widget message ratings."""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.errors import ErrorCode
from app.middleware.auth import require_auth
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.message_feedback import FeedbackRating, MessageFeedback
from app.schemas.base import MetaData, MinimalEnvelope
from app.schemas.feedback import (
    DailyFeedbackTrend,
    FeedbackAnalyticsResponse,
    FeedbackCreate,
    FeedbackResponse,
    RecentNegativeFeedback,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/feedback", tags=["feedback"])


def _is_uuid_message_id(message_id: str) -> bool:
    """Check if message_id is a UUID string."""
    try:
        uuid.UUID(message_id)
        return True
    except (ValueError, TypeError):
        return False


@router.post("", response_model=MinimalEnvelope)
async def submit_feedback(
    feedback: FeedbackCreate,
    db: AsyncSession = Depends(get_db),
) -> MinimalEnvelope:
    """Submit or update feedback for a message.

    AC2: Clicking again updates rating (upsert behavior).

    Supports both integer message IDs (persisted) and UUID message IDs (non-persisted widget messages).

    Args:
        feedback: Feedback data including message_id, rating, and comment
        db: Database session

    Returns:
        Created or updated feedback record

    Raises:
        HTTPException: If message not found (for integer message_id)
    """
    message_id_int: int | None = None
    conversation_id: int | None = None
    widget_message_id: str | None = None

    is_uuid = _is_uuid_message_id(feedback.message_id)

    if is_uuid:
        widget_message_id = feedback.message_id
        result = await db.execute(
            select(Conversation.id).where(
                Conversation.platform_sender_id == feedback.session_id,
            )
        )
        conv_id = result.scalars().first()
        if conv_id is not None:
            conversation_id = conv_id
    else:
        try:
            message_id_int = int(feedback.message_id)
        except (ValueError, TypeError):
            widget_message_id = feedback.message_id

        if message_id_int is not None:
            message = await db.get(Message, message_id_int)
            if not message:
                raise HTTPException(
                    status_code=404,
                    detail={
                        "error_code": ErrorCode.MESSAGE_NOT_FOUND,
                        "message": "Message not found",
                        "details": f"Message ID {feedback.message_id} does not exist",
                    },
                )
            conversation_id = feedback.conversation_id or message.conversation_id

        if feedback.conversation_id is not None:
            conversation = await db.get(Conversation, feedback.conversation_id)
            if conversation is None:
                raise HTTPException(
                    status_code=404,
                    detail={
                        "error_code": ErrorCode.CONVERSATION_NOT_FOUND,
                        "message": "Conversation not found",
                        "details": f"Conversation ID {feedback.conversation_id} does not exist",
                    },
                )
            conversation_id = conversation.id

    existing_query = select(MessageFeedback).where(
        MessageFeedback.session_id == feedback.session_id,
    )
    if message_id_int is not None:
        existing_query = existing_query.where(
            MessageFeedback.message_id == message_id_int,
        )
    elif widget_message_id is not None:
        existing_query = existing_query.where(
            MessageFeedback.widget_message_id == widget_message_id,
        )

    existing_result = await db.execute(existing_query)
    existing_feedback = existing_result.scalar_one_or_none()

    if existing_feedback:
        existing_feedback.rating = FeedbackRating(feedback.rating)
        existing_feedback.comment = feedback.comment
        await db.commit()
        await db.refresh(existing_feedback)
        logger.info(
            "Feedback updated",
            extra={
                "feedback_id": existing_feedback.id,
                "message_id": feedback.message_id,
                "rating": feedback.rating,
                "session_id": feedback.session_id[:8],
            },
        )
        return MinimalEnvelope(
            data=FeedbackResponse(
                id=existing_feedback.id,
                messageId=existing_feedback.message_id
                or existing_feedback.widget_message_id
                or feedback.message_id,
                widgetMessageId=existing_feedback.widget_message_id,
                rating=existing_feedback.rating.value,
                comment=existing_feedback.comment,
                createdAt=existing_feedback.created_at,
            ),
            meta=MetaData(
                request_id=str(uuid.uuid4()),
                timestamp=datetime.now(UTC).isoformat(),
            ),
        )

    new_feedback = MessageFeedback(
        message_id=message_id_int,
        widget_message_id=widget_message_id,
        conversation_id=conversation_id,
        merchant_id=feedback.merchant_id,
        rating=FeedbackRating(feedback.rating),
        comment=feedback.comment,
        session_id=feedback.session_id,
    )
    db.add(new_feedback)
    await db.commit()
    await db.refresh(new_feedback)

    logger.info(
        "Feedback created",
        extra={
            "feedback_id": new_feedback.id,
            "message_id": feedback.message_id,
            "widget_message_id": widget_message_id,
            "rating": feedback.rating,
            "session_id": feedback.session_id[:8],
        },
    )

    return MinimalEnvelope(
        data=FeedbackResponse(
            id=new_feedback.id,
            messageId=str(
                new_feedback.message_id or new_feedback.widget_message_id or feedback.message_id
            ),
            widgetMessageId=new_feedback.widget_message_id,
            rating=new_feedback.rating.value,
            comment=new_feedback.comment,
            createdAt=new_feedback.created_at,
        ),
        meta=MetaData(
            request_id=str(uuid.uuid4()),
            timestamp=datetime.now(UTC).isoformat(),
        ),
    )


@router.get("/analytics", response_model=MinimalEnvelope)
async def get_feedback_analytics(
    request: Request,
    start_date: date | None = None,
    end_date: date | None = None,
    db: AsyncSession = Depends(get_db),
    merchant_id: int = Depends(require_auth),
) -> MinimalEnvelope:
    """Get feedback analytics for merchant dashboard.

    AC4: Feedback analytics available in dashboard.
    This endpoint requires authentication (dashboard endpoint with CSRF).

    Args:
        request: FastAPI request
        start_date: Optional start date filter
        end_date: Optional end date filter
        db: Database session
        merchant_id: Authenticated merchant ID

    Returns:
        Aggregated feedback analytics
    """
    if not start_date:
        start_date = (datetime.now(UTC) - timedelta(days=7)).date()
    if not end_date:
        end_date = datetime.now(UTC).date()

    start_datetime = datetime.combine(start_date, datetime.min.time()).replace(tzinfo=UTC)
    end_datetime = datetime.combine(end_date, datetime.max.time()).replace(tzinfo=UTC)

    query = (
        select(
            MessageFeedback.rating,
            func.count(MessageFeedback.id).label("count"),
        )
        .where(
            MessageFeedback.merchant_id == merchant_id,
            MessageFeedback.created_at >= start_datetime,
            MessageFeedback.created_at <= end_datetime,
        )
        .group_by(MessageFeedback.rating)
    )

    result = await db.execute(query)
    rows = result.fetchall()
    positive_count: int = 0
    negative_count: int = 0
    for row in rows:
        if row.rating == FeedbackRating.POSITIVE:
            positive_count = int(row.count)  # type: ignore[assignment]
        elif row.rating == FeedbackRating.NEGATIVE:
            negative_count = int(row.count)  # type: ignore[assignment]
    total_ratings = positive_count + negative_count
    positive_percent = (positive_count / total_ratings * 100) if total_ratings > 0 else 0.0
    negative_percent = (negative_count / total_ratings * 100) if total_ratings > 0 else 0.0
    recent_negative_query = (
        select(MessageFeedback)
        .where(
            MessageFeedback.merchant_id == merchant_id,
            MessageFeedback.rating == FeedbackRating.NEGATIVE,
            MessageFeedback.comment.isnot(None),
        )
        .order_by(MessageFeedback.created_at.desc())
        .limit(10)
    )
    recent_negative_result = await db.execute(recent_negative_query)
    recent_negative = [
        RecentNegativeFeedback(
            messageId=fb.message_id or fb.widget_message_id or "",
            widgetMessageId=fb.widget_message_id,
            comment=fb.comment,
            createdAt=fb.created_at,
        )
        for fb in recent_negative_result.scalars().all()
    ]
    trend: list[DailyFeedbackTrend] = []
    for i in range(7):
        day = end_date - timedelta(days=6 - i)
        day_start = datetime.combine(day, datetime.min.time()).replace(tzinfo=UTC)
        day_end = datetime.combine(day, datetime.max.time()).replace(tzinfo=UTC)
        day_query = (
            select(
                MessageFeedback.rating,
                func.count(MessageFeedback.id).label("count"),
            )
            .where(
                MessageFeedback.merchant_id == merchant_id,
                MessageFeedback.created_at >= day_start,
                MessageFeedback.created_at <= day_end,
            )
            .group_by(MessageFeedback.rating)
        )
        day_result = await db.execute(day_query)
        day_rows = day_result.fetchall()
        day_positive: int = 0
        day_negative: int = 0
        for row in day_rows:
            if row.rating == FeedbackRating.POSITIVE:
                day_positive = int(row.count)
            elif row.rating == FeedbackRating.NEGATIVE:
                day_negative = int(row.count)
        trend.append(
            DailyFeedbackTrend(
                date=day.isoformat(),
                positive=day_positive,
                negative=day_negative,
            ),
        )
    return MinimalEnvelope(
        data=FeedbackAnalyticsResponse(
            totalRatings=total_ratings,
            positiveCount=positive_count,
            negativeCount=negative_count,
            positivePercent=round(positive_percent, 1),
            negativePercent=round(negative_percent, 1),
            recentNegative=recent_negative,
            trend=trend,
        ),
        meta=MetaData(
            request_id=str(uuid.uuid4()),
            timestamp=datetime.now(UTC).isoformat(),
        ),
    )
