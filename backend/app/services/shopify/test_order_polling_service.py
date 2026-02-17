"""Unit tests for OrderPollingService.

Story 4-4 Task 2 & 3: Order polling with distributed locking, order comparison, and processing
"""

from __future__ import annotations

import os
import re
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aioresponses import aioresponses
from sqlalchemy import select

from app.models.order import Order, OrderStatus
from app.models.shopify_integration import ShopifyIntegration
from app.services.shopify.order_polling_service import (
    OrderPollingService,
    PollingResult,
    PollingStatus,
)
from app.services.shopify.admin_client import ShopifyAPIError, ShopifyAuthError


class TestOrderPollingService:
    """Tests for OrderPollingService."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        db = AsyncMock()
        return db

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client."""
        redis = AsyncMock()
        redis.set = AsyncMock(return_value=True)
        redis.delete = AsyncMock(return_value=1)
        redis.get = AsyncMock(return_value=None)
        return redis

    @pytest.fixture
    def polling_service(self, mock_redis):
        """Create polling service instance."""
        return OrderPollingService(redis_client=mock_redis)

    @pytest.fixture
    def mock_shopify_integration(self):
        """Mock Shopify integration."""
        integration = MagicMock(spec=ShopifyIntegration)
        integration.merchant_id = 1
        integration.shop_domain = "test-shop.myshopify.com"
        integration.admin_token_encrypted = "encrypted_token"
        integration.admin_api_verified = True
        return integration

    @pytest.fixture
    def mock_orders_api_response(self):
        """Sample orders response from Shopify Admin API."""
        now = datetime.now(timezone.utc)
        return {
            "orders": [
                {
                    "id": 123456789,
                    "order_number": 1001,
                    "email": "customer@example.com",
                    "financial_status": "paid",
                    "fulfillment_status": "fulfilled",
                    "created_at": (now - timedelta(hours=1)).isoformat(),
                    "updated_at": now.isoformat(),
                    "customer": {
                        "id": 987654321,
                        "email": "customer@example.com",
                    },
                    "line_items": [
                        {
                            "id": 111,
                            "title": "Test Product",
                            "quantity": 1,
                            "price": "29.99",
                        }
                    ],
                    "note_attributes": [{"name": "messenger_psid", "value": "test_psid_123"}],
                    "tracking_numbers": ["TRACK123"],
                    "tracking_urls": ["https://tracking.example.com/TRACK123"],
                },
            ]
        }

    def test_polling_result_initialization(self):
        """Test PollingResult dataclass."""
        result = PollingResult(
            status=PollingStatus.SUCCESS,
            merchant_id=1,
            orders_polled=5,
            orders_created=2,
            orders_updated=1,
            notifications_sent=1,
        )
        assert result.status == PollingStatus.SUCCESS
        assert result.merchant_id == 1
        assert result.orders_polled == 5

    @pytest.mark.asyncio
    async def test_acquire_lock_success(self, polling_service, mock_redis):
        """Test successful lock acquisition."""
        mock_redis.set = AsyncMock(return_value=True)

        acquired = await polling_service.acquire_lock(merchant_id=1)

        assert acquired is True
        mock_redis.set.assert_called_once()
        call_args = mock_redis.set.call_args
        assert "polling_lock:1" in call_args[0][0]
        assert call_args[1]["nx"] is True
        assert call_args[1]["ex"] == 600

    @pytest.mark.asyncio
    async def test_acquire_lock_already_exists(self, polling_service, mock_redis):
        """Test lock acquisition when lock already exists."""
        mock_redis.set = AsyncMock(return_value=None)

        acquired = await polling_service.acquire_lock(merchant_id=1)

        assert acquired is False

    @pytest.mark.asyncio
    async def test_acquire_lock_redis_unavailable(self, polling_service, mock_redis):
        """Test lock acquisition when Redis is unavailable (degraded mode)."""
        mock_redis.set = AsyncMock(side_effect=Exception("Redis connection failed"))

        acquired = await polling_service.acquire_lock(merchant_id=1)

        assert acquired is True  # Degraded mode - proceed without lock

    @pytest.mark.asyncio
    async def test_release_lock(self, polling_service, mock_redis):
        """Test lock release."""
        await polling_service.release_lock(merchant_id=1)

        mock_redis.delete.assert_called_once()
        call_args = mock_redis.delete.call_args
        assert "polling_lock:1" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_filter_orders_within_24_hours(self, polling_service, mock_orders_api_response):
        """Test that only orders <24 hours old are processed."""
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
            {
                "id": 3,
                "created_at": (now - timedelta(hours=12)).isoformat(),
                "updated_at": now.isoformat(),
            },
        ]

        filtered = polling_service.filter_orders_within_24_hours(orders_data)

        assert len(filtered) == 2
        assert filtered[0]["id"] == 1
        assert filtered[1]["id"] == 3

    @pytest.mark.asyncio
    async def test_poll_recent_orders_no_integration(self, polling_service, mock_db):
        """Test polling when merchant has no Shopify integration."""
        mock_db.execute = AsyncMock()
        mock_db.execute.return_value.scalars.return_value.all = AsyncMock(return_value=[])

        with patch.object(polling_service, "_get_shopify_credentials", return_value=None):
            result = await polling_service.poll_recent_orders(merchant_id=1, db=mock_db)

        assert result.status == PollingStatus.SKIPPED_NO_INTEGRATION

    @pytest.mark.asyncio
    async def test_poll_recent_orders_not_verified(
        self, polling_service, mock_db, mock_shopify_integration
    ):
        """Test polling when integration is not verified."""
        mock_shopify_integration.admin_api_verified = False

        with patch.object(polling_service, "_get_shopify_credentials", return_value=None):
            result = await polling_service.poll_recent_orders(merchant_id=1, db=mock_db)

        assert result.status == PollingStatus.SKIPPED_NO_INTEGRATION

    @pytest.mark.asyncio
    async def test_poll_recent_orders_lock_not_acquired(self, polling_service, mock_db, mock_redis):
        """Test polling when lock cannot be acquired (another instance polling)."""
        mock_redis.set = AsyncMock(return_value=None)

        with patch.object(
            polling_service,
            "_get_shopify_credentials",
            return_value={"shop_domain": "test-shop.myshopify.com", "admin_token": "test_token"},
        ):
            result = await polling_service.poll_recent_orders(merchant_id=1, db=mock_db)

        assert result.status == PollingStatus.SKIPPED_LOCK_EXISTS

    @pytest.mark.asyncio
    async def test_poll_recent_orders_success(
        self,
        polling_service,
        mock_db,
        mock_redis,
        mock_shopify_integration,
        mock_orders_api_response,
    ):
        """Test successful polling with new orders."""
        mock_redis.set = AsyncMock(return_value=True)

        with patch.object(
            polling_service,
            "_get_shopify_credentials",
            return_value={"shop_domain": "test-shop.myshopify.com", "admin_token": "test_token"},
        ):
            with patch.object(
                polling_service,
                "_fetch_orders_from_shopify",
                return_value=mock_orders_api_response["orders"],
            ):
                with patch.object(
                    polling_service,
                    "_process_orders",
                    return_value={"created": 1, "updated": 0, "notifications": 1},
                ):
                    result = await polling_service.poll_recent_orders(merchant_id=1, db=mock_db)

        assert result.status == PollingStatus.SUCCESS
        assert result.orders_created == 1
        assert result.notifications_sent == 1

    @pytest.mark.asyncio
    async def test_poll_recent_orders_api_error(
        self,
        polling_service,
        mock_db,
        mock_redis,
        mock_shopify_integration,
    ):
        """Test polling handles API errors gracefully."""
        mock_redis.set = AsyncMock(return_value=True)

        with patch.object(
            polling_service,
            "_get_shopify_credentials",
            return_value={"shop_domain": "test-shop.myshopify.com", "admin_token": "test_token"},
        ):
            with patch.object(
                polling_service,
                "_fetch_orders_from_shopify",
                side_effect=ShopifyAPIError("API error"),
            ):
                result = await polling_service.poll_recent_orders(merchant_id=1, db=mock_db)

        assert result.status == PollingStatus.ERROR_API
        assert result.error_code == 7050

    @pytest.mark.asyncio
    async def test_poll_recent_orders_auth_error(
        self,
        polling_service,
        mock_db,
        mock_redis,
        mock_shopify_integration,
    ):
        """Test polling handles auth errors (marks merchant disconnected)."""
        mock_redis.set = AsyncMock(return_value=True)

        with patch.object(
            polling_service,
            "_get_shopify_credentials",
            return_value={"shop_domain": "test-shop.myshopify.com", "admin_token": "test_token"},
        ):
            with patch.object(
                polling_service,
                "_fetch_orders_from_shopify",
                side_effect=ShopifyAuthError(),
            ):
                result = await polling_service.poll_recent_orders(merchant_id=1, db=mock_db)

        assert result.status == PollingStatus.ERROR_AUTH
        assert result.error_code == 7052

    @pytest.mark.asyncio
    async def test_poll_all_merchants_sequential(self, polling_service, mock_db, mock_redis):
        """Test that multiple merchants are polled sequentially with delay."""
        mock_redis.set = AsyncMock(return_value=True)

        merchant_ids = [1, 2, 3]
        polled_order = []

        async def track_poll(merchant_id, db):
            polled_order.append(merchant_id)
            return PollingResult(
                status=PollingStatus.SUCCESS,
                merchant_id=merchant_id,
                orders_polled=0,
            )

        with patch.object(polling_service, "poll_recent_orders", side_effect=track_poll):
            results = await polling_service.poll_all_merchants(
                merchant_ids=merchant_ids,
                db=mock_db,
                delay_between_merchants=0.01,
            )

        assert len(results) == 3
        assert polled_order == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_poll_all_merchants_continues_on_error(
        self, polling_service, mock_db, mock_redis
    ):
        """Test that polling continues even if one merchant fails."""
        mock_redis.set = AsyncMock(return_value=True)

        merchant_ids = [1, 2, 3]
        call_count = 0

        async def track_poll(merchant_id, db):
            nonlocal call_count
            call_count += 1
            if merchant_id == 2:
                raise Exception("Unexpected error")
            return PollingResult(
                status=PollingStatus.SUCCESS,
                merchant_id=merchant_id,
                orders_polled=0,
            )

        with patch.object(polling_service, "poll_recent_orders", side_effect=track_poll):
            results = await polling_service.poll_all_merchants(
                merchant_ids=merchant_ids,
                db=mock_db,
                delay_between_merchants=0,
            )

        assert call_count == 3
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_compare_and_identify_updates_new_order(self, polling_service, mock_db):
        """Test identifying new orders that don't exist locally."""
        now = datetime.now(timezone.utc)
        shopify_orders = [
            {
                "id": 999,
                "updated_at": now.isoformat(),
                "created_at": now.isoformat(),
            }
        ]

        mock_db.execute = AsyncMock()
        mock_db.execute.return_value.scalars.return_value.first = AsyncMock(return_value=None)

        with patch.object(polling_service, "_get_existing_order", return_value=None):
            updates = await polling_service.compare_and_identify_updates(
                shopify_orders=shopify_orders,
                db=mock_db,
            )

        assert len(updates["new_orders"]) == 1
        assert len(updates["updated_orders"]) == 0

    @pytest.mark.asyncio
    async def test_compare_and_identify_updates_newer_timestamp(self, polling_service, mock_db):
        """Test identifying orders with newer Shopify timestamps."""
        now = datetime.utcnow()
        older_ts = now - timedelta(hours=1)
        newer_ts = now

        shopify_orders = [
            {
                "id": 123,
                "updated_at": newer_ts.replace(tzinfo=timezone.utc).isoformat(),
                "created_at": older_ts.replace(tzinfo=timezone.utc).isoformat(),
            }
        ]

        existing_order = MagicMock(spec=Order)
        existing_order.shopify_order_id = "gid://shopify/Order/123"
        existing_order.shopify_updated_at = older_ts
        existing_order.fulfillment_status = None

        with patch.object(polling_service, "_get_existing_order", return_value=existing_order):
            updates = await polling_service.compare_and_identify_updates(
                shopify_orders=shopify_orders,
                db=mock_db,
            )

        assert len(updates["new_orders"]) == 0
        assert len(updates["updated_orders"]) == 1

    @pytest.mark.asyncio
    async def test_compare_and_identify_updates_older_timestamp_skip(
        self, polling_service, mock_db
    ):
        """Test skipping orders with older timestamps (out-of-order)."""
        now = datetime.utcnow()
        older_ts = now - timedelta(hours=1)
        newer_ts = now

        shopify_orders = [
            {
                "id": 123,
                "updated_at": older_ts.replace(tzinfo=timezone.utc).isoformat(),
                "created_at": older_ts.replace(tzinfo=timezone.utc).isoformat(),
            }
        ]

        existing_order = MagicMock(spec=Order)
        existing_order.shopify_order_id = "gid://shopify/Order/123"
        existing_order.shopify_updated_at = newer_ts
        existing_order.fulfillment_status = None

        with patch.object(polling_service, "_get_existing_order", return_value=existing_order):
            updates = await polling_service.compare_and_identify_updates(
                shopify_orders=shopify_orders,
                db=mock_db,
            )

        assert len(updates["new_orders"]) == 0
        assert len(updates["updated_orders"]) == 0

    @pytest.mark.asyncio
    async def test_detect_newly_fulfilled_order(self, polling_service):
        """Test detecting orders that changed from not fulfilled to fulfilled."""
        existing_order = MagicMock(spec=Order)
        existing_order.fulfillment_status = None

        shopify_order = {
            "fulfillment_status": "fulfilled",
            "tracking_numbers": ["TRACK123"],
        }

        is_newly_fulfilled = polling_service.is_newly_fulfilled(existing_order, shopify_order)

        assert is_newly_fulfilled is True

    @pytest.mark.asyncio
    async def test_detect_not_newly_fulfilled_already_fulfilled(self, polling_service):
        """Test that already fulfilled orders are not detected as newly fulfilled."""
        existing_order = MagicMock(spec=Order)
        existing_order.fulfillment_status = "fulfilled"

        shopify_order = {
            "fulfillment_status": "fulfilled",
            "tracking_numbers": ["TRACK123"],
        }

        is_newly_fulfilled = polling_service.is_newly_fulfilled(existing_order, shopify_order)

        assert is_newly_fulfilled is False

    def test_get_health_status(self, polling_service):
        """Test health status retrieval."""
        from app.services.shopify.order_polling_service import MerchantPollingStatus

        polling_service._last_poll_timestamp = datetime.now(timezone.utc)
        polling_service._total_orders_synced = 42
        polling_service._errors_last_hour = 2
        polling_service._merchant_status = {
            1: MerchantPollingStatus(
                last_poll=datetime.now(timezone.utc),
                status="healthy",
            ),
        }

        health = polling_service.get_health_status()

        assert health["scheduler_running"] is False
        assert health["total_orders_synced"] == 42
        assert health["errors_last_hour"] == 2
        assert len(health["merchant_status"]) == 1
