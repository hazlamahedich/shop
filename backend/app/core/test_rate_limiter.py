"""Unit tests for rate limiting module.

Tests cover:
- IP-based rate limiting for authentication
- Email-based rate limiting for authentication
- Combined IP + email rate limiting
- Rate limit cleanup
- Reset functionality
- Widget rate limiting
- Widget analytics rate limiting
- LLM configuration rate limiting
"""

from __future__ import annotations

import os
import time
from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException, Request, status

from app.core.rate_limiter import (
    RateLimiter,
)


class TestAuthRateLimiting:
    """Tests for authentication rate limiting (AC 7)."""

    def setup_method(self):
        RateLimiter._requests.clear()

    def test_auth_max_requests_config(self):
        assert RateLimiter.AUTH_MAX_REQUESTS == 5

    def test_auth_period_config(self):
        assert RateLimiter.AUTH_PERIOD_SECONDS == 15 * 60

    def test_auth_not_limited_initially(self):
        assert (
            RateLimiter.is_rate_limited(
                "auth:ip:192.168.1.1",
                max_requests=RateLimiter.AUTH_MAX_REQUESTS,
                period_seconds=RateLimiter.AUTH_PERIOD_SECONDS,
            )
            is False
        )

    def test_auth_tracks_ip_attempts(self):
        client_id = "auth:ip:192.168.1.1"
        for _ in range(5):
            RateLimiter.is_rate_limited(
                client_id,
                max_requests=RateLimiter.AUTH_MAX_REQUESTS,
                period_seconds=RateLimiter.AUTH_PERIOD_SECONDS,
            )

        assert (
            RateLimiter.is_rate_limited(
                client_id,
                max_requests=RateLimiter.AUTH_MAX_REQUESTS,
                period_seconds=RateLimiter.AUTH_PERIOD_SECONDS,
            )
            is True
        )

    def test_auth_tracks_email_attempts(self):
        client_id = "auth:email:test@example.com"
        for _ in range(5):
            RateLimiter.is_rate_limited(
                client_id,
                max_requests=RateLimiter.AUTH_MAX_REQUESTS,
                period_seconds=RateLimiter.AUTH_PERIOD_SECONDS,
            )

        assert (
            RateLimiter.is_rate_limited(
                client_id,
                max_requests=RateLimiter.AUTH_MAX_REQUESTS,
                period_seconds=RateLimiter.AUTH_PERIOD_SECONDS,
            )
            is True
        )

    def test_auth_different_ips_separate(self):
        for _ in range(5):
            RateLimiter.is_rate_limited(
                "auth:ip:192.168.1.1",
                max_requests=RateLimiter.AUTH_MAX_REQUESTS,
                period_seconds=RateLimiter.AUTH_PERIOD_SECONDS,
            )

        assert (
            RateLimiter.is_rate_limited(
                "auth:ip:192.168.1.1",
                max_requests=RateLimiter.AUTH_MAX_REQUESTS,
                period_seconds=RateLimiter.AUTH_PERIOD_SECONDS,
            )
            is True
        )

        assert (
            RateLimiter.is_rate_limited(
                "auth:ip:192.168.1.2",
                max_requests=RateLimiter.AUTH_MAX_REQUESTS,
                period_seconds=RateLimiter.AUTH_PERIOD_SECONDS,
            )
            is False
        )

    def test_auth_different_emails_separate(self):
        for _ in range(5):
            RateLimiter.is_rate_limited(
                "auth:email:user1@example.com",
                max_requests=RateLimiter.AUTH_MAX_REQUESTS,
                period_seconds=RateLimiter.AUTH_PERIOD_SECONDS,
            )

        assert (
            RateLimiter.is_rate_limited(
                "auth:email:user1@example.com",
                max_requests=RateLimiter.AUTH_MAX_REQUESTS,
                period_seconds=RateLimiter.AUTH_PERIOD_SECONDS,
            )
            is True
        )

        assert (
            RateLimiter.is_rate_limited(
                "auth:email:user2@example.com",
                max_requests=RateLimiter.AUTH_MAX_REQUESTS,
                period_seconds=RateLimiter.AUTH_PERIOD_SECONDS,
            )
            is False
        )

    def test_auth_combined_ip_email(self):
        combined_id = "192.168.1.1:user1@example.com"
        for _ in range(5):
            RateLimiter.is_rate_limited(
                combined_id,
                max_requests=RateLimiter.AUTH_MAX_REQUESTS,
                period_seconds=RateLimiter.AUTH_PERIOD_SECONDS,
            )

        assert (
            RateLimiter.is_rate_limited(
                combined_id,
                max_requests=RateLimiter.AUTH_MAX_REQUESTS,
                period_seconds=RateLimiter.AUTH_PERIOD_SECONDS,
            )
            is True
        )

        assert (
            RateLimiter.is_rate_limited(
                "192.168.1.1:user2@example.com",
                max_requests=RateLimiter.AUTH_MAX_REQUESTS,
                period_seconds=RateLimiter.AUTH_PERIOD_SECONDS,
            )
            is False
        )


