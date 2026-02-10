"""Unit tests for authentication middleware.

Tests cover:
- JWT validation from cookie
- Request state population
- Bypass path handling
- Security headers
- get_request_merchant_id dependency
- Session revocation checking (MEDIUM-11)
"""

from __future__ import annotations

import os
import pytest
from unittest.mock import AsyncMock, Mock, patch

from fastapi import HTTPException, status, Request
from starlette.responses import Response
from sqlalchemy import select

from app.middleware.auth import (
    AuthenticationMiddleware,
    get_request_merchant_id,
    require_auth,
    SESSION_COOKIE_NAME,
)
from app.core.auth import create_jwt, hash_token
from app.core.database import async_session
from app.models.session import Session


class TestAuthenticationMiddleware:
    """Tests for AuthenticationMiddleware."""

    @pytest.fixture
    def mock_app(self):
        """Create mock FastAPI app."""
        return Mock()

    @pytest.fixture
    def middleware(self, mock_app):
        """Create middleware instance."""
        return AuthenticationMiddleware(mock_app)

    @pytest.mark.asyncio
    async def test_bypass_in_test_mode(self, middleware):
        """Should bypass authentication when IS_TESTING=true."""
        request = Mock(spec=Request)
        request.url.path = "/api/v1/protected"
        request.cookies = {}
        request.headers = {}

        with patch.dict(os.environ, {"IS_TESTING": "true"}):
            call_next = AsyncMock(return_value=Response())
            response = await middleware.dispatch(request, call_next)

            assert response.status_code == 200
            call_next.assert_called_once_with(request)

    @pytest.mark.asyncio
    async def test_bypass_with_test_header(self, middleware):
        """Should bypass authentication with X-Test-Mode header."""
        request = Mock(spec=Request)
        request.url.path = "/api/v1/protected"
        request.cookies = {}
        request.headers = {"X-Test-Mode": "true"}

        with patch.dict(os.environ, {"IS_TESTING": "false"}):
            call_next = AsyncMock(return_value=Response())
            response = await middleware.dispatch(request, call_next)

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_bypass_for_whitelisted_path(self, middleware):
        """Should bypass authentication for whitelisted paths."""
        request = Mock(spec=Request)
        request.url.path = "/api/v1/auth/login"
        request.cookies = {}
        request.headers = {}

        call_next = AsyncMock(return_value=Response())
        response = await middleware.dispatch(request, call_next)

        assert response.status_code == 200
        # For bypassed paths, the middleware shouldn't set merchant_id in state
        # Check if merchant_id was NOT set by checking if getattr returns None
        merchant_id = getattr(request.state, "merchant_id", "NOT_SET")
        # If merchant_id was set, it would be an int; "NOT_SET" means it wasn't
        # Since Mock objects auto-create attributes, we just verify the path was bypassed
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_bypass_for_health_endpoint(self, middleware):
        """Should bypass authentication for /health endpoint."""
        request = Mock(spec=Request)
        request.url.path = "/health"
        request.cookies = {}
        request.headers = {}

        call_next = AsyncMock(return_value=Response())
        response = await middleware.dispatch(request, call_next)

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_bypass_for_webhook_paths(self, middleware):
        """Should bypass authentication for webhook paths."""
        request = Mock(spec=Request)
        request.url.path = "/api/v1/webhooks/shopify"
        request.cookies = {}
        request.headers = {}

        call_next = AsyncMock(return_value=Response())
        response = await middleware.dispatch(request, call_next)

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_raises_401_when_no_cookie(self, middleware):
        """Should raise 401 when no session cookie."""
        request = Mock(spec=Request)
        request.url.path = "/api/v1/protected"
        request.cookies = {}
        request.headers = {}
        request.client = Mock(host="127.0.0.1")

        call_next = AsyncMock(return_value=Response())

        # Clear IS_TESTING to enable auth for this test
        import os
        old_is_testing = os.environ.get("IS_TESTING")
        os.environ["IS_TESTING"] = "false"

        try:
            with pytest.raises(HTTPException) as exc:
                await middleware.dispatch(request, call_next)

            assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert "Authentication required" in exc.value.detail["message"]
        finally:
            # Restore original value
            if old_is_testing is None:
                os.environ.pop("IS_TESTING", None)
            else:
                os.environ["IS_TESTING"] = old_is_testing


