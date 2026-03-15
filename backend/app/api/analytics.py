"""Geographic Analytics API (Story 4-13).

Provides sales breakdown by country, city, and province for merchants.
"""

from __future__ import annotations

from typing import Any

import structlog
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.errors import APIError, ErrorCode
from app.middleware.auth import require_auth
from app.models.order import Order
from app.services.analytics.aggregated_analytics_service import AggregatedAnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])
logger = structlog.get_logger(__name__)


class GeographicBreakdown(BaseModel):
    """Geographic sales breakdown."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    country: str = Field(description="Country code (ISO 3166-1 alpha-2)")
    country_name: str | None = Field(None, description="Full country name")
    order_count: int = Field(description="Number of orders")
    total_revenue: float = Field(description="Total revenue in merchant currency")


class GeographicAnalyticsResponse(BaseModel):
    """Response for geographic analytics endpoint."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    by_country: list[GeographicBreakdown] = Field(default_factory=list)
    by_city: list[dict[str, Any]] = Field(default_factory=list)
    by_province: list[dict[str, Any]] = Field(default_factory=list)
    total_orders: int = Field(description="Total orders with geographic data")
    total_revenue: float = Field(description="Total revenue from orders with geographic data")


class TierDistributionResponse(BaseModel):
    """Response for tier distribution endpoint."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    conversations: dict[str, int] = Field(description="Conversation counts by tier")
    messages: dict[str, int] = Field(description="Message counts by tier")
    orders: dict[str, int] = Field(description="Order counts by tier")
    summary: dict[str, int] = Field(description="Summary totals by tier")


class AnonymizedSummaryResponse(BaseModel):
    """Response for anonymized analytics summary."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    merchant_id: int = Field(description="Merchant ID")
    tier_distribution: dict[str, Any] = Field(description="Tier distribution breakdown")
    conversation_stats: dict[str, Any] = Field(description="Conversation statistics (30 days)")
    order_stats: dict[str, Any] = Field(description="Order statistics (anonymized)")
    generated_at: str = Field(description="Timestamp when summary was generated")
    tier: str = Field(description="Data tier (always 'anonymized')", default="anonymized")


class TopProduct(BaseModel):
    """Top selling product details."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    product_id: str = Field(description="Shopify product ID")
    title: str = Field(description="Product title")
    quantity_sold: int = Field(description="Total quantity sold")
    total_revenue: float = Field(description="Total revenue from product")
    image_url: str | None = Field(None, description="Product image URL from Shopify")


class TopProductsResponse(BaseModel):
    """Response for top products endpoint."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    items: list[TopProduct] = Field(default_factory=list, description="List of top products")
    merchant_id: int = Field(description="Merchant ID")
    days: int = Field(description="Number of days included in aggregation")


class PendingOrder(BaseModel):
    """Pending order details."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    order_number: str = Field(description="Order number")
    status: str = Field(description="Order status")
    total: float = Field(description="Order total amount")
    currency_code: str = Field(description="Currency code")
    estimated_delivery: str | None = Field(None, description="Estimated delivery date ISO string")
    created_at: str | None = Field(None, description="Creation date ISO string")


class PendingOrdersResponse(BaseModel):
    """Response for pending orders endpoint."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    items: list[PendingOrder] = Field(default_factory=list, description="List of pending orders")
    merchant_id: int = Field(description="Merchant ID")


COUNTRY_NAMES: dict[str, str] = {
    "US": "United States",
    "CA": "Canada",
    "GB": "United Kingdom",
    "AU": "Australia",
    "DE": "Germany",
    "FR": "France",
    "JP": "Japan",
    "MX": "Mexico",
    "BR": "Brazil",
    "IN": "India",
    "NZ": "New Zealand",
    "ES": "Spain",
    "IT": "Italy",
    "NL": "Netherlands",
    "SE": "Sweden",
    "CH": "Switzerland",
}


