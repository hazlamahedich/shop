"""Feedback API endpoints for widget message ratings."""

from __future__ import annotations

import logging
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.errors import ErrorCode
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.message_feedback import FeedbackRating, MessageFeedback
from app.schemas.base import MinimalEnvelope, MetaData
from app.schemas.feedback import (
    FeedbackAnalyticsResponse,
    FeedbackCreate,
    FeedbackResponse,
    RecentNegativeFeedback,
    DailyFeedbackTrend,
)
from app.middleware.auth import require_auth

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/feedback", tags=["feedback"])


@router.post("", response_model=MinimalEnvelope)
async def submit_feedback(
    feedback: FeedbackCreate,
    db: AsyncSession = Depends(get_db),
) -> MinimalEnvelope:
    """Submit or update feedback for a message.

    AC2: Clicking again updates rating (upsert behavior).

    Args:
        feedback: Feedback data including message_id, rating, and optional comment
        db: Database session

    Returns:
        Created or updated feedback record

    Raises:
        HTTPException: If message not found
    """
    message = await db.get(Message, feedback.message_id)
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
    if feedback.conversation_id:
        conversation = await db.get(Conversation, feedback.conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=404,
                detail={
                    "error_code": ErrorCode.CONVERSATION_NOT_FOUND,
                    "message": "Conversation not found",
                    "details": f"Conversation ID {feedback.conversation_id} does not exist",
                },
            )

    existing_result = await db.execute(
        select(MessageFeedback).where(
            MessageFeedback.message_id == feedback.message_id,
            MessageFeedback.session_id == feedback.session_id,
        )
    )
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
            data=FeedbackResponse.model_validate(existing_feedback),
            meta=MetaData(
                request_id=str(uuid.uuid4()),
                timestamp=datetime.now(timezone.utc).isoformat(),
            ),
        )

    new_feedback = MessageFeedback(
        message_id=feedback.message_id,
        conversation_id=conversation_id,
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
            "rating": feedback.rating,
            "session_id": feedback.session_id[:8],
        },
    )

    return MinimalEnvelope(
        data=FeedbackResponse.model_validate(new_feedback),
        meta=MetaData(
            request_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
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
        start_date = (datetime.now(timezone.utc) - timedelta(days=7)).date()
    if not end_date:
        end_date = datetime.now(timezone.utc).date()

    start_datetime = datetime.combine(start_date, datetime.min.time()).replace(tzinfo=timezone.utc)
    end_datetime = datetime.combine(end_date, datetime.max.time()).replace(tzinfo=timezone.utc)

    query = (
        select(
            MessageFeedback.rating,
            func.count(MessageFeedback.id).label("count"),
        )
        .join(Message)
        .join(Conversation)
        .where(
            Conversation.merchant_id == merchant_id,
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
            positive_count = int(row.count)
        elif row.rating == FeedbackRating.NEGATIVE:
            negative_count = int(row.count)
    total_ratings = positive_count + negative_count
    positive_percent = (positive_count / total_ratings * 100) if total_ratings > 0 else 0.0
    negative_percent = (negative_count / total_ratings * 100) if total_ratings > 0 else 0.0
    recent_negative_query = (
        select(MessageFeedback)
        .join(Message)
        .join(Conversation)
        .where(
            Conversation.merchant_id == merchant_id,
            MessageFeedback.rating == FeedbackRating.NEGATIVE,
            MessageFeedback.comment.isnot(None),
        )
        .order_by(MessageFeedback.created_at.desc())
        .limit(10)
    )
    recent_negative_result = await db.execute(recent_negative_query)
    recent_negative = [
        RecentNegativeFeedback(
            messageId=fb.message_id,
            comment=fb.comment,
            createdAt=fb.created_at,
        )
        for fb in recent_negative_result.scalars().all()
    ]
    trend: list[DailyFeedbackTrend] = []
    for i in range(7):
        day = end_date - timedelta(days=6 - i)
        day_start = datetime.combine(day, datetime.min.time()).replace(tzinfo=timezone.utc)
        day_end = datetime.combine(day, datetime.max.time()).replace(tzinfo=timezone.utc)
        day_query = (
            select(
                MessageFeedback.rating,
                func.count(MessageFeedback.id).label("count"),
            )
            .join(Message)
            .join(Conversation)
            .where(
                Conversation.merchant_id == merchant_id,
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
            timestamp=datetime.now(timezone.utc).isoformat(),
        ),
    )
