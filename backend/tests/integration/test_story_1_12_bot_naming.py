"""Integration tests for Story 1.12: Bot Naming.

Tests the full bot name configuration flow and integration with bot responses.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.merchant import Merchant


class TestBotNamingIntegration:
    """Integration tests for bot naming configuration flow."""

    @pytest.fixture
    def merchant_headers(self):
        """Get merchant authentication headers for DEBUG mode."""
        return {"X-Merchant-Id": "1"}

    @pytest.mark.asyncio
    async def test_full_bot_naming_flow(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        merchant_headers: dict,
    ):
        """Test complete bot naming flow: GET config, UPDATE bot name, VERIFY persistence (Story 1.12).

        Flow:
        1. Create merchant in database
        2. GET initial bot config (should have no bot name)
        3. UPDATE bot name to "GearBot"
        4. GET config again to verify persistence
        5. UPDATE bot name to empty string (clear it)
        6. GET config again to verify cleared
        """
        # Step 0: Create merchant with ID=1
        merchant = Merchant(
            id=1,
            merchant_key="test-merchant-1",
            platform="facebook",
            status="active",
        )
        db_session.add(merchant)
        await db_session.commit()
        await db_session.refresh(merchant)

        # Step 1: Get initial config (no bot name)
        response = await async_client.get(
            "/api/v1/merchant/bot-config",
            headers=merchant_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["botName"] is None

        # Step 2: Update bot name to "GearBot"
        response = await async_client.put(
            "/api/v1/merchant/bot-config",
            json={"bot_name": "GearBot"},
            headers=merchant_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["botName"] == "GearBot"

        # Step 3: Verify persistence by getting config again
        response = await async_client.get(
            "/api/v1/merchant/bot-config",
            headers=merchant_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["botName"] == "GearBot"

        # Verify database has the value (refresh to see committed changes from API)
        await db_session.refresh(merchant)
        assert merchant.bot_name == "GearBot"

        # Step 4: Clear bot name with empty string
        response = await async_client.put(
            "/api/v1/merchant/bot-config",
            json={"bot_name": ""},
            headers=merchant_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["botName"] is None

        # Step 5: Verify cleared
        response = await async_client.get(
            "/api/v1/merchant/bot-config",
            headers=merchant_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["botName"] is None

    @pytest.mark.asyncio
    async def test_bot_name_whitespace_handling(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        merchant_headers: dict,
    ):
        """Test whitespace is automatically stripped from bot name (Story 1.12 AC 2)."""
        # Create merchant
        merchant = Merchant(
            id=1,
            merchant_key="test-merchant-2",
            platform="facebook",
            status="active",
        )
        db_session.add(merchant)
        await db_session.commit()

        # Update with extra whitespace
        response = await async_client.put(
            "/api/v1/merchant/bot-config",
            json={"bot_name": "  GearBot  "},
            headers=merchant_headers,
        )
        assert response.status_code == 200
        data = response.json()
        # Should be stripped
        assert data["data"]["botName"] == "GearBot"

    @pytest.mark.asyncio
    async def test_bot_name_max_length_validation(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        merchant_headers: dict,
    ):
        """Test bot name max length validation (Story 1.12 AC 2)."""
        # Create merchant
        merchant = Merchant(
            id=1,
            merchant_key="test-merchant-3",
            platform="facebook",
            status="active",
        )
        db_session.add(merchant)
        await db_session.commit()

        # 51 characters should fail
        long_name = "A" * 51
        response = await async_client.put(
            "/api/v1/merchant/bot-config",
            json={"bot_name": long_name},
            headers=merchant_headers,
        )
        assert response.status_code == 422  # Validation error

        # 50 characters should succeed
        valid_name = "A" * 50
        response = await async_client.put(
            "/api/v1/merchant/bot-config",
            json={"bot_name": valid_name},
            headers=merchant_headers,
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_bot_name_persistence_across_sessions(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        merchant_headers: dict,
    ):
        """Test bot name persists across merchant sessions (Story 1.12 AC 2)."""
        # Create merchant
        merchant = Merchant(
            id=1,
            merchant_key="test-merchant-4",
            platform="facebook",
            status="active",
        )
        db_session.add(merchant)
        await db_session.commit()

        # Set bot name
        response = await async_client.put(
            "/api/v1/merchant/bot-config",
            json={"bot_name": "PersistentBot"},
            headers=merchant_headers,
        )
        assert response.status_code == 200

        # Verify in database
        result = await db_session.execute(select(Merchant).where(Merchant.id == 1))
        merchant_obj = result.scalar_one_or_none()
        assert merchant_obj.bot_name == "PersistentBot"

        # Simulate new session by getting config again
        response = await async_client.get(
            "/api/v1/merchant/bot-config",
            headers=merchant_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["botName"] == "PersistentBot"


class TestBotNamingErrorCases:
    """Integration tests for bot naming error handling."""

    @pytest.fixture
    def merchant_headers(self):
        """Get merchant authentication headers for DEBUG mode."""
        return {"X-Merchant-Id": "1"}

    @pytest.mark.asyncio
    async def test_get_without_merchant_id_fails(
        self,
        async_client: AsyncClient,
    ):
        """Test getting bot config without authentication fails (Story 1.12 AC 5)."""
        response = await async_client.get("/api/v1/merchant/bot-config")
        # In DEBUG mode without X-Merchant-Id header, it tries merchant_id=None
        # which leads to MERCHANT_NOT_FOUND (404)
        assert response.status_code in (401, 404)

    @pytest.mark.asyncio
    async def test_update_without_merchant_id_fails(
        self,
        async_client: AsyncClient,
    ):
        """Test updating bot name without authentication fails (Story 1.12 AC 5)."""
        response = await async_client.put(
            "/api/v1/merchant/bot-config",
            json={"bot_name": "HackerBot"},
        )
        # In DEBUG mode without X-Merchant-Id header, it tries merchant_id=None
        # which leads to MERCHANT_NOT_FOUND (404)
        assert response.status_code in (401, 404)

    @pytest.mark.asyncio
    async def test_nonexistent_merchant_returns_404(
        self,
        async_client: AsyncClient,
        merchant_headers: dict,
    ):
        """Test accessing config for non-existent merchant returns 404."""
        # Don't create merchant - ID 999 doesn't exist
        response = await async_client.get(
            "/api/v1/merchant/bot-config",
            headers={"X-Merchant-Id": "999"},
        )
        assert response.status_code == 404
