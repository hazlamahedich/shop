"""Tests for merchant personality configuration API endpoints (Story 1.10).

Tests the GET and PATCH endpoints for bot personality configuration.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.merchant import Merchant, PersonalityType


class TestGetPersonalityConfiguration:
    """Tests for GET /api/merchant/personality endpoint."""

    @pytest.mark.asyncio
    async def test_get_personality_configuration_friendly(self, async_client: AsyncClient, db_session: AsyncSession) -> None:
        """Test getting personality configuration with friendly personality (Story 1.10 AC 5)."""
        # Create merchant with friendly personality
        merchant = Merchant(
            merchant_key="test-get-personality-friendly",
            platform="facebook",
            status="active",
            personality=PersonalityType.FRIENDLY,
            custom_greeting="Hey! 👋 Welcome to my store!",
        )
        db_session.add(merchant)
        await db_session.commit()
        await db_session.refresh(merchant)

        # Get personality configuration
        response = await async_client.get(
            "/api/merchant/personality",
            headers={"X-Merchant-Id": str(merchant.id)},
        )

        assert response.status_code == 200
        response_data = response.json()
        # MinimalEnvelope format: {"data": {...}, "meta": {...}}
        data = response_data["data"]
        assert data["personality"] == "friendly"
        assert data["custom_greeting"] == "Hey! 👋 Welcome to my store!"

    @pytest.mark.asyncio
    async def test_get_personality_configuration_professional(self, async_client: AsyncClient, db_session: AsyncSession) -> None:
        """Test getting personality configuration with professional personality."""
        merchant = Merchant(
            merchant_key="test-get-personality-professional",
            platform="facebook",
            status="active",
            personality=PersonalityType.PROFESSIONAL,
            custom_greeting="Thank you for visiting. How may I assist you?",
        )
        db_session.add(merchant)
        await db_session.commit()
        await db_session.refresh(merchant)

        response = await async_client.get(
            "/api/merchant/personality",
            headers={"X-Merchant-Id": str(merchant.id)},
        )

        assert response.status_code == 200
        response_data = response.json()
        data = response_data["data"]
        assert data["personality"] == "professional"
        assert data["custom_greeting"] == "Thank you for visiting. How may I assist you?"

    @pytest.mark.asyncio
    async def test_get_personality_configuration_enthusiastic(self, async_client: AsyncClient, db_session: AsyncSession) -> None:
        """Test getting personality configuration with enthusiastic personality."""
        merchant = Merchant(
            merchant_key="test-get-personality-enthusiastic",
            platform="facebook",
            status="active",
            personality=PersonalityType.ENTHUSIASTIC,
            custom_greeting="YAY!!! Welcome to our AMAZING store!!! 🎉✨",
        )
        db_session.add(merchant)
        await db_session.commit()
        await db_session.refresh(merchant)

        response = await async_client.get(
            "/api/merchant/personality",
            headers={"X-Merchant-Id": str(merchant.id)},
        )

        assert response.status_code == 200
        response_data = response.json()
        data = response_data["data"]
        assert data["personality"] == "enthusiastic"
        assert data["custom_greeting"] == "YAY!!! Welcome to our AMAZING store!!! 🎉✨"

    @pytest.mark.asyncio
    async def test_get_personality_configuration_no_custom_greeting(self, async_client: AsyncClient, db_session: AsyncSession) -> None:
        """Test getting personality configuration without custom greeting (Story 1.10 AC 3)."""
        merchant = Merchant(
            merchant_key="test-get-personality-no-greeting",
            platform="facebook",
            status="active",
            personality=PersonalityType.FRIENDLY,
        )
        db_session.add(merchant)
        await db_session.commit()
        await db_session.refresh(merchant)

        response = await async_client.get(
            "/api/merchant/personality",
            headers={"X-Merchant-Id": str(merchant.id)},
        )

        assert response.status_code == 200
        response_data = response.json()
        data = response_data["data"]
        assert data["personality"] == "friendly"
        assert data["custom_greeting"] is None

    @pytest.mark.asyncio
    async def test_get_personality_configuration_default_personality(self, async_client: AsyncClient, db_session: AsyncSession) -> None:
        """Test that new merchants default to friendly personality (Story 1.10 AC 3)."""
        merchant = Merchant(
            merchant_key="test-get-personality-default",
            platform="facebook",
            status="active",
        )
        db_session.add(merchant)
        await db_session.commit()
        await db_session.refresh(merchant)

        response = await async_client.get(
            "/api/merchant/personality",
            headers={"X-Merchant-Id": str(merchant.id)},
        )

        assert response.status_code == 200
        response_data = response.json()
        data = response_data["data"]
        assert data["personality"] == "friendly"


class TestUpdatePersonalityConfiguration:
    """Tests for PATCH /api/merchant/personality endpoint."""

    @pytest.mark.asyncio
    async def test_update_personality_to_professional(self, async_client: AsyncClient, db_session: AsyncSession) -> None:
        """Test updating personality to professional (Story 1.10 AC 5)."""
        merchant = Merchant(
            merchant_key="test-update-personality-professional",
            platform="facebook",
            status="active",
            personality=PersonalityType.FRIENDLY,
        )
        db_session.add(merchant)
        await db_session.commit()
        await db_session.refresh(merchant)

        response = await async_client.patch(
            "/api/merchant/personality",
            json={"personality": "professional"},
            headers={"X-Merchant-Id": str(merchant.id)},
        )

        assert response.status_code == 200
        response_data = response.json()
        data = response_data["data"]
        assert data["personality"] == "professional"

        # Verify in database
        await db_session.refresh(merchant)
        assert merchant.personality == PersonalityType.PROFESSIONAL

    @pytest.mark.asyncio
    async def test_update_personality_to_enthusiastic(self, async_client: AsyncClient, db_session: AsyncSession) -> None:
        """Test updating personality to enthusiastic."""
        merchant = Merchant(
            merchant_key="test-update-personality-enthusiastic",
            platform="facebook",
            status="active",
            personality=PersonalityType.FRIENDLY,
        )
        db_session.add(merchant)
        await db_session.commit()
        await db_session.refresh(merchant)

        response = await async_client.patch(
            "/api/merchant/personality",
            json={"personality": "enthusiastic"},
            headers={"X-Merchant-Id": str(merchant.id)},
        )

        assert response.status_code == 200
        response_data = response.json()
        data = response_data["data"]
        assert data["personality"] == "enthusiastic"

    @pytest.mark.asyncio
    async def test_update_custom_greeting(self, async_client: AsyncClient, db_session: AsyncSession) -> None:
        """Test updating custom greeting (Story 1.10 AC 5)."""
        merchant = Merchant(
            merchant_key="test-update-greeting",
            platform="facebook",
            status="active",
            personality=PersonalityType.FRIENDLY,
        )
        db_session.add(merchant)
        await db_session.commit()
        await db_session.refresh(merchant)

        new_greeting = "Hey there! Welcome to Alex's Awesome Shop! How can I help you today?"
        response = await async_client.patch(
            "/api/merchant/personality",
            json={"custom_greeting": new_greeting},
            headers={"X-Merchant-Id": str(merchant.id)},
        )

        assert response.status_code == 200
        response_data = response.json()
        data = response_data["data"]
        assert data["custom_greeting"] == new_greeting

    @pytest.mark.asyncio
    async def test_update_both_personality_and_greeting(self, async_client: AsyncClient, db_session: AsyncSession) -> None:
        """Test updating both personality and custom greeting simultaneously."""
        merchant = Merchant(
            merchant_key="test-update-both",
            platform="facebook",
            status="active",
            personality=PersonalityType.FRIENDLY,
        )
        db_session.add(merchant)
        await db_session.commit()
        await db_session.refresh(merchant)

        response = await async_client.patch(
            "/api/merchant/personality",
            json={
                "personality": "enthusiastic",
                "custom_greeting": "WOOHOO!!! Welcome to the BEST store EVER!!! 🎉🔥",
            },
            headers={"X-Merchant-Id": str(merchant.id)},
        )

        assert response.status_code == 200
        response_data = response.json()
        data = response_data["data"]
        assert data["personality"] == "enthusiastic"
        assert data["custom_greeting"] == "WOOHOO!!! Welcome to the BEST store EVER!!! 🎉🔥"

    @pytest.mark.asyncio
    async def test_update_clear_custom_greeting(self, async_client: AsyncClient, db_session: AsyncSession) -> None:
        """Test clearing custom greeting by setting to empty string."""
        merchant = Merchant(
            merchant_key="test-clear-greeting",
            platform="facebook",
            status="active",
            personality=PersonalityType.FRIENDLY,
            custom_greeting="Old greeting",
        )
        db_session.add(merchant)
        await db_session.commit()
        await db_session.refresh(merchant)

        response = await async_client.patch(
            "/api/merchant/personality",
            json={"custom_greeting": ""},
            headers={"X-Merchant-Id": str(merchant.id)},
        )

        assert response.status_code == 200
        response_data = response.json()
        data = response_data["data"]
        assert data["custom_greeting"] is None

    @pytest.mark.asyncio
    async def test_update_custom_greeting_max_length(self, async_client: AsyncClient, db_session: AsyncSession) -> None:
        """Test updating custom greeting with exactly 500 characters (Story 1.10 AC 2)."""
        merchant = Merchant(
            merchant_key="test-update-greeting-max",
            platform="facebook",
            status="active",
            personality=PersonalityType.FRIENDLY,
        )
        db_session.add(merchant)
        await db_session.commit()
        await db_session.refresh(merchant)

        # Create greeting with exactly 500 characters
        max_greeting = "Welcome! " * 100  # "Welcome! " is 9 chars, 9 * 100 = 900 chars... wait let me fix
        max_greeting = "Hi! " * 125  # "Hi! " is 4 chars, 4 * 125 = 500 chars

        response = await async_client.patch(
            "/api/merchant/personality",
            json={"custom_greeting": max_greeting},
            headers={"X-Merchant-Id": str(merchant.id)},
        )

        assert response.status_code == 200
        response_data = response.json()
        data = response_data["data"]
        assert len(data["custom_greeting"]) == 500

    @pytest.mark.asyncio
    async def test_update_custom_greeting_exceeds_max_length(self, async_client: AsyncClient, db_session: AsyncSession) -> None:
        """Test that custom greeting exceeding 500 characters is rejected (Story 1.10 AC 2)."""
        merchant = Merchant(
            merchant_key="test-update-greeting-exceeds",
            platform="facebook",
            status="active",
            personality=PersonalityType.FRIENDLY,
        )
        db_session.add(merchant)
        await db_session.commit()
        await db_session.refresh(merchant)

        # Create greeting with 501 characters
        too_long_greeting = "Hi! " * 125 + "!"  # 500 + 1 = 501 characters

        response = await async_client.patch(
            "/api/merchant/personality",
            json={"custom_greeting": too_long_greeting},
            headers={"X-Merchant-Id": str(merchant.id)},
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_update_personality_no_changes(self, async_client: AsyncClient, db_session: AsyncSession) -> None:
        """Test updating with empty body returns current configuration."""
        merchant = Merchant(
            merchant_key="test-update-no-changes",
            platform="facebook",
            status="active",
            personality=PersonalityType.PROFESSIONAL,
            custom_greeting="Original greeting",
        )
        db_session.add(merchant)
        await db_session.commit()
        await db_session.refresh(merchant)

        response = await async_client.patch(
            "/api/merchant/personality",
            json={},
            headers={"X-Merchant-Id": str(merchant.id)},
        )

        assert response.status_code == 200
        response_data = response.json()
        data = response_data["data"]
        assert data["personality"] == "professional"
        assert data["custom_greeting"] == "Original greeting"

    @pytest.mark.asyncio
    async def test_update_personality_invalid_type(self, async_client: AsyncClient, db_session: AsyncSession) -> None:
        """Test that invalid personality type is rejected."""
        merchant = Merchant(
            merchant_key="test-update-invalid-personality",
            platform="facebook",
            status="active",
            personality=PersonalityType.FRIENDLY,
        )
        db_session.add(merchant)
        await db_session.commit()
        await db_session.refresh(merchant)

        response = await async_client.patch(
            "/api/merchant/personality",
            json={"personality": "aggressive"},  # Invalid personality type
            headers={"X-Merchant-Id": str(merchant.id)},
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_update_personality_merchant_not_found(self, async_client: AsyncClient, db_session: AsyncSession) -> None:
        """Test updating configuration for non-existent merchant."""
        response = await async_client.patch(
            "/api/merchant/personality",
            json={"personality": "professional"},
            headers={"X-Merchant-Id": "99999"},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_personality_merchant_not_found(self, async_client: AsyncClient, db_session: AsyncSession) -> None:
        """Test getting configuration for non-existent merchant."""
        response = await async_client.get(
            "/api/merchant/personality",
            headers={"X-Merchant-Id": "99999"},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_personality_whitespace_greeting(self, async_client: AsyncClient, db_session: AsyncSession) -> None:
        """Test that whitespace-only greeting is treated as None."""
        merchant = Merchant(
            merchant_key="test-update-whitespace-greeting",
            platform="facebook",
            status="active",
            personality=PersonalityType.FRIENDLY,
            custom_greeting="Original greeting",
        )
        db_session.add(merchant)
        await db_session.commit()
        await db_session.refresh(merchant)

        response = await async_client.patch(
            "/api/merchant/personality",
            json={"custom_greeting": "   "},
            headers={"X-Merchant-Id": str(merchant.id)},
        )

        assert response.status_code == 200
        response_data = response.json()
        data = response_data["data"]
        assert data["custom_greeting"] is None
