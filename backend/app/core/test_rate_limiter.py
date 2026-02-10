"""Unit tests for rate limiting module.

Tests cover:
- IP-based rate limiting for authentication
- Email-based rate limiting for authentication
- Combined IP + email rate limiting
- Rate limit cleanup
- Reset functionality
"""

from __future__ import annotations

import os
import pytest
import time
from unittest.mock import Mock, patch

from fastapi import HTTPException, status, Request

from app.core.rate_limiter import (
    RateLimiter,
    check_auth_rate_limit,
    check_llm_rate_limit,
)


class TestAuthRateLimiting:
    """Tests for authentication rate limiting (AC 7)."""

    def setup_method(self):
        """Reset rate limiter state before each test."""
        RateLimiter._auth_attempts.clear()

    def test_auth_max_attempts_config(self):
        """Should have correct max attempts configuration."""
        assert RateLimiter.AUTH_MAX_ATTEMPTS == 5

    def test_auth_period_config(self):
        """Should have 15 minute period configuration."""
        assert RateLimiter.AUTH_PERIOD_SECONDS == 15 * 60

    @pytest.mark.parametrize("email,ip_address", [
        ("test@example.com", "127.0.0.1"),
        ("test@example.com", None),
        (None, "127.0.0.1"),
    ])
    def test_is_auth_rate_limited_returns_false_initially(self, email, ip_address):
        """Should not be rate limited initially."""
        result = RateLimiter.is_auth_rate_limited(email=email, ip_address=ip_address)
        assert result is False

    def test_is_auth_rate_limited_tracks_ip_attempts(self):
        """Should track IP-based attempts."""
        # Make 5 attempts (at the limit)
        for _ in range(5):
            RateLimiter.is_auth_rate_limited(ip_address="192.168.1.1")

        # 6th attempt should be rate limited
        result = RateLimiter.is_auth_rate_limited(ip_address="192.168.1.1")
        assert result is True

    def test_is_auth_rate_limited_tracks_email_attempts(self):
        """Should track email-based attempts."""
        # Make 5 attempts (at the limit)
        for _ in range(5):
            RateLimiter.is_auth_rate_limited(email="test@example.com")

        # 6th attempt should be rate limited
        result = RateLimiter.is_auth_rate_limited(email="test@example.com")
        assert result is True

    def test_is_auth_rate_limited_combined_tracking(self):
        """Should track both IP and email independently."""
        # Reset state first
        RateLimiter._auth_attempts.clear()

        # Make 3 attempts from one IP with different emails
        # Note: We need to check the return value - False means NOT rate limited yet
        RateLimiter.is_auth_rate_limited(email="user1@example.com", ip_address="192.168.1.1")
        RateLimiter.is_auth_rate_limited(email="user2@example.com", ip_address="192.168.1.1")
        RateLimiter.is_auth_rate_limited(email="user3@example.com", ip_address="192.168.1.1")

        # IP is not rate limited yet (3 < 5)
        assert RateLimiter.is_auth_rate_limited(email="user4@example.com", ip_address="192.168.1.1") is False

        # Make 2 more attempts with same email from different IPs
        # user1@example.com now has 1 + 2 = 3 attempts
        RateLimiter.is_auth_rate_limited(email="user1@example.com", ip_address="192.168.1.2")
        RateLimiter.is_auth_rate_limited(email="user1@example.com", ip_address="192.168.1.3")

        # user1@example.com now has 3 attempts total, need 2 more to hit limit
        assert RateLimiter.is_auth_rate_limited(email="user1@example.com", ip_address="192.168.1.4") is False
        assert RateLimiter.is_auth_rate_limited(email="user1@example.com", ip_address="192.168.1.5") is False

        # Now user1@example.com has 5 attempts, should be rate limited
        assert RateLimiter.is_auth_rate_limited(email="user1@example.com", ip_address="192.168.1.6") is True

        # But a different email from the same IP should still work (192.168.1.1 has 4 attempts)
        assert RateLimiter.is_auth_rate_limited(email="user5@example.com", ip_address="192.168.1.1") is False

    def test_is_auth_rate_limited_different_ips_separate(self):
        """Different IPs should have separate rate limits."""
        # Make 5 attempts from IP1
        for _ in range(5):
            RateLimiter.is_auth_rate_limited(ip_address="192.168.1.1")

        # IP1 should be rate limited
        assert RateLimiter.is_auth_rate_limited(ip_address="192.168.1.1") is True

        # IP2 should not be rate limited
        assert RateLimiter.is_auth_rate_limited(ip_address="192.168.1.2") is False

    def test_is_auth_rate_limited_different_emails_separate(self):
        """Different emails should have separate rate limits."""
        # Make 5 attempts for email1
        for _ in range(5):
            RateLimiter.is_auth_rate_limited(email="user1@example.com")

        # email1 should be rate limited
        assert RateLimiter.is_auth_rate_limited(email="user1@example.com") is True

        # email2 should not be rate limited
        assert RateLimiter.is_auth_rate_limited(email="user2@example.com") is False

    def test_cleanup_auth_attempts_removes_old(self):
        """Should cleanup old auth attempts."""
        # Add some old attempts (by manually manipulating storage)
        old_time = time.time() - RateLimiter.AUTH_WINDOW_SECONDS - 100
        RateLimiter._auth_attempts["ip:192.168.1.1"] = [old_time, old_time, old_time]

        # Cleanup should remove old entries
        RateLimiter._cleanup_auth_attempts("ip:192.168.1.1")
        assert len(RateLimiter._auth_attempts["ip:192.168.1.1"]) == 0

    def test_get_auth_attempt_count(self):
        """Should count attempts within time window."""
        now = time.time()

        # Add attempts at different times
        RateLimiter._auth_attempts["ip:192.168.1.1"] = [
            now - 100,  # Within 15 minutes
            now - 200,  # Within 15 minutes
            now - 1000, # Outside 15 minutes (older than 900 seconds)
        ]

        count = RateLimiter._get_auth_attempt_count("ip:192.168.1.1")
        assert count == 2

    def test_reset_auth_attempts_by_email(self):
        """Should reset attempts for specific email."""
        # Make some attempts
        for _ in range(3):
            RateLimiter.is_auth_rate_limited(email="test@example.com")

        # Verify tracked
        assert len(RateLimiter._auth_attempts["email:test@example.com"]) == 3

        # Reset
        RateLimiter.reset_auth_attempts(email="test@example.com")

        # Should be cleared
        assert "email:test@example.com" not in RateLimiter._auth_attempts

    def test_reset_auth_attempts_by_ip(self):
        """Should reset attempts for specific IP."""
        # Make some attempts
        for _ in range(3):
            RateLimiter.is_auth_rate_limited(ip_address="192.168.1.1")

        # Verify tracked
        assert len(RateLimiter._auth_attempts["ip:192.168.1.1"]) == 3

        # Reset
        RateLimiter.reset_auth_attempts(ip_address="192.168.1.1")

        # Should be cleared
        assert "ip:192.168.1.1" not in RateLimiter._auth_attempts


