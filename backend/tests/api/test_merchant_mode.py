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
    await async_session.flush()  # Ensure ID is generated before commit
    await async_session.commit()
    assert merchant.id is not None, "Merchant ID should be populated after flush"
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
        assert "onboardingMode" in data["data"]["merchant"]


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
        assert response.json()["data"]["merchant"]["onboardingMode"] == "ecommerce"

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


# ==============================================================================
# STORY 8.2 TESTS: Onboarding Mode Selection During Registration
# ==============================================================================


class TestRegistrationWithMode:
    """Tests for Story 8.2 AC1 and AC3: Registration with mode selection."""

    @pytest.mark.asyncio
    @pytest.mark.p0
    async def test_registration_with_general_mode_stores_correctly(
        self,
        async_client: AsyncClient,
    ) -> None:
        """Test ID: 8.2-API-001 | Priority: P0

        AC1: Verify registration with mode='general' stores correctly.

        Given: A registration request with mode='general'
        When: POST /api/v1/auth/register is called
        Then: Merchant should be created with onboarding_mode='general'
        """
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "general-mode@test.com",
                "password": "TestPass123",
                "mode": "general",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert "data" in data
        assert "merchant" in data["data"]
        assert data["data"]["merchant"]["onboardingMode"] == "general"

    @pytest.mark.asyncio
    @pytest.mark.p0
    async def test_registration_with_ecommerce_mode_stores_correctly(
        self,
        async_client: AsyncClient,
    ) -> None:
        """Test ID: 8.2-API-002 | Priority: P0

        AC1: Verify registration with mode='ecommerce' stores correctly.

        Given: A registration request with mode='ecommerce'
        When: POST /api/v1/auth/register is called
        Then: Merchant should be created with onboarding_mode='ecommerce'
        """
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "ecommerce-mode@test.com",
                "password": "TestPass123",
                "mode": "ecommerce",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert "data" in data
        assert "merchant" in data["data"]
        assert data["data"]["merchant"]["onboardingMode"] == "ecommerce"

    @pytest.mark.asyncio
    @pytest.mark.p0
    async def test_registration_without_mode_defaults_to_general(
        self,
        async_client: AsyncClient,
    ) -> None:
        """Test ID: 8.2-API-003 | Priority: P0

        AC3: Verify registration without mode defaults to 'general'.

        Given: A registration request without mode field
        When: POST /api/v1/auth/register is called
        Then: Merchant should be created with onboarding_mode='general'
        """
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "no-mode@test.com",
                "password": "TestPass123",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert "data" in data
        assert "merchant" in data["data"]
        assert data["data"]["merchant"]["onboardingMode"] == "general"

    @pytest.mark.asyncio
    @pytest.mark.p2
    async def test_registration_with_invalid_mode_returns_422(
        self,
        async_client: AsyncClient,
    ) -> None:
        """Test ID: 8.2-API-004 | Priority: P2

        Verify registration with invalid mode returns validation error.

        Given: A registration request with mode='invalid'
        When: POST /api/v1/auth/register is called
        Then: Response should return 422 Unprocessable Entity
        """
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "invalid-mode@test.com",
                "password": "TestPass123",
                "mode": "invalid",
            },
        )

        assert response.status_code == 422


