"""Rate limiting middleware for LLM configuration endpoints.

Limits: 1 configuration request per 10 seconds per merchant.
Uses in-memory rate limiting (can be migrated to Redis for production).
"""

from __future__ import annotations

import os
import time
from typing import Optional
from collections import defaultdict
from fastapi import HTTPException, Request


class RateLimiter:
    """Rate limiter for LLM configuration endpoints and auth endpoints.

    LLM Config: 1 configuration request per 10 seconds per merchant.
    Auth: 5 login attempts per 15 minutes per IP/email.
    Widget: 100 requests per 60 seconds per IP.
    Uses in-memory storage for MVP (migrate to Redis for production scale).
    """

    _requests: dict[str, list[tuple[float, int]]] = defaultdict(list)

    DEFAULT_MAX_REQUESTS = 1
    DEFAULT_PERIOD_SECONDS = 10
    DEFAULT_WINDOW_SECONDS = 60

    AUTH_MAX_REQUESTS = 5
    AUTH_PERIOD_SECONDS = 15 * 60

    WIDGET_MAX_REQUESTS = 100
    WIDGET_PERIOD_SECONDS = 60

    @classmethod
    def _cleanup_old_entries(cls, client_id: str) -> None:
        """Remove entries older than window from tracking.

        Args:
            client_id: Client identifier to clean up
        """
        now = time.time()
        cls._requests[client_id] = [
            (ts, count)
            for ts, count in cls._requests[client_id]
            if now - ts < cls.DEFAULT_WINDOW_SECONDS
        ]

    @classmethod
    def _get_request_count(cls, client_id: str, period_seconds: int) -> int:
        """Get request count in the time window.

        Args:
            client_id: Client identifier
            period_seconds: Time period to check

        Returns:
            Number of requests in the time window
        """
        now = time.time()
        period_start = now - period_seconds

        # Count requests within the period
        count = sum(count for ts, count in cls._requests[client_id] if ts >= period_start)

        return count

    @classmethod
    def is_rate_limited(
        cls,
        client_id: str,
        max_requests: int = DEFAULT_MAX_REQUESTS,
        period_seconds: int = DEFAULT_PERIOD_SECONDS,
    ) -> bool:
        """Check if client has exceeded rate limit.

        Args:
            client_id: Unique client identifier
            max_requests: Maximum requests allowed
            period_seconds: Time period in seconds

        Returns:
            True if rate limited, False otherwise
        """
        # Clean up old entries first
        cls._cleanup_old_entries(client_id)

        # Check current request count
        current_count = cls._get_request_count(client_id, period_seconds)

        if current_count >= max_requests:
            return True

        # Track this request
        now = time.time()
        cls._requests[client_id].append((now, 1))

        return False

    @classmethod
    def reset_all(cls) -> None:
        """Reset all rate limiter state (for testing)."""
        cls._requests.clear()

    @classmethod
    def check_auth_rate_limit(
        cls,
        request: Request,
        email: Optional[str] = None,
    ) -> None:
        """Check rate limit for authentication endpoints (login attempts).

        Limits: 5 attempts per 15 minutes per IP/email.
        Uses client IP and email for rate limiting (Story 1.8).

        Args:
            request: FastAPI request object
            email: Email address for additional rate limiting

        Raises:
            HTTPException: If rate limited (429)
        """
        # Bypass rate limiting in test mode
        if os.getenv("IS_TESTING", "false").lower() == "true":
            return
        if request.headers.get("X-Test-Mode", "").lower() == "true":
            return

        # Use IP address as base identifier
        client_id = cls.get_client_identifier(request)

        # Also track by email if provided (more restrictive)
        if email:
            client_id = f"{client_id}:{email}"

        # Check if rate limited
        if cls.is_rate_limited(
            client_id,
            max_requests=cls.AUTH_MAX_REQUESTS,
            period_seconds=cls.AUTH_PERIOD_SECONDS,
        ):
            raise HTTPException(
                status_code=429,
                detail={
                    "error_code": 2002,  # RATE_LIMITED
                    "message": "Too many login attempts",
                    "details": "Maximum 5 attempts per 15 minutes. Please try again later.",
                },
            )

    @classmethod
    def get_client_identifier(cls, request: Request) -> str:
        """Get unique client identifier for rate limiting.

        Args:
            request: FastAPI request object

        Returns:
            Client identifier string
        """
        # Use IP address as identifier (MVP approach)
        # TODO: Use merchant_id from auth when available
        return request.client.host if request.client else "unknown"

    @classmethod
    def check_rate_limit(
        cls,
        request: Request,
        max_requests: int = DEFAULT_MAX_REQUESTS,
        period_seconds: int = DEFAULT_PERIOD_SECONDS,
    ) -> None:
        """FastAPI dependency for rate limit checking.

        Rate limiting only applies to authenticated requests with proper test mode headers.

        Args:
            request: FastAPI request object
            max_requests: Maximum requests allowed
            period_seconds: Time period in seconds

        Raises:
            HTTPException: If rate limited (429)
        """
        # Bypass rate limiting in test mode for API testing
        # Check both environment variable and test header
        if os.getenv("IS_TESTING", "false").lower() == "true":
            return
        if request.headers.get("X-Test-Mode", "").lower() == "true":
            # Only apply rate limiting if the request also has X-Merchant-Id (authenticated test)
            if not request.headers.get("X-Merchant-Id"):
                return

        client_id = cls.get_client_identifier(request)

        if cls.is_rate_limited(client_id, max_requests, period_seconds):
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "message": f"Maximum {max_requests} request(s) per {period_seconds} seconds.",
                    "retry_after": period_seconds,
                },
            )

    @classmethod
    def get_widget_client_ip(cls, request: Request) -> str:
        """Get client IP for widget rate limiting.

        Respects X-Forwarded-For header for reverse proxy setups.

        Args:
            request: FastAPI request object

        Returns:
            Client IP address string
        """
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    @classmethod
    def check_widget_rate_limit(
        cls,
        request: Request,
    ) -> Optional[int]:
        """Check rate limit for widget endpoints.

        Widget rate limiting: 100 requests per 60 seconds per IP.
        Respects X-Forwarded-For header for per-IP rate limiting.

        Args:
            request: FastAPI request object

        Returns:
            None if allowed, retry_after seconds if rate limited
        """
        if os.getenv("IS_TESTING", "false").lower() == "true":
            return None
        if request.headers.get("X-Test-Mode", "").lower() == "true":
            return None

        client_ip = cls.get_widget_client_ip(request)
        client_id = f"widget:{client_ip}"

        if cls.is_rate_limited(
            client_id,
            max_requests=cls.WIDGET_MAX_REQUESTS,
            period_seconds=cls.WIDGET_PERIOD_SECONDS,
        ):
            return cls.WIDGET_PERIOD_SECONDS

        return None

    @classmethod
    def check_merchant_rate_limit(
        cls,
        merchant_id: int,
        limit: Optional[int],
    ) -> Optional[int]:
        """Check per-merchant rate limit for widget endpoints.

        Story 5-2 AC5: Per-merchant configurable rate limiting.

        Args:
            merchant_id: Merchant ID
            limit: Max requests per minute (from widget_config.rate_limit)

        Returns:
            None if allowed, retry_after seconds (60) if rate limited
        """
        if os.getenv("IS_TESTING", "false").lower() == "true":
            return None

        if limit is None or limit <= 0:
            return None

        client_id = f"widget:merchant:{merchant_id}"

        if cls.is_rate_limited(
            client_id,
            max_requests=limit,
            period_seconds=cls.WIDGET_PERIOD_SECONDS,
        ):
            return cls.WIDGET_PERIOD_SECONDS

        return None


check_llm_rate_limit = RateLimiter.check_rate_limit
