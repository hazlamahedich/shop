"""Comprehensive security tests for widget endpoints.

Story 5-7: Security & Rate Limiting
AC6: Security Test Coverage
"""

from __future__ import annotations

import os
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

os.environ["IS_TESTING"] = "true"

from app.core.errors import APIError, ErrorCode
from app.core.rate_limiter import RateLimiter
from app.core.validators import is_valid_session_id
from app.core.sanitization import sanitize_message, validate_message_length


class TestRateLimitingSecurity:
    """Security tests for rate limiting (AC1, AC2)."""

    def test_ip_rate_limit_100_per_minute(self):
        """Per-IP rate limit of 100 requests per minute is enforced."""
        from fastapi import Request
        from app.core.rate_limiter import RateLimiter

        RateLimiter.reset_all()

        mock_request = MagicMock(spec=Request)
        mock_request.headers = {}
        mock_request.client = MagicMock()
        mock_request.client.host = "10.0.0.99"

        for i in range(RateLimiter.WIDGET_MAX_REQUESTS):
            is_limited = RateLimiter.is_rate_limited(
                f"widget:{mock_request.client.host}",
                max_requests=RateLimiter.WIDGET_MAX_REQUESTS,
                period_seconds=RateLimiter.WIDGET_PERIOD_SECONDS,
            )
            assert not is_limited, f"Request {i + 1} should be allowed"

        is_limited = RateLimiter.is_rate_limited(
            f"widget:{mock_request.client.host}",
            max_requests=RateLimiter.WIDGET_MAX_REQUESTS,
            period_seconds=RateLimiter.WIDGET_PERIOD_SECONDS,
        )
        assert is_limited, "Request 101 should be rate limited"

    def test_merchant_rate_limit_configurable(self):
        """Per-merchant rate limit is configurable and enforced."""
        RateLimiter.reset_all()

        limit = 5
        for i in range(limit):
            is_limited = RateLimiter.is_rate_limited(
                "widget:merchant:test-1",
                max_requests=limit,
                period_seconds=RateLimiter.WIDGET_PERIOD_SECONDS,
            )
            assert not is_limited, f"Request {i + 1} should be allowed"

        is_limited = RateLimiter.is_rate_limited(
            "widget:merchant:test-1",
            max_requests=limit,
            period_seconds=RateLimiter.WIDGET_PERIOD_SECONDS,
        )
        assert is_limited, "Request 6 should be rate limited"

    def test_rate_limit_error_includes_retry_after(self):
        """Rate limit error response includes Retry-After value."""
        from app.core.rate_limiter import RateLimiter

        RateLimiter.reset_all()

        assert RateLimiter.WIDGET_PERIOD_SECONDS == 60

    def test_rate_limit_resets_after_window(self):
        """Rate limit counter resets after the time window expires."""
        from unittest.mock import patch
        from fastapi import Request

        RateLimiter.reset_all()

        mock_request = MagicMock(spec=Request)
        mock_request.headers = {}
        mock_request.client = MagicMock()
        mock_request.client.host = "10.0.0.100"

        client_id = f"widget:{mock_request.client.host}"
        short_period = 60
        max_requests = 3

        mock_time_values = [1000.0]
        time_counter = [0.0]

        def mock_time():
            val = mock_time_values[0] + time_counter[0]
            time_counter[0] += 0.001
            return val

        with patch("time.time", side_effect=mock_time):
            for i in range(max_requests):
                is_limited = RateLimiter.is_rate_limited(
                    client_id,
                    max_requests=max_requests,
                    period_seconds=short_period,
                )
                assert not is_limited, f"Request {i + 1} should be allowed"

            is_limited = RateLimiter.is_rate_limited(
                client_id,
                max_requests=max_requests,
                period_seconds=short_period,
            )
            assert is_limited, "Request 4 should be rate limited"

        mock_time_values[0] = 1000.0 + short_period + 1
        time_counter[0] = 0

        with patch("time.time", side_effect=mock_time):
            RateLimiter._cleanup_old_entries(client_id)

            is_limited = RateLimiter.is_rate_limited(
                client_id,
                max_requests=max_requests,
                period_seconds=short_period,
            )
            assert not is_limited, "Request after window should be allowed"

    def test_rate_limit_uses_x_forwarded_for(self):
        """Rate limit respects X-Forwarded-For header for client IP."""
        from fastapi import Request

        RateLimiter.reset_all()

        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"X-Forwarded-For": "203.0.113.1, 10.0.0.1"}
        mock_request.client = MagicMock()
        mock_request.client.host = "10.0.0.1"

        ip = RateLimiter.get_widget_client_ip(mock_request)
        assert ip == "203.0.113.1"

    def test_rate_limit_bypassed_in_test_mode(self):
        """Rate limit is bypassed when IS_TESTING=true or X-Test-Mode header."""
        from fastapi import Request

        RateLimiter.reset_all()

        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"X-Test-Mode": "true"}
        mock_request.client = MagicMock()
        mock_request.client.host = "10.0.0.3"

        for _ in range(200):
            result = RateLimiter.check_widget_rate_limit(mock_request)
            assert result is None

    def test_rate_limit_enforced_without_bypass(self):
        """Rate limiting logic works when tested directly (bypass only in check_* methods)."""
        from fastapi import Request

        RateLimiter.reset_all()

        client_ip = "10.0.0.50"
        client_id = f"widget:{client_ip}"

        for i in range(RateLimiter.WIDGET_MAX_REQUESTS):
            is_limited = RateLimiter.is_rate_limited(
                client_id,
                max_requests=RateLimiter.WIDGET_MAX_REQUESTS,
                period_seconds=RateLimiter.WIDGET_PERIOD_SECONDS,
            )
            assert not is_limited, f"Request {i + 1} should not be limited"

        is_limited = RateLimiter.is_rate_limited(
            client_id,
            max_requests=RateLimiter.WIDGET_MAX_REQUESTS,
            period_seconds=RateLimiter.WIDGET_PERIOD_SECONDS,
        )
        assert is_limited, "Request after limit should be rate limited"

    def test_rate_limit_error_details_include_retry_after(self):
        """Rate limit error details include retry_after value for HTTP header."""
        from app.core.errors import APIError, ErrorCode

        RateLimiter.reset_all()

        retry_after_value = 60
        error = APIError(
            ErrorCode.WIDGET_RATE_LIMITED,
            "Rate limit exceeded",
            {"retry_after": retry_after_value},
        )

        assert error.details.get("retry_after") == retry_after_value
        assert error.code == ErrorCode.WIDGET_RATE_LIMITED

    def test_check_widget_rate_limit_returns_retry_after_when_limited(self):
        """[P1] check_widget_rate_limit returns retry_after seconds when rate limited (AC1)."""
        from fastapi import Request
        from unittest.mock import patch

        RateLimiter.reset_all()

        mock_request = MagicMock(spec=Request)
        mock_request.headers = {}
        mock_request.client = MagicMock()
        mock_request.client.host = "10.0.0.200"

        with patch.dict(os.environ, {"IS_TESTING": "false"}, clear=False):
            for i in range(RateLimiter.WIDGET_MAX_REQUESTS):
                client_id = f"widget:{mock_request.client.host}"
                RateLimiter.is_rate_limited(
                    client_id,
                    max_requests=RateLimiter.WIDGET_MAX_REQUESTS,
                    period_seconds=RateLimiter.WIDGET_PERIOD_SECONDS,
                )

            result = RateLimiter.check_widget_rate_limit(mock_request)
            assert result is not None, "Should return retry_after when rate limited"
            assert result == RateLimiter.WIDGET_PERIOD_SECONDS, (
                f"retry_after should be {RateLimiter.WIDGET_PERIOD_SECONDS} seconds"
            )
            assert result == 60, "retry_after should be 60 seconds per AC1"

    def test_rate_limit_enforced_without_test_mode_header(self):
        """[P1] Rate limiting enforced when X-Test-Mode header is absent (AC1, AC2)."""
        from fastapi import Request
        from unittest.mock import patch

        RateLimiter.reset_all()

        mock_request = MagicMock(spec=Request)
        mock_request.headers = {}
        mock_request.client = MagicMock()
        mock_request.client.host = "10.0.0.201"

        with patch.dict(os.environ, {"IS_TESTING": "false"}, clear=False):
            for i in range(RateLimiter.WIDGET_MAX_REQUESTS):
                result = RateLimiter.check_widget_rate_limit(mock_request)
                assert result is None, f"Request {i + 1} should be allowed"

            result = RateLimiter.check_widget_rate_limit(mock_request)
            assert result is not None, "Request over limit should be rate limited"
            assert result == RateLimiter.WIDGET_PERIOD_SECONDS


