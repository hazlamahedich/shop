"""Geographic Analytics API (Story 4-13), Widget Analytics API (Story 9-10), and Dashboard Analytics.

Provides sales breakdown by country, city, and province for merchants.
Also provides widget analytics event ingestion and metrics.
And dashboard analytics including summary, knowledge gaps, etc.
"""

from __future__ import annotations

from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse
from fastapi import status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.middleware.auth import require_auth
from app.services.analytics.aggregated_analytics_service import AggregatedAnalyticsService
from app.services.analytics.widget_analytics_service import WidgetAnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])
logger = structlog.get_logger(__name__)


def _get_merchant_id_from_request(request: Request) -> int:
    """Extract merchant_id from authenticated request.

    Uses request.state.merchant_id set by authentication middleware.
    Falls back to X-Merchant-Id header in DEBUG mode or X-Test-Mode for testing.
    Defaults to merchant_id=1 for development when no auth is present.
    """
    merchant_id = getattr(request.state, "merchant_id", None)
    if merchant_id:
        return merchant_id

    if settings().get("IS_TESTING"):
        return 1

    if request.headers.get("X-Test-Mode", "").lower() == "true":
        merchant_id_header = request.headers.get("X-Merchant-Id")
        if merchant_id_header:
            try:
                return int(merchant_id_header)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid X-Merchant-Id header format",
                )
        return 1

    if settings()["DEBUG"]:
        merchant_id_header = request.headers.get("X-Merchant-Id")
        if merchant_id_header:
            try:
                return int(merchant_id_header)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid X-Merchant-Id header format",
                )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Provide X-Merchant-Id header for testing.",
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
    )


class WidgetAnalyticsEventPayload(BaseModel):
    """Single analytics event payload."""

    type: str
    timestamp: str
    session_id: str
    metadata: dict[str, Any] | None = None


class WidgetAnalyticsEventsRequest(BaseModel):
    """Batch request for analytics events."""

    merchant_id: int
    events: list[WidgetAnalyticsEventPayload]


class WidgetAnalyticsEventsResponse(BaseModel):
    """Response for analytics events endpoint."""

    accepted: int


@router.post("/widget/events", response_model=WidgetAnalyticsEventsResponse)
async def ingest_widget_analytics_events(
    request: Request,
    data: WidgetAnalyticsEventsRequest,
    db: AsyncSession = Depends(get_db),
):
    """Ingest widget analytics events (public endpoint for widget).

    Story 9-10: Analytics & Performance Monitoring

    This endpoint is called by the frontend widget to track user interactions.
    Rate limited to 100 events/minute per session.
    """
    # Rate limiting: 100 events per minute per session
    from app.core.rate_limiter import RateLimiter

    # Check rate limit for each session
    session_ids = [e.session_id for e in data.events if e.session_id]
    for session_id in session_ids:
        RateLimiter.check_widget_analytics_rate_limit(request, session_id)

    service = WidgetAnalyticsService(db)

    events_data = [
        {
            "type": event.type,
            "timestamp": event.timestamp,
            "session_id": event.session_id,
            "metadata": event.metadata or {},
        }
        for event in data.events
    ]

    accepted = await service.ingest_events(data.merchant_id, events_data)

    return WidgetAnalyticsEventsResponse(accepted=accepted)


@router.get("/widget")
async def get_widget_analytics_metrics(
    request: Request,
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    db: AsyncSession = Depends(get_db),
):
    """Get widget analytics metrics for a merchant.

    Story 9-10: Analytics & Performance Monitoring

    Returns aggregated metrics including open rates, message rates,
    quick reply usage, voice input usage, and carousel engagement.
    """
    merchant_id = _get_merchant_id_from_request(request)
    service = WidgetAnalyticsService(db)
    metrics = await service.get_metrics(merchant_id, days)
    return metrics


