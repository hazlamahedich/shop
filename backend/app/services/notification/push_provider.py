"""Push notification provider stub.

Story 4-6: Handoff Notifications - AC8 (Optional)

This is a STUB implementation for browser push notifications.
Future enhancement: Implement Web Push API for real-time notifications.

TODO (Future):
- Implement Web Push API using VAPID keys
- Add browser subscription management
- Support notification actions (dismiss, respond)
- Add merchant preference toggle in settings

See: https://developer.mozilla.org/en-US/docs/Web/API/Push_API
"""

from __future__ import annotations

from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class PushNotificationProvider:
    """Stub provider for browser push notifications.

    This is a placeholder that logs intent but does not send notifications.
    Can be extended in the future to implement actual push notifications.

    Usage:
        provider = PushNotificationProvider()
        await provider.send(
            merchant_id=1,
            message="Customer needs help",
            metadata={"conversation_id": 123, "urgency": "high"},
        )
    """

    def __init__(self) -> None:
        """Initialize push notification provider stub."""
        self.enabled = False  # Disabled until implemented

    async def send(
        self,
        merchant_id: int,
        message: str,
        metadata: dict[str, Any],
    ) -> bool:
        """Send a push notification (stub implementation).

        Currently logs the notification intent without actually sending.
        Returns True to indicate "success" for testing purposes.

        Args:
            merchant_id: Target merchant ID
            message: Notification message body
            metadata: Additional data (urgency, conversation_id, etc.)

        Returns:
            True (always succeeds in stub mode)
        """
        logger.info(
            "push_notification_stub",
            merchant_id=merchant_id,
            message=message[:100],
            urgency=metadata.get("urgency", "unknown"),
            note="Push notifications not yet implemented - see AC8",
        )

        return True

    async def is_subscribed(self, merchant_id: int) -> bool:
        """Check if merchant has push notifications enabled.

        Args:
            merchant_id: Merchant ID to check

        Returns:
            False (stub always returns false)
        """
        return False

    async def subscribe(self, merchant_id: int, subscription: dict[str, Any]) -> bool:
        """Register a push notification subscription for a merchant.

        Args:
            merchant_id: Merchant ID
            subscription: Browser PushSubscription JSON

        Returns:
            False (stub always fails)
        """
        logger.warning(
            "push_subscription_stub",
            merchant_id=merchant_id,
            note="Push subscription not yet implemented",
        )
        return False


__all__ = [
    "PushNotificationProvider",
]