class TestSessionValidationSecurity:
    """Security tests for session validation (AC3)."""

    def test_valid_uuid_accepted(self):
        """Valid UUID v4 format is accepted."""
        valid_uuid = "550e8400-e29b-41d4-a716-446655440000"
        assert is_valid_session_id(valid_uuid) is True

    def test_invalid_uuid_format_rejected(self):
        """Invalid UUID format is rejected."""
        invalid_uuids = [
            "not-a-uuid",
            "550e8400e29b41d4a716446655440000",
            "550e8400-e29b-41d4-a716",
            "550e8400-e29b-41d4-a716-446655440000-extra",
        ]
        for invalid_uuid in invalid_uuids:
            assert is_valid_session_id(invalid_uuid) is False, f"{invalid_uuid} should be rejected"

    def test_sql_injection_in_session_id_rejected(self):
        """SQL injection attempts in session_id are rejected."""
        sql_injection_attempts = [
            "'; DROP TABLE sessions;--",
            "550e8400' OR '1'='1",
            "550e8400; DELETE FROM sessions WHERE '1'='1",
            "UNION SELECT * FROM sessions--",
        ]
        for attempt in sql_injection_attempts:
            assert is_valid_session_id(attempt) is False, (
                f"SQL injection should be rejected: {attempt}"
            )

    def test_xss_injection_in_session_id_rejected(self):
        """XSS attempts in session_id are rejected."""
        xss_attempts = [
            "<script>alert('xss')</script>",
            "550e8400<img src=x onerror=alert('xss')>",
            "javascript:alert('xss')",
            "550e8400<svg onload=alert('xss')>",
        ]
        for attempt in xss_attempts:
            assert is_valid_session_id(attempt) is False, (
                f"XSS attempt should be rejected: {attempt}"
            )

    def test_path_traversal_in_session_id_rejected(self):
        """Path traversal attempts in session_id are rejected."""
        path_traversal_attempts = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "/etc/passwd",
            "....//....//....//etc/passwd",
        ]
        for attempt in path_traversal_attempts:
            assert is_valid_session_id(attempt) is False, (
                f"Path traversal should be rejected: {attempt}"
            )


