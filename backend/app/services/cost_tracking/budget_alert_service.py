"""Budget Alert Service.

Handles budget threshold detection, alert creation, and bot pause/resume logic.
Implements Redis+PostgreSQL dual-write pattern for bot pause state.

Story 3-8: Budget Alert Notifications
- Configurable thresholds (warning: 50-95%, critical: 80-99%)
- Three alert levels: warning (80%), critical (95%), exceeded (100%)
- Redis snooze with 24h TTL
- Email + in-app notifications
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

import redis.asyncio as redis
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.budget_alert import BudgetAlert
from app.models.merchant import Merchant
from app.services.notification.in_app_provider import InAppNotificationProvider

logger = structlog.get_logger(__name__)

ThresholdStatus = Literal["ok", "warning", "critical", "exceeded"]

DEFAULT_WARNING_THRESHOLD = 80
DEFAULT_CRITICAL_THRESHOLD = 95
SNOOZE_DURATION_SECONDS = 86400  # 24 hours


class BudgetAlertService:
    """Service for budget alert management.

    Provides:
    - Budget threshold detection with Decimal precision
    - Configurable warning/critical thresholds
    - Alert creation with deduplication
    - Bot pause/resume with Redis+PostgreSQL dual-write
    - Snooze functionality with Redis TTL
    - LLM request budget checking
    """

    PAUSED_BOT_MESSAGE = "I've reached my message limit. Please contact support."
    ZERO_BUDGET_MESSAGE = "Budget is $0. Please set a budget to enable the bot."

    BOT_PAUSED_REDIS_TTL_SECONDS = 86400  # 24 hours

    def __init__(
        self,
        db: AsyncSession | None = None,
        redis_client: redis.Redis | None = None,
    ) -> None:
        """Initialize budget alert service.

        Args:
            db: Database session (optional - only needed for alert creation)
            redis_client: Optional Redis client (created if not provided)
        """
        self.db = db
        self.notification_provider = InAppNotificationProvider(db) if db else None

        if redis_client is None:
            config = settings()
            redis_url = config.get("REDIS_URL", "redis://localhost:6379/0")
            self.redis = redis.from_url(redis_url, decode_responses=True)
        else:
            self.redis = redis_client

    def _get_bot_paused_redis_key(self, merchant_id: int) -> str:
        """Generate Redis key for bot paused state.

        Args:
            merchant_id: Merchant ID

        Returns:
            Redis key string
        """
        return f"merchant:{merchant_id}:bot_paused"

    def _get_thresholds(self, merchant: Merchant | None) -> tuple[int, int]:
        """Get configurable thresholds from merchant config.

        Args:
            merchant: Merchant instance (may be None)

        Returns:
            Tuple of (warning_threshold, critical_threshold)
        """
        if not merchant or not merchant.config:
            return (DEFAULT_WARNING_THRESHOLD, DEFAULT_CRITICAL_THRESHOLD)

        warning = merchant.config.get("alert_warning_threshold", DEFAULT_WARNING_THRESHOLD)
        critical = merchant.config.get("alert_critical_threshold", DEFAULT_CRITICAL_THRESHOLD)

        return (int(warning), int(critical))

    async def check_budget_threshold(
        self,
        merchant_id: int,
        monthly_spend: Decimal,
        budget_cap: Decimal | None,
    ) -> ThresholdStatus:
        """Check budget threshold status with configurable thresholds.

        Args:
            merchant_id: Merchant ID (for logging)
            monthly_spend: Current month's spending
            budget_cap: Monthly budget cap (None = no limit)

        Returns:
            "ok": Under warning threshold or no budget set
            "warning": At or above warning threshold
            "critical": At or above critical threshold
            "exceeded": 100% or above, or budget is $0
        """
        if budget_cap is None:
            return "ok"

        if budget_cap == Decimal("0"):
            return "exceeded"

        if budget_cap <= Decimal("0"):
            return "exceeded"

        merchant = await self._get_merchant(merchant_id)
        warning_threshold, critical_threshold = self._get_thresholds(merchant)

        percentage = (monthly_spend / budget_cap) * Decimal("100")

        if percentage >= Decimal("100"):
            return "exceeded"
        elif percentage >= Decimal(str(critical_threshold)):
            return "critical"
        elif percentage >= Decimal(str(warning_threshold)):
            return "warning"

        return "ok"

    async def get_bot_paused_state(self, merchant_id: int) -> tuple[bool, str | None]:
        """Get bot paused state (Redis-first, Postgres-fallback).

        Args:
            merchant_id: Merchant ID

        Returns:
            Tuple of (is_paused, pause_reason)
        """
        redis_key = self._get_bot_paused_redis_key(merchant_id)

        try:
            cached = await self.redis.get(redis_key)
            if cached is not None:
                is_paused = cached == "true"

                if is_paused:
                    merchant = await self._get_merchant(merchant_id)
                    pause_reason = None
                    if merchant and merchant.config:
                        pause_reason = merchant.config.get("pause_reason")
                    return (True, pause_reason)

                return (False, None)
        except Exception as e:
            logger.warning(
                "redis_get_failed_fallback_to_postgres",
                merchant_id=merchant_id,
                error=str(e),
            )

        merchant = await self._get_merchant(merchant_id)
        if not merchant or not merchant.config:
            return (False, None)

        is_paused = merchant.config.get("is_bot_paused", False)
        pause_reason = merchant.config.get("pause_reason")

        try:
            await self.redis.set(
                redis_key,
                "true" if is_paused else "false",
                ex=self.BOT_PAUSED_REDIS_TTL_SECONDS,
            )
        except Exception as e:
            logger.warning(
                "redis_cache_set_failed",
                merchant_id=merchant_id,
                error=str(e),
            )

        return (is_paused, pause_reason)

    async def set_bot_paused_state(
        self,
        merchant_id: int,
        paused: bool,
        reason: str | None = None,
    ) -> bool:
        """Set bot paused state with dual-write (Redis + PostgreSQL).

        Both writes must succeed for the operation to complete.

        Args:
            merchant_id: Merchant ID
            paused: Whether bot should be paused
            reason: Optional pause reason

        Returns:
            True if both writes succeeded
        """
        merchant = await self._get_merchant(merchant_id)
        if not merchant:
            logger.error("merchant_not_found", merchant_id=merchant_id)
            return False

        current_config = merchant.config or {}
        new_config = dict(current_config)
        new_config["is_bot_paused"] = paused
        new_config["pause_reason"] = reason

        merchant.config = new_config

        redis_key = self._get_bot_paused_redis_key(merchant_id)

        try:
            if self.db:
                await self.db.flush()

            await self.redis.set(
                redis_key,
                "true" if paused else "false",
                ex=self.BOT_PAUSED_REDIS_TTL_SECONDS,
            )

            logger.info(
                "bot_paused_state_updated",
                merchant_id=merchant_id,
                paused=paused,
                reason=reason,
            )

            return True

        except Exception as e:
            logger.error(
                "dual_write_failed",
                merchant_id=merchant_id,
                paused=paused,
                error=str(e),
            )
            return False

    async def create_alert_if_needed(
        self,
        merchant_id: int,
        threshold: int,
        budget_cap: Decimal,
    ) -> BudgetAlert | None:
        """Create an alert if not already sent for this threshold in current period.

        Args:
            merchant_id: Merchant ID
            threshold: Threshold percentage (80 or 100)
            budget_cap: Budget cap amount

        Returns:
            Created alert or None if duplicate or no db session
        """
        if self.db is None:
            return None

        merchant = await self._get_merchant(merchant_id)
        if not merchant:
            return None

        current_config = merchant.config or {}
        last_alert_threshold = current_config.get("last_alert_threshold")
        last_alert_month = current_config.get("last_alert_month")
        current_month = datetime.utcnow().strftime("%Y-%m")

        if last_alert_threshold == threshold and last_alert_month == current_month:
            logger.info(
                "alert_already_sent_this_month",
                merchant_id=merchant_id,
                threshold=threshold,
            )
            return None

        message = f"Budget alert: {threshold}% of your ${budget_cap:.2f} budget used"

        alert = await self._create_alert_record(merchant_id, threshold, message)

        new_config = dict(current_config)
        new_config["last_alert_threshold"] = threshold
        new_config["last_alert_month"] = current_month
        merchant.config = new_config

        await self.db.flush()

        logger.info(
            "budget_alert_created",
            merchant_id=merchant_id,
            threshold=threshold,
            alert_id=alert.id,
        )

        return alert

    async def _create_alert_record(
        self,
        merchant_id: int,
        threshold: int,
        message: str,
    ) -> BudgetAlert:
        """Create a BudgetAlert record.

        Args:
            merchant_id: Merchant ID
            threshold: Threshold percentage
            message: Alert message

        Returns:
            Created alert

        Raises:
            ValueError: If no database session available
        """
        if self.db is None:
            raise ValueError("Database session required for alert creation")

        alert = BudgetAlert(
            merchant_id=merchant_id,
            threshold=threshold,
            message=message,
            is_read=False,
        )
        self.db.add(alert)
        await self.db.flush()
        return alert

    async def _get_merchant(self, merchant_id: int) -> Merchant | None:
        """Get merchant by ID.

        Args:
            merchant_id: Merchant ID

        Returns:
            Merchant or None
        """
        if self.db is None:
            return None

        query = select(Merchant).where(Merchant.id == merchant_id)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_alerts(
        self,
        merchant_id: int,
        unread_only: bool = False,
    ) -> list[BudgetAlert]:
        """Get budget alerts for a merchant.

        Args:
            merchant_id: Merchant ID
            unread_only: Only return unread alerts

        Returns:
            List of alerts (empty if no db session)
        """
        if self.db is None:
            return []

        query = select(BudgetAlert).where(BudgetAlert.merchant_id == merchant_id)

        if unread_only:
            query = query.where(BudgetAlert.is_read.is_(False))

        query = query.order_by(BudgetAlert.created_at.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def mark_alert_read(
        self,
        alert_id: int,
        merchant_id: int,
    ) -> bool:
        """Mark an alert as read.

        Args:
            alert_id: Alert ID
            merchant_id: Merchant ID (for isolation)

        Returns:
            True if marked as read
        """
        if self.notification_provider is None:
            return False
        return await self.notification_provider.mark_as_read(alert_id, merchant_id)

    async def resume_bot(self, merchant_id: int) -> tuple[bool, str]:
        """Resume bot by clearing pause state.

        Args:
            merchant_id: Merchant ID

        Returns:
            Tuple of (success, message)
        """
        is_paused, _ = await self.get_bot_paused_state(merchant_id)

        if not is_paused:
            return (True, "Bot is already active")

        success = await self.set_bot_paused_state(merchant_id, False, None)

        if success:
            return (True, "Bot resumed successfully")
        else:
            return (False, "Failed to resume bot")

    async def check_and_handle_budget_state(
        self,
        merchant_id: int,
        monthly_spend: Decimal,
        budget_cap: Decimal | None,
    ) -> tuple[ThresholdStatus, str | None]:
        """Check budget and handle alerts/pause state.

        This is the main entry point for LLM wrapper integration.

        Args:
            merchant_id: Merchant ID
            monthly_spend: Current month's spending
            budget_cap: Monthly budget cap

        Returns:
            Tuple of (status, message_if_blocked)
        """
        if budget_cap is None:
            return ("ok", None)

        if budget_cap == Decimal("0"):
            return ("exceeded", self.ZERO_BUDGET_MESSAGE)

        status = await self.check_budget_threshold(merchant_id, monthly_spend, budget_cap)

        if status == "exceeded":
            is_paused, _ = await self.get_bot_paused_state(merchant_id)
            if not is_paused:
                await self.set_bot_paused_state(
                    merchant_id,
                    True,
                    "Budget exceeded",
                )
                await self.create_alert_if_needed(merchant_id, 100, budget_cap)

            return ("exceeded", self.PAUSED_BOT_MESSAGE)

        if status == "critical":
            await self.create_alert_if_needed(merchant_id, 95, budget_cap)

        if status == "warning":
            is_snoozed = await self.is_snoozed(merchant_id)
            if not is_snoozed:
                await self.create_alert_if_needed(merchant_id, 80, budget_cap)

        return (status, None)

    async def snooze(self, merchant_id: int) -> bool:
        """Snooze warning alerts for 24 hours.

        Args:
            merchant_id: Merchant ID

        Returns:
            True if snooze was set successfully
        """
        redis_key = f"budget_alert_snooze:{merchant_id}"

        try:
            await self.redis.set(
                redis_key,
                datetime.utcnow().isoformat(),
                ex=SNOOZE_DURATION_SECONDS,
            )
            logger.info("budget_alert_snoozed", merchant_id=merchant_id)
            return True
        except Exception as e:
            logger.warning("snooze_set_failed", merchant_id=merchant_id, error=str(e))
            return False

    async def is_snoozed(self, merchant_id: int) -> bool:
        """Check if alerts are snoozed for this merchant.

        Args:
            merchant_id: Merchant ID

        Returns:
            True if snoozed (Redis key exists)
        """
        redis_key = f"budget_alert_snooze:{merchant_id}"

        try:
            snoozed_at = await self.redis.get(redis_key)
            return snoozed_at is not None
        except Exception as e:
            logger.warning("snooze_check_failed", merchant_id=merchant_id, error=str(e))
            return False

    async def clear_snooze(self, merchant_id: int) -> bool:
        """Clear snooze state for a merchant.

        Args:
            merchant_id: Merchant ID

        Returns:
            True if snooze was cleared
        """
        redis_key = f"budget_alert_snooze:{merchant_id}"

        try:
            await self.redis.delete(redis_key)
            logger.info("budget_alert_snooze_cleared", merchant_id=merchant_id)
            return True
        except Exception as e:
            logger.warning("snooze_clear_failed", merchant_id=merchant_id, error=str(e))
            return False

    async def get_alert_config(self, merchant_id: int) -> dict:
        """Get alert configuration for a merchant.

        Args:
            merchant_id: Merchant ID

        Returns:
            Dict with warning_threshold, critical_threshold, enabled
        """
        merchant = await self._get_merchant(merchant_id)
        warning_threshold, critical_threshold = self._get_thresholds(merchant)

        enabled = True
        if merchant and merchant.config:
            enabled = merchant.config.get("alerts_enabled", True)

        return {
            "warning_threshold": warning_threshold,
            "critical_threshold": critical_threshold,
            "enabled": enabled,
        }

    async def update_alert_config(
        self,
        merchant_id: int,
        warning_threshold: int | None = None,
        critical_threshold: int | None = None,
        enabled: bool | None = None,
    ) -> bool:
        """Update alert configuration for a merchant.

        Args:
            merchant_id: Merchant ID
            warning_threshold: Warning threshold (50-95%)
            critical_threshold: Critical threshold (80-99%)
            enabled: Whether alerts are enabled

        Returns:
            True if update succeeded
        """
        if self.db is None:
            return False

        merchant = await self._get_merchant(merchant_id)
        if not merchant:
            return False

        current_config = merchant.config or {}
        new_config = dict(current_config)

        if warning_threshold is not None:
            if 50 <= warning_threshold <= 95:
                new_config["alert_warning_threshold"] = warning_threshold

        if critical_threshold is not None:
            if 80 <= critical_threshold <= 99:
                new_config["alert_critical_threshold"] = critical_threshold

        if enabled is not None:
            new_config["alerts_enabled"] = enabled

        merchant.config = new_config
        await self.db.flush()

        logger.info(
            "alert_config_updated",
            merchant_id=merchant_id,
            warning_threshold=new_config.get("alert_warning_threshold"),
            critical_threshold=new_config.get("alert_critical_threshold"),
            enabled=new_config.get("alerts_enabled"),
        )

        return True
