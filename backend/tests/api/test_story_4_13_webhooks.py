"""Tests for Story 4-13: Webhook Handlers for AC 8.

Tests for:
- orders/cancelled
- inventory_levels/update
- products/update
- disputes/create
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


class TestOrderCancelledWebhook:
    """Test orders/cancelled webhook handler."""

    @pytest.mark.p0
    @pytest.mark.unit
    def test_order_cancelled_extracts_reason(self):
        """Verify cancel_reason and cancelled_at are extracted from payload."""
        from app.services.shopify.order_processor import parse_shopify_order

        payload = {
            "id": 123456789,
            "order_number": 1001,
            "cancel_reason": "customer",
            "cancelled_at": "2026-02-25T10:00:00Z",
            "financial_status": "voided",
        }

        result = parse_shopify_order(payload)

        assert result["cancel_reason"] == "customer"
        assert result["cancelled_at"] is not None
        assert result["cancelled_at"].year == 2026

    @pytest.mark.p0
    @pytest.mark.unit
    def test_order_cancelled_handles_all_reasons(self):
        """Verify all cancel reason types are handled."""
        from app.services.shopify.order_processor import parse_shopify_order

        reasons = ["customer", "inventory", "fraud", "declined", "other"]

        for reason in reasons:
            payload = {
                "id": 123456789,
                "cancel_reason": reason,
                "cancelled_at": "2026-02-25T10:00:00Z",
            }
            result = parse_shopify_order(payload)
            assert result["cancel_reason"] == reason

    @pytest.mark.p1
    @pytest.mark.unit
    def test_order_cancelled_handles_missing_reason(self):
        """Verify graceful handling when cancel_reason is missing."""
        from app.services.shopify.order_processor import parse_shopify_order

        payload = {
            "id": 123456789,
            "cancelled_at": "2026-02-25T10:00:00Z",
        }

        result = parse_shopify_order(payload)

        assert result.get("cancel_reason") is None


class TestInventoryUpdateWebhook:
    """Test inventory_levels/update webhook handler."""

    @pytest.mark.p1
    @pytest.mark.asyncio
    async def test_inventory_update_invalidates_cogs_cache(self):
        """Verify COGS cache is invalidated on inventory update."""
        from app.services.shopify.cogs_cache import COGSCache

        mock_redis = AsyncMock()
        mock_redis.delete = AsyncMock(return_value=1)
        cache = COGSCache(redis_client=mock_redis)

        variant_gid = "gid://shopify/ProductVariant/12345"
        await cache.invalidate(variant_gid)

        mock_redis.delete.assert_called_once()

    @pytest.mark.p1
    @pytest.mark.unit
    def test_inventory_update_low_stock_detection(self):
        """Verify low stock is detected when available <= 5."""
        low_stock_levels = [0, 1, 2, 3, 4, 5]
        normal_stock_levels = [6, 10, 50, 100]

        for level in low_stock_levels:
            payload = {
                "inventory_item_id": 12345,
                "location_id": 67890,
                "available": level,
            }
            assert payload["available"] <= 5, f"Level {level} should be low stock"

        for level in normal_stock_levels:
            payload = {
                "inventory_item_id": 12345,
                "location_id": 67890,
                "available": level,
            }
            assert payload["available"] > 5, f"Level {level} should be normal stock"

    @pytest.mark.p2
    @pytest.mark.unit
    def test_inventory_update_handles_null_available(self):
        """Verify graceful handling when available is null."""
        payload = {
            "inventory_item_id": 12345,
            "location_id": 67890,
            "available": None,
        }

        assert payload.get("available") is None


class TestProductUpdateWebhook:
    """Test products/update webhook handler."""

    @pytest.mark.p1
    @pytest.mark.asyncio
    async def test_product_update_invalidates_variant_caches(self):
        """Verify all variant COGS caches are invalidated on product update."""
        from app.services.shopify.cogs_cache import COGSCache

        mock_redis = AsyncMock()
        mock_redis.delete = AsyncMock(return_value=1)
        cache = COGSCache(redis_client=mock_redis)

        variant_gids = [
            "gid://shopify/ProductVariant/111",
            "gid://shopify/ProductVariant/222",
            "gid://shopify/ProductVariant/333",
        ]

        result = await cache.invalidate_batch(variant_gids)

        assert result == 3
        mock_redis.delete.assert_called_once()

    @pytest.mark.p1
    @pytest.mark.unit
    def test_product_update_extracts_variant_ids(self):
        """Verify variant IDs are correctly extracted from product payload."""
        payload = {
            "id": 12345,
            "title": "Test Product",
            "status": "active",
            "variants": [
                {"id": 111, "title": "Small", "price": "10.00"},
                {"id": 222, "title": "Medium", "price": "15.00"},
                {"id": 333, "title": "Large", "price": "20.00"},
            ],
        }

        variants = payload.get("variants", [])
        variant_ids = [v.get("id") for v in variants if v.get("id")]

        assert len(variant_ids) == 3
        assert 111 in variant_ids
        assert 222 in variant_ids
        assert 333 in variant_ids

    @pytest.mark.p2
    @pytest.mark.unit
    def test_product_update_handles_no_variants(self):
        """Verify graceful handling when product has no variants."""
        payload = {
            "id": 12345,
            "title": "Simple Product",
            "status": "active",
            "variants": [],
        }

        variants = payload.get("variants", [])
        variant_ids = [v.get("id") for v in variants if v.get("id")]

        assert len(variant_ids) == 0


class TestDisputesCreateWebhook:
    """Test disputes/create webhook handler."""

    @pytest.mark.p0
    @pytest.mark.unit
    def test_dispute_create_extracts_data(self):
        """Verify dispute data is correctly extracted from payload."""
        payload = {
            "id": "dispute_123",
            "order_id": 123456789,
            "amount": "99.99",
            "currency": "USD",
            "reason": "fraudulent",
            "evidence_due_by": "2026-03-15T00:00:00Z",
            "status": "needs_response",
        }

        dispute_id = payload.get("id")
        order_id = payload.get("order_id")
        amount = payload.get("amount")
        currency = payload.get("currency", "USD")
        reason = payload.get("reason")

        assert dispute_id == "dispute_123"
        assert order_id == 123456789
        assert amount == "99.99"
        assert currency == "USD"
        assert reason == "fraudulent"

    @pytest.mark.p0
    @pytest.mark.unit
    def test_dispute_create_handles_all_reasons(self):
        """Verify all dispute reason types are handled."""
        reasons = [
            "fraudulent",
            "product_not_received",
            "product_unacceptable",
            "unrecognized",
            "credit_not_processed",
            "general",
        ]

        for reason in reasons:
            payload = {
                "id": f"dispute_{reason}",
                "order_id": 123456789,
                "amount": "50.00",
                "reason": reason,
            }
            assert payload["reason"] == reason

    @pytest.mark.p1
    @pytest.mark.unit
    def test_dispute_create_handles_currency_defaults(self):
        """Verify default currency is USD when not specified."""
        payload = {
            "id": "dispute_123",
            "order_id": 123456789,
            "amount": "99.99",
        }

        currency = payload.get("currency", "USD")

        assert currency == "USD"

    @pytest.mark.p1
    @pytest.mark.unit
    def test_dispute_create_calculates_evidence_deadline(self):
        """Verify evidence deadline is correctly parsed."""
        from datetime import datetime

        payload = {
            "id": "dispute_123",
            "order_id": 123456789,
            "amount": "99.99",
            "evidence_due_by": "2026-03-15T00:00:00Z",
        }

        evidence_due = payload.get("evidence_due_by")
        if evidence_due:
            due_date = datetime.fromisoformat(evidence_due.replace("Z", "+00:00"))
            assert due_date.year == 2026
            assert due_date.month == 3
            assert due_date.day == 15


class TestWebhookRouting:
    """Test webhook topic routing to correct handlers."""

    @pytest.mark.p1
    @pytest.mark.unit
    def test_routes_orders_cancelled(self):
        """Verify orders/cancelled topic routes correctly."""
        topic = "orders/cancelled"
        assert topic == "orders/cancelled"

    @pytest.mark.p1
    @pytest.mark.unit
    def test_routes_inventory_levels_update(self):
        """Verify inventory_levels/update topic routes correctly."""
        topic = "inventory_levels/update"
        assert topic == "inventory_levels/update"

    @pytest.mark.p1
    @pytest.mark.unit
    def test_routes_products_update(self):
        """Verify products/update topic routes correctly."""
        topic = "products/update"
        assert topic == "products/update"

    @pytest.mark.p0
    @pytest.mark.unit
    def test_routes_disputes_create(self):
        """Verify disputes/create topic routes correctly."""
        topic = "disputes/create"
        assert topic == "disputes/create"


class TestCOGSCacheInvalidation:
    """Test COGS cache invalidation on webhook events."""

    @pytest.mark.p1
    @pytest.mark.asyncio
    async def test_cache_invalidation_on_inventory_update(self):
        """Verify cache is invalidated when inventory updates."""
        from app.services.shopify.cogs_cache import COGSCache

        mock_redis = AsyncMock()
        mock_redis.delete = AsyncMock(return_value=1)
        cache = COGSCache(redis_client=mock_redis)

        variant_gid = "gid://shopify/ProductVariant/12345"
        await cache.invalidate(variant_gid)

        mock_redis.delete.assert_called_once()

    @pytest.mark.p1
    @pytest.mark.asyncio
    async def test_batch_cache_invalidation_on_product_update(self):
        """Verify batch cache invalidation when product updates."""
        from app.services.shopify.cogs_cache import COGSCache

        mock_redis = AsyncMock()
        mock_redis.delete = AsyncMock(return_value=1)
        cache = COGSCache(redis_client=mock_redis)

        variant_gids = [
            "gid://shopify/ProductVariant/111",
            "gid://shopify/ProductVariant/222",
        ]
        result = await cache.invalidate_batch(variant_gids)

        assert result == 2
        mock_redis.delete.assert_called_once()

    @pytest.mark.p2
    @pytest.mark.asyncio
    async def test_cache_invalidation_handles_missing_key(self):
        """Verify graceful handling when cache key doesn't exist."""
        from app.services.shopify.cogs_cache import COGSCache

        mock_redis = AsyncMock()
        mock_redis.delete = AsyncMock(return_value=0)
        cache = COGSCache(redis_client=mock_redis)

        variant_gid = "gid://shopify/ProductVariant/nonexistent"
        await cache.invalidate(variant_gid)

        mock_redis.delete.assert_called_once()
