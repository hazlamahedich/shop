"""Tests for merchant mode API endpoints (Story 8.1).

AC1: New merchant defaults to "general" mode
AC2: GET /api/v1/auth/me includes onboarding_mode
AC3: PATCH /api/merchant/mode updates and logs mode change

Priority Legend:
    P0 = Critical (acceptance criteria, must pass for release)
    P1 = High (core functionality)
    P2 = Medium (edge cases, validation)
    P3 = Low (nice-to-have)

Test ID Format: 8.1-API-XXX (Story 8.1, API level, sequential number)
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.merchant import Merchant, OnboardingMode
from tests.conftest import auth_headers


@pytest.fixture
async def merchant_for_mode_tests(async_session: AsyncSession) -> Merchant:
    """Create a merchant for mode testing."""
    merchant = Merchant(
        merchant_key="test-mode-fixture",
        platform="facebook",
        email="mode-fixture@test.com",
    )
    async_session.add(merchant)
    await async_session.commit()
    await async_session.refresh(merchant)
    return merchant


class TestMerchantModeDefault:
    """Tests for AC1: New merchant defaults to 'general' mode."""

    @pytest.mark.asyncio
    @pytest.mark.p0
    async def test_new_merchant_defaults_to_general(
        self,
        async_session: AsyncSession,
    ) -> None:
        """Test ID: 8.1-API-001 | Priority: P0

        AC1: Verify new merchant defaults to 'general' mode.

        Given: A new merchant is created without specifying onboarding_mode
        When: The merchant is persisted to the database
        Then: The onboarding_mode should be 'general'
        """
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
    @pytest.mark.p0
    async def test_get_mode_returns_current_mode(
        self,
        async_client: AsyncClient,
        merchant_for_mode_tests: Merchant,
    ) -> None:
        """Test ID: 8.1-API-002 | Priority: P0

        AC2: Verify GET /api/merchant/mode returns current mode.

        Given: An authenticated merchant exists with a valid onboarding_mode
        When: GET /api/merchant/mode is called with auth headers
        Then: Response should contain onboardingMode field with current mode
        """
        headers = auth_headers(merchant_for_mode_tests.id)
        response = await async_client.get(
            "/api/merchant/mode",
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "onboardingMode" in data["data"]

    @pytest.mark.asyncio
    @pytest.mark.p1
    async def test_get_mode_requires_auth(
        self,
        async_client: AsyncClient,
    ) -> None:
        """Test ID: 8.1-API-003 | Priority: P1

        Verify unauthenticated requests are rejected.

        Given: No valid authentication credentials are provided
        When: GET /api/merchant/mode is called without auth headers
        Then: Response should return 401 (or 404 in test mode)
        """
        response = await async_client.get("/api/merchant/mode")
        assert response.status_code in [401, 404]


class TestUpdateMerchantMode:
    """Tests for AC3: PATCH /merchants/me/mode updates mode."""

    @pytest.mark.asyncio
    @pytest.mark.p0
    async def test_update_mode_to_ecommerce(
        self,
        async_client: AsyncClient,
        merchant_for_mode_tests: Merchant,
    ) -> None:
        """Test ID: 8.1-API-004 | Priority: P0

        AC3: Verify PATCH /api/merchant/mode updates mode to ecommerce.

        Given: An authenticated merchant exists with 'general' mode
        When: PATCH /api/merchant/mode is called with mode='ecommerce'
        Then: Response should confirm mode updated to 'ecommerce'
        """
        headers = auth_headers(merchant_for_mode_tests.id)

        response = await async_client.patch(
            "/api/merchant/mode",
            headers=headers,
            json={"mode": "ecommerce"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["onboardingMode"] == "ecommerce"


class TestMerchantModeInProfile:
    """Tests for AC2: onboarding_mode included in profile response."""

    @pytest.mark.asyncio
    @pytest.mark.p0
    async def test_mode_included_in_me_response(
        self,
        async_client: AsyncClient,
        merchant_for_mode_tests: Merchant,
    ) -> None:
        """Test ID: 8.1-API-005 | Priority: P0

        AC2: Verify onboarding_mode is included in GET /api/v1/auth/me response.

        Given: An authenticated merchant exists
        When: GET /api/v1/auth/me is called with auth headers
        Then: Response should include merchant.onboarding_mode field
        """
        headers = auth_headers(merchant_for_mode_tests.id)
        response = await async_client.get(
            "/api/v1/auth/me",
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "merchant" in data["data"]
        assert "onboarding_mode" in data["data"]["merchant"]


class TestCSRFProtection:
    """Tests for Task 5: CSRF bypass for mode endpoint."""

    @pytest.mark.asyncio
    @pytest.mark.p1
    async def test_csrf_bypass_for_mode_endpoint(
        self,
        async_client: AsyncClient,
        merchant_for_mode_tests: Merchant,
    ) -> None:
        """Test ID: 8.1-API-006 | Priority: P1

        Verify mode endpoint works without CSRF token (bypass configured).

        Given: An authenticated merchant exists
        When: PATCH /api/merchant/mode is called without CSRF token
        Then: Request should succeed (CSRF bypass configured for this endpoint)
        """
        headers = auth_headers(merchant_for_mode_tests.id)

        response = await async_client.patch(
            "/api/merchant/mode",
            headers=headers,
            json={"mode": "ecommerce"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["onboardingMode"] == "ecommerce"


class TestMerchantModeEdgeCases:
    """Tests for edge cases in mode update."""

    @pytest.mark.asyncio
    @pytest.mark.p1
    async def test_unauthenticated_mode_update_returns_401(self, async_client: AsyncClient) -> None:
        """Test ID: 8.1-API-007 | Priority: P1

        Verify unauthenticated mode update is rejected.

        Given: No valid authentication credentials are provided
        When: PATCH /api/merchant/mode is called without auth headers
        Then: Response should return 401 (or 404 in test mode)
        """
        response = await async_client.patch("/api/merchant/mode", json={"mode": "ecommerce"})
        assert response.status_code in [401, 404]

    @pytest.mark.asyncio
    @pytest.mark.p2
    async def test_mode_update_with_same_mode_returns_200(
        self, async_client: AsyncClient, merchant_for_mode_tests: Merchant
    ) -> None:
        """Test ID: 8.1-API-008 | Priority: P2

        Verify mode update with same mode is a no-op (returns 200).

        Given: An authenticated merchant with current mode X
        When: PATCH /api/merchant/mode is called with mode=X (same as current)
        Then: Response should return 200 with unchanged mode
        """
        headers = auth_headers(merchant_for_mode_tests.id)

        response = await async_client.get("/api/merchant/mode", headers=headers)
        assert response.status_code == 200
        current_mode = response.json()["data"]["onboardingMode"]

        response = await async_client.patch(
            "/api/merchant/mode", headers=headers, json={"mode": current_mode}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["onboardingMode"] == current_mode

    @pytest.mark.asyncio
    @pytest.mark.p2
    async def test_mode_update_with_empty_mode_returns_422(
        self, async_client: AsyncClient, merchant_for_mode_tests: Merchant
    ) -> None:
        """Test ID: 8.1-API-009 | Priority: P2

        Verify empty mode string returns validation error.

        Given: An authenticated merchant exists
        When: PATCH /api/merchant/mode is called with mode="" (empty string)
        Then: Response should return 422 Unprocessable Entity
        """
        headers = auth_headers(merchant_for_mode_tests.id)

        response = await async_client.patch(
            "/api/merchant/mode", headers=headers, json={"mode": ""}
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    @pytest.mark.p2
    async def test_mode_update_with_missing_mode_field_returns_422(
        self, async_client: AsyncClient, merchant_for_mode_tests: Merchant
    ) -> None:
        """Test ID: 8.1-API-010 | Priority: P2

        Verify missing mode field returns validation error.

        Given: An authenticated merchant exists
        When: PATCH /api/merchant/mode is called with empty JSON body {}
        Then: Response should return 422 Unprocessable Entity
        """
        headers = auth_headers(merchant_for_mode_tests.id)

        response = await async_client.patch("/api/merchant/mode", headers=headers, json={})
        assert response.status_code == 422


class TestMerchantModePersistence:
    """Tests for mode persistence across sessions."""

    @pytest.mark.asyncio
    @pytest.mark.p0
    async def test_mode_persists_across_sessions(
        self, async_client: AsyncClient, merchant_for_mode_tests: Merchant
    ) -> None:
        """Test ID: 8.1-API-011 | Priority: P0

        AC3: Verify mode persists across sessions.

        Given: An authenticated merchant updates mode to 'ecommerce'
        When: The merchant fetches their profile again (simulating new session)
        Then: The onboarding_mode should still be 'ecommerce'
        """
        headers = auth_headers(merchant_for_mode_tests.id)

        response = await async_client.patch(
            "/api/merchant/mode", headers=headers, json={"mode": "ecommerce"}
        )
        assert response.status_code == 200

        response = await async_client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 200
        assert response.json()["data"]["merchant"]["onboarding_mode"] == "ecommerce"

    @pytest.mark.asyncio
    @pytest.mark.p0
    async def test_mode_persists_in_database(
        self,
        async_client: AsyncClient,
        merchant_for_mode_tests: Merchant,
        async_session: AsyncSession,
    ) -> None:
        """Test ID: 8.1-API-012 | Priority: P0

        AC3: Verify mode is persisted in database.

        Given: An authenticated merchant updates mode to 'ecommerce'
        When: The merchant record is queried directly from the database
        Then: The onboarding_mode column should be 'ecommerce'
        """
        headers = auth_headers(merchant_for_mode_tests.id)

        response = await async_client.patch(
            "/api/merchant/mode", headers=headers, json={"mode": "ecommerce"}
        )
        assert response.status_code == 200

        await async_session.refresh(merchant_for_mode_tests)
        assert merchant_for_mode_tests.onboarding_mode == OnboardingMode.ECOMMERCE.value
