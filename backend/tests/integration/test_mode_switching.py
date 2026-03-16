"""Integration tests for mode switching.

Story 8-9: Testing & Quality Assurance
Task 2.1: Create backend/tests/integration/test_mode_switching.py
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.merchant import Merchant
from tests.conftest import auth_headers as make_auth_headers


class TestModeSwitchingIntegration:
    """Integration tests for switching between E-commerce and General modes."""

    @pytest.mark.asyncio
    @pytest.mark.test_id("8-9-INT-005")
    @pytest.mark.priority("P0")
    async def test_mode_switch_general_to_ecommerce(
        self,
        async_client: AsyncClient,
        async_session: AsyncSession,
        test_merchant: int,
    ):
        """Test switching from General to E-commerce mode."""
        merchant_id = test_merchant
        headers = make_auth_headers(merchant_id)

        # 1. Ensure starting in general mode
        result = await async_session.execute(select(Merchant).where(Merchant.id == merchant_id))
        merchant = result.scalar_one()
        merchant.onboarding_mode = "general"
        await async_session.commit()

        # 2. Switch to ecommerce mode
        response = await async_client.patch(
            "/api/merchant/mode",
            json={"mode": "ecommerce"},
            headers=headers,
        )

        assert response.status_code == 200
        assert response.json()["data"]["onboardingMode"] == "ecommerce"

        # 3. Verify in database
        await async_session.refresh(merchant)
        assert merchant.onboarding_mode == "ecommerce"

    @pytest.mark.asyncio
    @pytest.mark.test_id("8-9-INT-006")
    @pytest.mark.priority("P0")
    async def test_mode_switch_ecommerce_to_general(
        self,
        async_client: AsyncClient,
        async_session: AsyncSession,
        test_merchant: int,
    ):
        """Test switching from E-commerce to General mode."""
        merchant_id = test_merchant
        headers = make_auth_headers(merchant_id)

        # 1. Ensure starting in ecommerce mode
        result = await async_session.execute(select(Merchant).where(Merchant.id == merchant_id))
        merchant = result.scalar_one()
        merchant.onboarding_mode = "ecommerce"
        await async_session.commit()

        # 2. Switch to general mode
        response = await async_client.patch(
            "/api/merchant/mode",
            json={"mode": "general"},
            headers=headers,
        )

        assert response.status_code == 200
        assert response.json()["data"]["onboardingMode"] == "general"

        # 3. Verify in database
        await async_session.refresh(merchant)
        assert merchant.onboarding_mode == "general"

    @pytest.mark.asyncio
    @pytest.mark.test_id("8-9-INT-007")
    @pytest.mark.priority("P2")
    async def test_invalid_mode_switch_fails(
        self,
        async_client: AsyncClient,
        test_merchant: int,
    ):
        """Test switching to an invalid mode fails."""
        headers = make_auth_headers(test_merchant)

        response = await async_client.patch(
            "/api/merchant/mode",
            json={"mode": "invalid-mode"},
            headers=headers,
        )

        assert response.status_code in [400, 422]  # Validation error or bad request

    @pytest.mark.asyncio
    @pytest.mark.test_id("8-9-INT-008")
    @pytest.mark.priority("P1")
    async def test_mode_persistence_after_update(
        self,
        async_client: AsyncClient,
        async_session: AsyncSession,
        test_merchant: int,
    ):
        """Test that mode persists across multiple requests after update."""
        merchant_id = test_merchant
        headers = make_auth_headers(merchant_id)

        # 1. Update to general
        await async_client.patch(
            "/api/merchant/mode",
            json={"mode": "general"},
            headers=headers,
        )

        # 2. Get mode to verify persistence
        response = await async_client.get(
            "/api/merchant/mode",
            headers=headers,
        )

        assert response.status_code == 200
        assert response.json()["data"]["onboardingMode"] == "general"