@router.get("/widget/export", response_class=PlainTextResponse)
async def export_widget_analytics_csv(
    request: Request,
    start_date: str | None = Query(None, description="ISO date string for start of range"),
    end_date: str | None = Query(None, description="ISO date string for end of range"),
    event_type: str | None = Query(None, description="Filter by event type"),
    db: AsyncSession = Depends(get_db),
):
    """Export widget analytics as CSV.

    Story 9-10: Analytics & Performance Monitoring

    Returns CSV file with widget analytics events for the specified period.
    """
    merchant_id = _get_merchant_id_from_request(request)
    service = WidgetAnalyticsService(db)
    csv_data = await service.export_csv(merchant_id, start_date, end_date, event_type)
    return csv_data


@router.get("/summary")
async def get_analytics_summary(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Get anonymized analytics summary for dashboard.

    Story 6-4: Data Tier Separation - Tier-aware analytics

    Returns combined analytics including:
    - Tier distribution
    - Conversation stats (30 days)
    - Order stats with MoM comparison
    """
    merchant_id = _get_merchant_id_from_request(request)
    service = AggregatedAnalyticsService(db)
    summary = await service.get_anonymized_summary(merchant_id)
    return summary


@router.get("/knowledge-gaps")
async def get_knowledge_gaps(
    request: Request,
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of gaps to return"),
    db: AsyncSession = Depends(get_db),
):
    """Get knowledge gaps detected from conversations.

    Story 7 Sprint 2: KnowledgeGapWidget

    Returns detected gaps in bot knowledge for FAQ creation.
    """
    merchant_id = _get_merchant_id_from_request(request)
    service = AggregatedAnalyticsService(db)
    gaps = await service.get_knowledge_gaps(merchant_id, days, limit)
    return gaps


@router.get("/peak-hours")
async def get_peak_hours(
    request: Request,
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db),
):
    """Get peak hours heatmap data for dashboard widget.

    Returns hourly breakdown of conversation activity by day of week.
    Used by PeakHoursHeatmapWidget to show when customers are most active.
    """
    merchant_id = _get_merchant_id_from_request(request)
    service = AggregatedAnalyticsService(db)
    peak_hours_data = await service.get_peak_hours(merchant_id, days)
    return peak_hours_data


@router.get("/bot-quality")
async def get_bot_quality(
    request: Request,
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db),
):
    """Get bot quality metrics for dashboard widget.

    Returns metrics including CSAT score, response time, fallback rate, and resolution rate.
    Used by BotQualityWidget to show bot performance.
    """
    merchant_id = _get_merchant_id_from_request(request)
    service = AggregatedAnalyticsService(db)
    metrics = await service.get_bot_quality_metrics(merchant_id, days)
    return metrics


@router.get("/conversion-funnel")
async def get_conversion_funnel(
    request: Request,
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db),
):
    """Get conversion funnel data for dashboard widget.

    Returns funnel stages from conversation to purchase.
    Used by ConversionFunnelWidget to show conversion journey.
    """
    merchant_id = _get_merchant_id_from_request(request)
    service = AggregatedAnalyticsService(db)
    funnel_data = await service.get_conversion_funnel(merchant_id, days)
    return funnel_data


@router.get("/benchmarks")
async def get_benchmarks(
    request: Request,
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db),
):
    """Get benchmark comparison data for dashboard widget.

    Returns comparison metrics against industry averages.
    Used by QualityMetricsWidget to show benchmark comparison.
    """
    merchant_id = _get_merchant_id_from_request(request)
    service = AggregatedAnalyticsService(db)
    benchmark_data = await service.get_benchmark_comparison(merchant_id, days)
    return benchmark_data


@router.get("/sentiment-trend")
async def get_sentiment_trend(
    request: Request,
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db),
):
    """Get sentiment trend data for dashboard widget.

    Returns sentiment analysis of customer messages.
    Used by QualityMetricsWidget to show customer sentiment.
    """
    merchant_id = _get_merchant_id_from_request(request)
    service = AggregatedAnalyticsService(db)
    sentiment_data = await service.get_sentiment_trend(merchant_id, days)
    return sentiment_data
