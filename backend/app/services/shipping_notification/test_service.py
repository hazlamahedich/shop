"""Unit tests for shipping notification service.

Story 4-3: Shipping Notifications

Tests cover:
- Notification message formatting
- Rate limiting
- Tracking link formatting
- Consent checking
- Idempotency
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.errors import ErrorCode
from app.models.order import Order
from app.services.shipping_notification import (
    ConsentChecker,
    NotificationResult,
    NotificationStatus,
    ShippingNotificationService,
    ShippingRateLimiter,
    TrackingFormatter,
)
from app.services.shipping_notification.rate_limiter import RateLimitResult


class TestTrackingFormatter:
    """Tests for tracking link formatting (AC5)."""

    def test_detect_carrier_ups(self):
        result = TrackingFormatter.detect_carrier("1Z999AA10123456784")
        assert result is not None
        assert result.name == "UPS"
        assert "ups.com" in result.tracking_url

    def test_detect_carrier_fedex_12digit(self):
        result = TrackingFormatter.detect_carrier("123456789012")
        assert result is not None
        assert result.name == "FedEx"
        assert "fedex.com" in result.tracking_url

    def test_detect_carrier_usps(self):
        result = TrackingFormatter.detect_carrier("9400111899223334445566")
        assert result is not None
        assert result.name == "USPS"
        assert "usps.com" in result.tracking_url

    def test_detect_carrier_dhl(self):
        result = TrackingFormatter.detect_carrier("1234567890")
        assert result is not None
        assert result.name == "DHL"
        assert "dhl.com" in result.tracking_url

    def test_detect_carrier_canada_post(self):
        result = TrackingFormatter.detect_carrier("0012345678901234")
        assert result is not None
        assert result.name == "CanadaPost"

    def test_detect_carrier_royal_mail(self):
        result = TrackingFormatter.detect_carrier("AB123456789GB")
        assert result is not None
        assert result.name == "RoyalMail"

    def test_detect_carrier_unknown(self):
        result = TrackingFormatter.detect_carrier("UNKNOWN123")
        assert result is None

    def test_format_tracking_message_with_url(self):
        message = TrackingFormatter.format_tracking_message(
            order_number="1001",
            tracking_number="1Z999AA10123456784",
            tracking_url="https://custom.tracking/url",
        )
        assert "#1001" in message
        assert "https://custom.tracking/url" in message
        assert "\U0001f4e6" in message

    def test_format_tracking_message_without_url_detects_carrier(self):
        message = TrackingFormatter.format_tracking_message(
            order_number="1001",
            tracking_number="1Z999AA10123456784",
            tracking_url=None,
        )
        assert "#1001" in message
        assert "ups.com" in message

    def test_format_tracking_message_no_tracking_info(self):
        message = TrackingFormatter.format_tracking_message(
            order_number="1001",
            tracking_number=None,
            tracking_url=None,
        )
        assert "#1001" in message
        assert "Tracking" not in message or "tracking" not in message.lower()

    def test_get_tracking_link_prefers_provided_url(self):
        link = TrackingFormatter.get_tracking_link(
            tracking_number="1Z999AA10123456784",
            tracking_url="https://custom.url",
        )
        assert link == "https://custom.url"

    def test_get_tracking_link_detects_from_number(self):
        link = TrackingFormatter.get_tracking_link(
            tracking_number="1Z999AA10123456784",
            tracking_url=None,
        )
        assert "ups.com" in link


class TestShippingRateLimiter:
    """Tests for rate limiting (AC4) and idempotency (AC7)."""

    @pytest.mark.asyncio
    async def test_rate_limit_allows_first_notification(self):
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        mock_redis.ping.return_value = True

        limiter = ShippingRateLimiter(redis_client=mock_redis)
        result = await limiter.check_rate_limit("test_psid")

        assert result.allowed is True

    @pytest.mark.asyncio
    async def test_rate_limit_blocks_second_notification_same_day(self):
        mock_redis = AsyncMock()
        mock_redis.get.return_value = "1"
        mock_redis.ping.return_value = True

        limiter = ShippingRateLimiter(redis_client=mock_redis)
        result = await limiter.check_rate_limit("test_psid")

        assert result.allowed is False
        assert result.reason == "daily_limit_reached"

    @pytest.mark.asyncio
    async def test_rate_limit_fail_open_when_redis_unavailable(self):
        limiter = ShippingRateLimiter(redis_client=None)
        limiter._redis_available = False

        result = await limiter.check_rate_limit("test_psid")

        assert result.allowed is True
        assert "redis" in result.reason or "unavailable" in result.reason

    @pytest.mark.asyncio
    async def test_idempotency_detects_duplicate(self):
        mock_redis = AsyncMock()
        mock_redis.exists.return_value = 1
        mock_redis.ping.return_value = True

        limiter = ShippingRateLimiter(redis_client=mock_redis)
        is_duplicate = await limiter.check_idempotency("order_123", "fulfillment_456")

        assert is_duplicate is True

    @pytest.mark.asyncio
    async def test_idempotency_allows_new_webhook(self):
        mock_redis = AsyncMock()
        mock_redis.exists.return_value = 0
        mock_redis.ping.return_value = True

        limiter = ShippingRateLimiter(redis_client=mock_redis)
        is_duplicate = await limiter.check_idempotency("order_123", "fulfillment_456")

        assert is_duplicate is False


class TestConsentChecker:
    """Tests for consent checking (AC6)."""

    @pytest.mark.asyncio
    async def test_consent_check_allows_when_opted_in(self):
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = {"notification_consent": True}
        mock_db.execute.return_value = mock_result

        has_consent = await ConsentChecker.check_notification_consent("test_psid", mock_db)

        assert has_consent is True

    @pytest.mark.asyncio
    async def test_consent_check_blocks_when_opted_out(self):
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = {"notification_consent": False}
        mock_db.execute.return_value = mock_result

        has_consent = await ConsentChecker.check_notification_consent("test_psid", mock_db)

        assert has_consent is False

    @pytest.mark.asyncio
    async def test_consent_check_defaults_to_true_when_no_conversation(self):
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        has_consent = await ConsentChecker.check_notification_consent("test_psid", mock_db)

        assert has_consent is True

    @pytest.mark.asyncio
    async def test_consent_check_defaults_to_true_when_field_not_set(self):
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = {}
        mock_db.execute.return_value = mock_result

        has_consent = await ConsentChecker.check_notification_consent("test_psid", mock_db)

        assert has_consent is True


class TestShippingNotificationService:
    """Tests for the main notification service."""

    def _create_mock_order(
        self,
        order_number="1001",
        psid="test_psid",
        tracking_number="1Z999AA10123456784",
        tracking_url=None,
        shopify_order_id="gid://shopify/Order/123",
        created_at=None,
    ):
        order = MagicMock(spec=Order)
        order.order_number = order_number
        order.platform_sender_id = psid
        order.tracking_number = tracking_number
        order.tracking_url = tracking_url
        order.shopify_order_id = shopify_order_id
        order.created_at = created_at or datetime.utcnow()
        return order

    @pytest.mark.asyncio
    async def test_send_notification_formats_correct_message(self):
        mock_send_service = AsyncMock()
        mock_send_service.send_message.return_value = {"message_id": "mid.123"}

        mock_rate_limiter = AsyncMock()
        mock_rate_limiter.check_rate_limit.return_value = RateLimitResult(allowed=True)
        mock_rate_limiter.check_idempotency.return_value = False

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = {"notification_consent": True}
        mock_db.execute.return_value = mock_result

        service = ShippingNotificationService(
            send_service=mock_send_service,
            rate_limiter=mock_rate_limiter,
        )

        order = self._create_mock_order()
        result = await service.send_shipping_notification(order, mock_db)

        assert result.status == NotificationStatus.SUCCESS
        assert result.psid == "test_psid"
        assert result.order_number == "1001"

        call_args = mock_send_service.send_message.call_args
        assert call_args[1]["tag"] == "order_update"
        message_payload = call_args[1]["message_payload"]
        assert "#1001" in message_payload["text"]

    @pytest.mark.asyncio
    async def test_send_notification_uses_order_update_tag(self):
        mock_send_service = AsyncMock()
        mock_send_service.send_message.return_value = {"message_id": "mid.123"}

        mock_rate_limiter = AsyncMock()
        mock_rate_limiter.check_rate_limit.return_value = RateLimitResult(allowed=True)
        mock_rate_limiter.check_idempotency.return_value = False

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = {"notification_consent": True}
        mock_db.execute.return_value = mock_result

        service = ShippingNotificationService(
            send_service=mock_send_service,
            rate_limiter=mock_rate_limiter,
        )

        order = self._create_mock_order()
        await service.send_shipping_notification(order, mock_db)

        call_args = mock_send_service.send_message.call_args
        assert call_args[1]["tag"] == "order_update"

    @pytest.mark.asyncio
    async def test_send_notification_handles_missing_tracking_url(self):
        mock_send_service = AsyncMock()
        mock_send_service.send_message.return_value = {"message_id": "mid.123"}

        mock_rate_limiter = AsyncMock()
        mock_rate_limiter.check_rate_limit.return_value = RateLimitResult(allowed=True)
        mock_rate_limiter.check_idempotency.return_value = False

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = {"notification_consent": True}
        mock_db.execute.return_value = mock_result

        service = ShippingNotificationService(
            send_service=mock_send_service,
            rate_limiter=mock_rate_limiter,
        )

        order = self._create_mock_order(tracking_url=None, tracking_number="1Z999AA10123456784")
        result = await service.send_shipping_notification(order, mock_db)

        assert result.status == NotificationStatus.SUCCESS
        call_args = mock_send_service.send_message.call_args
        assert "ups.com" in call_args[1]["message_payload"]["text"]

    @pytest.mark.asyncio
    async def test_rate_limiter_blocks_second_notification_same_day(self):
        mock_send_service = AsyncMock()

        mock_rate_limiter = AsyncMock()
        mock_rate_limiter.check_rate_limit.return_value = RateLimitResult(
            allowed=False, reason="daily_limit_reached"
        )
        mock_rate_limiter.check_idempotency.return_value = False

        mock_db = AsyncMock()

        service = ShippingNotificationService(
            send_service=mock_send_service,
            rate_limiter=mock_rate_limiter,
        )

        order = self._create_mock_order()
        result = await service.send_shipping_notification(order, mock_db)

        assert result.status == NotificationStatus.SKIPPED_RATE_LIMITED
        assert result.error_code == ErrorCode.SHIPPING_RATE_LIMITED
        mock_send_service.send_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_consent_check_skips_notification_when_opted_out(self):
        mock_send_service = AsyncMock()

        mock_rate_limiter = AsyncMock()
        mock_rate_limiter.check_rate_limit.return_value = RateLimitResult(allowed=True)
        mock_rate_limiter.check_idempotency.return_value = False

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = {"notification_consent": False}
        mock_db.execute.return_value = mock_result

        service = ShippingNotificationService(
            send_service=mock_send_service,
            rate_limiter=mock_rate_limiter,
        )

        order = self._create_mock_order()
        result = await service.send_shipping_notification(order, mock_db)

        assert result.status == NotificationStatus.SKIPPED_NO_CONSENT
        assert result.error_code == ErrorCode.SHIPPING_CONSENT_DISABLED

    @pytest.mark.asyncio
    async def test_idempotency_skips_duplicate_webhook(self):
        mock_send_service = AsyncMock()

        mock_rate_limiter = AsyncMock()
        mock_rate_limiter.check_rate_limit.return_value = RateLimitResult(allowed=True)
        mock_rate_limiter.check_idempotency.return_value = True

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = {"notification_consent": True}
        mock_db.execute.return_value = mock_result

        service = ShippingNotificationService(
            send_service=mock_send_service,
            rate_limiter=mock_rate_limiter,
        )

        order = self._create_mock_order()
        result = await service.send_shipping_notification(
            order, mock_db, fulfillment_id="fulfillment_456"
        )

        assert result.status == NotificationStatus.SKIPPED_DUPLICATE
        assert result.error_code == ErrorCode.SHIPPING_DUPLICATE_WEBHOOK

    @pytest.mark.asyncio
    async def test_old_order_age_check(self):
        mock_send_service = AsyncMock()
        mock_send_service.send_message.return_value = {"message_id": "mid.123"}

        mock_rate_limiter = AsyncMock()
        mock_rate_limiter.check_rate_limit.return_value = RateLimitResult(allowed=True)
        mock_rate_limiter.check_idempotency.return_value = False

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = {"notification_consent": True}
        mock_db.execute.return_value = mock_result

        service = ShippingNotificationService(
            send_service=mock_send_service,
            rate_limiter=mock_rate_limiter,
        )

        old_order = self._create_mock_order(created_at=datetime.utcnow() - timedelta(hours=48))
        result = await service.send_shipping_notification(old_order, mock_db)

        assert result.status == NotificationStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_old_order_sends_without_order_update_tag(self):
        mock_send_service = AsyncMock()
        mock_send_service.send_message.return_value = {"message_id": "mid.123"}

        mock_rate_limiter = AsyncMock()
        mock_rate_limiter.check_rate_limit.return_value = RateLimitResult(allowed=True)
        mock_rate_limiter.check_idempotency.return_value = False

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = {"notification_consent": True}
        mock_db.execute.return_value = mock_result

        service = ShippingNotificationService(
            send_service=mock_send_service,
            rate_limiter=mock_rate_limiter,
        )

        old_order = self._create_mock_order(created_at=datetime.utcnow() - timedelta(hours=48))
        await service.send_shipping_notification(old_order, mock_db)

        call_args = mock_send_service.send_message.call_args
        assert call_args[1]["tag"] is None

    @pytest.mark.asyncio
    async def test_no_tracking_info_skips_notification(self):
        mock_send_service = AsyncMock()

        mock_rate_limiter = AsyncMock()
        mock_rate_limiter.check_rate_limit.return_value = RateLimitResult(allowed=True)
        mock_rate_limiter.check_idempotency.return_value = False

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = {"notification_consent": True}
        mock_db.execute.return_value = mock_result

        service = ShippingNotificationService(
            send_service=mock_send_service,
            rate_limiter=mock_rate_limiter,
        )

        order = self._create_mock_order(tracking_number=None)
        result = await service.send_shipping_notification(order, mock_db)

        assert result.status == NotificationStatus.SKIPPED_NO_TRACKING
        assert result.error_code == ErrorCode.SHIPPING_NO_TRACKING_INFO
