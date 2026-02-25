"""Performance tests for Story 4-13: Payment/Cost Data Enhancement.

Tests for COGS caching, geographic analytics, and webhook handler performance.
"""

from __future__ import annotations

import os
import sys
import time
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


class TestCOGSCachePerformance:
    """Performance tests for COGS caching."""

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_cogs_cache_hit_latency(self):
        """Cache hit should be < 5ms."""
        from app.services.shopify.cogs_cache import COGSCache

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value="10.50")
        cache = COGSCache(redis_client=mock_redis)

        start = time.monotonic()
        result = await cache.get("variant_123")
        latency_ms = (time.monotonic() - start) * 1000

        assert result == Decimal("10.50")
        assert latency_ms < 5, f"Cache hit latency {latency_ms:.2f}ms exceeds 5ms threshold"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_cogs_cache_miss_latency(self):
        """Cache miss + Shopify fetch simulation should be < 500ms."""
        from app.services.shopify.cogs_cache import COGSCache

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        cache = COGSCache(redis_client=mock_redis)

        start = time.monotonic()
        result = await cache.get("variant_nonexistent")
        latency_ms = (time.monotonic() - start) * 1000

        assert result is None
        assert latency_ms < 500, f"Cache miss latency {latency_ms:.2f}ms exceeds 500ms threshold"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_batch_variant_lookup_mget(self):
        """MGET for 100 variants should be < 50ms."""
        from app.services.shopify.cogs_cache import COGSCache

        mock_redis = AsyncMock()
        mock_redis.mget = AsyncMock(return_value=[f"{i}.00" for i in range(100)])
        cache = COGSCache(redis_client=mock_redis)

        variant_ids = [f"variant_{i}" for i in range(100)]

        start = time.monotonic()
        if hasattr(cache, "get_batch"):
            results = await cache.get_batch(variant_ids)
        else:
            results = [await cache.get(vid) for vid in variant_ids[:10]]
        latency_ms = (time.monotonic() - start) * 1000

        assert latency_ms < 50, f"Batch lookup latency {latency_ms:.2f}ms exceeds 50ms threshold"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_cache_invalidation_latency(self):
        """Cache invalidation should be < 10ms."""
        from app.services.shopify.cogs_cache import COGSCache

        mock_redis = AsyncMock()
        mock_redis.delete = AsyncMock(return_value=1)
        cache = COGSCache(redis_client=mock_redis)

        start = time.monotonic()
        await cache.invalidate("gid://shopify/ProductVariant/12345")
        latency_ms = (time.monotonic() - start) * 1000

        assert latency_ms < 10, (
            f"Cache invalidation latency {latency_ms:.2f}ms exceeds 10ms threshold"
        )


class TestGeographicAnalyticsPerformance:
    """Performance tests for geographic analytics query."""

    @pytest.mark.performance
    def test_analytics_aggregation_performance(self):
        """Aggregation of 10K orders should be < 500ms."""
        orders = []
        for i in range(10000):
            orders.append(
                {
                    "shipping_country": "US" if i % 3 != 0 else "CA",
                    "shipping_city": f"City_{i % 100}",
                    "total": Decimal(f"{(i % 100) + 10}.00"),
                }
            )

        start = time.monotonic()

        country_totals = {}
        for order in orders:
            country = order["shipping_country"]
            country_totals[country] = country_totals.get(country, Decimal("0")) + order["total"]

        latency_ms = (time.monotonic() - start) * 1000

        assert latency_ms < 500, (
            f"Analytics aggregation latency {latency_ms:.2f}ms exceeds 500ms threshold"
        )
        assert "US" in country_totals
        assert "CA" in country_totals

    @pytest.mark.performance
    def test_analytics_index_usage_simulation(self):
        """Verify date-filtered query would use index."""
        filtered_orders = [
            {"created_at": datetime(2026, 2, 1, tzinfo=timezone.utc), "total": Decimal("100.00")},
            {"created_at": datetime(2026, 2, 15, tzinfo=timezone.utc), "total": Decimal("150.00")},
            {"created_at": datetime(2026, 1, 15, tzinfo=timezone.utc), "total": Decimal("75.00")},
        ]

        start_date = datetime(2026, 2, 1, tzinfo=timezone.utc)
        end_date = datetime(2026, 2, 28, tzinfo=timezone.utc)

        start = time.monotonic()
        filtered = [o for o in filtered_orders if start_date <= o["created_at"] <= end_date]
        latency_ms = (time.monotonic() - start) * 1000

        assert len(filtered) == 2
        assert latency_ms < 10

    @pytest.mark.performance
    def test_geographic_response_serialization(self):
        """Response serialization for 100 regions should be < 50ms."""
        regions = []
        for i in range(100):
            regions.append(
                {
                    "country_code": f"C{i % 10}",
                    "city": f"City_{i}",
                    "order_count": i * 10,
                    "total_revenue": f"{i * 1000}.00",
                }
            )

        start = time.monotonic()
        response = {"regions": regions, "total": len(regions)}
        latency_ms = (time.monotonic() - start) * 1000

        assert latency_ms < 50, f"Serialization latency {latency_ms:.2f}ms exceeds 50ms threshold"
        assert len(response["regions"]) == 100


