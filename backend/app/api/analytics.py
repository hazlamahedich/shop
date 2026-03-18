"""Geographic Analytics API (Story 4-13) and Widget Analytics API (Story 9-10).

Provides sales breakdown by country, city, and province for merchants.
Also provides widget analytics event ingestion and metrics.
"""

from __future__ import annotations

from typing import Any

import structlog
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import require_auth
from app.services.analytics.widget_analytics_service import WidgetAnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])
logger = structlog.get_logger(__name__)


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
    from app.core.rate_limiter import rate_limiter

    # Check rate limit for each session
    session_ids = [e.session_id for e in data.events if e.session_id]
    for session_id in session_ids:
        rate_limiter.check_widget_analytics_rate_limit(request, session_id)

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
    merchant_id: int = Query(..., description="Merchant ID"),
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_auth),
):
    """Get widget analytics metrics for a merchant.

    Story 9-10: Analytics & Performance Monitoring

    Returns aggregated metrics including open rates, message rates,
    quick reply usage, voice input usage, and carousel engagement.
    """
    service = WidgetAnalyticsService(db)
    metrics = await service.get_metrics(merchant_id, days)
    return metrics


@router.get("/widget/export", response_class=PlainTextResponse)
async def export_widget_analytics_csv(
    merchant_id: int = Query(..., description="Merchant ID"),
    start_date: str | None = Query(None, description="ISO date string for start of range"),
    end_date: str | None = Query(None, description="ISO date string for end of range"),
    event_type: str | None = Query(None, description="Filter by event type"),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_auth),
):
    """Export widget analytics as CSV.

    Story 9-10: Analytics & Performance Monitoring

    Returns CSV file with widget analytics events for the specified period.
    """
    service = WidgetAnalyticsService(db)
    csv_data = await service.export_csv(merchant_id, start_date, end_date, event_type)
    return csv_data
