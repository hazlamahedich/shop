"""Cart retention service for extended cart persistence.

Manages cart data beyond the default 24-hour TTL for opted-in shoppers.
Provides GDPR-compliant cleanup for extended retention carts.

Story 2-7: Persistent Cart Sessions
- 30-day extended retention for opted-in shoppers
- Background job cleanup for expired extended carts
- Voluntary data only (operational data preserved)
"""

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

import redis.asyncio as redis
import structlog

from app.core.config import settings


class CartRetentionService:
    """Service for managing extended cart retention.

    Extended Retention:
    - Default: 24-hour TTL (CartService)
    - Extended: 30-day TTL for opted-in shoppers
    - Cleanup: Background job removes carts older than 30 days

    Redis Keys:
    - cart:{psid} - Standard cart (24h TTL from CartService)
    - cart_extended:{psid} - Extended cart metadata (30d TTL)
    - cart_extended_timestamp:{psid} - Creation timestamp for cleanup
    """

    EXTENDED_TTL_SECONDS = 30 * 24 * 60 * 60  # 30 days
    TIMESTAMP_KEY_PREFIX = "cart_extended_timestamp:"

    def __init__(self, redis_client: Optional[redis.Redis] = None) -> None:
        """Initialize cart retention service.

        Args:
            redis_client: Redis client instance (creates default if not provided)
        """
        if redis_client is None:
            config = settings()
            redis_url = config.get("REDIS_URL", "redis://localhost:6379/0")
            self.redis = redis.from_url(redis_url, decode_responses=True)
        else:
            self.redis = redis_client

        self.logger = structlog.get_logger(__name__)

    def _get_extended_timestamp_key(self, psid: str) -> str:
        """Generate Redis key for extended cart timestamp.

        Args:
            psid: Facebook Page-Scoped ID

        Returns:
            Redis timestamp key
        """
        return f"{self.TIMESTAMP_KEY_PREFIX}{psid}"

    async def enable_extended_retention(self, psid: str) -> dict[str, Any]:
        """Enable extended 30-day retention for shopper's cart.

        Sets metadata flags and timestamps for extended retention.
        The actual cart key (cart:{psid}) is managed by CartService.

        Args:
            psid: Facebook Page-Scoped ID

        Returns:
            Dictionary with retention details
        """
        timestamp_key = self._get_extended_timestamp_key(psid)

        # Store creation timestamp for cleanup tracking
        timestamp_data = {
            "psid": psid,
            "extended_at": datetime.now(timezone.utc).isoformat(),
            "retention_days": 30,
        }

        await self.redis.setex(timestamp_key, self.EXTENDED_TTL_SECONDS, json.dumps(timestamp_data))

        self.logger.info("cart_extended_retention_enabled", psid=psid, retention_days=30)

        return {
            "psid": psid,
            "extended_retention": True,
            "retention_days": 30,
            "expires_at": (
                datetime.now(timezone.utc) + timedelta(seconds=self.EXTENDED_TTL_SECONDS)
            ).isoformat(),
        }

    async def is_extended_retention(self, psid: str) -> bool:
        """Check if shopper has extended cart retention enabled.

        Args:
            psid: Facebook Page-Scoped ID

        Returns:
            True if extended retention is enabled
        """
        timestamp_key = self._get_extended_timestamp_key(psid)
        return await self.redis.exists(timestamp_key) > 0

    async def get_cart_age_days(self, psid: str) -> Optional[int]:
        """Get age of extended cart in days.

        Args:
            psid: Facebook Page-Scoped ID

        Returns:
            Age in days, or None if not extended retention
        """
        timestamp_key = self._get_extended_timestamp_key(psid)
        timestamp_data = await self.redis.get(timestamp_key)

        if not timestamp_data:
            return None

        try:
            data = json.loads(timestamp_data)
            created_at = datetime.fromisoformat(data["extended_at"])
            age = datetime.now(timezone.utc) - created_at
            return age.days
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            self.logger.error("cart_timestamp_parse_error", psid=psid, error=str(e))
            return None

    async def disable_extended_retention(self, psid: str) -> None:
        """Disable extended retention for shopper's cart.

        Removes the extended retention metadata.
        The cart itself remains with standard 24-hour TTL.

        Args:
            psid: Facebook Page-Scoped ID
        """
        timestamp_key = self._get_extended_timestamp_key(psid)
        await self.redis.delete(timestamp_key)

        self.logger.info("cart_extended_retention_disabled", psid=psid)

    async def cleanup_expired_extended_carts(self, max_age_days: int = 30) -> dict[str, Any]:
        """Clean up extended carts older than max_age_days.

        Background job task for Story 2-7 AC-3.
        Scans all extended cart timestamps and removes expired ones.
        The actual cart keys (cart:{psid}) will expire via their own TTL.

        Args:
            max_age_days: Maximum age in days (default 30)

        Returns:
            Dictionary with cleanup results
        """
        logger = structlog.get_logger(__name__)
        logger.info("cart_retention_cleanup_started", max_age_days=max_age_days)

        results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "max_age_days": max_age_days,
            "scanned": 0,
            "removed": 0,
            "errors": 0,
        }

        try:
            # Scan for all extended cart timestamp keys
            pattern = f"{self.TIMESTAMP_KEY_PREFIX}*"
            cursor = "0"
            removed_psids = []

            while cursor != 0:
                cursor, keys = await self.redis.scan(cursor=cursor, match=pattern, count=100)

                results["scanned"] += len(keys)

                for key in keys:
                    try:
                        # Extract psid from key
                        psid = key.replace(self.TIMESTAMP_KEY_PREFIX, "")

                        # Check cart age
                        age_days = await self.get_cart_age_days(psid)

                        if age_days is None:
                            # Invalid timestamp data, remove
                            await self.redis.delete(key)
                            results["removed"] += 1
                            removed_psids.append(psid)
                            continue

                        if age_days > max_age_days:
                            # Cart is too old, remove extended retention
                            await self.disable_extended_retention(psid)
                            results["removed"] += 1
                            removed_psids.append(psid)

                            logger.info(
                                "cart_extended_retention_expired",
                                psid=psid,
                                age_days=age_days,
                                max_age_days=max_age_days,
                            )

                    except Exception as e:
                        results["errors"] += 1
                        logger.error("cart_cleanup_error", key=key, error=str(e))

            logger.info(
                "cart_retention_cleanup_completed",
                **results,
                removed_samples=removed_psids[:10],  # Log first 10
            )

        except Exception as e:
            logger.error("cart_retention_cleanup_failed", error=str(e), error_type=type(e).__name__)
            results["error"] = str(e)
            raise

        return results


async def run_cart_retention_cleanup() -> dict:
    """Run cart retention cleanup job.

    Wrapper for background job scheduler compatibility.
    Matches the pattern of data_retention.py's run_retention_cleanup().

    Returns:
        Dictionary with cleanup results
    """
    service = CartRetentionService()
    return await service.cleanup_expired_extended_carts(max_age_days=30)
