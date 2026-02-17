"""Notification consent checker for shipping notifications.

Story 4-3 AC6: Notification consent check

Checks if user has opted out of notifications via conversation_data JSONB field.
"""

from __future__ import annotations

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation

logger = structlog.get_logger(__name__)


class ConsentChecker:
    """Check notification consent for shipping notifications.

    Uses the existing conversation_data JSONB field to store consent preference.
    Default is opt-in (consent=True if not explicitly set).
    """

    @staticmethod
    async def check_notification_consent(
        psid: str,
        db: AsyncSession,
    ) -> bool:
        """Check if user has consented to shipping notifications.

        AC6: Notification consent check

        Args:
            psid: Facebook PSID of the user
            db: Database session

        Returns:
            True if notifications allowed, False if opted out
        """
        try:
            result = await db.execute(
                select(Conversation.conversation_data)
                .where(Conversation.platform_sender_id == psid)
                .limit(1)
            )
            conversation_data = result.scalar_one_or_none()

            if conversation_data is None:
                return True

            consent = conversation_data.get("notification_consent", True)

            if not consent:
                logger.warning(
                    "shipping_notification_consent_disabled",
                    psid=psid,
                    error_code=7043,
                )
                return False

            return True

        except Exception as e:
            logger.error(
                "shipping_consent_check_failed",
                psid=psid,
                error=str(e),
            )
            return True
