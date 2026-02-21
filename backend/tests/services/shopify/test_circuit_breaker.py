"""Tests for Shopify circuit breaker.

Story 5-10 Task 15: Circuit Breaker for Shopify

Tests all three circuit states (closed, open, half-open) and
state transitions.
"""

from __future__ import annotations

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.shopify.circuit_breaker import (
    CircuitOpenError,
    CircuitState,
    ShopifyCircuitBreaker,
)


@pytest.fixture(autouse=True)
def reset_circuit_breaker():
    """Reset circuit breaker state before each test."""
    ShopifyCircuitBreaker.reset()
    yield
    ShopifyCircuitBreaker.reset()


class TestCircuitBreakerStates:
    """Tests for circuit breaker state management."""

    def test_initial_state_is_closed(self):
        """Circuit should start in CLOSED state."""
        merchant_id = 1

        state = ShopifyCircuitBreaker.get_state(merchant_id)

        assert state == CircuitState.CLOSED

    def test_get_metrics_returns_state_info(self):
        """get_metrics should return circuit state details."""
        merchant_id = 1

        metrics = ShopifyCircuitBreaker.get_metrics(merchant_id)

        assert metrics["state"] == "closed"
        assert metrics["failure_count"] == 0
        assert "last_failure_time" in metrics
        assert "last_state_change" in metrics


class TestCircuitBreakerClosed:
    """Tests for CLOSED state behavior."""

    @pytest.mark.asyncio
    async def test_executes_function_when_closed(self):
        """Circuit should execute function when in CLOSED state."""
        merchant_id = 1

        async def success_func():
            return "success"

        result = await ShopifyCircuitBreaker.execute(
            merchant_id,
            success_func,
        )

        assert result == "success"

    @pytest.mark.asyncio
    async def test_passes_args_to_function(self):
        """Circuit should pass arguments to the wrapped function."""
        merchant_id = 1

        async def add_func(a, b):
            return a + b

        result = await ShopifyCircuitBreaker.execute(
            merchant_id,
            add_func,
            2,
            3,
        )

        assert result == 5

    @pytest.mark.asyncio
    async def test_passes_kwargs_to_function(self):
        """Circuit should pass keyword arguments to the wrapped function."""
        merchant_id = 1

        async def greet_func(name, greeting="Hello"):
            return f"{greeting}, {name}!"

        result = await ShopifyCircuitBreaker.execute(
            merchant_id,
            greet_func,
            "World",
            greeting="Hi",
        )

        assert result == "Hi, World!"

    @pytest.mark.asyncio
    async def test_counts_failures(self):
        """Circuit should count failures towards threshold."""
        merchant_id = 1

        async def failing_func():
            raise ValueError("Shopify error")

        for _ in range(3):
            with pytest.raises(ValueError):
                await ShopifyCircuitBreaker.execute(
                    merchant_id,
                    failing_func,
                )

        metrics = ShopifyCircuitBreaker.get_metrics(merchant_id)
        assert metrics["failure_count"] == 3

    @pytest.mark.asyncio
    async def test_success_resets_failure_count(self):
        """Successful call should reset failure count."""
        merchant_id = 1

        async def failing_func():
            raise ValueError("Shopify error")

        async def success_func():
            return "ok"

        for _ in range(3):
            with pytest.raises(ValueError):
                await ShopifyCircuitBreaker.execute(merchant_id, failing_func)

        metrics = ShopifyCircuitBreaker.get_metrics(merchant_id)
        assert metrics["failure_count"] == 3

        await ShopifyCircuitBreaker.execute(merchant_id, success_func)

        metrics = ShopifyCircuitBreaker.get_metrics(merchant_id)
        assert metrics["failure_count"] == 0