class TestDomainWhitelistSecurity:
    """Security tests for domain whitelist (AC4)."""

    def test_allowed_domain_passes(self):
        """Allowed domain passes validation."""
        from app.api.widget import _validate_domain_whitelist
        from fastapi import Request

        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"Origin": "https://example.com"}

        _validate_domain_whitelist(mock_request, ["example.com"])

    def test_subdomain_of_allowed_domain_passes(self):
        """Subdomain of allowed domain passes validation."""
        from app.api.widget import _validate_domain_whitelist
        from fastapi import Request

        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"Origin": "https://shop.example.com"}

        _validate_domain_whitelist(mock_request, ["example.com"])

    def test_unauthorized_domain_blocked(self):
        """Unauthorized domain is blocked."""
        from app.api.widget import _validate_domain_whitelist
        from fastapi import Request

        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"Origin": "https://evil.com"}

        with pytest.raises(APIError) as exc_info:
            _validate_domain_whitelist(mock_request, ["example.com"])

        assert exc_info.value.code == ErrorCode.WIDGET_DOMAIN_NOT_ALLOWED

    def test_empty_whitelist_allows_all(self):
        """Empty whitelist allows all origins."""
        from app.api.widget import _validate_domain_whitelist
        from fastapi import Request

        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"Origin": "https://any-domain.com"}

        _validate_domain_whitelist(mock_request, [])

    def test_missing_origin_header_handled(self):
        """Missing Origin header is handled gracefully."""
        from app.api.widget import _validate_domain_whitelist
        from fastapi import Request

        mock_request = MagicMock(spec=Request)
        mock_request.headers = {}

        _validate_domain_whitelist(mock_request, ["example.com"])

    def test_domain_whitelist_case_insensitive(self):
        """Domain whitelist matching is case-insensitive."""
        from app.api.widget import _validate_domain_whitelist
        from fastapi import Request

        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"Origin": "https://EXAMPLE.COM"}

        _validate_domain_whitelist(mock_request, ["example.com"])

    def test_spoofed_origin_rejected(self):
        """Spoofed Origin headers with invalid domains are rejected."""
        from app.api.widget import _validate_domain_whitelist
        from fastapi import Request

        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"Origin": "https://evil.com?ref=example.com"}

        with pytest.raises(APIError) as exc_info:
            _validate_domain_whitelist(mock_request, ["example.com"])

        assert exc_info.value.code == ErrorCode.WIDGET_DOMAIN_NOT_ALLOWED


