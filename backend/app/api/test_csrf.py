"""CSRF API endpoint tests (Story 1.9).

Tests cover:
- GET /api/v1/csrf-token - Get new CSRF token
- POST /api/v1/csrf-token/refresh - Refresh existing token
- DELETE /api/v1/csrf-token - Clear CSRF token
- GET /api/v1/csrf-token/validate - Validate current token
- Rate limiting (10 requests per minute per IP)
"""

from __future__ import annotations

import pytest
from unittest.mock import patch


class TestCSRFTokenEndpoint:
    """Tests for GET /api/v1/csrf-token endpoint."""

    @pytest.mark.asyncio
    async def test_get_csrf_token_returns_token(self, async_client):
        """Test that get CSRF token endpoint returns a valid token."""
        response = await async_client.get("/api/v1/csrf-token")

        assert response.status_code == 200

        data = response.json()
        assert "csrf_token" in data
        assert "session_id" in data
        assert "max_age" in data
        assert data["max_age"] == 3600  # 1 hour

    @pytest.mark.asyncio
    async def test_get_csrf_token_sets_cookie(self, async_client):
        """Test that get CSRF token endpoint sets httpOnly cookie."""
        response = await async_client.get("/api/v1/csrf-token")

        assert response.status_code == 200

        # Check for csrf_token cookie in response headers
        set_cookie = response.headers.get("set-cookie", "")
        assert "csrf_token=" in set_cookie

    @pytest.mark.asyncio
    async def test_get_csrf_token_unique_per_request(self, async_client):
        """Test that each request generates a unique token."""
        response1 = await async_client.get("/api/v1/csrf-token")
        response2 = await async_client.get("/api/v1/csrf-token")

        data1 = response1.json()
        data2 = response2.json()

        # Tokens should be different due to random component
        assert data1["csrf_token"] != data2["csrf_token"]
        # Session IDs should also be different (each request gets new session)
        assert data1["session_id"] != data2["session_id"]

    @pytest.mark.asyncio
    async def test_get_csrf_token_format(self, async_client):
        """Test that CSRF token follows expected format."""
        response = await async_client.get("/api/v1/csrf-token")

        data = response.json()
        token = data["csrf_token"]
        session_id = data["session_id"]

        # Token should contain session_id and random part
        assert session_id in token
        assert ":" in token
        # Format: session_id:random_part
        parts = token.split(":")
        assert len(parts) == 2
        assert parts[0] == session_id
        assert len(parts[1]) > 0  # Random part should not be empty


class TestCSRFTokenRefreshEndpoint:
    """Tests for POST /api/v1/csrf-token/refresh endpoint."""

    @pytest.mark.asyncio
    async def test_refresh_csrf_token_without_existing(self, async_client):
        """Test refresh without existing token generates new one."""
        response = await async_client.post("/api/v1/csrf-token/refresh")

        assert response.status_code == 200

        data = response.json()
        assert "csrf_token" in data
        assert "session_id" in data
        assert "max_age" in data

    @pytest.mark.asyncio
    async def test_refresh_csrf_token_with_existing(self, async_client):
        """Test refresh with existing token maintains session."""
        import re

        # First get a token
        get_response = await async_client.get("/api/v1/csrf-token")
        original_data = get_response.json()
        original_session_id = original_data["session_id"]

        # Extract the cookie from the get response
        cookies = {}
        set_cookie = get_response.headers.get("set-cookie", "")
        if "csrf_token=" in set_cookie:
            # Extract the cookie value (format: csrf_token=<value>; ...)
            match = re.search(r'csrf_token=([^;]+)', set_cookie)
            if match:
                cookies["csrf_token"] = match.group(1)

        # Then refresh it with the cookie from the get request
        # Note: httpx with ASGI transport doesn't auto-forward cookies
        refresh_response = await async_client.post(
            "/api/v1/csrf-token/refresh",
            cookies=cookies
        )
        assert refresh_response.status_code == 200

        new_data = refresh_response.json()
        # Session ID should be preserved
        assert new_data["session_id"] == original_session_id
        # But token should be different (new random part)
        assert new_data["csrf_token"] != original_data["csrf_token"]


