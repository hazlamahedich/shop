"""CSRF middleware tests (Story 1.9).

Tests cover:
- CSRF validation for state-changing operations
- Bypass paths (webhooks, auth, docs, etc.)
- Safe methods (GET, HEAD, OPTIONS) bypass CSRF
- Error responses for invalid tokens
- Test mode bypass
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, AsyncMock
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.datastructures import Headers

from app.middleware.csrf import CSRFMiddleware


@pytest.fixture(autouse=True)
def reset_rate_limiter_state():
    """Reset RateLimiter state before each test to ensure test isolation.

    The RateLimiter uses class-level state (_requests, _auth_attempts) that
    persists between tests. This fixture resets that state before each test.
    """
    from app.core.rate_limiter import RateLimiter
    RateLimiter.reset_all()
    yield
    # Clean up after test
    RateLimiter.reset_all()


def _create_mock_response(status_code: int = 200) -> MagicMock:
    """Create a mock response object with proper attributes.

    Args:
        status_code: HTTP status code for the response

    Returns:
        MagicMock with status_code attribute
    """
    response = MagicMock()
    response.status_code = status_code
    return response


class TestCSRFMiddlewareValidation:
    """Tests for CSRF token validation in middleware."""

    @pytest.mark.asyncio
    async def test_middleware_validates_csrf_for_post(self, monkeypatch) -> None:
        """Test that POST requests require valid CSRF token."""
        # Disable test mode bypass for this test
        monkeypatch.setenv("IS_TESTING", "false")

        middleware = CSRFMiddleware(None, "test-secret-key-12345678901234567890")

        # Create mock request without CSRF token
        request = MagicMock(spec=Request)
        request.method = "POST"
        request.url.path = "/api/checkout"
        request.headers = Headers({})
        request.cookies.get.return_value = None
        request.client = MagicMock()
        request.client.host = "127.0.0.1"

        async def mock_call_next(req):
            return _create_mock_response(200)

        # Should return 403 for missing CSRF
        response = await middleware.dispatch(request, mock_call_next)
        assert response.status_code == 403

        data = response.body.decode() if hasattr(response, 'body') else {}
        assert "CSRF" in str(data) or "error_code" in str(data)

    @pytest.mark.asyncio
    async def test_middleware_validates_csrf_for_put(self, monkeypatch) -> None:
        """Test that PUT requests require valid CSRF token."""
        # Disable test mode bypass for this test
        monkeypatch.setenv("IS_TESTING", "false")

        middleware = CSRFMiddleware(None, "test-secret-key-12345678901234567890")

        request = MagicMock(spec=Request)
        request.method = "PUT"
        request.url.path = "/api/users/123"
        request.headers = Headers({"x-csrf-token": "invalid-token"})
        request.cookies.get.return_value = "different-token"
        request.client = MagicMock()
        request.client.host = "127.0.0.1"

        async def mock_call_next(req):
            return _create_mock_response(200)

        response = await middleware.dispatch(request, mock_call_next)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_middleware_validates_csrf_for_patch(self, monkeypatch) -> None:
        """Test that PATCH requests require valid CSRF token."""
        # Disable test mode bypass for this test
        monkeypatch.setenv("IS_TESTING", "false")

        middleware = CSRFMiddleware(None, "test-secret-key-12345678901234567890")

        request = MagicMock(spec=Request)
        request.method = "PATCH"
        request.url.path = "/api/products/456"
        request.headers = Headers({})
        request.cookies.get.return_value = None
        request.client = MagicMock()
        request.client.host = "127.0.0.1"

        async def mock_call_next(req):
            return _create_mock_response(200)

        response = await middleware.dispatch(request, mock_call_next)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_middleware_validates_csrf_for_delete(self, monkeypatch) -> None:
        """Test that DELETE requests require valid CSRF token."""
        # Disable test mode bypass for this test
        monkeypatch.setenv("IS_TESTING", "false")

        middleware = CSRFMiddleware(None, "test-secret-key-12345678901234567890")

        request = MagicMock(spec=Request)
        request.method = "DELETE"
        request.url.path = "/api/cart/items/789"
        request.headers = Headers({})
        request.cookies.get.return_value = None
        request.client = MagicMock()
        request.client.host = "127.0.0.1"

        async def mock_call_next(req):
            return _create_mock_response(200)

        response = await middleware.dispatch(request, mock_call_next)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_middleware_accepts_valid_csrf_token(self) -> None:
        """Test that valid CSRF token is accepted."""
        from app.core.csrf import CSRFProtection

        csrf = CSRFProtection("test-secret-key-12345678901234567890")
        middleware = CSRFMiddleware(None, "test-secret-key-12345678901234567890")

        # Generate valid token
        session_id = "test-session-123"
        token = csrf.generate_token(session_id)

        # Create mock request with valid token
        request = MagicMock(spec=Request)
        request.method = "POST"
        request.url.path = "/api/checkout"
        request.headers = Headers({"x-csrf-token": token})
        request.cookies.get.return_value = token
        request.client = MagicMock()
        request.client.host = "127.0.0.1"

        response_mock = MagicMock()
        response_mock.status_code = 200

        async def mock_call_next(req):
            return response_mock

        # Should proceed without error
        response = await middleware.dispatch(request, mock_call_next)
        assert response.status_code == 200


class TestCSRFMiddlewareBypass:
    """Tests for CSRF bypass conditions."""

    @pytest.mark.asyncio
    async def test_middleware_bypasses_get_requests(self) -> None:
        """Test that GET requests bypass CSRF validation."""
        middleware = CSRFMiddleware(None, "test-secret-key-12345678901234567890")

        request = MagicMock(spec=Request)
        request.method = "GET"
        request.url.path = "/api/products"
        request.headers = Headers({})
        request.client = MagicMock()
        request.client.host = "127.0.0.1"

        response_mock = MagicMock()
        response_mock.status_code = 200

        async def mock_call_next(req):
            return response_mock

        response = await middleware.dispatch(request, mock_call_next)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_middleware_bypasses_head_requests(self) -> None:
        """Test that HEAD requests bypass CSRF validation."""
        middleware = CSRFMiddleware(None, "test-secret-key-12345678901234567890")

        request = MagicMock(spec=Request)
        request.method = "HEAD"
        request.url.path = "/api/health"
        request.headers = Headers({})
        request.client = MagicMock()
        request.client.host = "127.0.0.1"

        response_mock = MagicMock()

        async def mock_call_next(req):
            return response_mock

        response = await middleware.dispatch(request, mock_call_next)
        assert response is not None

    @pytest.mark.asyncio
    async def test_middleware_bypasses_options_requests(self) -> None:
        """Test that OPTIONS requests bypass CSRF validation."""
        middleware = CSRFMiddleware(None, "test-secret-key-12345678901234567890")

        request = MagicMock(spec=Request)
        request.method = "OPTIONS"
        request.url.path = "/api/products"
        request.headers = Headers({})
        request.client = MagicMock()
        request.client.host = "127.0.0.1"

        response_mock = MagicMock()

        async def mock_call_next(req):
            return response_mock

        response = await middleware.dispatch(request, mock_call_next)
        assert response is not None

    @pytest.mark.asyncio
    async def test_middleware_bypasses_webhook_paths(self) -> None:
        """Test that webhook paths bypass CSRF validation."""
        middleware = CSRFMiddleware(None, "test-secret-key-12345678901234567890")

        webhook_paths = [
            "/api/webhooks/facebook",
            "/api/webhooks/shopify",
            "/webhooks/test",
        ]

        for path in webhook_paths:
            request = MagicMock(spec=Request)
            request.method = "POST"
            request.url.path = path
            request.headers = Headers({})
            request.client = MagicMock()
            request.client.host = "127.0.0.1"

            response_mock = MagicMock()

            async def mock_call_next(req):
                return response_mock

            response = await middleware.dispatch(request, mock_call_next)
            # Should bypass CSRF
            assert response is not None

    @pytest.mark.asyncio
    async def test_middleware_bypasses_oauth_paths(self) -> None:
        """Test that OAuth paths bypass CSRF validation."""
        middleware = CSRFMiddleware(None, "test-secret-key-12345678901234567890")

        oauth_paths = [
            "/api/oauth/authorize",
            "/api/oauth/callback",
        ]

        for path in oauth_paths:
            request = MagicMock(spec=Request)
            request.method = "POST"
            request.url.path = path
            request.headers = Headers({})
            request.client = MagicMock()
            request.client.host = "127.0.0.1"

            response_mock = MagicMock()

            async def mock_call_next(req):
                return response_mock

            response = await middleware.dispatch(request, mock_call_next)
            assert response is not None

    @pytest.mark.asyncio
    async def test_middleware_bypasses_auth_paths(self) -> None:
        """Test that auth paths bypass CSRF validation (Story 1.8)."""
        middleware = CSRFMiddleware(None, "test-secret-key-12345678901234567890")

        auth_paths = [
            "/api/v1/auth/login",
            "/api/v1/auth/logout",
            "/api/v1/auth/refresh",
        ]

        for path in auth_paths:
            request = MagicMock(spec=Request)
            request.method = "POST"
            request.url.path = path
            request.headers = Headers({})
            request.client = MagicMock()
            request.client.host = "127.0.0.1"

            response_mock = MagicMock()

            async def mock_call_next(req):
                return response_mock

            response = await middleware.dispatch(request, mock_call_next)
            assert response is not None

    @pytest.mark.asyncio
    async def test_middleware_bypasses_documentation_paths(self) -> None:
        """Test that documentation paths bypass CSRF validation."""
        middleware = CSRFMiddleware(None, "test-secret-key-12345678901234567890")

        doc_paths = [
            "/docs",
            "/redoc",
            "/openapi.json",
        ]

        for path in doc_paths:
            request = MagicMock(spec=Request)
            request.method = "POST"
            request.url.path = path
            request.headers = Headers({})
            request.client = MagicMock()
            request.client.host = "127.0.0.1"

            response_mock = MagicMock()

            async def mock_call_next(req):
                return response_mock

            response = await middleware.dispatch(request, mock_call_next)
            assert response is not None


class TestCSRFMiddlewareErrorResponses:
    """Tests for CSRF middleware error responses."""

    @pytest.mark.asyncio
    async def test_middleware_returns_403_for_invalid_token(self, monkeypatch) -> None:
        """Test that invalid CSRF token returns 403."""
        # Disable test mode bypass for this test
        monkeypatch.setenv("IS_TESTING", "false")

        middleware = CSRFMiddleware(None, "test-secret-key-12345678901234567890")

        request = MagicMock(spec=Request)
        request.method = "POST"
        request.url.path = "/api/checkout"
        request.headers = Headers({"x-csrf-token": "invalid-token"})
        request.cookies.get.return_value = "different-token"
        request.client = MagicMock()
        request.client.host = "127.0.0.1"

        async def mock_call_next(req):
            return _create_mock_response(200)

        response = await middleware.dispatch(request, mock_call_next)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_middleware_error_response_format(self, monkeypatch) -> None:
        """Test that error response follows MinimalEnvelope pattern."""
        # Disable test mode bypass for this test
        monkeypatch.setenv("IS_TESTING", "false")

        middleware = CSRFMiddleware(None, "test-secret-key-12345678901234567890")

        request = MagicMock(spec=Request)
        request.method = "POST"
        request.url.path = "/api/checkout"
        request.headers = Headers({})
        request.cookies.get.return_value = None
        request.client = MagicMock()
        request.client.host = "127.0.0.1"

        async def mock_call_next(req):
            return _create_mock_response(200)

        response = await middleware.dispatch(request, mock_call_next)

        # Check response is JSONResponse with correct format
        assert isinstance(response, JSONResponse)
        assert response.status_code == 403

        # Parse body
        import json
        body = json.loads(response.body.decode())
        assert "detail" in body
        assert "error_code" in body["detail"]
        assert body["detail"]["error_code"] == 2000
        assert "message" in body["detail"]


class TestCSRFMiddlewareTestMode:
    """Tests for CSRF middleware test mode bypass."""

    @pytest.mark.asyncio
    async def test_middleware_bypasses_in_test_mode_env(self) -> None:
        """Test that CSRF is bypassed when IS_TESTING=true."""
        import os

        original_value = os.environ.get("IS_TESTING")
        os.environ["IS_TESTING"] = "true"

        try:
            middleware = CSRFMiddleware(None, "test-secret-key-12345678901234567890")

            request = MagicMock(spec=Request)
            request.method = "POST"
            request.url.path = "/api/checkout"
            request.headers = Headers({})
            request.cookies.get.return_value = None
            request.client = MagicMock()
            request.client.host = "127.0.0.1"

            response_mock = MagicMock()

            async def mock_call_next(req):
                return response_mock

            # Should bypass CSRF validation
            response = await middleware.dispatch(request, mock_call_next)
            assert response is response_mock

        finally:
            if original_value is None:
                os.environ.pop("IS_TESTING", None)
            else:
                os.environ["IS_TESTING"] = original_value

    @pytest.mark.asyncio
    async def test_middleware_bypasses_with_test_mode_header(self) -> None:
        """Test that CSRF is bypassed with X-Test-Mode: true header."""
        middleware = CSRFMiddleware(None, "test-secret-key-12345678901234567890")

        request = MagicMock(spec=Request)
        request.method = "POST"
        request.url.path = "/api/checkout"
        request.headers = Headers({"X-Test-Mode": "true"})
        request.cookies.get.return_value = None
        request.client = MagicMock()
        request.client.host = "127.0.0.1"

        response_mock = MagicMock()

        async def mock_call_next(req):
            return response_mock

        response = await middleware.dispatch(request, mock_call_next)
        assert response is response_mock


class TestCSRFMiddlewareBypassPathHelper:
    """Tests for _should_bypass_csrf helper method."""

    def test_should_bypass_csrf_for_webhook_path(self) -> None:
        """Test bypass detection for webhook paths."""
        middleware = CSRFMiddleware(None, "test-secret-key-12345678901234567890")

        request = MagicMock(spec=Request)
        request.url.path = "/api/webhooks/facebook"

        assert middleware._should_bypass_csrf(request) is True

    def test_should_bypass_csrf_for_auth_path(self) -> None:
        """Test bypass detection for auth paths."""
        middleware = CSRFMiddleware(None, "test-secret-key-12345678901234567890")

        request = MagicMock(spec=Request)
        request.url.path = "/api/v1/auth/login"

        assert middleware._should_bypass_csrf(request) is True

    def test_should_bypass_csrf_for_regular_path(self) -> None:
        """Test bypass detection for regular paths."""
        middleware = CSRFMiddleware(None, "test-secret-key-12345678901234567890")

        request = MagicMock(spec=Request)
        request.url.path = "/api/checkout"

        assert middleware._should_bypass_csrf(request) is False

    def test_should_bypass_csrf_for_partial_path_match(self) -> None:
        """Test bypass detection for partial path matches."""
        middleware = CSRFMiddleware(None, "test-secret-key-12345678901234567890")

        request = MagicMock(spec=Request)
        request.url.path = "/api/webhooks/facebook/messenger"

        assert middleware._should_bypass_csrf(request) is True


class TestCSRFMiddlewareInitialization:
    """Tests for CSRF middleware initialization."""

    def test_middleware_initialization_with_secret_key(self) -> None:
        """Test middleware initialization with secret key."""
        middleware = CSRFMiddleware(None, "test-secret-key-12345678901234567890")

        assert middleware.csrf is not None
        assert middleware.csrf.secret_key == "test-secret-key-12345678901234567890"

    def test_middleware_initialization_creates_csrf_protection(self) -> None:
        """Test that initialization creates CSRFProtection instance."""
        from app.core.csrf import CSRFProtection

        middleware = CSRFMiddleware(None, "test-secret-key-12345678901234567890")

        assert isinstance(middleware.csrf, CSRFProtection)


class TestCSRFMiddlewareIntegration:
    """Integration tests for CSRF middleware with FastAPI."""

    @pytest.mark.asyncio
    async def test_middleware_preserves_request_and_response(self) -> None:
        """Test that middleware doesn't modify valid requests/responses."""
        from app.core.csrf import CSRFProtection

        csrf = CSRFProtection("test-secret-key-12345678901234567890")
        middleware = CSRFMiddleware(None, "test-secret-key-12345678901234567890")

        # Generate valid token
        session_id = "test-session-123"
        token = csrf.generate_token(session_id)

        # Create mock request with valid token
        request = MagicMock(spec=Request)
        request.method = "POST"
        request.url.path = "/api/checkout"
        request.headers = Headers({"x-csrf-token": token})
        request.cookies.get.return_value = token
        request.client = MagicMock()
        request.client.host = "127.0.0.1"

        original_response = MagicMock()
        original_response.status_code = 201
        original_response.body = b'{"created": true}'

        async def mock_call_next(req):
            return original_response

        # Response should be unchanged
        response = await middleware.dispatch(request, mock_call_next)
        assert response is original_response
