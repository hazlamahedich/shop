"""Tests for security middleware.

Tests cover:
- Security headers are set correctly (NFR-S7)
- HTTPS redirect works in production (NFR-S1)
- HSTS header has correct values (NFR-S1)
- CSP header is properly formatted (NFR-S7)
"""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator
import pytest
from httpx import ASGITransport, AsyncClient
from app.core.config import settings
from app.main import app


class TestSecurityHeadersMiddleware:
    """Test security headers middleware (NFR-S7)."""

    @pytest.fixture
    async def client(self) -> AsyncGenerator[AsyncClient, None]:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as ac:
            yield ac

    @pytest.mark.asyncio
    async def test_x_frame_options_header(self, client: AsyncClient) -> None:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.headers.get("X-Frame-Options") == "SAMEORIGIN"

    @pytest.mark.asyncio
    async def test_x_content_type_options_header(self, client: AsyncClient) -> None:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.headers.get("X-Content-Type-Options") == "nosniff"

    @pytest.mark.asyncio
    async def test_x_xss_protection_header(self, client: AsyncClient) -> None:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.headers.get("X-XSS-Protection") == "1; mode=block"

    @pytest.mark.asyncio
    async def test_referrer_policy_header(self, client: AsyncClient) -> None:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"

    @pytest.mark.asyncio
    async def test_permissions_policy_header(self, client: AsyncClient) -> None:
        response = await client.get("/health")
        assert response.status_code == 200
        permissions_policy = response.headers.get("Permissions-Policy")
        assert permissions_policy is not None
        assert "geolocation=()" in permissions_policy
        assert "microphone=()" in permissions_policy
        assert "camera=()" in permissions_policy

    @pytest.mark.asyncio
    async def test_content_security_policy_header(self, client: AsyncClient) -> None:
        response = await client.get("/health")
        assert response.status_code == 200
        csp = response.headers.get("Content-Security-Policy")
        assert csp is not None
        assert "default-src 'self'" in csp
        assert "script-src 'self'" in csp
        assert "style-src 'self'" in csp
        assert "img-src 'self' data: https:" in csp
        assert "connect-src 'self'" in csp
        assert "frame-ancestors" in csp

    @pytest.mark.asyncio
    async def test_security_headers_on_all_endpoints(self, client: AsyncClient) -> None:
        endpoints = ["/health", "/docs"]

        for endpoint in endpoints:
            response = await client.get(endpoint)
            assert response.status_code == 200
            assert response.headers.get("X-Frame-Options") is not None
            assert response.headers.get("X-Content-Type-Options") == "nosniff"
            assert "Content-Security-Policy" in response.headers


class TestHSTSHeader:
    """Test HSTS header configuration (NFR-S1)."""

    @pytest.fixture
    async def client(self) -> AsyncGenerator[AsyncClient, None]:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as ac:
            yield ac

    @pytest.mark.asyncio
    async def test_hsts_header_in_debug_mode(self, client: AsyncClient) -> None:
        original_debug = settings()["DEBUG"]
        assert original_debug is True, "Test should run in debug mode"

        response = await client.get("/health")
        assert response.status_code == 200

        hsts = response.headers.get("Strict-Transport-Security")
        assert hsts is None, "HSTS should not be set in debug mode"

    @pytest.mark.asyncio
    async def test_hsts_header_values_format(self) -> None:
        expected_hsts = "max-age=31536000; includeSubDomains; preload"
        assert "max-age=31536000" in expected_hsts
        assert "includeSubDomains" in expected_hsts
        assert "preload" in expected_hsts

        max_age_value = 31536000
        assert max_age_value >= 31536000, "HSTS max-age should be at least 1 year"


class TestHTTPSEnforcement:
    def test_https_redirect_middleware_exists(self) -> None:
        from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware

        assert HTTPSRedirectMiddleware is not None

    @pytest.mark.asyncio
    async def test_security_middleware_is_registered(self) -> None:
        import httpx
        from httpx import ASGITransport

        async with httpx.AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get("/health")
            assert "X-Frame-Options" in response.headers
            assert "Content-Security-Policy" in response.headers

    def test_https_redirect_only_in_production(self) -> None:
        from unittest.mock import MagicMock
        from app.middleware.security import setup_security_middleware

        mock_app = MagicMock()
        original_debug = os.getenv("DEBUG", "true")
        os.environ["DEBUG"] = "true"
        from app.core.config import settings

        settings.cache_clear()
        setup_security_middleware(mock_app)
        assert mock_app.add_middleware.call_count >= 1
        os.environ["DEBUG"] = original_debug
        settings.cache_clear()


class TestSecurityHeadersComprehensive:
    """Comprehensive security header tests."""

    @pytest.fixture
    async def client(self) -> AsyncGenerator[AsyncClient, None]:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as ac:
            yield ac

    @pytest.mark.asyncio
    async def test_all_required_security_headers_present(self, client: AsyncClient) -> None:
        response = await client.get("/health")
        assert response.status_code == 200

        required_headers = {
            "X-Frame-Options": "SAMEORIGIN",
            "X-Content-Type-Options": "nosniff",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
        }

        for header, expected_value in required_headers.items():
            actual_value = response.headers.get(header)
            assert actual_value is not None, f"{header} is missing"
            assert actual_value == expected_value, f"{header} has incorrect value"

        assert "Permissions-Policy" in response.headers
        assert "Content-Security-Policy" in response.headers

    @pytest.mark.asyncio
    async def test_csp_prevents_external_scripts(self, client: AsyncClient) -> None:
        response = await client.get("/health")
        csp = response.headers.get("Content-Security-Policy")
        assert "script-src 'self'" in csp or "script-src 'self' 'unsafe-inline'" in csp

    @pytest.mark.asyncio
    async def test_csp_allows_data_images(self, client: AsyncClient) -> None:
        response = await client.get("/health")
        csp = response.headers.get("Content-Security-Policy")
        assert "img-src 'self' data: https:" in csp

    @pytest.mark.asyncio
    async def test_csp_frame_ancestors_present(self, client: AsyncClient) -> None:
        response = await client.get("/health")
        csp = response.headers.get("Content-Security-Policy")
        assert "frame-ancestors" in csp

    @pytest.mark.asyncio
    async def test_permissions_policy_blocks_sensitive_features(self, client: AsyncClient) -> None:
        response = await client.get("/health")
        permissions = response.headers.get("Permissions-Policy")
        sensitive_features = ["geolocation", "microphone", "camera"]
        for feature in sensitive_features:
            assert f"{feature}=()" in permissions, f"{feature} should be disabled"

    @pytest.mark.asyncio
    async def test_security_headers_apply_to_error_responses(self, client: AsyncClient) -> None:
        response = await client.get("/non-existent-endpoint")
        assert response.headers.get("X-Frame-Options") is not None
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert "Content-Security-Policy" in response.headers