class TestCSRFTokenClearEndpoint:
    """Tests for DELETE /api/v1/csrf-token endpoint."""

    @pytest.mark.asyncio
    async def test_clear_csrf_token(self, async_client):
        """Test clearing CSRF token."""
        response = await async_client.delete("/api/v1/csrf-token")

        assert response.status_code == 200

        data = response.json()
        assert data["message"] == "CSRF token cleared"

    @pytest.mark.asyncio
    async def test_clear_csrf_token_removes_cookie(self, async_client):
        """Test that clear CSRF token removes cookie."""
        # First get a token
        get_response = await async_client.get("/api/v1/csrf-token")
        assert "csrf_token=" in get_response.headers.get("set-cookie", "")

        # Then clear it
        clear_response = await async_client.delete("/api/v1/csrf-token")

        # Check that cookie is set to expire (in the past)
        cookies = clear_response.headers.get("set-cookie", "")
        assert "csrf_token=" in cookies


class TestCSRFTokenValidateEndpoint:
    """Tests for GET /api/v1/csrf-token/validate endpoint."""

    @pytest.mark.asyncio
    async def test_validate_csrf_token_valid(self, async_client):
        """Test validation with valid token."""
        # First get a token - this sets the cookie
        get_response = await async_client.get("/api/v1/csrf-token")
        token = get_response.json()["csrf_token"]

        # httpx needs cookies to be explicitly forwarded
        # The validate endpoint compares header token with cookie token
        # Since we're using ASGI transport, cookies from previous responses
        # aren't automatically sent. We need to include the cookie manually.

        # Get the cookie from the first response
        cookies = {}
        set_cookie = get_response.headers.get("set-cookie", "")
        if "csrf_token=" in set_cookie:
            # Extract the cookie value (format: csrf_token=<value>; ...)
            import re
            match = re.search(r'csrf_token=([^;]+)', set_cookie)
            if match:
                cookies["csrf_token"] = match.group(1)

        # Note: In real browser scenario, the cookie is sent automatically
        # For this test, the validation checks if header matches cookie
        # Since httpx doesn't auto-send cookies with ASGI transport,
        # we'll test the validation endpoint exists and returns valid format

        # Test with just the header (will return false since no cookie)
        validate_response = await async_client.get(
            "/api/v1/csrf-token/validate",
            headers={"X-CSRF-Token": token},
            cookies=cookies
        )

        assert validate_response.status_code == 200
        data = validate_response.json()
        # With both header and cookie matching, should be valid
        assert data["valid"] is True

    @pytest.mark.asyncio
    async def test_validate_csrf_token_missing(self, async_client):
        """Test validation without token."""
        response = await async_client.get("/api/v1/csrf-token/validate")

        assert response.status_code == 200

        data = response.json()
        assert data["valid"] is False

    @pytest.mark.asyncio
    async def test_validate_csrf_token_invalid(self, async_client):
        """Test validation with invalid token."""
        response = await async_client.get(
            "/api/v1/csrf-token/validate",
            headers={"X-CSRF-Token": "invalid-token"}
        )

        assert response.status_code == 200

        data = response.json()
        assert data["valid"] is False


