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

from app.core.database import async_session
from app.core.errors import APIError, ErrorCode
from app.middleware.auth import require_auth
from app.models.order import Order
from app.services.analytics.aggregated_analytics_service import AggregatedAnalyticsService

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])
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
    db: AsyncSession = Depends(async_session),
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
    db: AsyncSession = Depends(async_session),
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