class TestAuthRateLimitDependency:
    """Tests for check_auth_rate_limit FastAPI dependency."""

    def setup_method(self):
        RateLimiter._requests.clear()

    def test_check_auth_rate_limit_passes_initially(self):
        request = Mock(spec=Request)
        request.client = Mock(host="192.168.1.1")
        request.headers = {}

        with patch.dict(os.environ, {"IS_TESTING": "false"}):
            RateLimiter.check_auth_rate_limit(request, email="test@example.com")

    def test_check_auth_rate_limit_raises_when_limited(self, monkeypatch):
        monkeypatch.setenv("IS_TESTING", "false")

        request = Mock(spec=Request)
        request.client = Mock(host="192.168.1.1")
        request.headers = {}

        RateLimiter._requests.clear()

        client_id = "192.168.1.1:test@example.com"
        for _ in range(5):
            RateLimiter.is_rate_limited(
                client_id,
                max_requests=RateLimiter.AUTH_MAX_REQUESTS,
                period_seconds=RateLimiter.AUTH_PERIOD_SECONDS,
            )

        with pytest.raises(HTTPException) as exc:
            RateLimiter.check_auth_rate_limit(request, email="test@example.com")

        assert exc.value.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert exc.value.detail["error_code"] == 2002
        assert "Too many login attempts" in exc.value.detail["message"]

    def test_check_auth_rate_limit_bypasses_in_test_mode_env(self):
        request = Mock(spec=Request)
        request.client = Mock(host="192.168.1.1")
        request.headers = {}

        with patch.dict(os.environ, {"IS_TESTING": "true"}):
            RateLimiter.check_auth_rate_limit(request, email="test@example.com")

    def test_check_auth_rate_limit_bypasses_with_test_header(self):
        request = Mock(spec=Request)
        request.client = Mock(host="192.168.1.1")
        request.headers = {"X-Test-Mode": "true"}

        with patch.dict(os.environ, {"IS_TESTING": "false"}):
            RateLimiter.check_auth_rate_limit(request, email="test@example.com")

    def test_check_auth_rate_limit_without_email(self):
        request = Mock(spec=Request)
        request.client = Mock(host="10.0.0.1")
        request.headers = {}

        with patch.dict(os.environ, {"IS_TESTING": "false"}):
            RateLimiter.check_auth_rate_limit(request)

    def test_check_auth_rate_limit_uses_ip_only_when_no_email(self, monkeypatch):
        monkeypatch.setenv("IS_TESTING", "false")

        request = Mock(spec=Request)
        request.client = Mock(host="10.0.0.99")
        request.headers = {}

        RateLimiter._requests.clear()

        for _ in range(5):
            RateLimiter.is_rate_limited(
                "10.0.0.99",
                max_requests=RateLimiter.AUTH_MAX_REQUESTS,
                period_seconds=RateLimiter.AUTH_PERIOD_SECONDS,
            )

        with pytest.raises(HTTPException):
            RateLimiter.check_auth_rate_limit(request)