@router.get("/geographic", response_model=GeographicAnalyticsResponse)
async def get_geographic_analytics(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> GeographicAnalyticsResponse:
    """Get sales breakdown by country, city, and province.

    Story 4-13: Geographic analytics for sales distribution.

    Requires JWT authentication. Results are scoped to the authenticated merchant.

    Returns:
        GeographicAnalyticsResponse with breakdown by country, city, and province
    """
    merchant_id = require_auth(request)

    log = logger.bind(merchant_id=merchant_id)
    log.info("geographic_analytics_request")

    try:
        by_country_result = await db.execute(
            select(
                Order.shipping_country,
                func.count(Order.id).label("order_count"),
                func.sum(Order.total).label("total_revenue"),
            )
            .where(Order.merchant_id == merchant_id)
            .where(Order.shipping_country.isnot(None))
            .where(Order.is_test.is_(False))
            .group_by(Order.shipping_country)
            .order_by(func.sum(Order.total).desc())
        )
        by_country_rows = by_country_result.all()

        by_country = [
            GeographicBreakdown(
                country=row.shipping_country,
                country_name=COUNTRY_NAMES.get(row.shipping_country, row.shipping_country),
                order_count=row.order_count,
                total_revenue=float(row.total_revenue or 0),
            )
            for row in by_country_rows
        ]

        by_city_result = await db.execute(
            select(
                Order.shipping_city,
                Order.shipping_country,
                func.count(Order.id).label("order_count"),
                func.sum(Order.total).label("total_revenue"),
            )
            .where(Order.merchant_id == merchant_id)
            .where(Order.shipping_city.isnot(None))
            .where(Order.is_test.is_(False))
            .group_by(Order.shipping_city, Order.shipping_country)
            .order_by(func.sum(Order.total).desc())
            .limit(20)
        )
        by_city_rows = by_city_result.all()

        by_city = [
            {
                "city": row.shipping_city,
                "country": row.shipping_country,
                "orderCount": row.order_count,
                "totalRevenue": float(row.total_revenue or 0),
            }
            for row in by_city_rows
        ]

        by_province_result = await db.execute(
            select(
                Order.shipping_province,
                Order.shipping_country,
                func.count(Order.id).label("order_count"),
                func.sum(Order.total).label("total_revenue"),
            )
            .where(Order.merchant_id == merchant_id)
            .where(Order.shipping_province.isnot(None))
            .where(Order.is_test.is_(False))
            .group_by(Order.shipping_province, Order.shipping_country)
            .order_by(func.sum(Order.total).desc())
            .limit(20)
        )
        by_province_rows = by_province_result.all()

        by_province = [
            {
                "province": row.shipping_province,
                "country": row.shipping_country,
                "orderCount": row.order_count,
                "totalRevenue": float(row.total_revenue or 0),
            }
            for row in by_province_rows
        ]

        total_orders = sum(b.order_count for b in by_country)
        total_revenue = sum(b.total_revenue for b in by_country)

        log.info(
            "geographic_analytics_success",
            country_count=len(by_country),
            city_count=len(by_city),
            total_orders=total_orders,
            total_revenue=total_revenue,
        )

        return GeographicAnalyticsResponse(
            by_country=by_country,
            by_city=by_city,
            by_province=by_province,
            total_orders=total_orders,
            total_revenue=total_revenue,
        )

    except APIError:
        raise
    except Exception as e:
        log.error("geographic_analytics_failed", error=str(e))
        raise APIError(
            ErrorCode.GEOGRAPHIC_QUERY_ERROR,
            f"Failed to retrieve geographic analytics: {str(e)}",
        )


@router.get("/summary", response_model=AnonymizedSummaryResponse)
async def get_anonymized_summary(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> AnonymizedSummaryResponse:
    """Get anonymized analytics summary with tier distribution.

    Story 6-4: Tier-aware analytics with PII stripping.

    Returns:
        - Tier distribution (voluntary/operational/anonymized counts)
        - Conversation stats (30 days, no PII)
        - Order stats (anonymized, no customer data)

    All data is tier=ANONYMIZED with no personal identifiers.
    """
    merchant_id = require_auth(request)

    log = logger.bind(merchant_id=merchant_id)
    log.info("anonymized_summary_request")

    try:
        service = AggregatedAnalyticsService(db)
        summary = await service.get_anonymized_summary(merchant_id)

        log.info(
            "anonymized_summary_success",
            merchant_id=merchant_id,
        )

        return AnonymizedSummaryResponse(
            merchant_id=summary["merchantId"],
            tier_distribution=summary["tierDistribution"],
            conversation_stats=summary["conversationStats"],
            order_stats=summary["orderStats"],
            generated_at=summary["generatedAt"],
            tier=summary["tier"],
        )

    except APIError:
        raise
    except Exception as e:
        log.error("anonymized_summary_failed", error=str(e))
        raise APIError(
            ErrorCode.INTERNAL_ERROR,
            f"Failed to retrieve anonymized summary: {str(e)}",
        )


@router.get("/top-products", response_model=TopProductsResponse)
async def get_top_products(
    request: Request,
    days: int = 30,
    limit: int = 5,
    db: AsyncSession = Depends(get_db),
) -> TopProductsResponse:
    """Get top products for dashboard.

    Story 7: Dashboard Widgets.

    Returns the top products for the last N days by quantity sold,
    including total revenue and Shopify images.
    """
    merchant_id = require_auth(request)
    log = logger.bind(merchant_id=merchant_id, days=days, limit=limit)
    log.info("top_products_request")

    try:
        service = AggregatedAnalyticsService(db)
        products = await service.get_top_products(
            merchant_id=merchant_id,
            days=days,
            limit=limit,
        )

        return TopProductsResponse(
            items=[TopProduct(**p) for p in products],
            merchant_id=merchant_id,
            days=days,
        )

    except APIError:
        raise
    except Exception as e:
        log.error("top_products_error", error=str(e))
        raise APIError(ErrorCode.INTERNAL_ERROR, f"Failed to fetch top products: {str(e)}")


class BotQualityMetrics(BaseModel):
    """Response for bot quality metrics endpoint."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    merchant_id: int = Field(description="Merchant ID")
    period: dict[str, Any] = Field(description="Aggregation period details")
    avg_response_time_seconds: float = Field(description="Average bot response time in seconds")
    fallback_rate: float = Field(
        description="Percentage of conversations with low confidence triggers"
    )
    resolution_rate: float = Field(
        description="Percentage of conversations resolved without handoff"
    )
    csat_score: float | None = Field(None, description="Customer satisfaction score (1-5 scale)")
    csat_change: float | None = Field(None, description="Change in CSAT score from previous period")
    satisfaction_rate: float | None = Field(None, description="Customer satisfaction percentage")
    total_conversations: int = Field(description="Total conversations in period")
    health_status: str = Field(description="Bot health status: healthy, warning, or critical")
    metrics: dict[str, Any] = Field(description="Detailed metric breakdown")


@router.get("/bot-quality", response_model=BotQualityMetrics)
async def get_bot_quality(
    request: Request,
    days: int = 30,
    db: AsyncSession = Depends(get_db),
) -> BotQualityMetrics:
    """Get bot quality metrics for dashboard widget.

    Story 7 Sprint 1: BotQualityWidget - Dashboard decision support.

    Returns metrics for bot performance including:
    - Average response time
    - Fallback rate (conversations with low confidence triggers)
    - Resolution rate (conversations resolved without handoff)
    - Customer satisfaction score

    Args:
        request: FastAPI request
        days: Number of days to aggregate (default 30)
        db: Database session

    Returns:
        BotQualityMetrics with bot performance data
    """
    merchant_id = require_auth(request)
    log = logger.bind(merchant_id=merchant_id, days=days)
    log.info("bot_quality_request")

    try:
        service = AggregatedAnalyticsService(db)
        metrics = await service.get_bot_quality_metrics(
            merchant_id=merchant_id,
            days=days,
        )

        return BotQualityMetrics(
            merchant_id=metrics["merchantId"],
            period=metrics["period"],
            avg_response_time_seconds=metrics["avgResponseTimeSeconds"],
            fallback_rate=metrics["fallbackRate"],
            resolution_rate=metrics["resolutionRate"],
            csat_score=metrics["csatScore"],
            satisfaction_rate=metrics["satisfactionRate"],
            total_conversations=metrics["totalConversations"],
            health_status=metrics["healthStatus"],
            metrics=metrics["metrics"],
        )

    except APIError:
        raise
    except Exception as e:
        log.error("bot_quality_error", error=str(e))
        raise APIError(ErrorCode.INTERNAL_ERROR, f"Failed to fetch bot quality metrics: {str(e)}")


@router.get("/pending-orders", response_model=PendingOrdersResponse)
async def get_pending_orders(
    request: Request,
    limit: int = 5,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
) -> PendingOrdersResponse:
    """Get pending orders for dashboard.

    Returns the unresolved orders (not delivered or cancelled),
    sorted by estimated delivery date ascending.
    """
    merchant_id = require_auth(request)
    log = logger.bind(merchant_id=merchant_id, limit=limit)
    log.info("pending_orders_request")

    try:
        service = AggregatedAnalyticsService(db)
        orders = await service.get_pending_orders(
            merchant_id=merchant_id,
            limit=limit,
            offset=offset,
        )

        return PendingOrdersResponse(
            items=[PendingOrder(**o) for o in orders],
            merchant_id=merchant_id,
        )

    except APIError:
        raise
    except Exception as e:
        log.error("pending_orders_error", error=str(e))
        raise APIError(ErrorCode.INTERNAL_ERROR, f"Failed to fetch pending orders: {str(e)}")


class PeakHoursResponse(BaseModel):
    """Response for peak hours endpoint."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    period: dict[str, Any] = Field(description="Aggregation period details")
    hourly_breakdown: list[dict[str, Any]] = Field(
        default_factory=list, description="Hourly conversation counts"
    )
    peak_hours: list[int] = Field(default_factory=list, description="Peak hour indices")
    peak_day: int | None = Field(None, description="Day of week with most conversations (0=Mon)")
    peak_hour: int | None = Field(None, description="Hour with most conversations (0-23)")
    total_conversations: int = Field(description="Total conversations in period")


@router.get("/peak-hours", response_model=PeakHoursResponse)
async def get_peak_hours(
    request: Request,
    days: int = 30,
    db: AsyncSession = Depends(get_db),
) -> PeakHoursResponse:
    """Get peak hours heatmap data.

    Story 7 Sprint 2: PeakHoursHeatmapWidget - Staff scheduling decisions.

    Returns hourly conversation distribution for heatmap visualization.
    """
    merchant_id = require_auth(request)
    log = logger.bind(merchant_id=merchant_id, days=days)
    log.info("peak_hours_request")

    try:
        service = AggregatedAnalyticsService(db)
        data = await service.get_peak_hours(merchant_id=merchant_id, days=days)

        return PeakHoursResponse(
            period=data["period"],
            hourly_breakdown=data["hourlyBreakdown"],
            peak_hours=data["peakHours"],
            peak_day=data["peakDay"],
            peak_hour=data["peakHour"],
            total_conversations=data["totalConversations"],
        )

    except APIError:
        raise
    except Exception as e:
        log.error("peak_hours_error", error=str(e))
        raise APIError(ErrorCode.INTERNAL_ERROR, f"Failed to fetch peak hours: {str(e)}")


class FunnelStage(BaseModel):
    """Single funnel stage."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    name: str = Field(description="Stage name")
    count: int = Field(description="Number of items at this stage")
    percentage: float = Field(description="Percentage of total")
    dropoff_from_previous: float | None = Field(
        None, description="Drop-off percentage from previous stage"
    )


class ConversionFunnelResponse(BaseModel):
    """Response for conversion funnel endpoint."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    period: dict[str, Any] = Field(description="Aggregation period details")
    stages: list[FunnelStage] = Field(default_factory=list, description="Funnel stages")
    overall_conversion_rate: float = Field(description="Overall conversion rate")
    mom_change: float | None = Field(None, description="Month-over-month change")


@router.get("/conversion-funnel", response_model=ConversionFunnelResponse)
async def get_conversion_funnel(
    request: Request,
    days: int = 30,
    db: AsyncSession = Depends(get_db),
) -> ConversionFunnelResponse:
    """Get conversion funnel data.

    Story 7 Sprint 2: ConversionFunnelWidget - Sales effectiveness decisions.

    Returns conversation-to-sale funnel metrics.
    """
    merchant_id = require_auth(request)
    log = logger.bind(merchant_id=merchant_id, days=days)
    log.info("conversion_funnel_request")

    try:
        service = AggregatedAnalyticsService(db)
        data = await service.get_conversion_funnel(merchant_id=merchant_id, days=days)

        return ConversionFunnelResponse(
            period=data["period"],
            stages=[FunnelStage(**s) for s in data["stages"]],
            overall_conversion_rate=data["overallConversionRate"],
            mom_change=data.get("momChange"),
        )

    except APIError:
        raise
    except Exception as e:
        log.error("conversion_funnel_error", error=str(e))
        raise APIError(ErrorCode.INTERNAL_ERROR, f"Failed to fetch conversion funnel: {str(e)}")


class KnowledgeGap(BaseModel):
    """Single knowledge gap."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    id: str = Field(description="Gap identifier")
    intent: str = Field(description="Detected intent")
    count: int = Field(description="Number of occurrences")
    last_occurrence: str = Field(description="Last occurrence timestamp")
    suggested_action: str = Field(description="Suggested action to resolve")


class KnowledgeGapsResponse(BaseModel):
    """Response for knowledge gaps endpoint."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    period: dict[str, Any] = Field(description="Aggregation period details")
    gaps: list[KnowledgeGap] = Field(default_factory=list, description="Knowledge gaps")
    total_gaps: int = Field(description="Total number of gaps detected")


@router.get("/knowledge-gaps", response_model=KnowledgeGapsResponse)
async def get_knowledge_gaps(
    request: Request,
    days: int = 30,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
) -> KnowledgeGapsResponse:
    """Get knowledge gaps data.

    Story 7 Sprint 2: KnowledgeGapWidget - Content improvement decisions.

    Returns detected gaps in bot knowledge for FAQ creation.
    """
    merchant_id = require_auth(request)
    log = logger.bind(merchant_id=merchant_id, days=days, limit=limit)
    log.info("knowledge_gaps_request")

    try:
        service = AggregatedAnalyticsService(db)
        data = await service.get_knowledge_gaps(merchant_id=merchant_id, days=days, limit=limit)

        return KnowledgeGapsResponse(
            period=data["period"],
            gaps=[KnowledgeGap(**g) for g in data["gaps"]],
            total_gaps=data["totalGaps"],
        )

    except APIError:
        raise
    except Exception as e:
        log.error("knowledge_gaps_error", error=str(e))
        raise APIError(ErrorCode.INTERNAL_ERROR, f"Failed to fetch knowledge gaps: {str(e)}")


# ─────────────────────────────────────────────────────────────────────────────
# P2 Widgets: Benchmark Comparison & Customer Sentiment
# ─────────────────────────────────────────────────────────────────────────────

INDUSTRY_BENCHMARKS = {
    "costPerConversation": {
        "industry": 0.035,
        "top10Percentile": 0.015,
        "bottom10Percentile": 0.08,
        "unit": "USD",
    },
    "responseTime": {
        "industry": 2.5,
        "top10Percentile": 1.0,
        "bottom10Percentile": 5.0,
        "unit": "seconds",
    },
    "resolutionRate": {
        "industry": 0.75,
        "top10Percentile": 0.90,
        "bottom10Percentile": 0.50,
        "unit": "percentage",
    },
    "csatScore": {
        "industry": 4.0,
        "top10Percentile": 4.5,
        "bottom10Percentile": 3.5,
        "unit": "score",
    },
    "fallbackRate": {
        "industry": 0.08,
        "top10Percentile": 0.03,
        "bottom10Percentile": 0.15,
        "unit": "percentage",
    },
}


class BenchmarkMetric(BaseModel):
    """Single benchmark metric comparison."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    name: str = Field(description="Metric name")
    your_value: float = Field(description="Your value")
    industry_avg: float = Field(description="Industry average")
    percentile: int = Field(description="Your percentile (0-100)")
    status: str = Field(description="above_avg, below_avg, at_avg")
    unit: str = Field(description="Unit of measurement")


class BenchmarkComparisonResponse(BaseModel):
    """Response for benchmark comparison endpoint."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    period: dict[str, Any] = Field(description="Aggregation period details")
    metrics: list[BenchmarkMetric] = Field(
        default_factory=list, description="Benchmark comparisons"
    )
    overall_percentile: int = Field(description="Overall performance percentile")
    summary: str = Field(description="Human-readable summary")


@router.get("/benchmarks", response_model=BenchmarkComparisonResponse)
async def get_benchmarks(
    request: Request,
    days: int = 30,
    db: AsyncSession = Depends(get_db),
) -> BenchmarkComparisonResponse:
    """Get cost/performance benchmark comparison.

    Story 7 P2: BenchmarkComparisonWidget - "Is my cost/performance normal?"

    Compares merchant metrics against industry benchmarks.
    """
    merchant_id = require_auth(request)
    log = logger.bind(merchant_id=merchant_id, days=days)
    log.info("benchmarks_request")

    try:
        service = AggregatedAnalyticsService(db)
        data = await service.get_benchmark_comparison(merchant_id=merchant_id, days=days)

        return BenchmarkComparisonResponse(
            period=data["period"],
            metrics=[BenchmarkMetric(**m) for m in data["metrics"]],
            overall_percentile=data["overallPercentile"],
            summary=data["summary"],
        )

    except APIError:
        raise
    except Exception as e:
        log.error("benchmarks_error", error=str(e))
        raise APIError(ErrorCode.INTERNAL_ERROR, f"Failed to fetch benchmarks: {str(e)}")


class SentimentTrendPoint(BaseModel):
    """Single sentiment data point."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    date: str = Field(description="Date (YYYY-MM-DD)")
    positive_count: int = Field(description="Number of positive messages")
    negative_count: int = Field(description="Number of negative messages")
    neutral_count: int = Field(description="Number of neutral messages")
    positive_rate: float = Field(description="Positive rate (0-1)")


class CustomerSentimentResponse(BaseModel):
    """Response for customer sentiment trend endpoint."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    period: dict[str, Any] = Field(description="Aggregation period details")
    current: dict[str, Any] = Field(description="Current sentiment summary")
    previous: dict[str, Any] | None = Field(None, description="Previous period summary")
    trend: str = Field(description="improving, declining, stable")
    trend_change: float | None = Field(None, description="Change percentage")
    daily_breakdown: list[SentimentTrendPoint] = Field(
        default_factory=list, description="Daily sentiment breakdown"
    )
    alert: str | None = Field(None, description="Alert message if sentiment declining")


@router.get("/sentiment-trend", response_model=CustomerSentimentResponse)
async def get_sentiment_trend(
    request: Request,
    days: int = 30,
    db: AsyncSession = Depends(get_db),
) -> CustomerSentimentResponse:
    """Get customer sentiment trend.

    Story 7 P2: CustomerSentimentWidget - "Are customers getting happier?"

    Returns sentiment analysis of customer messages over time.
    """
    merchant_id = require_auth(request)
    log = logger.bind(merchant_id=merchant_id, days=days)
    log.info("sentiment_trend_request")

    try:
        service = AggregatedAnalyticsService(db)
        data = await service.get_sentiment_trend(merchant_id=merchant_id, days=days)

        return CustomerSentimentResponse(
            period=data["period"],
            current=data["current"],
            previous=data.get("previous"),
            trend=data["trend"],
            trend_change=data.get("trendChange"),
            daily_breakdown=[SentimentTrendPoint(**p) for p in data.get("dailyBreakdown", [])],
            alert=data.get("alert"),
        )

    except APIError:
        raise
    except Exception as e:
        log.error("sentiment_trend_error", error=str(e))
        raise APIError(ErrorCode.INTERNAL_ERROR, f"Failed to fetch sentiment trend: {str(e)}")
