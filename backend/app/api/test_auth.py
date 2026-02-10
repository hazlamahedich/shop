"""Unit tests for authentication API endpoints.

Tests cover:
- Login with valid credentials
- Login with invalid credentials
- Logout and session revocation
- Get current merchant
- Token refresh
- Error handling
"""

from __future__ import annotations

import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import (
    LoginRequest,
    MerchantResponse,
    SessionResponse,
    LoginResponse,
    AuthResponse,
    MeResponse,
    RefreshResponse,
    SESSION_COOKIE_NAME,
)
from app.core.auth import hash_password, create_jwt, hash_token
from app.models.session import Session
from app.models.merchant import Merchant
from app.schemas.base import MinimalEnvelope


class TestLoginRequestSchema:
    """Tests for LoginRequest schema."""

    def test_valid_login_request(self):
        """Valid login request should pass validation."""
        request = LoginRequest(email="test@example.com", password="SecurePass123")
        assert request.email == "test@example.com"
        assert request.password == "SecurePass123"

    def test_email_required(self):
        """Email should be required."""
        with pytest.raises(ValueError):
            LoginRequest(email="", password="SecurePass123")

    def test_password_min_length(self):
        """Password should be at least 8 characters."""
        with pytest.raises(ValueError):
            LoginRequest(email="test@example.com", password="Short1")


class TestLoginEndpoint:
    """Tests for POST /auth/login endpoint."""

    @pytest.mark.asyncio
    async def test_login_success(self, db_session: AsyncSession):
        """Successful login should return merchant info and set cookie."""
        # Create merchant with password
        merchant = Merchant(
            merchant_key="test-merchant",
            platform="shopify",
            status="active",
            email="test@example.com",
            password_hash=hash_password("SecurePass123"),
        )
        db_session.add(merchant)
        await db_session.commit()
        await db_session.refresh(merchant)

        # Create request and response mocks
        request = Mock()
        request.cookies = {}

        response = Mock()
        response.set_cookie = Mock()

        # Create login request
        credentials = LoginRequest(email="test@example.com", password="SecurePass123")

        # Call login (dependency injection would be done by FastAPI)
        from app.api.auth import login as login_fn

        with patch("app.api.auth.get_db", return_value=db_session):
            result = await login_fn(request, credentials, response, db_session)

            # Verify response
            assert isinstance(result, MinimalEnvelope)
            assert isinstance(result.data, LoginResponse)
            assert result.data.merchant.id == merchant.id
            assert result.data.merchant.email == "test@example.com"
            assert result.data.merchant.merchant_key == "test-merchant"

            # Verify cookie was set
            response.set_cookie.assert_called_once()

    @pytest.mark.asyncio
    async def test_login_invalid_email(self, db_session: AsyncSession):
        """Login with non-existent email should return generic error."""
        request = Mock()
        request.cookies = {}

        response = Mock()
        response.set_cookie = Mock()

        credentials = LoginRequest(email="nonexistent@example.com", password="SecurePass123")

        from app.api.auth import login as login_fn

        with pytest.raises(HTTPException) as exc:
            await login_fn(request, credentials, response, db_session)

        assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid email or password" in exc.value.detail["message"]

    @pytest.mark.asyncio
    async def test_login_invalid_password(self, db_session: AsyncSession):
        """Login with wrong password should return generic error."""
        merchant = Merchant(
            merchant_key="test-merchant",
            platform="shopify",
            status="active",
            email="test@example.com",
            password_hash=hash_password("SecurePass123"),
        )
        db_session.add(merchant)
        await db_session.commit()
        await db_session.refresh(merchant)

        request = Mock()
        request.cookies = {}

        response = Mock()
        response.set_cookie = Mock()

        credentials = LoginRequest(email="test@example.com", password="WrongPass123")

        from app.api.auth import login as login_fn

        with pytest.raises(HTTPException) as exc:
            await login_fn(request, credentials, response, db_session)

        assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid email or password" in exc.value.detail["message"]


class TestLogoutEndpoint:
    """Tests for POST /auth/logout endpoint."""

    @pytest.mark.asyncio
    async def test_logout_clears_cookie(self, db_session: AsyncSession):
        """Logout should clear session cookie."""
        request = Mock()
        request.cookies = {}

        response = Mock()
        response.delete_cookie = Mock()

        from app.api.auth import logout as logout_fn

        result = await logout_fn(request, response, db_session)

        assert isinstance(result, MinimalEnvelope)
        assert isinstance(result.data, AuthResponse)
        assert result.data.success is True
        response.delete_cookie.assert_called_once()

    @pytest.mark.asyncio
    async def test_logout_revokes_session(self, db_session: AsyncSession):
        """Logout should revoke session in database."""
        merchant = Merchant(
            merchant_key="test-merchant",
            platform="shopify",
            status="active",
            email="test@example.com",
            password_hash=hash_password("SecurePass123"),
        )
        db_session.add(merchant)
        await db_session.commit()
        await db_session.refresh(merchant)

        # Create session
        token = create_jwt(merchant_id=merchant.id, session_id="session-123")
        token_hash = hash_token(token)
        session = Session.create(merchant_id=merchant.id, token_hash=token_hash)
        db_session.add(session)
        await db_session.commit()

        request = Mock()
        request.cookies = {SESSION_COOKIE_NAME: token}

        response = Mock()
        response.delete_cookie = Mock()

        from app.api.auth import logout as logout_fn

        await logout_fn(request, response, db_session)

        # Verify session is revoked
        await db_session.refresh(session)
        assert session.revoked is True