class TestConnectionStatusInAuthResponses:
    """Tests for Story 8.2 AC2 and AC4: Connection flags in auth responses."""

    @pytest.mark.asyncio
    @pytest.mark.p0
    async def test_login_response_includes_all_connection_flags(
        self,
        async_client: AsyncClient,
    ) -> None:
        """Test ID: 8.2-API-005 | Priority: P0

        AC4: Verify login response includes onboarding_mode and connection flags.

        Given: A registered merchant
        When: POST /api/v1/auth/login is called
        Then: Response should include onboardingMode, hasStoreConnected, hasFacebookConnected
        """
        # Register first
        await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "login-flags@test.com",
                "password": "TestPass123",
                "mode": "general",
            },
        )

        # Login
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": "login-flags@test.com",
                "password": "TestPass123",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "merchant" in data["data"]
        merchant = data["data"]["merchant"]
        assert "onboardingMode" in merchant
        assert "hasStoreConnected" in merchant
        assert "hasFacebookConnected" in merchant

    @pytest.mark.asyncio
    @pytest.mark.p0
    async def test_register_response_includes_all_connection_flags(
        self,
        async_client: AsyncClient,
    ) -> None:
        """Test ID: 8.2-API-006 | Priority: P0

        AC4: Verify register response includes onboarding_mode and connection flags.

        Given: A registration request
        When: POST /api/v1/auth/register is called
        Then: Response should include onboardingMode, hasStoreConnected, hasFacebookConnected
        """
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "register-flags@test.com",
                "password": "TestPass123",
                "mode": "general",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert "data" in data
        assert "merchant" in data["data"]
        merchant = data["data"]["merchant"]
        assert "onboardingMode" in merchant
        assert "hasStoreConnected" in merchant
        assert "hasFacebookConnected" in merchant

    @pytest.mark.asyncio
    @pytest.mark.p0
    async def test_me_response_includes_all_connection_flags(
        self,
        async_client: AsyncClient,
    ) -> None:
        """Test ID: 8.2-API-011 | Priority: P0

        AC4: Verify /me endpoint includes onboarding_mode and connection flags.

        Given: A registered and logged-in merchant
        When: GET /api/v1/auth/me is called with auth headers
        Then: Response should include onboardingMode, hasStoreConnected, hasFacebookConnected
        """
        # Register and login
        register_response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "me-flags@test.com",
                "password": "TestPass123",
                "mode": "general",
            },
        )

        assert register_response.status_code == 201

        # Extract session token from cookie
        session_token = register_response.cookies.get("session_token")
        assert session_token is not None

        # Call /me endpoint with session cookie
        response = await async_client.get(
            "/api/v1/auth/me",
            cookies={"session_token": session_token},
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "merchant" in data["data"]
        merchant = data["data"]["merchant"]
        assert "onboardingMode" in merchant
        assert "hasStoreConnected" in merchant
        assert "hasFacebookConnected" in merchant

    @pytest.mark.asyncio
    @pytest.mark.p0
    async def test_general_mode_merchant_has_false_connection_flags(
        self,
        async_client: AsyncClient,
    ) -> None:
        """Test ID: 8.2-API-007 | Priority: P0

        AC2: Verify general mode merchant has false connection flags.

        Given: A merchant with mode='general'
        When: Auth status is retrieved
        Then: hasStoreConnected=false and hasFacebookConnected=false
        """
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "general-flags@test.com",
                "password": "TestPass123",
                "mode": "general",
            },
        )

        assert response.status_code == 201
        data = response.json()
        merchant = data["data"]["merchant"]
        assert merchant["onboardingMode"] == "general"
        assert merchant["hasStoreConnected"] is False
        assert merchant["hasFacebookConnected"] is False

    @pytest.mark.asyncio
    @pytest.mark.p1
    async def test_ecommerce_mode_with_no_connections_has_false_flags(
        self,
        async_client: AsyncClient,
    ) -> None:
        """Test ID: 8.2-API-008 | Priority: P1

        AC2: Verify ecommerce mode with no connections has false flags.

        Given: A merchant with mode='ecommerce' and no Shopify/Facebook connections
        When: Auth status is retrieved
        Then: hasStoreConnected=false and hasFacebookConnected=false
        """
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "ecommerce-no-conn@test.com",
                "password": "TestPass123",
                "mode": "ecommerce",
            },
        )

        assert response.status_code == 201
        data = response.json()
        merchant = data["data"]["merchant"]
        assert merchant["onboardingMode"] == "ecommerce"
        assert merchant["hasStoreConnected"] is False
        assert merchant["hasFacebookConnected"] is False

    @pytest.mark.asyncio
    @pytest.mark.p1
    async def test_ecommerce_mode_with_shopify_has_true_store_flag(
        self,
        async_client: AsyncClient,
        async_session: AsyncSession,
    ) -> None:
        """Test ID: 8.2-API-009 | Priority: P1

        AC2: Verify ecommerce mode with Shopify connection has true store flag.

        Given: A merchant with mode='ecommerce' and Shopify connected
        When: Auth status is retrieved
        Then: hasStoreConnected=true
        """
        # Register ecommerce merchant
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "ecommerce-shopify@test.com",
                "password": "TestPass123",
                "mode": "ecommerce",
            },
        )

        assert response.status_code == 201
        merchant_id = response.json()["data"]["merchant"]["id"]

        # Manually set store_provider to simulate Shopify connection
        from sqlalchemy import select

        result = await async_session.execute(select(Merchant).where(Merchant.id == merchant_id))
        merchant = result.scalars().first()
        assert merchant is not None, "Merchant should exist"
        merchant.store_provider = "shopify"
        await async_session.commit()

        # Login again to get updated flags
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": "ecommerce-shopify@test.com",
                "password": "TestPass123",
            },
        )

        assert response.status_code == 200
        data = response.json()
        merchant_data = data["data"]["merchant"]
        assert merchant_data["onboardingMode"] == "ecommerce"
        assert merchant_data["hasStoreConnected"] is True
        assert merchant_data["hasFacebookConnected"] is False

    @pytest.mark.asyncio
    @pytest.mark.p1
    async def test_any_mode_with_facebook_has_true_facebook_flag(
        self,
        async_client: AsyncClient,
        async_session: AsyncSession,
    ) -> None:
        """Test ID: 8.2-API-010 | Priority: P1

        AC2: Verify any mode with Facebook connection has true facebook flag.

        Given: A merchant with Facebook connected
        When: Auth status is retrieved
        Then: hasFacebookConnected=true
        """
        # Register merchant
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "facebook-conn@test.com",
                "password": "TestPass123",
                "mode": "general",
            },
        )

        assert response.status_code == 201
        merchant_id = response.json()["data"]["merchant"]["id"]

        # Create FacebookIntegration record to simulate Facebook connection
        from app.models.facebook_integration import FacebookIntegration

        fb_integration = FacebookIntegration(
            merchant_id=merchant_id,
            page_id="fb-page-123",
            page_name="Test Page",
            access_token_encrypted="encrypted_token",
            scopes=["pages_messaging"],
        )
        async_session.add(fb_integration)
        await async_session.commit()

        # Login again to get updated flags
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": "facebook-conn@test.com",
                "password": "TestPass123",
            },
        )

        assert response.status_code == 200
        data = response.json()
        merchant_data = data["data"]["merchant"]
        assert merchant_data["hasFacebookConnected"] is True
