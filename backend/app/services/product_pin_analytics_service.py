"""Product Pin Analytics Service.

Tracks engagement metrics for pinned products including views and cart additions.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, and_
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product_pin_analytics import ProductPinAnalytics
import structlog


logger = structlog.get_logger(__name__)


async def track_pinned_product_view(
    db: AsyncSession,
    merchant_id: int,
    product_id: str,
) -> None:
    """Track a view for a pinned product.

    Increments the view count and updates last_viewed_at timestamp.
    Creates a new analytics record if one doesn't exist.

    Args:
        db: Database session
        merchant_id: Merchant ID
        product_id: Shopify product ID
    """
    try:
        result = await db.execute(
            select(ProductPinAnalytics).where(
                and_(
                    ProductPinAnalytics.merchant_id == merchant_id,
                    ProductPinAnalytics.product_id == product_id,
                )
            )
        )
        analytics = result.scalars().first()

        now = datetime.now(timezone.utc)

        if analytics:
            analytics.views_count += 1
            analytics.last_viewed_at = now
        else:
            analytics = ProductPinAnalytics(
                merchant_id=merchant_id,
                product_id=product_id,
                views_count=1,
                last_viewed_at=now,
            )
            db.add(analytics)

        await db.flush()

        logger.debug(
            "pinned_product_view_tracked",
            merchant_id=merchant_id,
            product_id=product_id,
        )

    except Exception as e:
        logger.warning(
            "track_pinned_product_view_failed",
            merchant_id=merchant_id,
            product_id=product_id,
            error=str(e),
        )


async def track_pinned_product_cart_add(
    db: AsyncSession,
    merchant_id: int,
    product_id: str,
) -> None:
    """Track a cart addition for a pinned product.

    Increments the cart_adds_count and updates last_cart_add_at timestamp.
    Creates a new analytics record if one doesn't exist.

    Args:
        db: Database session
        merchant_id: Merchant ID
        product_id: Shopify product ID
    """
    try:
        result = await db.execute(
            select(ProductPinAnalytics).where(
                and_(
                    ProductPinAnalytics.merchant_id == merchant_id,
                    ProductPinAnalytics.product_id == product_id,
                )
            )
        )
        analytics = result.scalars().first()

        now = datetime.now(timezone.utc)

        if analytics:
            analytics.cart_adds_count += 1
            analytics.last_cart_add_at = now
        else:
            analytics = ProductPinAnalytics(
                merchant_id=merchant_id,
                product_id=product_id,
                cart_adds_count=1,
                last_cart_add_at=now,
            )
            db.add(analytics)

        await db.flush()

        logger.debug(
            "pinned_product_cart_add_tracked",
            merchant_id=merchant_id,
            product_id=product_id,
        )

    except Exception as e:
        logger.warning(
            "track_pinned_product_cart_add_failed",
            merchant_id=merchant_id,
            product_id=product_id,
            error=str(e),
        )


async def track_pinned_products_view(
    db: AsyncSession,
    merchant_id: int,
    product_ids: list[str],
) -> None:
    """Track views for multiple pinned products at once.

    Args:
        db: Database session
        merchant_id: Merchant ID
        product_ids: List of Shopify product IDs
    """
    for product_id in product_ids:
        await track_pinned_product_view(db, merchant_id, product_id)


async def get_pinned_product_analytics(
    db: AsyncSession,
    merchant_id: int,
    product_id: Optional[str] = None,
) -> list[dict]:
    """Get analytics for pinned products.

    Args:
        db: Database session
        merchant_id: Merchant ID
        product_id: Optional specific product ID to get analytics for

    Returns:
        List of analytics records with product_id, views_count, cart_adds_count
    """
    try:
        query = select(ProductPinAnalytics).where(ProductPinAnalytics.merchant_id == merchant_id)

        if product_id:
            query = query.where(ProductPinAnalytics.product_id == product_id)

        query = query.order_by(ProductPinAnalytics.views_count.desc())

        result = await db.execute(query)
        analytics_records = result.scalars().all()

        return [
            {
                "product_id": a.product_id,
                "views_count": a.views_count,
                "cart_adds_count": a.cart_adds_count,
                "last_viewed_at": a.last_viewed_at.isoformat() if a.last_viewed_at else None,
                "last_cart_add_at": a.last_cart_add_at.isoformat() if a.last_cart_add_at else None,
            }
            for a in analytics_records
        ]

    except Exception as e:
        logger.warning(
            "get_pinned_product_analytics_failed",
            merchant_id=merchant_id,
            error=str(e),
        )
        return []