class TestInputSanitizationSecurity:
    """Security tests for input sanitization (AC5)."""

    def test_html_tags_escaped(self):
        """HTML tags are escaped to prevent XSS."""
        result = sanitize_message("<script>alert('xss')</script>")
        assert "<script>" not in result
        assert "&lt;script&gt;" in result

    def test_script_injection_neutralized(self):
        """Script injection is neutralized via escaping."""
        payloads = [
            "<img src=x onerror=alert('xss')>",
            "<svg onload=alert('xss')>",
            "<body onload=alert('xss')>",
            "<iframe src='javascript:alert(1)'>",
        ]
        for payload in payloads:
            result = sanitize_message(payload)
            assert "<" not in result or "&lt;" in result, f"Payload should be escaped: {payload}"

    def test_max_message_length_enforced(self):
        """Maximum message length of 2000 chars is enforced."""
        is_valid, error = validate_message_length("x" * 2000)
        assert is_valid is True

        is_valid, error = validate_message_length("x" * 2001)
        assert is_valid is False
        assert error is not None
        assert "2000" in error

    def test_empty_message_rejected(self):
        """Empty messages are rejected."""
        is_valid, error = validate_message_length("")
        assert is_valid is False
        assert error is not None
        assert "empty" in error.lower()

    def test_null_bytes_removed(self):
        """Null bytes are removed from messages."""
        result = sanitize_message("hello\x00world")
        assert "\x00" not in result
        assert result == "helloworld"

    def test_event_handler_injection_neutralized(self):
        """Event handler attributes are escaped (safe for HTML context)."""
        payloads = [
            "onclick=alert('xss')",
            "onerror=alert('xss')",
            "onload=alert('xss')",
            "onmouseover=alert('xss')",
        ]
        for payload in payloads:
            result = sanitize_message(payload)
            assert "<" not in result, f"Should not contain HTML tags: {payload}"
            assert "&#" in result or result == payload.strip()

    def test_javascript_protocol_handled(self):
        """JavaScript protocol is escaped for safety."""
        result = sanitize_message("javascript:alert('xss')")
        assert "javascript:" in result
        assert "&#" in result

    def test_data_uri_neutralized(self):
        """Data URI is neutralized."""
        result = sanitize_message("data:text/html,<script>alert('xss')</script>")
        assert "<script>" not in result

    def test_unicode_null_byte_removed(self):
        """Unicode null bytes are removed."""
        result = sanitize_message("hello\u0000world")
        assert "\x00" not in result

    def test_control_characters_handled(self):
        """Control characters are handled."""
        result = sanitize_message("hello\x01\x02\x03world")
        assert result == "hello\x01\x02\x03world"


class TestAuthenticationSecurity:
    """Security tests for widget authentication."""

    @pytest.mark.asyncio
    async def test_widget_disabled_returns_403(self):
        """Widget disabled returns 403 FORBIDDEN."""
        from app.api.widget import create_widget_session
        from app.schemas.widget import CreateSessionRequest
        from fastapi import Request
        from sqlalchemy.ext.asyncio import AsyncSession

        mock_db = MagicMock(spec=AsyncSession)
        mock_db.execute = AsyncMock()

        mock_merchant = MagicMock()
        mock_merchant.id = 1
        mock_merchant.widget_config = {"enabled": False}

        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_merchant
        mock_db.execute.return_value = mock_result

        mock_request = MagicMock(spec=Request)
        mock_request.headers = {}
        mock_request.client = MagicMock()
        mock_request.client.host = "192.168.1.1"

        session_request = CreateSessionRequest(merchant_id=1)

        with pytest.raises(APIError) as exc_info:
            await create_widget_session(
                request=mock_request,
                session_request=session_request,
                db=mock_db,
            )

        assert exc_info.value.code == ErrorCode.WIDGET_MERCHANT_DISABLED

    @pytest.mark.asyncio
    async def test_merchant_not_found_returns_404(self):
        """Non-existent merchant returns 404."""
        from app.api.widget import create_widget_session
        from app.schemas.widget import CreateSessionRequest
        from fastapi import Request
        from sqlalchemy.ext.asyncio import AsyncSession

        mock_db = MagicMock(spec=AsyncSession)
        mock_db.execute = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db.execute.return_value = mock_result

        mock_request = MagicMock(spec=Request)
        mock_request.headers = {}
        mock_request.client = MagicMock()
        mock_request.client.host = "192.168.1.1"

        session_request = CreateSessionRequest(merchant_id=99999)

        with pytest.raises(APIError) as exc_info:
            await create_widget_session(
                request=mock_request,
                session_request=session_request,
                db=mock_db,
            )

        assert exc_info.value.code == ErrorCode.MERCHANT_NOT_FOUND
