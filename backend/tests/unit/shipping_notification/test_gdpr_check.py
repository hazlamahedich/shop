"""Unit tests for GDPR check in shipping notification service.

Story 6-6, Task 3.2: Update shipping notifications to respect GDPR privacy status.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ErrorCode
from app.models.deletion_audit_log import DeletionRequestType
from app.models.order import Order
from app.services.privacy.gdpr_service import GDPRDeletionService
from app.services.shipping_notification.service import (
    NotificationStatus,
    ShippingNotificationService,
)


class TestShippingNotificationGDPRCheck:
    """Test GDPR check integration with shipping notifications."""

    @pytest.mark.asyncio
    async def test_notification_skipped_for_gdpr_customer(
        self, async_session: AsyncSession, test_merchant: int
    ):
        """Test that notification is skipped when customer has GDPR request."""
        mock_order = MagicMock(spec=Order)
        mock_order.platform_sender_id = "test_psid_gdpr"
        mock_order.order_number = "1001"
        mock_order.shopify_order_id = "gid://shopify/Order/1234567890"
        mock_order.tracking_number = "1Z999AA10123456784"
        mock_order.tracking_url = "https://www.ups.com/track?tracknum=1Z999AA10123456784"
        mock_order.merchant_id = test_merchant
        mock_order.created_at = datetime.utcnow()

        gdpr_service = GDPRDeletionService()
        await gdpr_service.process_deletion_request(
            db=async_session,
            customer_id="test_psid_gdpr",
            merchant_id=test_merchant,
            request_type=DeletionRequestType.GDPR_FORMAL,
        )
        await async_session.commit()

        service = ShippingNotificationService(
            send_service=AsyncMock(),
            rate_limiter=AsyncMock(),
        )

        result = await service.send_shipping_notification(mock_order, async_session)

        assert result.status == NotificationStatus.SKIPPED_GDPR_REQUEST
        assert result.psid == "test_psid_gdpr"
        assert result.order_number == "1001"
        assert result.error_code == ErrorCode.GDPR_REQUEST_PENDING

    @pytest.mark.asyncio
    async def test_notification_sent_for_non_gdpr_customer(
        self, async_session: AsyncSession, test_merchant: int
    ):
        """Test that notification is sent when customer has no GDPR request."""
        from app.services.shipping_notification.rate_limiter import RateLimitResult

        mock_order = MagicMock(spec=Order)
        mock_order.platform_sender_id = "test_psid_normal"
        mock_order.order_number = "1002"
        mock_order.shopify_order_id = "gid://shopify/Order/9876543210"
        mock_order.tracking_number = "1Z999AA10123456785"
        mock_order.tracking_url = "https://www.ups.com/track?tracknum=1Z999AA10123456785"
        mock_order.merchant_id = test_merchant
        mock_order.created_at = datetime.utcnow()

        mock_rate_limiter = AsyncMock()
        mock_rate_limiter.check_rate_limit.return_value = RateLimitResult(allowed=True)
        mock_rate_limiter.check_idempotency.return_value = False

        mock_send_service = AsyncMock()
        mock_send_service.send_message.return_value = {"message_id": "mid.test"}

        service = ShippingNotificationService(
            send_service=mock_send_service,
            rate_limiter=mock_rate_limiter,
        )

        result = await service.send_shipping_notification(mock_order, async_session)

        assert result.status == NotificationStatus.SUCCESS
        assert result.psid == "test_psid_normal"
        assert result.order_number == "1002"

    @pytest.mark.asyncio
    async def test_notification_skipped_for_ccpa_customer(
        self, async_session: AsyncSession, test_merchant: int
    ):
        """Test that notification is skipped when customer has CCPA request."""
        mock_order = MagicMock(spec=Order)
        mock_order.platform_sender_id = "test_psid_ccpa"
        mock_order.order_number = "1003"
        mock_order.shopify_order_id = "gid://shopify/Order/1111111111"
        mock_order.tracking_number = "1Z999AA10123456786"
        mock_order.tracking_url = "https://www.ups.com/track?tracknum=1Z999AA10123456786"
        mock_order.merchant_id = test_merchant
        mock_order.created_at = datetime.utcnow()

        gdpr_service = GDPRDeletionService()
        await gdpr_service.process_deletion_request(
            db=async_session,
            customer_id="test_psid_ccpa",
            merchant_id=test_merchant,
            request_type=DeletionRequestType.CCPA_REQUEST,
        )
        await async_session.commit()

        service = ShippingNotificationService(
            send_service=AsyncMock(),
            rate_limiter=AsyncMock(),
        )

        result = await service.send_shipping_notification(mock_order, async_session)

        assert result.status == NotificationStatus.SKIPPED_GDPR_REQUEST
        assert result.error_code == ErrorCode.GDPR_REQUEST_PENDING

    @pytest.mark.asyncio
    async def test_notification_sent_after_gdpr_revoked(
        self, async_session: AsyncSession, test_merchant: int
    ):
        """Test that notification is sent after GDPR request is revoked."""
        from app.services.shipping_notification.rate_limiter import RateLimitResult

        mock_order = MagicMock(spec=Order)
        mock_order.platform_sender_id = "test_psid_revoked"
        mock_order.order_number = "1004"
        mock_order.shopify_order_id = "gid://shopify/Order/2222222222"
        mock_order.tracking_number = "1Z999AA10123456787"
        mock_order.tracking_url = "https://www.ups.com/track?tracknum=1Z999AA10123456787"
        mock_order.merchant_id = test_merchant
        mock_order.created_at = datetime.utcnow()

        gdpr_service = GDPRDeletionService()
        await gdpr_service.process_deletion_request(
            db=async_session,
            customer_id="test_psid_revoked",
            merchant_id=test_merchant,
            request_type=DeletionRequestType.GDPR_FORMAL,
        )
        await async_session.commit()

        await gdpr_service.revoke_gdpr_request(
            db=async_session,
            customer_id="test_psid_revoked",
            merchant_id=test_merchant,
        )
        await async_session.commit()

        mock_rate_limiter = AsyncMock()
        mock_rate_limiter.check_rate_limit.return_value = RateLimitResult(allowed=True)
        mock_rate_limiter.check_idempotency.return_value = False

        mock_send_service = AsyncMock()
        mock_send_service.send_message.return_value = {"message_id": "mid.test"}

        service = ShippingNotificationService(
            send_service=mock_send_service,
            rate_limiter=mock_rate_limiter,
        )

        result = await service.send_shipping_notification(mock_order, async_session)

        assert result.status == NotificationStatus.SUCCESS
        assert result.psid == "test_psid_revoked"