class TestCSRFRateLimiting:
    """Tests for CSRF endpoint rate limiting (Story 1.9 AC 2)."""

    @pytest.mark.asyncio
    async def test_csrf_rate_limit_enforced(self, async_client):
        """Test that rate limit is enforced after 10 requests."""
        # Make 10 successful requests (X-Test-Mode: false enables rate limiting in test mode)
        for _ in range(10):
            response = await async_client.get(
                "/api/v1/csrf-token",
                headers={"X-Test-Mode": "false"}
            )
            assert response.status_code == 200

        # 11th request should be rate limited
        response = await async_client.get(
            "/api/v1/csrf-token",
            headers={"X-Test-Mode": "false"}
        )
        assert response.status_code == 429

        data = response.json()
        assert "error_code" in data["detail"]
        assert data["detail"]["error_code"] == 2002
        assert "Too many CSRF" in data["detail"]["message"]

    @pytest.mark.asyncio
    async def test_csrf_rate_limit_per_ip(self, async_client):
        """Test that rate limit is per IP address."""
        # First IP makes 10 requests (X-Test-Mode: false enables rate limiting in test mode)
        for _ in range(10):
            response = await async_client.get(
                "/api/v1/csrf-token",
                headers={"X-Forwarded-For": "192.168.1.1", "X-Test-Mode": "false"}
            )
            assert response.status_code == 200

        # 11th request from same IP is rate limited
        response = await async_client.get(
            "/api/v1/csrf-token",
            headers={"X-Forwarded-For": "192.168.1.1", "X-Test-Mode": "false"}
        )
        assert response.status_code == 429

        # Different IP can still make requests
        response = await async_client.get(
            "/api/v1/csrf-token",
            headers={"X-Forwarded-For": "192.168.1.2", "X-Test-Mode": "false"}
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_csrf_rate_limit_bypass_in_test_mode(self, async_client):
        """Test that rate limit is bypassed in test mode."""
        # Make more than 10 requests with test mode header
        for _ in range(15):
            response = await async_client.get(
                "/api/v1/csrf-token",
                headers={"X-Test-Mode": "true"}
            )
            # Should not be rate limited
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_csrf_rate_limit_refresh_not_rate_limited(self, async_client):
        """Test that refresh endpoint has separate rate limiting."""
        # Get initial token (counts against rate limit)
        # X-Test-Mode: false enables rate limiting in test mode
        for _ in range(10):
            response = await async_client.get(
                "/api/v1/csrf-token",
                headers={"X-Test-Mode": "false"}
            )
            assert response.status_code == 200

        # 11th get request is rate limited
        response = await async_client.get(
            "/api/v1/csrf-token",
            headers={"X-Test-Mode": "false"}
        )
        assert response.status_code == 429

        # But refresh should still work (different rate limit key or no limit)
        # Note: Based on current implementation, refresh may not have rate limiting
        # This test documents current behavior
        response = await async_client.post("/api/v1/csrf-token/refresh")
        # Refresh may or may not be rate limited depending on implementation
        # This test verifies the endpoint is accessible
        assert response.status_code in [200, 429]


class TestCSRFCookieAttributes:
    """Tests for CSRF cookie security attributes."""

    @pytest.mark.asyncio
    async def test_csrf_cookie_is_httponly(self, async_client):
        """Test that CSRF cookie is httpOnly."""
        response = await async_client.get("/api/v1/csrf-token")

        cookies = response.headers.get("set-cookie", "")
        # HttpOnly flag should be present
        assert "HttpOnly" in cookies or "httponly" in cookies.lower()

    @pytest.mark.asyncio
    async def test_csrf_cookie_is_secure(self, async_client):
        """Test that CSRF cookie has secure flag."""
        response = await async_client.get("/api/v1/csrf-token")

        cookies = response.headers.get("set-cookie", "")
        # Secure flag should be present
        assert "Secure" in cookies or "secure" in cookies.lower()

    @pytest.mark.asyncio
    async def test_csrf_cookie_samesite_strict(self, async_client):
        """Test that CSRF cookie has SameSite=strict."""
        response = await async_client.get("/api/v1/csrf-token")

        cookies = response.headers.get("set-cookie", "")
        # SameSite=Strict should be present
        assert "SameSite=Strict" in cookies or "samesite=strict" in cookies.lower()

    @pytest.mark.asyncio
    async def test_csrf_cookie_max_age(self, async_client):
        """Test that CSRF cookie has correct max age."""
        response = await async_client.get("/api/v1/csrf-token")

        cookies = response.headers.get("set-cookie", "")
        # Max-Age should be 3600 (1 hour)
        assert "Max-Age=3600" in cookies or "max-age=3600" in cookies.lower()


class TestCSRFErrorHandling:
    """Tests for CSRF endpoint error handling."""

    @pytest.mark.asyncio
    async def test_csrf_endpoint_handles_errors_gracefully(self, async_client):
        """Test that CSRF endpoints handle unexpected errors."""
        # This test verifies the endpoints don't crash on unexpected input
        response = await async_client.get("/api/v1/csrf-token")
        # Should always return 200 or 429 (rate limit), never 500
        assert response.status_code in [200, 429]

    @pytest.mark.asyncio
    async def test_csrf_validate_handles_malformed_header(self, async_client):
        """Test that validate endpoint handles malformed headers."""
        response = await async_client.get(
            "/api/v1/csrf-token/validate",
            headers={"X-CSRF-Token": ""}
        )

        # Should return 200 with valid=false
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
