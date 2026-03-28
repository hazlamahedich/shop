"""CSRF middleware tests (Story 1.9).

Tests cover:
- CSRF validation for state-changing operations
- Bypass paths (webhooks, auth, docs, etc.)
- Safe methods (GET, HEAD, OPTIONS) bypass CSRF
- Error responses for invalid tokens
- Test mode bypass
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI, Request
from httpx import ASGITransport, AsyncClient
from starlette.datastructures import Headers

from app.middleware.csrf import CSRFMiddleware


def _build_app_with_csrf_middleware() -> FastAPI:
    app = FastAPI()

    @app.post("/api/checkout")
    async def checkout():
        return {"ok": True}

    @app.put("/api/users/123")
    async def update_user():
        return {"ok": True}

    @app.patch("/api/products/456")
    async def patch_product():
        return {"ok": True}

    @app.delete("/api/cart/items/789")
    async def delete_item():
        return {"ok": True}

    @app.get("/api/products")
    async def get_products():
        return {"ok": True}

    @app.head("/api/health")
    async def head_health():
        return {}

    @app.options("/api/products")
    async def options_products():
        return {}

    @app.post("/api/webhooks/facebook")
    async def webhook_facebook():
        return {"ok": True}

    @app.post("/api/oauth/authorize")
    async def oauth_authorize():
        return {"ok": True}

    @app.post("/api/v1/auth/login")
    async def auth_login():
        return {"ok": True}

    @app.post("/docs")
    async def docs():
        return {"ok": True}

    app.add_middleware(CSRFMiddleware, secret_key="test-secret-key-12345678901234567890")
    return app


@pytest.fixture(autouse=True)
def reset_rate_limiter_state():
    from app.core.rate_limiter import RateLimiter

    RateLimiter.reset_all()
    yield
    RateLimiter.reset_all()


class TestCSRFMiddlewareValidation:
    @pytest.mark.asyncio
    async def test_middleware_validates_csrf_for_post(self, monkeypatch) -> None:
        monkeypatch.setenv("IS_TESTING", "false")
        app = _build_app_with_csrf_middleware()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post("/api/checkout")
            assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_middleware_validates_csrf_for_put(self, monkeypatch) -> None:
        monkeypatch.setenv("IS_TESTING", "false")
        app = _build_app_with_csrf_middleware()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.put("/api/users/123", headers={"x-csrf-token": "invalid-token"})
            assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_middleware_validates_csrf_for_patch(self, monkeypatch) -> None:
        monkeypatch.setenv("IS_TESTING", "false")
        app = _build_app_with_csrf_middleware()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.patch("/api/products/456")
            assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_middleware_validates_csrf_for_delete(self, monkeypatch) -> None:
        monkeypatch.setenv("IS_TESTING", "false")
        app = _build_app_with_csrf_middleware()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.delete("/api/cart/items/789")
            assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_middleware_accepts_valid_csrf_token(self) -> None:
        from app.core.csrf import CSRFProtection

        csrf = CSRFProtection("test-secret-key-12345678901234567890")
        session_id = "test-session-123"
        token = csrf.generate_token(session_id)

        app = _build_app_with_csrf_middleware()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            client.cookies.set("csrf_token", token)
            response = await client.post(
                "/api/checkout",
                headers={"x-csrf-token": token},
            )
            assert response.status_code == 200


class TestCSRFMiddlewareBypass:
    @pytest.mark.asyncio
    async def test_middleware_bypasses_get_requests(self) -> None:
        app = _build_app_with_csrf_middleware()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get("/api/products")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_middleware_bypasses_head_requests(self) -> None:
        app = _build_app_with_csrf_middleware()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.head("/api/health")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_middleware_bypasses_options_requests(self) -> None:
        app = _build_app_with_csrf_middleware()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.options("/api/products")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_middleware_bypasses_webhook_paths(self) -> None:
        app = _build_app_with_csrf_middleware()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post("/api/webhooks/facebook")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_middleware_bypasses_oauth_paths(self) -> None:
        app = _build_app_with_csrf_middleware()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post("/api/oauth/authorize")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_middleware_bypasses_auth_paths(self) -> None:
        app = _build_app_with_csrf_middleware()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post("/api/v1/auth/login")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_middleware_bypasses_documentation_paths(self) -> None:
        app = _build_app_with_csrf_middleware()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post("/docs")
            assert response.status_code == 200


class TestCSRFMiddlewareErrorResponses:
    @pytest.mark.asyncio
    async def test_middleware_returns_403_for_invalid_token(self, monkeypatch) -> None:
        monkeypatch.setenv("IS_TESTING", "false")
        app = _build_app_with_csrf_middleware()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/api/checkout",
                headers={"x-csrf-token": "invalid-token"},
            )
            assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_middleware_error_response_format(self, monkeypatch) -> None:
        monkeypatch.setenv("IS_TESTING", "false")
        app = _build_app_with_csrf_middleware()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post("/api/checkout")
            assert response.status_code == 403

            body = response.json()
            assert "detail" in body
            detail = body["detail"]
            assert "error_code" in detail
            assert detail["error_code"] == 2000
            assert "message" in detail


class TestCSRFMiddlewareTestMode:
    @pytest.mark.asyncio
    async def test_middleware_bypasses_in_test_mode_env(self) -> None:
        original_value = os.environ.get("IS_TESTING")
        os.environ["IS_TESTING"] = "true"

        try:
            app = _build_app_with_csrf_middleware()
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                response = await client.post("/api/checkout")
                assert response.status_code == 200
        finally:
            if original_value is None:
                os.environ.pop("IS_TESTING", None)
            else:
                os.environ["IS_TESTING"] = original_value

    @pytest.mark.asyncio
    async def test_middleware_bypasses_with_test_mode_header(self) -> None:
        app = _build_app_with_csrf_middleware()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/api/checkout",
                headers={"X-Test-Mode": "true"},
            )
            assert response.status_code == 200


class TestCSRFMiddlewareBypassPathHelper:
    def test_should_bypass_csrf_for_webhook_path(self) -> None:
        middleware = CSRFMiddleware(None, "test-secret-key-12345678901234567890")
        request = MagicMock(spec=Request)
        request.url.path = "/api/webhooks/facebook"
        assert middleware._should_bypass_csrf(request) is True

    def test_should_bypass_csrf_for_auth_path(self) -> None:
        middleware = CSRFMiddleware(None, "test-secret-key-12345678901234567890")
        request = MagicMock(spec=Request)
        request.url.path = "/api/v1/auth/login"
        assert middleware._should_bypass_csrf(request) is True

    def test_should_bypass_csrf_for_regular_path(self) -> None:
        middleware = CSRFMiddleware(None, "test-secret-key-12345678901234567890")
        request = MagicMock(spec=Request)
        request.url.path = "/api/checkout"
        assert middleware._should_bypass_csrf(request) is False

    def test_should_bypass_csrf_for_partial_path_match(self) -> None:
        middleware = CSRFMiddleware(None, "test-secret-key-12345678901234567890")
        request = MagicMock(spec=Request)
        request.url.path = "/api/webhooks/facebook/messenger"
        assert middleware._should_bypass_csrf(request) is True


class TestCSRFMiddlewareInitialization:
    def test_middleware_initialization_with_secret_key(self) -> None:
        middleware = CSRFMiddleware(None, "test-secret-key-12345678901234567890")
        assert middleware.csrf is not None
        assert middleware.csrf.secret_key == "test-secret-key-12345678901234567890"

    def test_middleware_initialization_creates_csrf_protection(self) -> None:
        from app.core.csrf import CSRFProtection

        middleware = CSRFMiddleware(None, "test-secret-key-12345678901234567890")
        assert isinstance(middleware.csrf, CSRFProtection)


class TestCSRFMiddlewareIntegration:
    @pytest.mark.asyncio
    async def test_middleware_preserves_request_and_response(self) -> None:
        from app.core.csrf import CSRFProtection

        csrf = CSRFProtection("test-secret-key-12345678901234567890")
        session_id = "test-session-123"
        token = csrf.generate_token(session_id)

        app = _build_app_with_csrf_middleware()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            client.cookies.set("csrf_token", token)
            response = await client.post(
                "/api/checkout",
                headers={"x-csrf-token": token},
            )
            assert response.status_code == 200
            assert response.json() == {"ok": True}


import os