class TestCircuitBreakerOpen:
    """Tests for OPEN state behavior."""

    @pytest.mark.asyncio
    async def test_opens_after_failure_threshold(self):
        """Circuit should open after reaching failure threshold."""
        merchant_id = 1

        async def failing_func():
            raise ValueError("Shopify error")

        for _ in range(ShopifyCircuitBreaker.FAILURE_THRESHOLD):
            with pytest.raises(ValueError):
                await ShopifyCircuitBreaker.execute(merchant_id, failing_func)

        state = ShopifyCircuitBreaker.get_state(merchant_id)
        assert state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_blocks_requests_when_open(self):
        """Circuit should block requests when in OPEN state."""
        merchant_id = 1

        async def failing_func():
            raise ValueError("Shopify error")

        for _ in range(ShopifyCircuitBreaker.FAILURE_THRESHOLD):
            with pytest.raises(ValueError):
                await ShopifyCircuitBreaker.execute(merchant_id, failing_func)

        async def success_func():
            return "should not execute"

        with pytest.raises(CircuitOpenError) as exc_info:
            await ShopifyCircuitBreaker.execute(merchant_id, success_func)

        assert exc_info.value.merchant_id == merchant_id
        assert exc_info.value.retry_after > 0

    @pytest.mark.asyncio
    async def test_isolates_failures_per_merchant(self):
        """One merchant's circuit should not affect others."""
        merchant_1 = 1
        merchant_2 = 2

        async def failing_func():
            raise ValueError("Shopify error")

        for _ in range(ShopifyCircuitBreaker.FAILURE_THRESHOLD):
            with pytest.raises(ValueError):
                await ShopifyCircuitBreaker.execute(merchant_1, failing_func)

        assert ShopifyCircuitBreaker.get_state(merchant_1) == CircuitState.OPEN
        assert ShopifyCircuitBreaker.get_state(merchant_2) == CircuitState.CLOSED

        async def success_func():
            return "ok"

        result = await ShopifyCircuitBreaker.execute(merchant_2, success_func)
        assert result == "ok"


class TestCircuitBreakerHalfOpen:
    """Tests for HALF_OPEN state behavior."""

    @pytest.mark.asyncio
    async def test_transitions_to_half_open_after_timeout(self):
        """Circuit should transition to HALF_OPEN after recovery timeout."""
        merchant_id = 1
        ShopifyCircuitBreaker.RECOVERY_TIMEOUT = 0.1

        async def failing_func():
            raise ValueError("Shopify error")

        for _ in range(ShopifyCircuitBreaker.FAILURE_THRESHOLD):
            with pytest.raises(ValueError):
                await ShopifyCircuitBreaker.execute(merchant_id, failing_func)

        assert ShopifyCircuitBreaker.get_state(merchant_id) == CircuitState.OPEN

        await asyncio.sleep(0.15)

        ShopifyCircuitBreaker._update_state(merchant_id)
        assert ShopifyCircuitBreaker.get_state(merchant_id) == CircuitState.HALF_OPEN

    @pytest.mark.asyncio
    async def test_closes_after_success_threshold_in_half_open(self):
        """Circuit should close after enough successes in HALF_OPEN."""
        merchant_id = 1
        ShopifyCircuitBreaker.RECOVERY_TIMEOUT = 0.1
        ShopifyCircuitBreaker.SUCCESS_THRESHOLD = 2

        async def failing_func():
            raise ValueError("Shopify error")

        async def success_func():
            return "ok"

        for _ in range(ShopifyCircuitBreaker.FAILURE_THRESHOLD):
            with pytest.raises(ValueError):
                await ShopifyCircuitBreaker.execute(merchant_id, failing_func)

        await asyncio.sleep(0.15)

        for _ in range(ShopifyCircuitBreaker.SUCCESS_THRESHOLD):
            await ShopifyCircuitBreaker.execute(merchant_id, success_func)

        assert ShopifyCircuitBreaker.get_state(merchant_id) == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_reopens_on_failure_in_half_open(self):
        """Circuit should reopen if failure occurs in HALF_OPEN."""
        merchant_id = 1
        ShopifyCircuitBreaker.RECOVERY_TIMEOUT = 0.1

        async def failing_func():
            raise ValueError("Shopify error")

        for _ in range(ShopifyCircuitBreaker.FAILURE_THRESHOLD):
            with pytest.raises(ValueError):
                await ShopifyCircuitBreaker.execute(merchant_id, failing_func)

        await asyncio.sleep(0.15)

        with pytest.raises(ValueError):
            await ShopifyCircuitBreaker.execute(merchant_id, failing_func)

        assert ShopifyCircuitBreaker.get_state(merchant_id) == CircuitState.OPEN


