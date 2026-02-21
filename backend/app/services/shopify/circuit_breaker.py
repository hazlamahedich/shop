"""Circuit breaker for Shopify API calls.

Story 5-10 Task 15: Prevent cascade failures when Shopify is slow/down.

Circuit breaker states:
- CLOSED (normal): Requests go through, failures are counted
- OPEN (failed): Requests fail fast with graceful message
- HALF_OPEN (recovering): Test requests to check recovery

Usage:
    from app.services.shopify.circuit_breaker import ShopifyCircuitBreaker

    try:
        result = await ShopifyCircuitBreaker.execute(
            merchant_id=merchant.id,
            func=my_shopify_call,
            arg1, arg2,
        )
    except CircuitOpenError:
        return fallback_response
"""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict
from enum import Enum
from typing import Any, Callable, Optional, TypeVar

import structlog


logger = structlog.get_logger(__name__)

T = TypeVar("T")


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitOpenError(Exception):
    """Raised when circuit is open and request is blocked."""

    def __init__(self, merchant_id: int, retry_after: float):
        self.merchant_id = merchant_id
        self.retry_after = retry_after
        super().__init__(
            f"Circuit breaker open for merchant {merchant_id}. "
            f"Retry after {retry_after:.1f} seconds."
        )


class ShopifyCircuitBreaker:
    """Circuit breaker for Shopify API calls.

    Prevents cascade failures when Shopify API is slow or down.
    Each merchant has their own circuit breaker to isolate failures.

    Configuration:
        FAILURE_THRESHOLD: Open after N consecutive failures
        RECOVERY_TIMEOUT: Seconds before attempting recovery
        SUCCESS_THRESHOLD: Close after N consecutive successes in half-open
    """

    _circuits: dict[int, dict] = defaultdict(
        lambda: {
            "state": CircuitState.CLOSED,
            "failure_count": 0,
            "success_count": 0,
            "last_failure_time": 0.0,
            "last_state_change": time.time(),
        }
    )

    FAILURE_THRESHOLD = 5
    RECOVERY_TIMEOUT = 60.0
    SUCCESS_THRESHOLD = 2
    LOCK: Optional[asyncio.Lock] = None

    @classmethod
    def _get_lock(cls) -> asyncio.Lock:
        """Get or create the global lock."""
        if cls.LOCK is None:
            cls.LOCK = asyncio.Lock()
        return cls.LOCK

    @classmethod
    def get_state(cls, merchant_id: int) -> CircuitState:
        """Get current circuit state for a merchant.

        Args:
            merchant_id: Merchant ID to check

        Returns:
            Current CircuitState
        """
        cls._update_state(merchant_id)
        return cls._circuits[merchant_id]["state"]

    @classmethod
    def _update_state(cls, merchant_id: int) -> None:
        """Update circuit state based on time elapsed.

        Transitions OPEN -> HALF_OPEN after RECOVERY_TIMEOUT.

        Args:
            merchant_id: Merchant ID to update
        """
        circuit = cls._circuits[merchant_id]
        now = time.time()

        if circuit["state"] == CircuitState.OPEN:
            time_since_open = now - circuit["last_failure_time"]
            if time_since_open >= cls.RECOVERY_TIMEOUT:
                circuit["state"] = CircuitState.HALF_OPEN
                circuit["success_count"] = 0
                circuit["last_state_change"] = now
                logger.info(
                    "circuit_half_open",
                    merchant_id=merchant_id,
                    recovery_timeout=cls.RECOVERY_TIMEOUT,
                )

    @classmethod
    async def execute(
        cls,
        merchant_id: int,
        func: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Execute a function with circuit breaker protection.

        Args:
            merchant_id: Merchant ID for circuit isolation
            func: Async function to execute
            *args: Arguments to pass to func
            **kwargs: Keyword arguments to pass to func

        Returns:
            Result of func(*args, **kwargs)

        Raises:
            CircuitOpenError: If circuit is open
            Exception: Re-raises any exception from func
        """
        async with cls._get_lock():
            cls._update_state(merchant_id)
            circuit = cls._circuits[merchant_id]

            if circuit["state"] == CircuitState.OPEN:
                retry_after = cls.RECOVERY_TIMEOUT - (time.time() - circuit["last_failure_time"])
                retry_after = max(0, retry_after)

                logger.warning(
                    "circuit_open_blocked",
                    merchant_id=merchant_id,
                    retry_after=retry_after,
                )
                raise CircuitOpenError(merchant_id, retry_after)

        try:
            result = await func(*args, **kwargs)

            async with cls._get_lock():
                cls._record_success(merchant_id)

            return result

        except Exception as e:
            async with cls._get_lock():
                cls._record_failure(merchant_id)
            raise

    @classmethod
    def _record_success(cls, merchant_id: int) -> None:
        """Record successful call and update state.

        Args:
            merchant_id: Merchant ID to record success for
        """
        circuit = cls._circuits[merchant_id]

        if circuit["state"] == CircuitState.HALF_OPEN:
            circuit["success_count"] += 1
            if circuit["success_count"] >= cls.SUCCESS_THRESHOLD:
                circuit["state"] = CircuitState.CLOSED
                circuit["failure_count"] = 0
                circuit["success_count"] = 0
                circuit["last_state_change"] = time.time()
                logger.info(
                    "circuit_closed",
                    merchant_id=merchant_id,
                    success_count=cls.SUCCESS_THRESHOLD,
                )

        elif circuit["state"] == CircuitState.CLOSED:
            circuit["failure_count"] = 0

    @classmethod
    def _record_failure(cls, merchant_id: int) -> None:
        """Record failed call and update state.

        Args:
            merchant_id: Merchant ID to record failure for
        """
        circuit = cls._circuits[merchant_id]
        now = time.time()

        if circuit["state"] == CircuitState.HALF_OPEN:
            circuit["state"] = CircuitState.OPEN
            circuit["last_failure_time"] = now
            circuit["last_state_change"] = now
            logger.warning(
                "circuit_reopened",
                merchant_id=merchant_id,
            )

        elif circuit["state"] == CircuitState.CLOSED:
            circuit["failure_count"] += 1
            circuit["last_failure_time"] = now

            if circuit["failure_count"] >= cls.FAILURE_THRESHOLD:
                circuit["state"] = CircuitState.OPEN
                circuit["last_state_change"] = now
                logger.error(
                    "circuit_opened",
                    merchant_id=merchant_id,
                    failure_count=circuit["failure_count"],
                    threshold=cls.FAILURE_THRESHOLD,
                )

    @classmethod
    def get_fallback_message(cls, merchant: Any) -> str:
        """Get user-friendly message when circuit is open.

        Args:
            merchant: Merchant with business_name and shop_domain

        Returns:
            Friendly message for the user
        """
        business_name = getattr(merchant, "business_name", None) or "our store"
        return (
            f"Our checkout system is experiencing high demand at {business_name}. "
            "Please try again in a moment, or visit our store directly."
        )

    @classmethod
    def get_fallback_url(cls, merchant: Any) -> Optional[str]:
        """Get fallback URL when circuit is open.

        Args:
            merchant: Merchant with shop_domain

        Returns:
            Fallback URL or None
        """
        shop_domain = getattr(merchant, "shop_domain", None)
        if shop_domain:
            return f"https://{shop_domain}"
        return None

    @classmethod
    def reset(cls, merchant_id: Optional[int] = None) -> None:
        """Reset circuit breaker state (for testing).

        Args:
            merchant_id: Specific merchant to reset, or None for all
        """
        if merchant_id is not None:
            if merchant_id in cls._circuits:
                del cls._circuits[merchant_id]
        else:
            cls._circuits.clear()

    @classmethod
    def get_metrics(cls, merchant_id: int) -> dict:
        """Get circuit breaker metrics for monitoring.

        Args:
            merchant_id: Merchant ID to get metrics for

        Returns:
            Dict with state, failure_count, etc.
        """
        cls._update_state(merchant_id)
        circuit = cls._circuits[merchant_id]
        return {
            "state": circuit["state"].value,
            "failure_count": circuit["failure_count"],
            "success_count": circuit["success_count"],
            "last_failure_time": circuit["last_failure_time"],
            "last_state_change": circuit["last_state_change"],
        }