class TestGetCurrentMerchantEndpoint:
    """Tests for GET /auth/me endpoint."""

    @pytest.mark.asyncio
    async def test_me_returns_merchant_info(self, db_session: AsyncSession):
        """Should return current merchant info."""
        merchant = Merchant(
            merchant_key="test-merchant",
            platform="shopify",
            status="active",
            email="test@example.com",
            password_hash=hash_password("SecurePass123"),
        )
        db_session.add(merchant)
        await db_session.commit()
        await db_session.refresh(merchant)

        # Create session
        token = create_jwt(merchant_id=merchant.id, session_id="session-123")
        token_hash = hash_token(token)
        session = Session.create(merchant_id=merchant.id, token_hash=token_hash)
        db_session.add(session)
        await db_session.commit()

        request = Mock()
        request.cookies = {SESSION_COOKIE_NAME: token}

        from app.api.auth import get_current_merchant as me_fn

        result = await me_fn(request, db_session)

        assert isinstance(result, MinimalEnvelope)
        assert isinstance(result.data, MeResponse)
        assert result.data.merchant.id == merchant.id
        assert result.data.merchant.email == "test@example.com"

    @pytest.mark.asyncio
    async def test_me_no_token_raises_401(self, db_session: AsyncSession):
        """Should raise 401 when no token in cookie."""
        request = Mock()
        request.cookies = {}

        from app.api.auth import get_current_merchant as me_fn

        with pytest.raises(HTTPException) as exc:
            await me_fn(request, db_session)

        assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED


class TestRefreshTokenEndpoint:
    """Tests for POST /auth/refresh endpoint."""

    @pytest.mark.asyncio
    async def test_refresh_extends_session(self, db_session: AsyncSession):
        """Token refresh should extend session."""
        merchant = Merchant(
            merchant_key="test-merchant",
            platform="shopify",
            status="active",
            email="test@example.com",
            password_hash=hash_password("SecurePass123"),
        )
        db_session.add(merchant)
        await db_session.commit()
        await db_session.refresh(merchant)

        # Create session
        token = create_jwt(merchant_id=merchant.id, session_id="session-123")
        token_hash = hash_token(token)
        session = Session.create(merchant_id=merchant.id, token_hash=token_hash, hours=12)
        db_session.add(session)
        await db_session.commit()

        request = Mock()
        request.cookies = {SESSION_COOKIE_NAME: token}

        response = Mock()
        response.set_cookie = Mock()

        from app.api.auth import refresh_token as refresh_fn

        result = await refresh_fn(request, response, db_session)

        assert isinstance(result, MinimalEnvelope)
        assert isinstance(result.data, RefreshResponse)
        assert result.data.session.expiresAt is not None

        # Verify cookie was set
        response.set_cookie.assert_called_once()

        # Verify session was updated
        await db_session.refresh(session)
        # Expiration should be extended to 24 hours from now
        time_diff = (session.expires_at - datetime.utcnow()).total_seconds()
        assert 86300 <= time_diff <= 86500  # ~24 hours


class TestSessionRotation:
    """Tests for session rotation on login."""

    @pytest.mark.asyncio
    async def test_login_revokes_old_sessions(self, db_session: AsyncSession):
        """Login should revoke old sessions for merchant."""
        merchant = Merchant(
            merchant_key="test-merchant",
            platform="shopify",
            status="active",
            email="test@example.com",
            password_hash=hash_password("SecurePass123"),
        )
        db_session.add(merchant)
        await db_session.commit()
        await db_session.refresh(merchant)

        # Create old sessions
        token1 = create_jwt(merchant_id=merchant.id, session_id="session-1")
        token2 = create_jwt(merchant_id=merchant.id, session_id="session-2")
        session1 = Session.create(merchant_id=merchant.id, token_hash=hash_token(token1), hours=24)
        session2 = Session.create(merchant_id=merchant.id, token_hash=hash_token(token2), hours=24)
        db_session.add_all([session1, session2])
        await db_session.commit()

        # Login again
        request = Mock()
        request.cookies = {}

        response = Mock()
        response.set_cookie = Mock()

        credentials = LoginRequest(email="test@example.com", password="SecurePass123")

        from app.api.auth import login as login_fn

        await login_fn(request, credentials, response, db_session)

        # Verify old sessions are revoked
        await db_session.refresh(session1)
        await db_session.refresh(session2)
        assert session1.revoked is True
        assert session2.revoked is True
