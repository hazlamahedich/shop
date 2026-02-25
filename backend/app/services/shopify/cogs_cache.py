"""COGS (Cost of Goods Sold) Redis caching service.

Story 4-13: Shopify Payment/Cost Data Enhancement

Provides 24-hour TTL caching for variant costs fetched from Shopify Admin API.
Enables profit margin calculations without repeated API calls.
"""

from __future__ import annotations

import json
from decimal import Decimal
from typing import Any, Optional

import redis.asyncio as redis
import structlog

from app.core.config import settings


logger = structlog.get_logger(__name__)


class COGSCache:
    """Redis-based cache for Cost of Goods Sold data.

    Features:
    - 24-hour TTL for variant costs
    - Automatic invalidation on inventory updates
    - Batch get/set operations for efficiency
    - Graceful degradation on Redis errors

    Redis Keys:
    - cogs:variant:{variant_gid} - Individual variant cost (24h TTL)
    - cogs:inventory_item:{inventory_item_id} - Map to variant for invalidation
    """

    TTL_SECONDS = 86400  # 24 hours
    KEY_PREFIX = "cogs:variant"
    INVENTORY_KEY_PREFIX = "cogs:inventory_item"

    def __init__(
        self,
        redis_client: Optional[redis.Redis] = None,
    ) -> None:
        """Initialize COGS cache.

        Args:
            redis_client: Optional Redis client instance
        """
        if redis_client is None:
            config = settings()
            redis_url = config.get("REDIS_URL", "redis://localhost:6379/0")
            self.redis = redis.from_url(redis_url, decode_responses=True)
        else:
            self.redis = redis_client

    def _get_variant_key(self, variant_gid: str) -> str:
        """Generate Redis key for variant cost.

        Args:
            variant_gid: Shopify variant GID

        Returns:
            Redis key string
        """
        variant_id = variant_gid.split("/")[-1] if "/" in variant_gid else variant_gid
        return f"{self.KEY_PREFIX}:{variant_id}"

    def _get_inventory_key(self, inventory_item_id: str) -> str:
        """Generate Redis key for inventory item to variant mapping.

        Args:
            inventory_item_id: Shopify inventory item ID

        Returns:
            Redis key string
        """
        return f"{self.INVENTORY_KEY_PREFIX}:{inventory_item_id}"

    async def get(self, variant_gid: str) -> Optional[Decimal]:
        """Get cached cost for a variant.

        Args:
            variant_gid: Shopify variant GID

        Returns:
            Cached cost as Decimal, or None if not found
        """
        key = self._get_variant_key(variant_gid)
        try:
            cached = await self.redis.get(key)
            if cached:
                return Decimal(cached)
            return None
        except Exception as e:
            logger.warning(
                "cogs_cache_get_failed",
                variant_gid=variant_gid,
                error=str(e),
            )
            return None

    async def get_batch(
        self,
        variant_gids: list[str],
    ) -> dict[str, Optional[Decimal]]:
        """Get cached costs for multiple variants.

        Args:
            variant_gids: List of Shopify variant GIDs

        Returns:
            Dict mapping variant_gid to cached cost (or None if not found)
        """
        if not variant_gids:
            return {}

        results: dict[str, Optional[Decimal]] = {}
        keys = [self._get_variant_key(gid) for gid in variant_gids]

        try:
            cached_values = await self.redis.mget(keys)
            for gid, cached in zip(variant_gids, cached_values):
                if cached:
                    try:
                        results[gid] = Decimal(cached)
                    except Exception:
                        results[gid] = None
                else:
                    results[gid] = None
        except Exception as e:
            logger.warning(
                "cogs_cache_batch_get_failed",
                variant_count=len(variant_gids),
                error=str(e),
            )
            return {gid: None for gid in variant_gids}

        return results

    async def set(
        self,
        variant_gid: str,
        cost: Decimal,
    ) -> bool:
        """Cache cost for a variant.

        Args:
            variant_gid: Shopify variant GID
            cost: Unit cost as Decimal

        Returns:
            True if cached successfully
        """
        key = self._get_variant_key(variant_gid)
        try:
            await self.redis.setex(key, self.TTL_SECONDS, str(cost))
            logger.debug(
                "cogs_cache_set",
                variant_gid=variant_gid,
                cost=str(cost),
            )
            return True
        except Exception as e:
            logger.warning(
                "cogs_cache_set_failed",
                variant_gid=variant_gid,
                error=str(e),
            )
            return False

    async def set_batch(
        self,
        costs: dict[str, Decimal],
    ) -> int:
        """Cache costs for multiple variants.

        Args:
            costs: Dict mapping variant_gid to unit cost

        Returns:
            Number of variants cached successfully
        """
        if not costs:
            return 0

        success_count = 0
        try:
            pipe = self.redis.pipeline()
            for variant_gid, cost in costs.items():
                key = self._get_variant_key(variant_gid)
                pipe.setex(key, self.TTL_SECONDS, str(cost))
                success_count += 1
            await pipe.execute()

            logger.debug(
                "cogs_cache_batch_set",
                variant_count=len(costs),
            )
        except Exception as e:
            logger.warning(
                "cogs_cache_batch_set_failed",
                variant_count=len(costs),
                error=str(e),
            )
            return 0

        return success_count

    async def invalidate(self, variant_gid: str) -> bool:
        """Invalidate cached cost for a variant.

        Args:
            variant_gid: Shopify variant GID

        Returns:
            True if invalidated successfully
        """
        key = self._get_variant_key(variant_gid)
        try:
            await self.redis.delete(key)
            logger.debug(
                "cogs_cache_invalidated",
                variant_gid=variant_gid,
            )
            return True
        except Exception as e:
            logger.warning(
                "cogs_cache_invalidate_failed",
                variant_gid=variant_gid,
                error=str(e),
            )
            return False

    async def invalidate_by_inventory_item(
        self,
        inventory_item_id: str,
        variant_gid: str,
    ) -> bool:
        """Invalidate cached cost for a variant by inventory item ID.

        Called when inventory_levels/update webhook is received.

        Args:
            inventory_item_id: Shopify inventory item ID
            variant_gid: Shopify variant GID

        Returns:
            True if invalidated successfully
        """
        try:
            variant_key = self._get_variant_key(variant_gid)
            inventory_key = self._get_inventory_key(inventory_item_id)

            await self.redis.delete(variant_key)
            logger.debug(
                "cogs_cache_invalidated_by_inventory",
                inventory_item_id=inventory_item_id,
                variant_gid=variant_gid,
            )
            return True
        except Exception as e:
            logger.warning(
                "cogs_cache_invalidate_by_inventory_failed",
                inventory_item_id=inventory_item_id,
                error=str(e),
            )
            return False

    async def invalidate_batch(
        self,
        variant_gids: list[str],
    ) -> int:
        """Invalidate cached costs for multiple variants.

        Args:
            variant_gids: List of Shopify variant GIDs

        Returns:
            Number of variants invalidated
        """
        if not variant_gids:
            return 0

        try:
            keys = [self._get_variant_key(gid) for gid in variant_gids]
            await self.redis.delete(*keys)
            logger.debug(
                "cogs_cache_batch_invalidated",
                variant_count=len(variant_gids),
            )
            return len(variant_gids)
        except Exception as e:
            logger.warning(
                "cogs_cache_batch_invalidate_failed",
                variant_count=len(variant_gids),
                error=str(e),
            )
            return 0
