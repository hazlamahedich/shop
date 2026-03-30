"""Geographic Analytics API (Story 4-13), Widget Analytics API (Story 9-10), and Dashboard Analytics.

Provides sales breakdown by country, city, and province for merchants.
Also provides widget analytics event ingestion and metrics.
And dashboard analytics including summary, knowledge gaps, etc.
"""

from __future__ import annotations

import json
from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
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


@router.get("/knowledge-effectiveness")
async def get_knowledge_effectiveness(
    request: Request,
    days: int = Query(7, ge=1, le=30, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db),
):
    """Get knowledge base effectiveness metrics.

    Story 10-7: KnowledgeEffectivenessWidget

    Returns metrics on how effectively the knowledge base answers questions:
    - Total queries
    - Successful matches
    - No-match rate
    - Average confidence score
    - 7-day trend sparkline
    """
    merchant_id = _get_merchant_id_from_request(request)
    service = AggregatedAnalyticsService(db)
    effectiveness_data = await service.get_knowledge_effectiveness(merchant_id, days)
    return {"data": effectiveness_data}


@router.get("/top-topics")
async def get_top_topics(
    request: Request,
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db),
):
    """Get top topics for dashboard widget.

    Story 10-8: Top Topics Widget

    Returns most frequently queried topics from RAG query logs.
    Uses simple frequency ranking (MVP approach).
    """
    merchant_id = _get_merchant_id_from_request(request)
    service = AggregatedAnalyticsService(db)
    topics_data = await service.get_top_topics(merchant_id, days)

    import hashlib

    data_str = str(topics_data)
    etag = hashlib.md5(data_str.encode()).hexdigest()

    response = PlainTextResponse(
        content=json.dumps({"data": topics_data}),
        headers={
            "Cache-Control": "public, max-age=3600",
            "ETag": f'"{etag}"',
            "Vary": "Accept-Encoding",
        },
        media_type="application/json",
    )
    return response


@router.get("/top-products")
async def get_top_products(
    request: Request,
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    limit: int = Query(5, ge=1, le=100, description="Maximum number of products to return"),
    db: AsyncSession = Depends(get_db),
):
    """Get top selling products for dashboard widget.

    Story 7: Dashboard Widgets.
    Returns most sold products with quantity and revenue.
    """
    merchant_id = _get_merchant_id_from_request(request)
    service = AggregatedAnalyticsService(db)
    products = await service.get_top_products(merchant_id, days, limit)
    return {"items": products, "merchantId": merchant_id, "days": days}


@router.get("/pending-orders")
async def get_pending_orders(
    request: Request,
    limit: int = Query(5, ge=1, le=100, description="Maximum number of orders to return"),
    offset: int = Query(0, ge=0, description="Number of orders to offset"),
    db: AsyncSession = Depends(get_db),
):
    """Get pending orders for dashboard widget.

    Returns orders awaiting fulfillment.
    """
    merchant_id = _get_merchant_id_from_request(request)
    service = AggregatedAnalyticsService(db)
    orders = await service.get_pending_orders(merchant_id, limit, offset)
    return {"items": orders, "merchantId": merchant_id}


@router.get("/response-time-distribution")
async def get_response_time_distribution(
    request: Request,
    days: int = Query(7, ge=1, le=30, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db),
):
    """Get response time distribution metrics for dashboard widget.

    Story 10-9: ResponseTimeWidget

    Returns percentile metrics (P50, P95, P99), histogram distribution,
    previous period comparison, and warning for slow responses.
    """
    merchant_id = _get_merchant_id_from_request(request)
    service = AggregatedAnalyticsService(db)
    data = await service.get_response_time_distribution(merchant_id, days)
    return {"data": data}


@router.get("/faq-usage")
async def get_faq_usage(
    request: Request,
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    include_unused: bool = Query(True, description="Include FAQs with 0 clicks"),
    db: AsyncSession = Depends(get_db),
):
    """Get FAQ usage analytics for dashboard widget.

    Story 10-10: FAQ Usage Widget

    Returns top FAQs by click frequency, click counts, conversion rates,
    unused FAQ highlighting, and period comparison.
    """
    import hashlib

    merchant_id = _get_merchant_id_from_request(request)
    service = AggregatedAnalyticsService(db)
    data = await service.get_faq_usage(merchant_id, days, include_unused)

    data_str = json.dumps(data, default=str)
    etag = hashlib.md5(data_str.encode()).hexdigest()

    response = PlainTextResponse(
        content=data_str,
        headers={
            "Cache-Control": "public, max-age=3600",
            "ETag": f'"{etag}"',
            "Vary": "Accept-Encoding",
        },
        media_type="application/json",
    )
    return response