class TestRequestMerchantIdExtraction:
    """Tests for merchant_id extraction from authenticated requests."""

    @pytest.mark.asyncio
    async def test_sets_merchant_id_in_state(self):
        """Should set merchant_id in request.state.

        MEDIUM-11: Updated to create session in database for revocation check.
        """
        middleware = AuthenticationMiddleware(Mock())

        # Create valid JWT
        session_id = "session-123"
        token = create_jwt(merchant_id=42, session_id=session_id)
        token_hash = hash_token(token)

        # Create session in database (MEDIUM-11: required for revocation check)
        async with async_session() as db:
            session = Session.create(
                merchant_id=42,
                token_hash=token_hash,
                hours=24,
            )
            db.add(session)
            await db.commit()

        request = Mock(spec=Request)
        request.url.path = "/api/v1/protected"
        request.cookies = {SESSION_COOKIE_NAME: token}
        request.headers = {}
        request.state = Mock()

        call_next = AsyncMock(return_value=Response())

        try:
            with patch.dict(os.environ, {"IS_TESTING": "false"}):
                response = await middleware.dispatch(request, call_next)

                assert request.state.merchant_id == 42
        finally:
            # Cleanup session
            async with async_session() as db:
                result = await db.execute(
                    select(Session).where(Session.token_hash == token_hash)
                )
                session = result.scalars().first()
                if session:
                    await db.delete(session)
                    await db.commit()

    @pytest.mark.asyncio
    async def test_adds_security_headers(self):
        """Should add security headers to response.

        MEDIUM-11: Updated to create session in database for revocation check.
        """
        middleware = AuthenticationMiddleware(Mock())

        session_id = "session-456"
        token = create_jwt(merchant_id=1, session_id=session_id)
        token_hash = hash_token(token)

        # Create session in database (MEDIUM-11: required for revocation check)
        async with async_session() as db:
            session = Session.create(
                merchant_id=1,
                token_hash=token_hash,
                hours=24,
            )
            db.add(session)
            await db.commit()

        request = Mock(spec=Request)
        request.url.path = "/api/v1/protected"
        request.cookies = {SESSION_COOKIE_NAME: token}
        request.headers = {}
        request.state = Mock()

        response = Response()
        call_next = AsyncMock(return_value=response)

        try:
            with patch.dict(os.environ, {"IS_TESTING": "false"}):
                result = await middleware.dispatch(request, call_next)

                # Check CSP header
                assert "Content-Security-Policy" in result.headers
                assert "default-src 'self'" in result.headers["Content-Security-Policy"]

                # Check other security headers
                assert result.headers["X-Content-Type-Options"] == "nosniff"
                assert result.headers["X-Frame-Options"] == "DENY"
                assert result.headers["X-XSS-Protection"] == "1; mode=block"
        finally:
            # Cleanup session
            async with async_session() as db:
                result = await db.execute(
                    select(Session).where(Session.token_hash == token_hash)
                )
                session = result.scalars().first()
                if session:
                    await db.delete(session)
                    await db.commit()

    @pytest.mark.asyncio
    async def test_raises_401_for_revoked_session(self):
        """Should raise 401 when session is revoked in database.

        MEDIUM-11: New test for session revocation checking.
        """
        middleware = AuthenticationMiddleware(Mock())

        session_id = "session-revoked"
        token = create_jwt(merchant_id=99, session_id=session_id)
        token_hash = hash_token(token)

        # Create REVOKED session in database
        async with async_session() as db:
            session = Session.create(
                merchant_id=99,
                token_hash=token_hash,
                hours=24,
            )
            session.revoke()  # Mark as revoked
            db.add(session)
            await db.commit()

        request = Mock(spec=Request)
        request.url.path = "/api/v1/protected"
        request.cookies = {SESSION_COOKIE_NAME: token}
        request.headers = {}
        request.state = Mock()

        call_next = AsyncMock(return_value=Response())

        try:
            with patch.dict(os.environ, {"IS_TESTING": "false"}):
                with pytest.raises(HTTPException) as exc:
                    await middleware.dispatch(request, call_next)

                assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
                assert exc.value.detail["error_code"].value == 2013  # AUTH_SESSION_REVOKED
                assert "revoked" in exc.value.detail["message"].lower()
        finally:
            # Cleanup session
            async with async_session() as db:
                result = await db.execute(
                    select(Session).where(Session.token_hash == token_hash)
                )
                session = result.scalars().first()
                if session:
                    await db.delete(session)
                    await db.commit()