class TestLLMRateLimiting:
    """Tests for LLM configuration rate limiting (existing functionality)."""

    def setup_method(self):
        RateLimiter._requests.clear()

    def test_llm_max_requests_config(self):
        assert RateLimiter.DEFAULT_MAX_REQUESTS == 1

    def test_llm_period_config(self):
        assert RateLimiter.DEFAULT_PERIOD_SECONDS == 10

    def test_is_rate_limited_returns_false_initially(self):
        result = RateLimiter.is_rate_limited("client-123")
        assert result is False

    def test_is_rate_limited_tracks_requests(self):
        assert RateLimiter.is_rate_limited("client-123") is False
        assert RateLimiter.is_rate_limited("client-123") is True

    def test_is_rate_limited_different_clients_separate(self):
        assert RateLimiter.is_rate_limited("client-1") is False
        assert RateLimiter.is_rate_limited("client-2") is False

    def test_get_client_identifier_from_request(self):
        request = Mock(spec=Request)
        request.client = Mock(host="192.168.1.100")

        client_id = RateLimiter.get_client_identifier(request)
        assert client_id == "192.168.1.100"

    def test_get_client_identifier_unknown_when_no_client(self):
        request = Mock(spec=Request)
        request.client = None

        client_id = RateLimiter.get_client_identifier(request)
        assert client_id == "unknown"

    def test_cleanup_old_entries(self):
        old_time = time.time() - RateLimiter.DEFAULT_WINDOW_SECONDS - 10
        RateLimiter._requests["client-123"] = [(old_time, 1), (old_time, 1)]

        RateLimiter._cleanup_old_entries("client-123")
        assert len(RateLimiter._requests["client-123"]) == 0

    def test_get_request_count_within_period(self):
        now = time.time()
        RateLimiter._requests["client-count"] = [
            (now - 5, 1),
            (now - 8, 1),
            (now - 100, 1),
        ]

        count = RateLimiter._get_request_count("client-count", period_seconds=10)
        assert count == 2

    def test_reset_all(self):
        RateLimiter._requests["client-a"] = [(time.time(), 1)]
        RateLimiter._requests["client-b"] = [(time.time(), 1)]

        RateLimiter.reset_all()

        assert len(RateLimiter._requests) == 0


class TestWidgetRateLimiting:
    """Tests for widget rate limiting."""

    def setup_method(self):
        RateLimiter._requests.clear()

    def test_widget_not_limited_initially(self):
        request = Mock(spec=Request)
        request.client = Mock(host="10.0.0.1")
        request.headers = {}

        with patch.dict(os.environ, {"IS_TESTING": "false"}):
            result = RateLimiter.check_widget_rate_limit(request)
        assert result is None

    def test_widget_limited_after_max_requests(self, monkeypatch):
        monkeypatch.setenv("IS_TESTING", "false")

        request = Mock(spec=Request)
        request.client = Mock(host="10.0.0.1")
        request.headers = {}

        for _ in range(RateLimiter.WIDGET_MAX_REQUESTS):
            RateLimiter.is_rate_limited(
                "widget:10.0.0.1",
                max_requests=RateLimiter.WIDGET_MAX_REQUESTS,
                period_seconds=RateLimiter.WIDGET_PERIOD_SECONDS,
            )

        result = RateLimiter.check_widget_rate_limit(request)
        assert result == RateLimiter.WIDGET_PERIOD_SECONDS

    def test_widget_bypasses_in_test_mode(self):
        request = Mock(spec=Request)
        request.client = Mock(host="10.0.0.1")
        request.headers = {}

        with patch.dict(os.environ, {"IS_TESTING": "true"}):
            result = RateLimiter.check_widget_rate_limit(request)
        assert result is None

    def test_widget_respects_forwarded_for(self):
        request = Mock(spec=Request)
        request.client = Mock(host="10.0.0.1")
        request.headers = {"X-Forwarded-For": "1.2.3.4, 5.6.7.8"}

        with patch.dict(os.environ, {"IS_TESTING": "false"}):
            ip = RateLimiter.get_widget_client_ip(request)
        assert ip == "1.2.3.4"


class TestWidgetAnalyticsRateLimiting:
    """Tests for widget analytics rate limiting (Story 9-10)."""

    def setup_method(self):
        RateLimiter._requests.clear()

    def test_analytics_not_limited_initially(self):
        request = Mock(spec=Request)
        request.client = Mock(host="10.0.0.1")
        request.headers = {}

        with patch.dict(os.environ, {"IS_TESTING": "false"}):
            result = RateLimiter.check_widget_analytics_rate_limit(
                request, session_id="session-123"
            )
        assert result is None

    def test_analytics_limited_after_max_events(self, monkeypatch):
        monkeypatch.setenv("IS_TESTING", "false")

        request = Mock(spec=Request)
        request.client = Mock(host="10.0.0.1")
        request.headers = {}

        client_id = "widget_analytics:session-123"
        for _ in range(RateLimiter.WIDGET_ANALYTICS_MAX_EVENTS):
            RateLimiter.is_rate_limited(
                client_id,
                max_requests=RateLimiter.WIDGET_ANALYTICS_MAX_EVENTS,
                period_seconds=RateLimiter.WIDGET_ANALYTICS_PERIOD_SECONDS,
            )

        result = RateLimiter.check_widget_analytics_rate_limit(request, session_id="session-123")
        assert result == RateLimiter.WIDGET_ANALYTICS_PERIOD_SECONDS