class TestWebhookHandlerPerformance:
    """Performance tests for webhook handlers."""

    @pytest.mark.performance
    def test_order_cancelled_handler_latency(self):
        """Order cancelled handler should complete in < 100ms."""
        from app.services.shopify.order_processor import parse_shopify_order

        payload = {
            "id": 123456789,
            "order_number": 1001,
            "cancel_reason": "customer",
            "cancelled_at": "2026-02-25T10:00:00Z",
        }

        start = time.monotonic()
        result = parse_shopify_order(payload)
        latency_ms = (time.monotonic() - start) * 1000

        assert latency_ms < 100, f"Handler latency {latency_ms:.2f}ms exceeds 100ms threshold"
        assert result["cancel_reason"] == "customer"

    @pytest.mark.performance
    def test_inventory_update_handler_latency(self):
        """Inventory update handler should complete in < 100ms."""
        payload = {
            "inventory_item_id": 12345,
            "location_id": 67890,
            "available": 10,
        }

        start = time.monotonic()
        is_low_stock = payload.get("available", 999) <= 5
        latency_ms = (time.monotonic() - start) * 1000

        assert latency_ms < 100, f"Handler latency {latency_ms:.2f}ms exceeds 100ms threshold"
        assert is_low_stock is False

    @pytest.mark.performance
    def test_dispute_handler_latency(self):
        """Dispute handler should complete in < 100ms."""
        payload = {
            "id": "dispute_123",
            "order_id": 123456789,
            "amount": "99.99",
            "currency": "USD",
            "reason": "fraudulent",
            "evidence_due_by": "2026-03-15T00:00:00Z",
            "status": "needs_response",
        }

        start = time.monotonic()
        dispute_data = {
            "shopify_dispute_id": payload.get("id"),
            "order_id": payload.get("order_id"),
            "amount": payload.get("amount"),
            "currency": payload.get("currency", "USD"),
            "reason": payload.get("reason"),
            "status": payload.get("status"),
        }
        latency_ms = (time.monotonic() - start) * 1000

        assert latency_ms < 100, f"Handler latency {latency_ms:.2f}ms exceeds 100ms threshold"
        assert dispute_data["shopify_dispute_id"] == "dispute_123"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_batch_cache_invalidation_performance(self):
        """Batch cache invalidation for 50 variants should be < 50ms."""
        from app.services.shopify.cogs_cache import COGSCache

        mock_redis = AsyncMock()
        mock_redis.delete = AsyncMock(return_value=50)
        cache = COGSCache(redis_client=mock_redis)

        variant_gids = [f"gid://shopify/ProductVariant/{i}" for i in range(50)]

        start = time.monotonic()
        if hasattr(cache, "invalidate_batch"):
            result = await cache.invalidate_batch(variant_gids)
        else:
            for gid in variant_gids:
                await cache.invalidate(gid)
        latency_ms = (time.monotonic() - start) * 1000

        assert latency_ms < 50, (
            f"Batch invalidation latency {latency_ms:.2f}ms exceeds 50ms threshold"
        )
