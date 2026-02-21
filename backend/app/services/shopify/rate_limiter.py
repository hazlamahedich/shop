"""Shopify API rate limiter for per-merchant throttling.

Story 5-10 Task 14: Production safeguard - prevent Shopify API abuse.

Shopify API limits:
- 2 calls/second per app (leaky bucket)
- 40 calls/minute per app

This module provides per-merchant rate limiting to prevent any single
merchant from consuming all available API capacity.
"""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict
from typing import Optional

import structlog


logger = structlog.get_logger(__name__)


class ShopifyRateLimiter:
    """Per-merchant Shopify API rate limiting.

    Uses token bucket algorithm for smooth rate limiting.
    Each merchant gets their own bucket to prevent one merchant
    from affecting others.

    Shopify limit: 2 calls/second per app (we use 1.5 to be safe).
    """

    _buckets: dict[int, dict] = defaultdict(
        lambda: {
            "tokens": 2.0,
            "last_update": time.time(),
        }
    )

    MAX_TOKENS = 2.0
    REFILL_RATE = 1.5  # tokens per second (slightly under Shopify's 2/sec)
    LOCK: Optional[asyncio.Lock] = None

    @classmethod
    def _get_lock(cls) -> asyncio.Lock:
        """Get or create the global lock."""
        if cls.LOCK is None:
            cls.LOCK = asyncio.Lock()
        return cls.LOCK

    @classmethod
    def _refill_tokens(cls, merchant_id: int) -> None:
        """Refill tokens based on elapsed time.

        Args:
            merchant_id: Merchant ID to refill tokens for
        """
        bucket = cls._buckets[merchant_id]
        now = time.time()
        elapsed = now - bucket["last_update"]

        new_tokens = elapsed * cls.REFILL_RATE
        bucket["tokens"] = min(cls.MAX_TOKENS, bucket["tokens"] + new_tokens)
        bucket["last_update"] = now

    @classmethod
    async def acquire(cls, merchant_id: int, timeout: float = 5.0) -> bool:
        """Acquire a token for Shopify API call.

        Waits if necessary until a token is available.

        Args:
            merchant_id: Merchant ID for per-merchant limiting
            timeout: Maximum time to wait for a token (seconds)

        Returns:
            True if token acquired, False if timeout exceeded
        """
        start_time = time.time()

        async with cls._get_lock():
            cls._refill_tokens(merchant_id)

            if cls._buckets[merchant_id]["tokens"] >= 1.0:
                cls._buckets[merchant_id]["tokens"] -= 1.0
                return True

        wait_time = (1.0 - cls._buckets[merchant_id]["tokens"]) / cls.REFILL_RATE
        wait_time = min(wait_time, timeout - (time.time() - start_time))

        if wait_time > 0:
            await asyncio.sleep(wait_time)
            async with cls._get_lock():
                cls._refill_tokens(merchant_id)
                if cls._buckets[merchant_id]["tokens"] >= 1.0:
                    cls._buckets[merchant_id]["tokens"] -= 1.0
                    return True

        logger.warning(
            "shopify_rate_limit_timeout",
            merchant_id=merchant_id,
            timeout=timeout,
        )
        return False

    @classmethod
    async def try_acquire(cls, merchant_id: int) -> bool:
        """Try to acquire a token without waiting.

        Args:
            merchant_id: Merchant ID for per-merchant limiting

        Returns:
            True if token acquired immediately, False otherwise
        """
        async with cls._get_lock():
            cls._refill_tokens(merchant_id)

            if cls._buckets[merchant_id]["tokens"] >= 1.0:
                cls._buckets[merchant_id]["tokens"] -= 1.0
                return True

        return False

    @classmethod
    def get_available_tokens(cls, merchant_id: int) -> float:
        """Get current available tokens for a merchant.

        Args:
            merchant_id: Merchant ID to check

        Returns:
            Number of available tokens
        """
        cls._refill_tokens(merchant_id)
        return cls._buckets[merchant_id]["tokens"]

    @classmethod
    def reset(cls, merchant_id: Optional[int] = None) -> None:
        """Reset rate limiter state (for testing).

        Args:
            merchant_id: Specific merchant to reset, or None for all
        """
        if merchant_id is not None:
            if merchant_id in cls._buckets:
                del cls._buckets[merchant_id]
        else:
            cls._buckets.clear()
