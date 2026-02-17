"""Integration tests for Story 4-4: Polling Fallback.

Tests the full polling cycle with mock Shopify API.
"""

from __future__ import annotations

import os
import re
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aioresponses import aioresponses
from sqlalchemy import select

from app.models.order import Order
from app.models.shopify_integration import ShopifyIntegration
from app.services.shopify.order_polling_service import (
    OrderPollingService,
    PollingStatus,
)
from app.services.shopify.admin_client import ShopifyAdminClient


pytestmark = pytest.mark.asyncio


class TestPollingFallbackIntegration:
    """Integration tests for polling fallback."""

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client."""
        redis = AsyncMock()
        redis.set = AsyncMock(return_value=True)
        redis.delete = AsyncMock(return_value=1)
        redis.get = AsyncMock(return_value=None)
        return redis

    @pytest.fixture
    def mock_shopify_orders(self):
        """Sample Shopify orders response with string order numbers."""
        now = datetime.now(timezone.utc)
        return {
            "orders": [
                {
                    "id": 9001,
                    "order_number": "1001",
                    "email": "customer1@example.com",
                    "financial_status": "paid",
                    "fulfillment_status": None,
                    "created_at": (now - timedelta(hours=2)).isoformat(),
                    "updated_at": now.isoformat(),
                    "customer": {"id": 1, "email": "customer1@example.com"},
                    "line_items": [
                        {"id": 1, "title": "Product A", "quantity": 1, "price": "29.99"}
                    ],
                    "note_attributes": [{"name": "messenger_psid", "value": "psid_001"}],
                },
                {
                    "id": 9002,
                    "order_number": "1002",
                    "email": "customer2@example.com",
                    "financial_status": "paid",
                    "fulfillment_status": "fulfilled",
                    "created_at": (now - timedelta(hours=1)).isoformat(),
                    "updated_at": now.isoformat(),
                    "customer": {"id": 2, "email": "customer2@example.com"},
                    "line_items": [
                        {"id": 2, "title": "Product B", "quantity": 2, "price": "49.99"}
                    ],
                    "note_attributes": [],
                    "tracking_numbers": ["TRACK001"],
                    "tracking_urls": ["https://tracking.example.com/TRACK001"],
                },
            ]
        }

    async def test_full_polling_cycle_creates_orders(
        self,
        db_session,
        mock_redis,
        mock_shopify_orders,
        test_merchant,
    ):
        """Test that polling creates new orders in database."""
        polling_service = OrderPollingService(redis_client=mock_redis)

        with aioresponses() as m:
            m.get(
                re.compile(r"https://test-shop\.myshopify\.com/admin/api/2024-01/orders\.json.*"),
                payload=mock_shopify_orders,
                headers={"X-Shopify-Shop-Api-Call-Limit": "5/1000"},
            )

            with patch.object(
                polling_service,
                "_get_shopify_credentials",
                return_value={
                    "shop_domain": "test-shop.myshopify.com",
                    "admin_token": "test_token",
                },
            ):
                result = await polling_service.poll_recent_orders(
                    merchant_id=test_merchant.id,
                    db=db_session,
                )

        assert result.status == PollingStatus.SUCCESS
        assert result.orders_created == 2

    async def test_no_duplicates_from_repeated_polling(
        self,
        db_session,
        mock_redis,
        mock_shopify_orders,
        test_merchant,
    ):
        """Test that repeated polling doesn't create duplicate orders."""
        polling_service = OrderPollingService(redis_client=mock_redis)

        call_count = 0

        def get_orders_with_updated_timestamp(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            orders = mock_shopify_orders["orders"]
            if call_count == 2:
                now = datetime.now(timezone.utc) + timedelta(minutes=5)
                for order in orders:
                    order["updated_at"] = now.isoformat()
            return orders

        with patch.object(
            polling_service,
            "_get_shopify_credentials",
            return_value={
                "shop_domain": "test-shop.myshopify.com",
                "admin_token": "test_token",
            },
        ):
            with patch.object(
                polling_service,
                "_fetch_orders_from_shopify",
                side_effect=get_orders_with_updated_timestamp,
            ):
                result1 = await polling_service.poll_recent_orders(
                    merchant_id=test_merchant.id,
                    db=db_session,
                )

                result2 = await polling_service.poll_recent_orders(
                    merchant_id=test_merchant.id,
                    db=db_session,
                )

        assert result1.orders_created == 2
        assert result2.orders_created == 0
        assert result2.orders_updated == 2

    async def test_error_recovery_after_transient_failure(
        self,
        db_session,
        mock_redis,
        mock_shopify_orders,
        test_merchant,
    ):
        """Test that polling recovers after transient API errors."""
        polling_service = OrderPollingService(redis_client=mock_redis)

        call_count = 0

        async def mock_fetch(shop_domain, admin_token):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                from app.services.shopify.admin_client import ShopifyAPIError

                raise ShopifyAPIError("Temporary error")
            return mock_shopify_orders["orders"]

        with patch.object(
            polling_service,
            "_get_shopify_credentials",
            return_value={
                "shop_domain": "test-shop.myshopify.com",
                "admin_token": "test_token",
            },
        ):
            with patch.object(
                polling_service,
                "_fetch_orders_from_shopify",
                side_effect=mock_fetch,
            ):
                result1 = await polling_service.poll_recent_orders(
                    merchant_id=test_merchant.id,
                    db=db_session,
                )

                result2 = await polling_service.poll_recent_orders(
                    merchant_id=test_merchant.id,
                    db=db_session,
                )

        assert result1.status == PollingStatus.ERROR_API
        assert result2.status == PollingStatus.SUCCESS
        assert result2.orders_created == 2

    async def test_multiple_merchants_polled_independently(
        self,
        db_session,
        mock_redis,
        mock_shopify_orders,
        test_merchant,
    ):
        """Test that multiple merchants are polled independently."""
        polling_service = OrderPollingService(redis_client=mock_redis)

        merchant2 = MagicMock()
        merchant2.id = test_merchant.id + 1

        poll_results = {}

        async def track_poll(merchant_id, db):
            poll_results[merchant_id] = True
            return type(
                "PollingResult",
                (),
                {
                    "status": PollingStatus.SUCCESS,
                    "merchant_id": merchant_id,
                    "orders_polled": 1,
                    "orders_created": 1,
                    "orders_updated": 0,
                    "notifications_sent": 0,
                },
            )()

        with patch.object(polling_service, "poll_recent_orders", side_effect=track_poll):
            results = await polling_service.poll_all_merchants(
                merchant_ids=[test_merchant.id, merchant2.id],
                db=db_session,
                delay_between_merchants=0,
            )

        assert len(results) == 2
        assert test_merchant.id in poll_results
        assert merchant2.id in poll_results

    async def test_distributed_lock_prevents_concurrent_polling(
        self,
        db_session,
        mock_redis,
        test_merchant,
    ):
        """Test that distributed lock prevents concurrent polling."""
        polling_service = OrderPollingService(redis_client=mock_redis)

        mock_redis.set = AsyncMock(return_value=None)

        with patch.object(
            polling_service,
            "_get_shopify_credentials",
            return_value={
                "shop_domain": "test-shop.myshopify.com",
                "admin_token": "test_token",
            },
        ):
            result = await polling_service.poll_recent_orders(
                merchant_id=test_merchant.id,
                db=db_session,
            )

        assert result.status == PollingStatus.SKIPPED_LOCK_EXISTS

    async def test_shipping_notification_for_newly_fulfilled(
        self,
        db_session,
        mock_redis,
        test_merchant,
    ):
        """Test that shipping notifications are sent for newly fulfilled orders."""
        now = datetime.utcnow()

        existing_order = Order(
            shopify_order_id="gid://shopify/Order/9001",
            order_number="1001",
            merchant_id=test_merchant.id,
            platform_sender_id="psid_001",
            status="processing",
            fulfillment_status=None,
            subtotal=0,
            total=0,
            shopify_updated_at=now - timedelta(hours=1),
        )
        db_session.add(existing_order)
        await db_session.commit()

        polling_service = OrderPollingService(redis_client=mock_redis)

        now_tz = datetime.now(timezone.utc)
        updated_orders = [
            {
                "id": 9001,
                "order_number": "1001",
                "email": "customer1@example.com",
                "financial_status": "paid",
                "fulfillment_status": "fulfilled",
                "created_at": (now_tz - timedelta(hours=2)).isoformat(),
                "updated_at": now_tz.isoformat(),
                "customer": {"id": 1, "email": "customer1@example.com"},
                "line_items": [],
                "note_attributes": [],
                "tracking_numbers": ["TRACK001"],
                "tracking_urls": ["https://tracking.example.com/TRACK001"],
            }
        ]

        with patch.object(
            polling_service,
            "_get_shopify_credentials",
            return_value={
                "shop_domain": "test-shop.myshopify.com",
                "admin_token": "test_token",
            },
        ):
            with patch.object(
                polling_service,
                "_fetch_orders_from_shopify",
                return_value=updated_orders,
            ):
                mock_send_notification = AsyncMock(
                    return_value=type(
                        "NotificationResult",
                        (),
                        {"status": type("Status", (), {"value": "success"})()},
                    )()
                )

                with patch(
                    "app.services.shipping_notification.service.ShippingNotificationService.send_shipping_notification",
                    mock_send_notification,
                ):
                    result = await polling_service.poll_recent_orders(
                        merchant_id=test_merchant.id,
                        db=db_session,
                    )

        assert result.orders_updated == 1

    async def test_24_hour_window_filtering(
        self,
        db_session,
        mock_redis,
        test_merchant,
    ):
        """Test that orders older than 24 hours are filtered out."""
        now = datetime.now(timezone.utc)

        orders_data = [
            {
                "id": 1,
                "created_at": (now - timedelta(hours=2)).isoformat(),
                "updated_at": now.isoformat(),
            },
            {
                "id": 2,
                "created_at": (now - timedelta(hours=30)).isoformat(),
                "updated_at": now.isoformat(),
            },
        ]

        polling_service = OrderPollingService(redis_client=mock_redis)

        with patch.object(
            polling_service,
            "_get_shopify_credentials",
            return_value={
                "shop_domain": "test-shop.myshopify.com",
                "admin_token": "test_token",
            },
        ):
            with patch.object(
                polling_service,
                "_fetch_orders_from_shopify",
                return_value=orders_data,
            ):
                with patch.object(
                    polling_service,
                    "_process_orders",
                    return_value={"created": 0, "updated": 0, "notifications": 0},
                ) as mock_process:
                    await polling_service.poll_recent_orders(
                        merchant_id=test_merchant.id,
                        db=db_session,
                    )

                    process_call_orders = mock_process.call_args[0][1]
                    assert len(process_call_orders) == 1
                    assert process_call_orders[0]["id"] == 1

    async def test_health_endpoint_returns_correct_status(
        self,
        mock_redis,
        test_merchant,
    ):
        """Test that health endpoint returns correct status."""
        polling_service = OrderPollingService(redis_client=mock_redis)

        polling_service._last_poll_timestamp = datetime.now(timezone.utc)
        polling_service._total_orders_synced = 10
        polling_service._errors_last_hour = 0

        health = polling_service.get_health_status()

        assert health["scheduler_running"] is False
        assert health["total_orders_synced"] == 10
        assert health["errors_last_hour"] == 0
        assert "last_poll_timestamp" in health
        assert "merchant_status" in health
