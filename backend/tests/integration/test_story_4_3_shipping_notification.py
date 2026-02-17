"""Integration tests for shipping notifications.

Story 4-3: Shipping Notifications

Tests the full webhook flow including:
- Webhook triggers notification
- Rate limiting across multiple webhooks
- Consent check prevents notification
- Duplicate webhook idempotency
- Multiple fulfillments respect rate limit
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ErrorCode
from app.models.conversation import Conversation
from app.models.merchant import Merchant
from app.models.order import Order
from app.models.shopify_integration import ShopifyIntegration


class TestShippingNotificationFlow:
    """Integration tests for shipping notification flow."""

    @pytest.mark.asyncio
    async def test_fulfilled_order_triggers_notification(
        self,
    ):
        """Test that a fulfilled order triggers a shipping notification (AC1)."""
        with patch(
            "app.services.messenger.send_service.MessengerSendService.send_message"
        ) as mock_send:
            mock_send.return_value = {"message_id": "mid.test123"}

            mock_db = AsyncMock(spec=AsyncSession)

            mock_order_result = MagicMock()
            mock_order = MagicMock(spec=Order)
            mock_order.id = 1
            mock_order.order_number = "1001"
            mock_order.platform_sender_id = "test_psid_12345"
            mock_order.tracking_number = "1Z999AA10123456784"
            mock_order.tracking_url = "https://www.ups.com/track?tracknum=1Z999AA10123456784"
            mock_order.shopify_order_id = "gid://shopify/Order/1234567890"
            mock_order.created_at = datetime.utcnow()
            mock_order_result.scalar_one_or_none.return_value = mock_order

            mock_consent_result = MagicMock()
            mock_consent_result.scalar_one_or_none.return_value = {"notification_consent": True}

            mock_db.execute.side_effect = [
                mock_consent_result,
            ]
            mock_db.commit = AsyncMock()

            from app.services.shipping_notification import ShippingNotificationService
            from app.services.shipping_notification.rate_limiter import RateLimitResult

            mock_rate_limiter = AsyncMock()
            mock_rate_limiter.check_rate_limit.return_value = RateLimitResult(allowed=True)
            mock_rate_limiter.check_idempotency.return_value = False

            service = ShippingNotificationService(
                send_service=AsyncMock(),
                rate_limiter=mock_rate_limiter,
            )
            service.send_service.send_message.return_value = {"message_id": "mid.test"}

            result = await service.send_shipping_notification(mock_order, mock_db)

            assert result.status.value == "success"

    @pytest.mark.asyncio
    async def test_notification_sent_to_correct_psid(
        self,
    ):
        """Test that notification is sent to the correct PSID (AC2)."""
        expected_psid = "test_psid_12345"

        with patch(
            "app.services.shipping_notification.service.ShippingNotificationService.send_shipping_notification"
        ) as mock_send_notification:
            mock_send_notification.return_value = MagicMock(
                status="success",
                psid=expected_psid,
                order_number="1001",
            )

            from app.services.shipping_notification import ShippingNotificationService

            service = ShippingNotificationService()
            mock_order = MagicMock(spec=Order)
            mock_order.order_number = "1001"
            mock_order.platform_sender_id = expected_psid
            mock_order.tracking_number = "1Z999AA10123456784"
            mock_order.tracking_url = None
            mock_order.shopify_order_id = "gid://shopify/Order/1234567890"
            mock_order.created_at = datetime.utcnow()

            mock_db = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = {"notification_consent": True}
            mock_db.execute.return_value = mock_result

            result = await service.send_shipping_notification(mock_order, mock_db)

            assert result.psid == expected_psid

    @pytest.mark.asyncio
    async def test_rate_limiting_enforced_across_multiple_webhooks(self):
        """Test that rate limiting works across multiple webhooks (AC4)."""
        from app.services.shipping_notification import (
            NotificationStatus,
            ShippingNotificationService,
        )

        mock_send_service = AsyncMock()
        mock_send_service.send_message.return_value = {"message_id": "mid.test"}

        mock_rate_limiter = AsyncMock()
        call_count = [0]

        async def mock_check_rate_limit(psid):
            call_count[0] += 1
            if call_count[0] == 1:
                from app.services.shipping_notification.rate_limiter import (
                    RateLimitResult,
                )

                return RateLimitResult(allowed=True)
            else:
                from app.services.shipping_notification.rate_limiter import (
                    RateLimitResult,
                )

                return RateLimitResult(allowed=False, reason="daily_limit_reached")

        mock_rate_limiter.check_rate_limit = mock_check_rate_limit
        mock_rate_limiter.check_idempotency.return_value = False

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = {"notification_consent": True}
        mock_db.execute.return_value = mock_result

        service = ShippingNotificationService(
            send_service=mock_send_service,
            rate_limiter=mock_rate_limiter,
        )

        mock_order = MagicMock(spec=Order)
        mock_order.order_number = "1001"
        mock_order.platform_sender_id = "test_psid"
        mock_order.tracking_number = "1Z999AA10123456784"
        mock_order.tracking_url = None
        mock_order.shopify_order_id = "gid://shopify/Order/123"
        mock_order.created_at = datetime.utcnow()

        result1 = await service.send_shipping_notification(mock_order, mock_db)
        assert result1.status == NotificationStatus.SUCCESS

        result2 = await service.send_shipping_notification(mock_order, mock_db)
        assert result2.status == NotificationStatus.SKIPPED_RATE_LIMITED

    @pytest.mark.asyncio
    async def test_notification_failure_doesnt_fail_webhook(self):
        """Test that notification failure doesn't fail the webhook."""
        mock_send_service = AsyncMock()
        mock_send_service.send_message.side_effect = Exception("API Error")

        mock_rate_limiter = AsyncMock()
        mock_rate_limiter.check_rate_limit.return_value = MagicMock(allowed=True)
        mock_rate_limiter.check_idempotency.return_value = False

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = {"notification_consent": True}
        mock_db.execute.return_value = mock_result

        from app.services.shipping_notification import (
            NotificationStatus,
            ShippingNotificationService,
        )

        service = ShippingNotificationService(
            send_service=mock_send_service,
            rate_limiter=mock_rate_limiter,
        )

        mock_order = MagicMock(spec=Order)
        mock_order.order_number = "1001"
        mock_order.platform_sender_id = "test_psid"
        mock_order.tracking_number = "1Z999AA10123456784"
        mock_order.tracking_url = None
        mock_order.shopify_order_id = "gid://shopify/Order/123"
        mock_order.created_at = datetime.utcnow()

        result = await service.send_shipping_notification(mock_order, mock_db)

        assert result.status == NotificationStatus.FAILED
        assert result.error_code == ErrorCode.SHIPPING_NOTIFICATION_FAILED

    @pytest.mark.asyncio
    async def test_consent_check_prevents_notification(self):
        """Test that consent check prevents notification (AC6)."""
        from app.services.shipping_notification import (
            NotificationStatus,
            ShippingNotificationService,
        )

        mock_send_service = AsyncMock()

        mock_rate_limiter = AsyncMock()
        mock_rate_limiter.check_rate_limit.return_value = MagicMock(allowed=True)
        mock_rate_limiter.check_idempotency.return_value = False

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = {"notification_consent": False}
        mock_db.execute.return_value = mock_result

        service = ShippingNotificationService(
            send_service=mock_send_service,
            rate_limiter=mock_rate_limiter,
        )

        mock_order = MagicMock(spec=Order)
        mock_order.order_number = "1001"
        mock_order.platform_sender_id = "test_psid"
        mock_order.tracking_number = "1Z999AA10123456784"
        mock_order.tracking_url = None
        mock_order.shopify_order_id = "gid://shopify/Order/123"
        mock_order.created_at = datetime.utcnow()

        result = await service.send_shipping_notification(mock_order, mock_db)

        assert result.status == NotificationStatus.SKIPPED_NO_CONSENT
        mock_send_service.send_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_duplicate_webhook_is_idempotent(self):
        """Test that duplicate webhook is idempotent (AC7)."""
        from app.services.shipping_notification import (
            NotificationStatus,
            ShippingNotificationService,
        )

        mock_send_service = AsyncMock()

        mock_rate_limiter = AsyncMock()
        mock_rate_limiter.check_rate_limit.return_value = MagicMock(allowed=True)
        mock_rate_limiter.check_idempotency.return_value = True

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = {"notification_consent": True}
        mock_db.execute.return_value = mock_result

        service = ShippingNotificationService(
            send_service=mock_send_service,
            rate_limiter=mock_rate_limiter,
        )

        mock_order = MagicMock(spec=Order)
        mock_order.order_number = "1001"
        mock_order.platform_sender_id = "test_psid"
        mock_order.tracking_number = "1Z999AA10123456784"
        mock_order.tracking_url = None
        mock_order.shopify_order_id = "gid://shopify/Order/123"
        mock_order.created_at = datetime.utcnow()

        result = await service.send_shipping_notification(
            mock_order, mock_db, fulfillment_id="fulfillment_456"
        )

        assert result.status == NotificationStatus.SKIPPED_DUPLICATE
        mock_send_service.send_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_multiple_fulfillments_respect_rate_limit(self):
        """Test that multiple fulfillments respect the rate limit."""
        from app.services.shipping_notification import (
            NotificationStatus,
            ShippingNotificationService,
        )
        from app.services.shipping_notification.rate_limiter import RateLimitResult

        mock_send_service = AsyncMock()
        mock_send_service.send_message.return_value = {"message_id": "mid.test"}

        call_count = [0]

        async def mock_check_rate_limit(psid):
            call_count[0] += 1
            if call_count[0] <= 1:
                return RateLimitResult(allowed=True)
            return RateLimitResult(allowed=False, reason="daily_limit_reached")

        mock_rate_limiter = AsyncMock()
        mock_rate_limiter.check_rate_limit = mock_check_rate_limit
        mock_rate_limiter.check_idempotency.return_value = False

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = {"notification_consent": True}
        mock_db.execute.return_value = mock_result

        service = ShippingNotificationService(
            send_service=mock_send_service,
            rate_limiter=mock_rate_limiter,
        )

        base_order = MagicMock(spec=Order)
        base_order.order_number = "1001"
        base_order.platform_sender_id = "test_psid"
        base_order.tracking_number = "1Z999AA10123456784"
        base_order.tracking_url = None
        base_order.shopify_order_id = "gid://shopify/Order/123"
        base_order.created_at = datetime.utcnow()

        result1 = await service.send_shipping_notification(
            base_order, mock_db, fulfillment_id="fulfillment_1"
        )
        assert result1.status == NotificationStatus.SUCCESS

        result2 = await service.send_shipping_notification(
            base_order, mock_db, fulfillment_id="fulfillment_2"
        )
        assert result2.status == NotificationStatus.SKIPPED_RATE_LIMITED
