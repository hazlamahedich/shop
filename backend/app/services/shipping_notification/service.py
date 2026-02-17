"""Shipping notification service.

Story 4-3: Shipping Notifications
Sends Messenger notifications when orders are fulfilled.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Optional

import structlog

from app.core.errors import ErrorCode
from app.models.order import Order
from app.services.messenger.send_service import MessengerSendService
from app.services.shipping_notification.consent_checker import ConsentChecker
from app.services.shipping_notification.rate_limiter import (
    RateLimitResult,
    ShippingRateLimiter,
)
from app.services.shipping_notification.tracking_formatter import TrackingFormatter

logger = structlog.get_logger(__name__)


class NotificationStatus(str, Enum):
    """Status of notification send attempt."""

    SUCCESS = "success"
    SKIPPED_RATE_LIMITED = "skipped_rate_limited"
    SKIPPED_NO_TRACKING = "skipped_no_tracking"
    SKIPPED_NO_CONSENT = "skipped_no_consent"
    SKIPPED_DUPLICATE = "skipped_duplicate"
    SKIPPED_OLD_ORDER = "skipped_old_order"
    FAILED = "failed"


@dataclass
class NotificationResult:
    """Result of shipping notification attempt."""

    status: NotificationStatus
    psid: Optional[str] = None
    order_number: Optional[str] = None
    message_id: Optional[str] = None
    error_code: Optional[ErrorCode] = None
    error_message: Optional[str] = None


class ShippingNotificationService:
    """Service for sending shipping notifications via Messenger.

    Features:
    - Sends notification with order_update tag (AC3)
    - Daily rate limiting (AC4)
    - Tracking link formatting (AC5)
    - Consent checking (AC6)
    - Idempotency for duplicate webhooks (AC7)
    - 24-hour rule compliance for old orders (AC3)
    """

    ORDER_AGE_LIMIT_HOURS = 24

    def __init__(
        self,
        send_service: Optional[MessengerSendService] = None,
        rate_limiter: Optional[ShippingRateLimiter] = None,
    ) -> None:
        """Initialize the shipping notification service.

        Args:
            send_service: MessengerSendService instance (created if not provided)
            rate_limiter: ShippingRateLimiter instance (created if not provided)
        """
        self.send_service = send_service or MessengerSendService()
        self.rate_limiter = rate_limiter or ShippingRateLimiter()
        self.tracking_formatter = TrackingFormatter()
        self.consent_checker = ConsentChecker()

    async def send_shipping_notification(
        self,
        order: Order,
        db,
        fulfillment_id: Optional[str] = None,
    ) -> NotificationResult:
        """Send shipping notification for a fulfilled order.

        Args:
            order: The Order object with tracking info
            db: Database session
            fulfillment_id: Optional fulfillment ID for idempotency

        Returns:
            NotificationResult with status and details
        """
        psid = order.platform_sender_id
        order_number = order.order_number
        shopify_order_id = order.shopify_order_id

        log = logger.bind(
            psid=psid,
            order_number=order_number,
            shopify_order_id=shopify_order_id,
        )

        if not psid:
            log.warning("shipping_notification_no_psid")
            return NotificationResult(
                status=NotificationStatus.FAILED,
                order_number=order_number,
                error_message="No PSID associated with order",
            )

        if fulfillment_id and shopify_order_id:
            is_duplicate = await self.rate_limiter.check_idempotency(
                shopify_order_id, fulfillment_id
            )
            if is_duplicate:
                return NotificationResult(
                    status=NotificationStatus.SKIPPED_DUPLICATE,
                    psid=psid,
                    order_number=order_number,
                    error_code=ErrorCode.SHIPPING_DUPLICATE_WEBHOOK,
                )

        has_consent = await self.consent_checker.check_notification_consent(psid, db)
        if not has_consent:
            return NotificationResult(
                status=NotificationStatus.SKIPPED_NO_CONSENT,
                psid=psid,
                order_number=order_number,
                error_code=ErrorCode.SHIPPING_CONSENT_DISABLED,
            )

        rate_result = await self.rate_limiter.check_rate_limit(psid)
        if not rate_result.allowed:
            return NotificationResult(
                status=NotificationStatus.SKIPPED_RATE_LIMITED,
                psid=psid,
                order_number=order_number,
                error_code=ErrorCode.SHIPPING_RATE_LIMITED,
            )

        if not order.tracking_number:
            log.warning(
                "shipping_notification_no_tracking_info",
                error_code=7042,
            )
            return NotificationResult(
                status=NotificationStatus.SKIPPED_NO_TRACKING,
                psid=psid,
                order_number=order_number,
                error_code=ErrorCode.SHIPPING_NO_TRACKING_INFO,
            )

        order_age_hours = self._get_order_age_hours(order)
        if order_age_hours > self.ORDER_AGE_LIMIT_HOURS:
            log.info(
                "shipping_notification_old_order",
                order_age_hours=order_age_hours,
            )

        message = TrackingFormatter.format_tracking_message(
            order_number=order_number,
            tracking_number=order.tracking_number,
            tracking_url=order.tracking_url,
        )

        try:
            if order_age_hours > self.ORDER_AGE_LIMIT_HOURS:
                tag = None
            else:
                tag = "order_update"
            response = await self.send_service.send_message(
                recipient_id=psid,
                message_payload={"text": message},
                tag=tag,
            )

            await self.rate_limiter.mark_notification_sent(psid)

            if fulfillment_id and shopify_order_id:
                await self.rate_limiter.mark_idempotency_processed(shopify_order_id, fulfillment_id)

            log.info(
                "shipping_notification_sent",
                order_number=order_number,
                tracking_number=order.tracking_number,
                message_id=response.get("message_id"),
            )

            return NotificationResult(
                status=NotificationStatus.SUCCESS,
                psid=psid,
                order_number=order_number,
                message_id=response.get("message_id"),
            )

        except Exception as e:
            log.error(
                "shipping_notification_failed",
                order_number=order_number,
                error=str(e),
                error_code=7040,
            )
            return NotificationResult(
                status=NotificationStatus.FAILED,
                psid=psid,
                order_number=order_number,
                error_code=ErrorCode.SHIPPING_NOTIFICATION_FAILED,
                error_message=str(e),
            )

    def _get_order_age_hours(self, order: Order) -> float:
        """Calculate order age in hours.

        Args:
            order: The Order object

        Returns:
            Age in hours
        """
        if not order.created_at:
            return 0.0
        age_delta = datetime.utcnow() - order.created_at
        return age_delta.total_seconds() / 3600

    async def close(self) -> None:
        """Close the send service client."""
        if self.send_service:
            await self.send_service.close()

    async def __aenter__(self) -> "ShippingNotificationService":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()