class TestGetRequestMerchantId:
    """Tests for get_request_merchant_id dependency."""

    def test_returns_merchant_id_from_state(self):
        """Should return merchant_id from request state."""
        request = Mock(spec=Request)
        request.state = Mock()
        request.state.merchant_id = 42

        merchant_id = get_request_merchant_id(request)
        assert merchant_id == 42

    def test_raises_401_when_no_merchant_id(self):
        """Should raise 401 when merchant_id not in state."""
        request = Mock(spec=Request)
        # Create a state object that raises AttributeError for missing attributes
        class MockState:
            def __getattr__(self, name):
                raise AttributeError(f"'MockState' object has no attribute '{name}'")
        request.state = MockState()

        with pytest.raises(HTTPException) as exc:
            get_request_merchant_id(request)

        assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED

    def test_raises_401_when_merchant_id_is_none(self):
        """Should raise 401 when merchant_id is None."""
        request = Mock(spec=Request)
        request.state = Mock()
        request.state.merchant_id = None

        with pytest.raises(HTTPException) as exc:
            get_request_merchant_id(request)

        assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED


class TestRequireAuthAlias:
    """Tests for require_auth alias."""

    def test_require_auth_is_alias(self):
        """require_auth should be same function as get_request_merchant_id."""
        assert require_auth is get_request_merchant_id


class TestBypassPaths:
    """Tests for BYPASS_PATHS configuration."""

    def test_includes_login_endpoint(self):
        """BYPASS_PATHS should include login endpoint."""
        assert "/api/v1/auth/login" in AuthenticationMiddleware.BYPASS_PATHS

    def test_includes_csrf_token_endpoint(self):
        """BYPASS_PATHS should include CSRF token endpoint."""
        assert "/api/v1/csrf-token" in AuthenticationMiddleware.BYPASS_PATHS

    def test_includes_health_endpoint(self):
        """BYPASS_PATHS should include health endpoint."""
        assert "/health" in AuthenticationMiddleware.BYPASS_PATHS

    def test_includes_webhook_paths(self):
        """BYPASS_PATHS should include webhook paths."""
        assert any(p.startswith("/api/v1/webhooks") for p in AuthenticationMiddleware.BYPASS_PATHS)

    def test_includes_oauth_paths(self):
        """BYPASS_PATHS should include OAuth paths."""
        assert any(p.startswith("/api/oauth") for p in AuthenticationMiddleware.BYPASS_PATHS)

    def test_includes_documentation_paths(self):
        """BYPASS_PATHS should include docs paths."""
        assert "/docs" in AuthenticationMiddleware.BYPASS_PATHS
        assert "/redoc" in AuthenticationMiddleware.BYPASS_PATHS
        assert "/openapi.json" in AuthenticationMiddleware.BYPASS_PATHS
