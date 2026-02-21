"""Tests for Shopify rate limiter.

Story 5-10 Task 14: Production safeguard tests.
"""

from __future__ import annotations

import asyncio
import time

import pytest

from app.services.shopify.rate_limiter import ShopifyRateLimiter


class TestShopifyRateLimiter:
    """Tests for ShopifyRateLimiter."""

    def setup_method(self) -> None:
        """Reset rate limiter before each test."""
        ShopifyRateLimiter.reset()

    def test_initial_tokens_available(self) -> None:
        """Test that tokens are initially available."""
        assert ShopifyRateLimiter.get_available_tokens(merchant_id=1) == 2.0

    @pytest.mark.asyncio
    async def test_try_acquire_succeeds(self) -> None:
        """Test successful token acquisition."""
        result = await ShopifyRateLimiter.try_acquire(merchant_id=1)
        assert result is True
        tokens = ShopifyRateLimiter.get_available_tokens(merchant_id=1)
        assert 0.9 < tokens < 1.1  # Allow for floating point precision

    @pytest.mark.asyncio
    async def test_try_acquire_exhausts_bucket(self) -> None:
        """Test that bucket can be exhausted."""
        await ShopifyRateLimiter.try_acquire(merchant_id=1)
        await ShopifyRateLimiter.try_acquire(merchant_id=1)

        assert ShopifyRateLimiter.get_available_tokens(merchant_id=1) < 1.0

        result = await ShopifyRateLimiter.try_acquire(merchant_id=1)
        assert result is False

    @pytest.mark.asyncio
    async def test_acquire_waits_for_token(self) -> None:
        """Test that acquire waits for token availability."""
        await ShopifyRateLimiter.try_acquire(merchant_id=1)
        await ShopifyRateLimiter.try_acquire(merchant_id=1)

        start = time.time()
        result = await ShopifyRateLimiter.acquire(merchant_id=1, timeout=2.0)
        elapsed = time.time() - start

        assert result is True
        assert elapsed >= 0.5

    @pytest.mark.asyncio
    async def test_acquire_timeout_exceeded(self) -> None:
        """Test that acquire returns False on timeout."""
        await ShopifyRateLimiter.try_acquire(merchant_id=1)
        await ShopifyRateLimiter.try_acquire(merchant_id=1)

        start = time.time()
        result = await ShopifyRateLimiter.acquire(merchant_id=1, timeout=0.1)
        elapsed = time.time() - start

        assert result is False
        assert elapsed < 0.5

    @pytest.mark.asyncio
    async def test_per_merchant_isolation(self) -> None:
        """Test that merchants have separate buckets."""
        await ShopifyRateLimiter.try_acquire(merchant_id=1)
        await ShopifyRateLimiter.try_acquire(merchant_id=1)

        result = await ShopifyRateLimiter.try_acquire(merchant_id=1)
        assert result is False

        result2 = await ShopifyRateLimiter.try_acquire(merchant_id=2)
        assert result2 is True
        tokens = ShopifyRateLimiter.get_available_tokens(merchant_id=2)
        assert 0.9 < tokens < 1.1  # Allow for floating point precision

    @pytest.mark.asyncio
    async def test_tokens_refill_over_time(self) -> None:
        """Test that tokens refill over time."""
        await ShopifyRateLimiter.try_acquire(merchant_id=1)
        await ShopifyRateLimiter.try_acquire(merchant_id=1)

        assert ShopifyRateLimiter.get_available_tokens(merchant_id=1) < 0.1

        await asyncio.sleep(0.7)

        tokens = ShopifyRateLimiter.get_available_tokens(merchant_id=1)
        assert tokens >= 1.0

    def test_reset_specific_merchant(self) -> None:
        """Test resetting a specific merchant's bucket."""
        ShopifyRateLimiter.reset(merchant_id=1)

        assert ShopifyRateLimiter.get_available_tokens(merchant_id=1) == 2.0

    def test_reset_all_merchants(self) -> None:
        """Test resetting all buckets."""
        ShopifyRateLimiter.reset()

        assert len(ShopifyRateLimiter._buckets) == 0
