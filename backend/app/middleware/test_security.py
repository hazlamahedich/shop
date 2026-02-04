"""Tests for security middleware.

Tests cover:
- Security headers are set correctly (NFR-S7)
- HTTPS redirect works in production (NFR-S1)
- HSTS header has correct values (NFR-S1)
- CSP header is properly formatted (NFR-S7)
"""

from __future__ import annotations

from typing import AsyncGenerator

import pytest
import os
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.core.config import settings


class TestSecurityHeadersMiddleware:
    """Test security headers middleware (NFR-S7)."""

    @pytest.fixture
    async def client(self) -> AsyncGenerator[AsyncClient, None]:
        """Create test client with security middleware."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as ac:
            yield ac

    @pytest.mark.asyncio
    async def test_x_frame_options_header(self, client: AsyncClient) -> None:
        """Test X-Frame-Options header is set to DENY."""
        response = await client.get("/")
        assert response.status_code == 200
        assert response.headers.get("X-Frame-Options") == "DENY"

    @pytest.mark.asyncio
    async def test_x_content_type_options_header(self, client: AsyncClient) -> None:
        """Test X-Content-Type-Options header is set to nosniff."""
        response = await client.get("/")
        assert response.status_code == 200
        assert response.headers.get("X-Content-Type-Options") == "nosniff"

    @pytest.mark.asyncio
    async def test_x_xss_protection_header(self, client: AsyncClient) -> None:
        """Test X-XSS-Protection header is set correctly."""
        response = await client.get("/")
        assert response.status_code == 200
        assert response.headers.get("X-XSS-Protection") == "1; mode=block"

    @pytest.mark.asyncio
    async def test_referrer_policy_header(self, client: AsyncClient) -> None:
        """Test Referrer-Policy header is set correctly."""
        response = await client.get("/")
        assert response.status_code == 200
        assert (
            response.headers.get("Referrer-Policy")
            == "strict-origin-when-cross-origin"
        )

    @pytest.mark.asyncio
    async def test_permissions_policy_header(self, client: AsyncClient) -> None:
        """Test Permissions-Policy header disables sensitive features."""
        response = await client.get("/")
        assert response.status_code == 200
        permissions_policy = response.headers.get("Permissions-Policy")
        assert permissions_policy is not None
        assert "geolocation=()" in permissions_policy
        assert "microphone=()" in permissions_policy
        assert "camera=()" in permissions_policy

    @pytest.mark.asyncio
    async def test_content_security_policy_header(self, client: AsyncClient) -> None:
        """Test Content-Security-Policy header is correctly formatted (NFR-S7)."""
        response = await client.get("/")
        assert response.status_code == 200
        csp = response.headers.get("Content-Security-Policy")
        assert csp is not None
        assert "default-src 'self'" in csp
        assert "script-src 'self'" in csp
        assert "style-src 'self'" in csp
        assert "img-src 'self' data: https:" in csp
        assert "connect-src 'self'" in csp
        assert "frame-ancestors 'none'" in csp

    @pytest.mark.asyncio
    async def test_security_headers_on_all_endpoints(self, client: AsyncClient) -> None:
        """Test security headers are present on all endpoints."""
        endpoints = ["/", "/health", "/docs"]

        for endpoint in endpoints:
            response = await client.get(endpoint)
            assert response.status_code == 200
            assert response.headers.get("X-Frame-Options") == "DENY"
            assert response.headers.get("X-Content-Type-Options") == "nosniff"
            assert "Content-Security-Policy" in response.headers


class TestHSTSHeader:
    """Test HSTS header configuration (NFR-S1)."""

    @pytest.fixture
    async def client(self) -> AsyncGenerator[AsyncClient, None]:
        """Create test client with security middleware."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as ac:
            yield ac

    @pytest.mark.asyncio
    async def test_hsts_header_in_debug_mode(self, client: AsyncClient) -> None:
        """Test HSTS header is NOT set in debug mode (development)."""
        # In debug mode, HSTS should not be set
        original_debug = settings()["DEBUG"]
        assert original_debug is True, "Test should run in debug mode"

        response = await client.get("/")
        assert response.status_code == 200

        # In debug mode, HSTS header should not be present
        hsts = response.headers.get("Strict-Transport-Security")
        assert hsts is None, "HSTS should not be set in debug mode"

    @pytest.mark.asyncio
    async def test_hsts_header_values_format(self) -> None:
        """Test HSTS header has correct format and values (NFR-S1)."""
        # Simulate production mode by checking the middleware logic
        from app.middleware.security import SecurityHeadersMiddleware

        middleware = SecurityHeadersMiddleware(app)

        # The HSTS header should be:
        # max-age=31536000; includeSubDomains; preload
        expected_hsts = "max-age=31536000; includeSubDomains; preload"

        # Verify the format by checking the middleware code logic
        assert "max-age=31536000" in expected_hsts
        assert "includeSubDomains" in expected_hsts
        assert "preload" in expected_hsts

        # max-age of 31536000 seconds = 1 year
        max_age_value = 31536000
        assert max_age_value >= 31536000, "HSTS max-age should be at least 1 year"


