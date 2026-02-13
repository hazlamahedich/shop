"""In-app notification provider.

Creates BudgetAlert records for in-app notifications.
"""

from __future__ import annotations

from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.budget_alert import BudgetAlert
from app.services.notification.base import NotificationProvider

logger = structlog.get_logger(__name__)


class NotificationError(Exception):
    """Base exception for notification errors."""

    pass


class InAppNotificationProvider(NotificationProvider):
    """In-app notification provider.

    Creates BudgetAlert records that appear in the merchant dashboard.
    """

    def __init__(self, db: AsyncSession) -> None:
        """Initialize provider with database session.

        Args:
            db: Database session for creating alerts
        """
        self.db = db

    async def send(
        self,
        merchant_id: int,
        message: str,
        metadata: dict[str, Any],
    ) -> bool:
        """Create an in-app notification (BudgetAlert record).

        Args:
            merchant_id: Target merchant ID
            message: Alert message
            metadata: Must contain 'threshold' key (80 or 100)

        Returns:
            True if alert was created successfully

        Raises:
            NotificationError: If creation fails
        """
        threshold = metadata.get("threshold", 0)

        try:
            alert = BudgetAlert(
                merchant_id=merchant_id,
                threshold=threshold,
                message=message,
                is_read=False,
            )

            self.db.add(alert)
            await self.db.flush()

            logger.info(
                "in_app_notification_created",
                merchant_id=merchant_id,
                alert_id=alert.id,
                threshold=threshold,
            )

            return True

        except Exception as e:
            logger.error(
                "in_app_notification_failed",
                merchant_id=merchant_id,
                threshold=threshold,
                error=str(e),
            )
            raise NotificationError(f"Failed to create in-app notification: {e}") from e

    async def send_batch(
        self,
        notifications: list[dict[str, Any]],
    ) -> int:
        """Create multiple in-app notifications.

        Args:
            notifications: List of dicts with merchant_id, message, metadata

        Returns:
            Number of successfully created notifications
        """
        success_count = 0

        for notification in notifications:
            try:
                await self.send(
                    merchant_id=notification["merchant_id"],
                    message=notification["message"],
                    metadata=notification.get("metadata", {}),
                )
                success_count += 1
            except NotificationError as e:
                logger.warning(
                    "batch_notification_failed",
                    merchant_id=notification.get("merchant_id"),
                    error=str(e),
                )

        return success_count

    async def get_unread_count(self, merchant_id: int) -> int:
        """Get count of unread alerts for a merchant.

        Args:
            merchant_id: Merchant ID

        Returns:
            Number of unread alerts
        """
        query = select(BudgetAlert).where(
            BudgetAlert.merchant_id == merchant_id,
            BudgetAlert.is_read.is_(False),
        )
        result = await self.db.execute(query)
        alerts = result.scalars().all()
        return len(alerts)

    async def mark_as_read(self, alert_id: int, merchant_id: int) -> bool:
        """Mark an alert as read.

        Args:
            alert_id: Alert ID
            merchant_id: Merchant ID (for isolation)

        Returns:
            True if alert was marked as read
        """
        query = select(BudgetAlert).where(
            BudgetAlert.id == alert_id,
            BudgetAlert.merchant_id == merchant_id,
        )
        result = await self.db.execute(query)
        alert = result.scalars().first()

        if not alert:
            return False

        alert.is_read = True
        await self.db.flush()

        return True
