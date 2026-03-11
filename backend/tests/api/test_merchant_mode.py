"""Tests for merchant mode API endpoints (Story 8.1).

AC1: New merchant defaults to "general" mode
AC2: GET /api/v1/merchants/me includes onboarding_mode
AC3: PATCH /api/v1/merchants/me/mode updates and logs mode change
"""

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.merchant import Merchant, OnboardingMode
from tests.conftest import auth_headers


class TestMerchantModeDefault:
    """Tests for AC1: New merchant defaults to 'general' mode."""

    @pytest.mark.asyncio
    async def test_new_merchant_defaults_to_general(
        self,
        async_session: AsyncSession,
    ) -> None:
        merchant = Merchant(
            merchant_key="test-mode-default",
            platform="facebook",
            email="mode-default@test.com",
        )
        async_session.add(merchant)
        await async_session.commit()
        await async_session.refresh(merchant)

        assert merchant.onboarding_mode == OnboardingMode.GENERAL.value


class TestGetMerchantMode:
    """Tests for AC2: GET /merchants/mode returns onboarding_mode."""

    @pytest.mark.asyncio
    async def test_get_mode_returns_current_mode(
        self,
        async_client: AsyncClient,
        test_merchant: int,
    ) -> None:
        headers = auth_headers(test_merchant)
        response = await async_client.get(
            "/api/v1/merchants/mode",
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "onboardingMode" in data["data"]

    @pytest.mark.asyncio
    async def test_get_mode_requires_auth(
        self,
        async_client: AsyncClient,
    ) -> None:
        response = await async_client.get("/api/v1/merchants/mode")
        assert response.status_code == 401


class TestUpdateMerchantMode:
    """Tests for AC3: PATCH /merchants/me/mode updates mode."""

    @pytest.fixture
    def merchant_with_headers(
        self,
        async_session: AsyncSession,
        test_merchant: int,
    ) -> dict:
        merchant = Merchant(
            merchant_key="test-mode-update",
            platform="facebook",
            email="mode-update@test.com",
        )
        async_session.add(merchant)
        await async_session.commit()
        await async_session.refresh(merchant)

        headers = auth_headers(merchant.id)
        return {"merchant": merchant, "headers": headers}


class TestMerchantModeInProfile:
    """Tests for AC2: onboarding_mode included in profile response."""

    @pytest.mark.asyncio
    async def test_mode_included_in_me_response(
        self,
        merchant_with_headers: dict,
        async_client: AsyncClient,
    ) -> None:
        headers = merchant_with_headers["headers"]
        response = await async_client.get(
            "/api/v1/auth/me",
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data


class TestCSRFProtection:
    """Tests for Task 5: CSRF bypass for mode endpoint."""

    @pytest.mark.asyncio
    async def test_csrf_bypass_for_mode_endpoint(
        self,
        merchant_with_headers: dict,
        async_client: AsyncClient,
    ) -> None:
        headers = merchant_with_headers["headers"]

        response = await async_client.patch(
            "/api/v1/merchants/mode",
            headers=headers,
            json={"mode": "ecommerce"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["onboardingMode"] == "ecommerce"