@router.get("/geographic")
async def get_geographic_analytics(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Get geographic breakdown of orders by country, city, and province.

    Story 4-13: Geographic Analytics

    Returns sales breakdown by country, city, and province.
    """
    merchant_id = _get_merchant_id_from_request(request)
    service = AggregatedAnalyticsService(db)
    data = await service.get_geographic_analytics(merchant_id)
    return data


@router.get("/faq-usage/export", response_class=PlainTextResponse)
async def export_faq_usage_csv(
    request: Request,
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db),
):
    """Export FAQ usage data as CSV.

    Story 10-10: FAQ Usage Widget

    Returns CSV with FAQ question, click count. conversion rate. and period.
    """
    import csv
    import io

    merchant_id = _get_merchant_id_from_request(request)
    service = AggregatedAnalyticsService(db)
    data = await service.get_faq_usage(merchant_id, days, include_unused=True)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["FAQ Question", "Clicks", "Conversion Rate (%)", "Follow-ups", "Period"])

    for faq in data.get("faqs", []):
        writer.writerow(
            [
                faq.get("question", ""),
                faq.get("clickCount", 0),
                faq.get("conversionRate", 0),
                faq.get("followupCount", 0),
                data.get("period", {}).get("days", 30),
            ]
        )

    csv_content = output.getvalue()

    return PlainTextResponse(
        content=csv_content,
        headers={
            "Content-Disposition": f'attachment; filename="faq-usage-{days}d.csv"',
            "Content-Type": "text/csv",
        },
    )


# ────────────────────────────────────────────────────────────────
# Answer Performance Dashboard Endpoints
# ────────────────────────────────────────────────────────────────


@router.get("/answer-quality")
async def get_answer_quality_score(
    request: Request,
    days: int = Query(30, ge=1, le=90, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db),
):
    """Get Answer Quality Score - Aggregate RAG performance metric.

    Calculates a composite score (0-100) based on:
    - Match rate (40%)
    - Average confidence (35%)
    - User feedback (25%)

    Returns score, status, and 14-day trend.
    """
    merchant_id = _get_merchant_id_from_request(request)
    service = AggregatedAnalyticsService(db)
    data = await service.calculate_answer_quality_score(merchant_id, days)
    return data


@router.get("/top-questions")
async def get_top_questions(
    request: Request,
    days: int = Query(30, ge=1, le=90, description="Number of days to analyze"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of questions to return"),
    db: AsyncSession = Depends(get_db),
):
    """Get Top Customer Questions with performance metrics.

    Returns most frequent queries with:
    - Frequency count
    - Match success rate
    - Average confidence
    - Category classification
    - Trend indicator (rising/falling/stable)
    """
    merchant_id = _get_merchant_id_from_request(request)
    service = AggregatedAnalyticsService(db)
    data = await service.get_top_questions_with_metrics(merchant_id, days, limit)
    return data


@router.get("/customer-feedback")
async def get_customer_feedback(
    request: Request,
    days: int = Query(30, ge=1, le=90, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db),
):
    """Get Customer Feedback Metrics for RAG answers.

    Returns:
    - Total feedback count
    - Positive/negative rates
    - Top feedback themes
    - Sentiment analysis
    """
    merchant_id = _get_merchant_id_from_request(request)
    service = AggregatedAnalyticsService(db)
    data = await service.get_customer_feedback_metrics(merchant_id, days)
    return data


@router.get("/document-performance")
async def get_document_performance(
    request: Request,
    days: int = Query(30, ge=1, le=90, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db),
):
    """Get Document Performance and Usage Analytics.

    Returns:
    - Most referenced documents
    - Unused documents
    - Average confidence per document
    - Document status (active/unused/outdated)
    """
    merchant_id = _get_merchant_id_from_request(request)
    service = AggregatedAnalyticsService(db)
    data = await service.get_document_usage_stats(merchant_id, days)
    return data


@router.get("/high-impact-improvements")
async def get_high_impact_improvements(
    request: Request,
    days: int = Query(30, ge=1, le=90, description="Number of days to analyze"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of improvements to return"),
    db: AsyncSession = Depends(get_db),
):
    """Get High-Impact Improvements - Prioritized action items.

    Returns prioritized list of improvements with:
    - Questions with high volume + low match rate
    - Estimated handoff reduction impact
    - Suggested actions (add FAQ, upload doc, update doc)
    - Priority level (high/medium/low)
    """
    merchant_id = _get_merchant_id_from_request(request)
    service = AggregatedAnalyticsService(db)
    data = await service.get_high_impact_improvements(merchant_id, days, limit)
    return data


@router.get("/question-categories")
async def get_question_categories(
    request: Request,
    days: int = Query(30, ge=1, le=90, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db),
):
    """Get Question Categories breakdown with performance metrics.

    Returns categories with:
    - Category name
    - Query volume
    - Match rate per category
    - Average confidence
    - Trend indicator
    - Top questions in category
    """
    merchant_id = _get_merchant_id_from_request(request)
    service = AggregatedAnalyticsService(db)
    data = await service.get_question_categories(merchant_id, days)
    return data


@router.get("/failed-queries")
async def get_failed_queries(
    request: Request,
    days: int = Query(30, ge=1, le=90, description="Number of days to analyze"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of queries to return"),
    db: AsyncSession = Depends(get_db),
):
    """Get Failed Queries - questions without answers.

    Returns unmatched queries with:
    - Query text
    - Frequency count
    - Last asked timestamp
    - Suggested action (add FAQ, upload doc, update doc)
    - Estimated impact
    - Category
    """
    merchant_id = _get_merchant_id_from_request(request)
    service = AggregatedAnalyticsService(db)
    data = await service.get_failed_queries(merchant_id, days, limit)
    return data


@router.get("/performance-alerts")
async def get_performance_alerts(
    request: Request,
    days: int = Query(1, ge=1, le=7, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db),
):
    """Get Performance Alerts for RAG health monitoring.

    Returns active alerts with:
    - Alert type (critical/warning/info)
    - Title and description
    - Metric and value
    - Threshold
    - Suggested action
    - Timestamp
    """
    merchant_id = _get_merchant_id_from_request(request)
    service = AggregatedAnalyticsService(db)
    data = await service.get_performance_alerts(merchant_id, days)
    return data


@router.get("/quick-actions")
async def get_quick_actions(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Get Quick Actions for immediate improvements.

    Returns prioritized action list with:
    - Action title and description
    - Icon type
    - Action URL
    - Priority level
    - Estimated time
    """
    merchant_id = _get_merchant_id_from_request(request)
    service = AggregatedAnalyticsService(db)
    data = await service.get_quick_actions(merchant_id)
    return data
