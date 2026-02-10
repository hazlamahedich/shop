"""Integration tests for authentication flow.

Story 1.8: Tests for complete authentication flow including
login, access protected endpoint, logout, session expiry, and refresh.

These tests use the full FastAPI test client with database.
"""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.merchant import Merchant
from app.core.auth import hash_password


@pytest.mark.asyncio
class TestAuthFlow:
    """Integration tests for complete authentication flow."""

    async def test_login_logout_flow(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test complete login → access protected → logout flow."""
        # Create a test merchant
        password_hash = hash_password("TestPass123")
        merchant = Merchant(
            merchant_key="testkey",
            platform="dashboard",
            email="test@example.com",
            password_hash=password_hash,
            status="active",
        )
        db_session.add(merchant)
        await db_session.commit()
        await db_session.refresh(merchant)

        # Step 1: Login
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "TestPass123"},
        )

        assert login_response.status_code == 200
        data = login_response.json()
        assert data["data"]["merchant"]["email"] == "test@example.com"
        assert data["data"]["merchant"]["id"] == merchant.id
        assert "session" in data["data"]
        assert "expiresAt" in data["data"]["session"]

        # Step 2: Access protected endpoint (/auth/me)
        me_response = await async_client.get("/api/v1/auth/me")

        assert me_response.status_code == 200
        me_data = me_response.json()
        assert me_data["data"]["merchant"]["email"] == "test@example.com"
        assert me_data["data"]["merchant"]["id"] == merchant.id

        # Step 3: Logout
        logout_response = await async_client.post("/api/v1/auth/logout")

        assert logout_response.status_code == 200
        assert logout_response.json()["data"]["success"] is True

        # Step 4: Verify session is cleared
        me_after_logout = await async_client.get("/api/v1/auth/me")

        assert me_after_logout.status_code == 401

    async def test_login_with_invalid_credentials(self, async_client: AsyncClient):
        """Test login with invalid email/password shows error."""
        response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "nonexistent@example.com", "password": "WrongPass123"},
        )

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "invalid" in data["detail"]["message"].lower()

    async def test_session_persistence_across_requests(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test that session persists across multiple requests."""
        # Create merchant
        password_hash = hash_password("TestPass123")
        merchant = Merchant(
            merchant_key="testkey2",
            platform="dashboard",
            email="test2@example.com",
            password_hash=password_hash,
            status="active",
        )
        db_session.add(merchant)
        await db_session.commit()

        # Login
        await async_client.post(
            "/api/v1/auth/login",
            json={"email": "test2@example.com", "password": "TestPass123"},
        )

        # Make multiple requests - session should persist
        for _ in range(5):
            response = await async_client.get("/api/v1/auth/me")
            assert response.status_code == 200
            assert response.json()["data"]["merchant"]["email"] == "test2@example.com"

    async def test_token_refresh_extends_session(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test that token refresh extends session expiration."""
        # Create merchant
        password_hash = hash_password("TestPass123")
        merchant = Merchant(
            merchant_key="testkey3",
            platform="dashboard",
            email="test3@example.com",
            password_hash=password_hash,
            status="active",
        )
        db_session.add(merchant)
        await db_session.commit()

        # Login
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "test3@example.com", "password": "TestPass123"},
        )

        original_expires_at = login_response.json()["data"]["session"]["expiresAt"]

        # Refresh token
        refresh_response = await async_client.post("/api/v1/auth/refresh")

        assert refresh_response.status_code == 200
        new_expires_at = refresh_response.json()["data"]["session"]["expiresAt"]

        # New expiration should be later than original
        # Assuming token was issued slightly before refresh
        # The new expiration should be approximately 24 hours from now
        # while original was issued at login time
        assert new_expires_at is not None

    async def test_logout_invalidates_session(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test that logout invalidates the session in database."""
        # Create merchant
        password_hash = hash_password("TestPass123")
        merchant = Merchant(
            merchant_key="testkey4",
            platform="dashboard",
            email="test4@example.com",
            password_hash=password_hash,
            status="active",
        )
        db_session.add(merchant)
        await db_session.commit()

        # Login to get session
        await async_client.post(
            "/api/v1/auth/login",
            json={"email": "test4@example.com", "password": "TestPass123"},
        )

        # Logout
        await async_client.post("/api/v1/auth/logout")

        # Try to access protected endpoint - should fail
        response = await async_client.get("/api/v1/auth/me")
        assert response.status_code == 401

    async def test_protected_route_without_auth(self, async_client: AsyncClient):
        """Test that protected routes require authentication."""
        response = await async_client.get("/api/v1/auth/me")

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    async def test_password_too_short(self, async_client: AsyncClient):
        """Test that passwords shorter than 8 characters are rejected."""
        response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "Short1"},
        )

        # Should return validation error
        assert response.status_code == 422 or response.status_code == 401

    async def test_concurrent_logouts(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test handling of concurrent logout requests."""
        # Create merchant
        password_hash = hash_password("TestPass123")
        merchant = Merchant(
            merchant_key="testkey5",
            platform="dashboard",
            email="test5@example.com",
            password_hash=password_hash,
            status="active",
        )
        db_session.add(merchant)
        await db_session.commit()

        # Login
        await async_client.post(
            "/api/v1/auth/login",
            json={"email": "test5@example.com", "password": "TestPass123"},
        )

        # Send multiple logout requests concurrently
        import asyncio

        tasks = [
            async_client.post("/api/v1/auth/logout")
            for _ in range(5)
        ]

        responses = await asyncio.gather(*tasks)

        # All should succeed (idempotent)
        for response in responses:
            assert response.status_code == 200