class TestAuthRateLimitDependency:
    """Tests for check_auth_rate_limit FastAPI dependency."""

    def setup_method(self):
        """Reset rate limiter state before each test."""
        RateLimiter._auth_attempts.clear()

    def test_check_auth_rate_limit_passes_initially(self):
        """Should pass initial attempt."""
        request = Mock(spec=Request)
        request.client = Mock(host="192.168.1.1")
        request.headers = {}

        # Should not raise
        RateLimiter.check_auth_rate_limit(request, email="test@example.com")

    def test_check_auth_rate_limit_raises_when_limited(self, monkeypatch):
        """Should raise 429 when rate limited."""
        # Disable IS_TESTING for this test to enable rate limiting
        monkeypatch.setenv("IS_TESTING", "false")

        request = Mock(spec=Request)
        request.client = Mock(host="192.168.1.1")
        request.headers = {}

        # Reset state first
        RateLimiter._auth_attempts.clear()

        # Make 5 attempts (at the limit)
        # When is_auth_rate_limited returns False, it tracks the attempt
        for _ in range(5):
            result = RateLimiter.is_auth_rate_limited(email="test@example.com", ip_address="192.168.1.1")
            assert result is False, f"Attempt {_+1} should not be rate limited yet"

        # Next check should raise because we're at the limit
        with pytest.raises(HTTPException) as exc:
            RateLimiter.check_auth_rate_limit(request, email="test@example.com")

        assert exc.value.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert exc.value.detail["error_code"] == 2011
        assert "Too many login attempts" in exc.value.detail["message"]

    def test_check_auth_rate_limit_bypasses_in_test_mode_env(self):
        """Should bypass rate limiting when IS_TESTING=true."""
        request = Mock(spec=Request)
        request.client = Mock(host="192.168.1.1")
        request.headers = {}

        # Make 5 attempts (at the limit)
        for _ in range(5):
            RateLimiter.is_auth_rate_limited(email="test@example.com", ip_address="192.168.1.1")

        # Should not raise in test mode
        with patch.dict(os.environ, {"IS_TESTING": "true"}):
            RateLimiter.check_auth_rate_limit(request, email="test@example.com")

    def test_check_auth_rate_limit_bypasses_with_test_header(self):
        """Should bypass rate limiting with X-Test-Mode header."""
        request = Mock(spec=Request)
        request.client = Mock(host="192.168.1.1")
        request.headers = {"X-Test-Mode": "true"}

        # Make 5 attempts (at the limit)
        for _ in range(5):
            RateLimiter.is_auth_rate_limited(email="test@example.com", ip_address="192.168.1.1")

        # Should not raise with test header
        RateLimiter.check_auth_rate_limit(request, email="test@example.com")


