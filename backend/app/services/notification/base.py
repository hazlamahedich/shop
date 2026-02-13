"""Notification provider base class.

Abstract base class for notification providers.
Enables extensibility for future notification channels (email, Slack, etc).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class NotificationProvider(ABC):
    """Abstract base class for notification providers.

    Provides a consistent interface for sending notifications
    across different channels (in-app, email, Slack, etc).
    """

    @abstractmethod
    async def send(
        self,
        merchant_id: int,
        message: str,
        metadata: dict[str, Any],
    ) -> bool:
        """Send a notification.

        Args:
            merchant_id: Target merchant ID
            message: Notification message
            metadata: Additional metadata (e.g., threshold, alert type)

        Returns:
            True if notification was sent successfully

        Raises:
            NotificationError: If notification fails
        """
        ...

    @abstractmethod
    async def send_batch(
        self,
        notifications: list[dict[str, Any]],
    ) -> int:
        """Send multiple notifications.

        Args:
            notifications: List of notification dicts with merchant_id, message, metadata

        Returns:
            Number of successfully sent notifications
        """
        ...