class TestMerchantRateLimiting:
    """Tests for per-merchant rate limiting (Story 5-2 AC5)."""

    def setup_method(self):
        RateLimiter._requests.clear()

    def test_merchant_not_limited_when_no_limit(self):
        with patch.dict(os.environ, {"IS_TESTING": "false"}):
            result = RateLimiter.check_merchant_rate_limit(merchant_id=1, limit=None)
        assert result is None

    def test_merchant_not_limited_when_zero_limit(self):
        with patch.dict(os.environ, {"IS_TESTING": "false"}):
            result = RateLimiter.check_merchant_rate_limit(merchant_id=1, limit=0)
        assert result is None

    def test_merchant_limited_after_max_requests(self, monkeypatch):
        monkeypatch.setenv("IS_TESTING", "false")

        for _ in range(10):
            RateLimiter.is_rate_limited(
                "widget:merchant:42",
                max_requests=10,
                period_seconds=RateLimiter.WIDGET_PERIOD_SECONDS,
            )

        result = RateLimiter.check_merchant_rate_limit(merchant_id=42, limit=10)
        assert result == RateLimiter.WIDGET_PERIOD_SECONDS


class TestCheckRateLimitDependency:
    """Tests for check_rate_limit (LLM) dependency."""

    def setup_method(self):
        RateLimiter._requests.clear()

    def test_check_rate_limit_passes_initially(self):
        request = Mock(spec=Request)
        request.client = Mock(host="10.0.0.1")
        request.headers = {}

        with patch.dict(os.environ, {"IS_TESTING": "false"}):
            RateLimiter.check_rate_limit(request)

    def test_check_rate_limit_raises_when_limited(self, monkeypatch):
        monkeypatch.setenv("IS_TESTING", "false")

        request = Mock(spec=Request)
        request.client = Mock(host="10.0.0.2")
        request.headers = {}

        RateLimiter.is_rate_limited("10.0.0.2")

        with pytest.raises(HTTPException) as exc:
            RateLimiter.check_rate_limit(request)

        assert exc.value.status_code == 429

    def test_check_rate_limit_bypasses_in_test_mode(self):
        request = Mock(spec=Request)
        request.client = Mock(host="10.0.0.1")
        request.headers = {}

        with patch.dict(os.environ, {"IS_TESTING": "true"}):
            RateLimiter.check_rate_limit(request)

    def test_check_rate_limit_bypasses_with_test_header_no_merchant(self):
        request = Mock(spec=Request)
        request.client = Mock(host="10.0.0.1")
        request.headers = {"X-Test-Mode": "true"}

        with patch.dict(os.environ, {"IS_TESTING": "false"}):
            RateLimiter.check_rate_limit(request)


class TestRateLimitConstants:
    """Tests for rate limiting configuration constants."""

    def test_auth_constants_match_ac7(self):
        assert RateLimiter.AUTH_MAX_REQUESTS == 5
        assert RateLimiter.AUTH_PERIOD_SECONDS == 15 * 60

    def test_llm_constants_match_requirements(self):
        assert RateLimiter.DEFAULT_MAX_REQUESTS == 1
        assert RateLimiter.DEFAULT_PERIOD_SECONDS == 10

    def test_widget_constants(self):
        assert RateLimiter.WIDGET_MAX_REQUESTS == 100
        assert RateLimiter.WIDGET_PERIOD_SECONDS == 60

    def test_widget_analytics_constants(self):
        assert RateLimiter.WIDGET_ANALYTICS_MAX_EVENTS == 100
        assert RateLimiter.WIDGET_ANALYTICS_PERIOD_SECONDS == 60


class TestRateLimitDependencyExports:
    """Tests for exported dependency functions."""

    def test_check_llm_rate_limit_is_classmethod(self):
        assert callable(RateLimiter.check_rate_limit)
        assert RateLimiter.check_rate_limit.__name__ == "check_rate_limit"

    def test_check_auth_rate_limit_is_classmethod(self):
        assert callable(RateLimiter.check_auth_rate_limit)
        assert RateLimiter.check_auth_rate_limit.__name__ == "check_auth_rate_limit"

    def test_check_llm_rate_limit_module_alias(self):
        from app.core.rate_limiter import check_llm_rate_limit

        assert check_llm_rate_limit.__func__ is RateLimiter.check_rate_limit.__func__