class TestLLMRateLimiting:
    """Tests for LLM configuration rate limiting (existing functionality)."""

    def setup_method(self):
        """Reset rate limiter state before each test."""
        RateLimiter._requests.clear()

    def test_llm_max_requests_config(self):
        """Should have correct max requests configuration."""
        assert RateLimiter.DEFAULT_MAX_REQUESTS == 1

    def test_llm_period_config(self):
        """Should have 10 second period configuration."""
        assert RateLimiter.DEFAULT_PERIOD_SECONDS == 10

    def test_is_rate_limited_returns_false_initially(self):
        """Should not be rate limited initially."""
        result = RateLimiter.is_rate_limited("client-123")
        assert result is False

    def test_is_rate_limited_tracks_requests(self):
        """Should track requests per client."""
        # First request should pass
        assert RateLimiter.is_rate_limited("client-123") is False

        # Second immediate request should be rate limited
        assert RateLimiter.is_rate_limited("client-123") is True

    def test_is_rate_limited_different_clients_separate(self):
        """Different clients should have separate rate limits."""
        # Client 1 makes a request
        assert RateLimiter.is_rate_limited("client-1") is False

        # Client 2 should not be affected
        assert RateLimiter.is_rate_limited("client-2") is False

    def test_get_client_identifier_from_request(self):
        """Should extract IP from request."""
        request = Mock(spec=Request)
        request.client = Mock(host="192.168.1.100")

        client_id = RateLimiter.get_client_identifier(request)
        assert client_id == "192.168.1.100"

    def test_get_client_identifier_unknown_when_no_client(self):
        """Should return 'unknown' when request has no client."""
        request = Mock(spec=Request)
        request.client = None

        client_id = RateLimiter.get_client_identifier(request)
        assert client_id == "unknown"

    def test_cleanup_old_entries(self):
        """Should cleanup old request entries."""
        # Add old entries manually
        old_time = time.time() - RateLimiter.DEFAULT_WINDOW_SECONDS - 10
        RateLimiter._requests["client-123"] = [(old_time, 1), (old_time, 1)]

        # Cleanup should remove them
        RateLimiter._cleanup_old_entries("client-123")
        assert len(RateLimiter._requests["client-123"]) == 0


class TestRateLimitConstants:
    """Tests for rate limiting configuration constants."""

    def test_auth_constants_match_ac7(self):
        """Auth rate limits should match AC 7 requirements."""
        # AC 7: 5 attempts per 15 minutes
        assert RateLimiter.AUTH_MAX_ATTEMPTS == 5
        assert RateLimiter.AUTH_PERIOD_SECONDS == 15 * 60  # 15 minutes
        assert RateLimiter.AUTH_WINDOW_SECONDS == 16 * 60  # 16 minutes for cleanup

    def test_llm_constants_match_requirements(self):
        """LLM rate limits should match requirements."""
        # 1 request per 10 seconds
        assert RateLimiter.DEFAULT_MAX_REQUESTS == 1
        assert RateLimiter.DEFAULT_PERIOD_SECONDS == 10


class TestRateLimitDependencyExports:
    """Tests for exported dependency functions."""

    def test_check_llm_rate_limit_exported(self):
        """check_llm_rate_limit should be exported and callable."""
        assert callable(check_llm_rate_limit)
        # Verify it's the same method by checking it works the same way
        assert check_llm_rate_limit.__name__ == "check_rate_limit"

    def test_check_auth_rate_limit_exported(self):
        """check_auth_rate_limit should be exported and callable."""
        assert callable(check_auth_rate_limit)
        # Verify it's the same method by checking it works the same way
        assert check_auth_rate_limit.__name__ == "check_auth_rate_limit"