class TestCircuitOpenError:
    """Tests for CircuitOpenError exception."""

    def test_contains_merchant_id(self):
        """Error should contain merchant ID."""
        error = CircuitOpenError(merchant_id=42, retry_after=30.0)

        assert error.merchant_id == 42

    def test_contains_retry_after(self):
        """Error should contain retry_after duration."""
        error = CircuitOpenError(merchant_id=1, retry_after=45.5)

        assert error.retry_after == 45.5

    def test_has_descriptive_message(self):
        """Error should have descriptive message."""
        error = CircuitOpenError(merchant_id=1, retry_after=60.0)

        assert "circuit breaker open" in str(error).lower()
        assert "1" in str(error)
        assert "60" in str(error)


class TestFallbackHelpers:
    """Tests for fallback message helpers."""

    def test_get_fallback_message_with_business_name(self):
        """Should use business name in fallback message."""
        merchant = MagicMock()
        merchant.business_name = "Acme Store"

        message = ShopifyCircuitBreaker.get_fallback_message(merchant)

        assert "Acme Store" in message
        assert "high demand" in message.lower()

    def test_get_fallback_message_without_business_name(self):
        """Should use default name when no business name."""
        merchant = MagicMock()
        merchant.business_name = None

        message = ShopifyCircuitBreaker.get_fallback_message(merchant)

        assert "our store" in message

    def test_get_fallback_url_with_domain(self):
        """Should return URL with shop domain."""
        merchant = MagicMock()
        merchant.shop_domain = "acme.myshopify.com"

        url = ShopifyCircuitBreaker.get_fallback_url(merchant)

        assert url == "https://acme.myshopify.com"

    def test_get_fallback_url_without_domain(self):
        """Should return None when no domain."""
        merchant = MagicMock()
        merchant.shop_domain = None

        url = ShopifyCircuitBreaker.get_fallback_url(merchant)

        assert url is None


class TestReset:
    """Tests for reset functionality."""

    @pytest.mark.asyncio
    async def test_reset_specific_merchant(self):
        """Reset should only affect specified merchant."""
        merchant_1 = 1
        merchant_2 = 2

        async def failing_func():
            raise ValueError("error")

        for _ in range(ShopifyCircuitBreaker.FAILURE_THRESHOLD):
            with pytest.raises(ValueError):
                await ShopifyCircuitBreaker.execute(merchant_1, failing_func)

        ShopifyCircuitBreaker.reset(merchant_1)

        assert ShopifyCircuitBreaker.get_state(merchant_1) == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_reset_all_merchants(self):
        """Reset without ID should clear all circuits."""
        merchant_1 = 1
        merchant_2 = 2

        async def failing_func():
            raise ValueError("error")

        for mid in [merchant_1, merchant_2]:
            for _ in range(ShopifyCircuitBreaker.FAILURE_THRESHOLD):
                with pytest.raises(ValueError):
                    await ShopifyCircuitBreaker.execute(mid, failing_func)

        ShopifyCircuitBreaker.reset()

        assert ShopifyCircuitBreaker.get_state(merchant_1) == CircuitState.CLOSED
        assert ShopifyCircuitBreaker.get_state(merchant_2) == CircuitState.CLOSED


class TestCascadeFailurePrevention:
    """Integration tests for cascade failure prevention."""

    @pytest.mark.asyncio
    async def test_prevents_cascade_failures(self):
        """Circuit should prevent cascade of failed requests."""
        merchant_id = 1
        call_count = 0

        async def failing_func():
            nonlocal call_count
            call_count += 1
            raise ValueError("Shopify down")

        for _ in range(ShopifyCircuitBreaker.FAILURE_THRESHOLD):
            with pytest.raises(ValueError):
                await ShopifyCircuitBreaker.execute(merchant_id, failing_func)

        initial_calls = call_count

        for _ in range(10):
            with pytest.raises(CircuitOpenError):
                await ShopifyCircuitBreaker.execute(merchant_id, failing_func)

        assert call_count == initial_calls
