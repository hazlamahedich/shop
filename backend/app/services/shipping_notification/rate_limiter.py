"""Rate limiter for shipping notifications.

Story 4-3 AC4: Daily rate limiting
Story 4-3 AC7: Idempotency for duplicate webhooks

Implements:
- 1 notification per user per day (AC4)
- Duplicate webhook detection (AC7)
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class RateLimitResult:
    """Result of rate limit check."""

    allowed: bool
    reason: Optional[str] = None


class ShippingRateLimiter:
    """Redis-based rate limiter for shipping notifications.

    Features:
    - Daily rate limiting (1 notification per user per day)
    - Idempotency checking (7-day TTL for duplicate prevention)
    - Graceful fail-open behavior when Redis unavailable
    """

    RATE_LIMIT_PREFIX = "shipping_notification"
    IDEMPOTENCY_PREFIX = "shipping_notification_idempotent"
    RATE_LIMIT_TTL_SECONDS = 86400  # 24 hours
    IDEMPOTENCY_TTL_SECONDS = 604800  # 7 days

    def __init__(self, redis_client=None) -> None:
        """Initialize rate limiter.

        Args:
            redis_client: Redis client instance (optional, created if not provided)
        """
        self.redis = redis_client
        self._redis_available: Optional[bool] = None

    async def _get_redis(self):
        """Get Redis client, creating if necessary.

        Returns:
            Redis client or None if unavailable
        """
        if self.redis is not None:
            return self.redis

        try:
            import redis.asyncio as redis

            redis_url = os.getenv("REDIS_URL")
            if not redis_url:
                return None
            self.redis = redis.from_url(redis_url, decode_responses=True)
            return self.redis
        except Exception as e:
            logger.warning("shipping_rate_limiter_redis_unavailable", error=str(e))
            return None

    async def _is_redis_available(self) -> bool:
        """Check if Redis is available.

        Returns:
            True if Redis is available, False otherwise
        """
        if self._redis_available is not None:
            return self._redis_available

        try:
            client = await self._get_redis()
            if client is None:
                self._redis_available = False
                return False
            await client.ping()
            self._redis_available = True
            return True
        except Exception:
            self._redis_available = False
            return False

    async def check_rate_limit(self, psid: str) -> RateLimitResult:
        """Check if notification is allowed for this user today.

        AC4: 1 order_update message per user per day

        Args:
            psid: Facebook PSID of the user

        Returns:
            RateLimitResult with allowed status and reason
        """
        try:
            if not await self._is_redis_available():
                logger.info(
                    "shipping_rate_limit_redis_unavailable_fail_open",
                    psid=psid,
                )
                return RateLimitResult(allowed=True, reason="redis_unavailable")

            client = await self._get_redis()
            today = datetime.utcnow().strftime("%Y-%m-%d")
            key = f"{self.RATE_LIMIT_PREFIX}:{psid}:{today}"

            count = await client.get(key)
            if count and int(count) >= 1:
                logger.warning(
                    "shipping_notification_rate_limited",
                    psid=psid,
                    count=int(count),
                    error_code=7041,
                )
                return RateLimitResult(
                    allowed=False,
                    reason="daily_limit_reached",
                )

            return RateLimitResult(allowed=True)

        except Exception as e:
            logger.error(
                "shipping_rate_limit_check_failed",
                psid=psid,
                error=str(e),
            )
            return RateLimitResult(allowed=True, reason="error_fail_open")

    async def mark_notification_sent(self, psid: str) -> None:
        """Mark notification as sent for rate limiting.

        Args:
            psid: Facebook PSID of the user
        """
        try:
            if not await self._is_redis_available():
                return

            client = await self._get_redis()
            today = datetime.utcnow().strftime("%Y-%m-%d")
            key = f"{self.RATE_LIMIT_PREFIX}:{psid}:{today}"

            now = datetime.utcnow()
            midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            ttl = int((midnight - now).total_seconds())

            await client.setex(key, max(ttl, 1), "1")

            logger.info(
                "shipping_notification_rate_limit_set",
                psid=psid,
                ttl_seconds=ttl,
            )

        except Exception as e:
            logger.error(
                "shipping_rate_limit_mark_failed",
                psid=psid,
                error=str(e),
            )

    async def check_idempotency(
        self,
        shopify_order_id: str,
        fulfillment_id: str,
    ) -> bool:
        """Check if this webhook has already been processed.

        AC7: Idempotency for duplicate webhooks

        Args:
            shopify_order_id: Shopify order GID
            fulfillment_id: Shopify fulfillment ID

        Returns:
            True if already processed (skip), False if new (process)
        """
        try:
            if not await self._is_redis_available():
                return False

            client = await self._get_redis()
            key = f"{self.IDEMPOTENCY_PREFIX}:{shopify_order_id}:{fulfillment_id}"

            exists = await client.exists(key)
            if exists:
                logger.info(
                    "shipping_notification_duplicate_skipped",
                    shopify_order_id=shopify_order_id,
                    fulfillment_id=fulfillment_id,
                    error_code=7044,
                )
                return True

            return False

        except Exception as e:
            logger.error(
                "shipping_idempotency_check_failed",
                shopify_order_id=shopify_order_id,
                fulfillment_id=fulfillment_id,
                error=str(e),
            )
            return False

    async def mark_idempotency_processed(
        self,
        shopify_order_id: str,
        fulfillment_id: str,
    ) -> None:
        """Mark webhook as processed for idempotency.

        Args:
            shopify_order_id: Shopify order GID
            fulfillment_id: Shopify fulfillment ID
        """
        try:
            if not await self._is_redis_available():
                return

            client = await self._get_redis()
            key = f"{self.IDEMPOTENCY_PREFIX}:{shopify_order_id}:{fulfillment_id}"

            await client.setex(key, self.IDEMPOTENCY_TTL_SECONDS, "1")

            logger.info(
                "shipping_idempotency_key_set",
                shopify_order_id=shopify_order_id,
                fulfillment_id=fulfillment_id,
                ttl_seconds=self.IDEMPOTENCY_TTL_SECONDS,
            )

        except Exception as e:
            logger.error(
                "shipping_idempotency_mark_failed",
                shopify_order_id=shopify_order_id,
                fulfillment_id=fulfillment_id,
                error=str(e),
            )
