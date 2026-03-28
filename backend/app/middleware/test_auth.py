"""Unit tests for authentication middleware.

Tests cover:
- JWT validation from cookie
- Request state population
- Bypass path handling
- get_request_merchant_id dependency
- Session revocation checking (MEDIUM-11)
"""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import FastAPI, HTTPException, Request, status
from httpx import ASGITransport, AsyncClient

from app.core.auth import create_jwt
from app.middleware.auth import (
    SESSION_COOKIE_NAME,
    AuthenticationMiddleware,
    get_request_merchant_id,
    require_auth,
)


def _build_app_with_auth_middleware() -> FastAPI:
    app = FastAPI()

    @app.get("/api/v1/protected")
    async def protected(request: Request):
        return {"merchant_id": getattr(request.state, "merchant_id", None)}

    @app.get("/api/v1/auth/login")
    async def login():
        return {"ok": True}

    @app.get("/health")
    async def health():
        return {"ok": True}

    @app.get("/api/v1/webhooks/shopify")
    async def webhooks():
        return {"ok": True}

    @app.get("/api/v1/auth/me")
    async def me(request: Request):
        return {"merchant_id": getattr(request.state, "merchant_id", None)}

    app.add_middleware(AuthenticationMiddleware)
    return app


def _make_mock_db(session_row=None):
    mock_db = AsyncMock()
    mock_db.__aenter__ = AsyncMock(return_value=mock_db)
    mock_db.__aexit__ = AsyncMock(return_value=False)

    mock_scalars = Mock()
    mock_scalars.first = Mock(return_value=session_row)

    mock_result = Mock()
    mock_result.scalars = Mock(return_value=mock_scalars)

    mock_db.execute = AsyncMock(return_value=mock_result)
    return mock_db


class TestAuthenticationMiddleware:
    @pytest.mark.asyncio
    async def test_bypass_in_test_mode(self):
        with patch.dict(os.environ, {"IS_TESTING": "true"}):
            app = _build_app_with_auth_middleware()
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                response = await client.get("/api/v1/protected")
                assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_bypass_with_test_header(self):
        with patch.dict(os.environ, {"IS_TESTING": "false"}):
            app = _build_app_with_auth_middleware()
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                response = await client.get(
                    "/api/v1/protected",
                    headers={"X-Test-Mode": "true"},
                )
                assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_bypass_for_whitelisted_path(self):
        app = _build_app_with_auth_middleware()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get("/api/v1/auth/login")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_bypass_for_health_endpoint(self):
        app = _build_app_with_auth_middleware()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get("/health")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_bypass_for_webhook_paths(self):
        app = _build_app_with_auth_middleware()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get("/api/v1/webhooks/shopify")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_returns_401_when_no_cookie(self):
        old_is_testing = os.environ.get("IS_TESTING")
        os.environ["IS_TESTING"] = "false"
        try:
            app = _build_app_with_auth_middleware()
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                response = await client.get("/api/v1/protected")
                assert response.status_code == 401
                body = response.json()
                assert "Authentication required" in body.get(
                    "message", body.get("detail", {}).get("message", "")
                )
        finally:
            if old_is_testing is None:
                os.environ.pop("IS_TESTING", None)
            else:
                os.environ["IS_TESTING"] = old_is_testing


class TestRequestMerchantIdExtraction:
    @pytest.mark.asyncio
    async def test_sets_merchant_id_in_state(self):
        token = create_jwt(merchant_id=42, session_id="session-test")

        with (
            patch.dict(os.environ, {"IS_TESTING": "false"}),
            patch("app.middleware.auth.async_session") as mock_accessor,
        ):
            mock_db = _make_mock_db(Mock(revoked=False))
            mock_accessor.return_value = Mock(return_value=mock_db)

            app = _build_app_with_auth_middleware()
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                client.cookies.set(SESSION_COOKIE_NAME, token)
                response = await client.get("/api/v1/protected")
                assert response.status_code == 200
                assert response.json()["merchant_id"] == 42

    @pytest.mark.asyncio
    async def test_raises_401_for_revoked_session(self):
        token = create_jwt(merchant_id=99, session_id="session-revoked-test")

        with (
            patch.dict(os.environ, {"IS_TESTING": "false"}),
            patch("app.middleware.auth.async_session") as mock_accessor,
        ):
            mock_db = _make_mock_db(Mock(revoked=True))
            mock_accessor.return_value = Mock(return_value=mock_db)

            app = _build_app_with_auth_middleware()
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                client.cookies.set(SESSION_COOKIE_NAME, token)
                response = await client.get("/api/v1/protected")
                assert response.status_code == 401
                body = response.json()
                assert (
                    "revoked"
                    in body.get("message", body.get("detail", {}).get("message", "")).lower()
                )

    @pytest.mark.asyncio
    async def test_raises_401_for_missing_session_in_db(self):
        token = create_jwt(merchant_id=99, session_id="session-missing-test")

        with (
            patch.dict(os.environ, {"IS_TESTING": "false"}),
            patch("app.middleware.auth.async_session") as mock_accessor,
        ):
            mock_db = _make_mock_db(None)
            mock_accessor.return_value = Mock(return_value=mock_db)

            app = _build_app_with_auth_middleware()
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                client.cookies.set(SESSION_COOKIE_NAME, token)
                response = await client.get("/api/v1/protected")
                assert response.status_code == 401


class TestGetRequestMerchantId:
    def test_returns_merchant_id_from_state(self):
        request = Mock(spec=Request)
        request.state = Mock()
        request.state.merchant_id = 42

        merchant_id = get_request_merchant_id(request)
        assert merchant_id == 42

    def test_raises_401_when_no_merchant_id(self):
        request = Mock(spec=Request)

        class MockState:
            def __getattr__(self, name):
                raise AttributeError(f"'MockState' object has no attribute '{name}'")

        request.state = MockState()

        with pytest.raises(HTTPException) as exc:
            get_request_merchant_id(request)

        assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED

    def test_raises_401_when_merchant_id_is_none(self):
        request = Mock(spec=Request)
        request.state = Mock()
        request.state.merchant_id = None

        with pytest.raises(HTTPException) as exc:
            get_request_merchant_id(request)

        assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED


class TestRequireAuthAlias:
    def test_require_auth_is_alias(self):
        assert require_auth is get_request_merchant_id


class TestBypassPaths:
    def test_includes_login_endpoint(self):
        assert "/api/v1/auth/login" in AuthenticationMiddleware.BYPASS_PATHS

    def test_includes_csrf_token_endpoint(self):
        assert "/api/v1/csrf-token" in AuthenticationMiddleware.BYPASS_PATHS

    def test_includes_health_endpoint(self):
        assert "/health" in AuthenticationMiddleware.BYPASS_PATHS

    def test_includes_webhook_paths(self):
        assert any(p.startswith("/api/v1/webhooks") for p in AuthenticationMiddleware.BYPASS_PATHS)

    def test_includes_oauth_paths(self):
        assert any(p.startswith("/api/oauth") for p in AuthenticationMiddleware.BYPASS_PATHS)

    def test_includes_documentation_paths(self):
        assert "/docs" in AuthenticationMiddleware.BYPASS_PATHS
        assert "/redoc" in AuthenticationMiddleware.BYPASS_PATHS
        assert "/openapi.json" in AuthenticationMiddleware.BYPASS_PATHS