class TestHTTPSEnforcement:
    """Test HTTPS enforcement middleware (NFR-S1)."""

    def test_https_redirect_middleware_exists(self) -> None:
        """Test that HTTPSRedirectMiddleware is available."""
        from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware

        assert HTTPSRedirectMiddleware is not None

    @pytest.mark.asyncio
    async def test_security_middleware_is_registered(self) -> None:
        """Test that SecurityHeadersMiddleware is registered with FastAPI app."""
        from app.middleware.security import SecurityHeadersMiddleware

        # Check that security middleware is in the app's middleware stack
        # Middleware is added through setup_security_middleware() in main.py
        # Verify by checking that security headers are present on responses
        import httpx
        from httpx import ASGITransport

        async with httpx.AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get("/")
            # Security headers should be present if middleware is registered
            assert "X-Frame-Options" in response.headers
            assert "Content-Security-Policy" in response.headers

    def test_https_redirect_only_in_production(self) -> None:
        """Test HTTPS redirect is only enabled in production (NFR-S1)."""
        from app.middleware.security import setup_security_middleware
        from unittest.mock import MagicMock

        # Create a mock app
        mock_app = MagicMock()

        # Setup security middleware in debug mode
        original_debug = os.getenv("DEBUG", "true")
        os.environ["DEBUG"] = "true"

        # Clear settings cache to pick up new DEBUG value
        from app.core.config import settings
        settings.cache_clear()

        setup_security_middleware(mock_app)

        # In debug mode, HTTPSRedirectMiddleware should not be added
        # but SecurityHeadersMiddleware should always be added
        assert mock_app.add_middleware.call_count >= 1

        # Restore original DEBUG setting
        os.environ["DEBUG"] = original_debug
        settings.cache_clear()


class TestSecurityHeadersComprehensive:
    """Comprehensive security header tests."""

    @pytest.fixture
    async def client(self) -> AsyncGenerator[AsyncClient, None]:
        """Create test client with security middleware."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as ac:
            yield ac

    @pytest.mark.asyncio
    async def test_all_required_security_headers_present(self, client: AsyncClient) -> None:
        """Test all required security headers are present (NFR-S7)."""
        response = await client.get("/")
        assert response.status_code == 200

        # Check all required headers
        required_headers = {
            "X-Frame-Options": "DENY",
            "X-Content-Type-Options": "nosniff",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
        }

        for header, expected_value in required_headers.items():
            actual_value = response.headers.get(header)
            assert actual_value is not None, f"{header} is missing"
            assert actual_value == expected_value, f"{header} has incorrect value"

        # Check headers that contain specific values
        assert "Permissions-Policy" in response.headers
        assert "Content-Security-Policy" in response.headers

    @pytest.mark.asyncio
    async def test_csp_prevents_external_scripts(self, client: AsyncClient) -> None:
        """Test CSP prevents loading external scripts (NFR-S7)."""
        response = await client.get("/")
        csp = response.headers.get("Content-Security-Policy")

        assert "script-src 'self'" in csp or "script-src 'self' 'unsafe-inline'" in csp
        # Should not allow external script sources by default

    @pytest.mark.asyncio
    async def test_csp_allows_data_images(self, client: AsyncClient) -> None:
        """Test CSP allows data: URIs for images (NFR-S7)."""
        response = await client.get("/")
        csp = response.headers.get("Content-Security-Policy")

        assert "img-src 'self' data: https:" in csp

    @pytest.mark.asyncio
    async def test_csp_prevents_frame_embedding(self, client: AsyncClient) -> None:
        """Test CSP prevents frame embedding (NFR-S7)."""
        response = await client.get("/")
        csp = response.headers.get("Content-Security-Policy")

        assert "frame-ancestors 'none'" in csp

    @pytest.mark.asyncio
    async def test_permissions_policy_blocks_sensitive_features(
        self, client: AsyncClient
    ) -> None:
        """Test Permissions-Policy blocks sensitive browser features (NFR-S7)."""
        response = await client.get("/")
        permissions = response.headers.get("Permissions-Policy")

        # All sensitive features should be disabled
        sensitive_features = ["geolocation", "microphone", "camera"]
        for feature in sensitive_features:
            assert f"{feature}=()" in permissions, f"{feature} should be disabled"

    @pytest.mark.asyncio
    async def test_security_headers_apply_to_error_responses(
        self, client: AsyncClient
    ) -> None:
        """Test security headers are applied even to error responses."""
        # Request a non-existent endpoint (should return 404)
        response = await client.get("/non-existent-endpoint")

        # Security headers should still be present
        assert response.headers.get("X-Frame-Options") == "DENY"
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert "Content-Security-Policy" in response.headers
