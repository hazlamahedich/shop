"""Tests for widget settings API endpoints.

Story 5.6: Merchant Widget Settings UI

Note: CSRF protection is enforced by middleware (app/middleware/csrf.py).
The middleware bypasses CSRF in test mode, so these tests don't need CSRF tokens.
CSRF enforcement is tested separately in test_csrf.py.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ErrorCode
from app.models.merchant import Merchant


class TestGetWidgetConfig:
    """Tests for GET /api/v1/merchants/widget-config endpoint."""

    @pytest.mark.asyncio
    async def test_get_widget_config_returns_current_config(
        self,
        async_client: AsyncClient,
        test_merchant: Merchant,
    ) -> None:
        """Test GET returns current widget configuration."""
        response = await async_client.get(
            "/api/v1/merchants/widget-config",
            headers={"X-Merchant-Id": str(test_merchant.id)},
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "meta" in data

        widget_config = data["data"]
        assert "enabled" in widget_config
        assert "botName" in widget_config
        assert "welcomeMessage" in widget_config
        assert "theme" in widget_config

    @pytest.mark.asyncio
    async def test_get_widget_config_returns_defaults_when_no_config(
        self,
        async_client: AsyncClient,
        test_merchant: Merchant,
    ) -> None:
        """Test GET returns defaults when merchant has no widget config.

        Uses test_merchant which has config=None by default.
        """
        response = await async_client.get(
            "/api/v1/merchants/widget-config",
            headers={"X-Merchant-Id": str(test_merchant.id)},
        )

        assert response.status_code == 200
        data = response.json()
        widget_config = data["data"]

        assert widget_config["enabled"] is True
        assert widget_config["botName"] == "Shopping Assistant"
        assert "Hi" in widget_config["welcomeMessage"]

    @pytest.mark.asyncio
    async def test_get_widget_config_merchant_not_found(
        self,
        async_client: AsyncClient,
    ) -> None:
        """Test GET with non-existent merchant returns error."""
        response = await async_client.get(
            "/api/v1/merchants/widget-config",
            headers={"X-Merchant-Id": "99999"},
        )

        assert response.status_code == 404
        data = response.json()
        assert data["error_code"] == ErrorCode.WIDGET_SETTINGS_NOT_FOUND


class TestUpdateWidgetConfig:
    """Tests for PATCH /api/v1/merchants/widget-config endpoint."""

    @pytest.mark.asyncio
    async def test_update_widget_config_enabled_only(
        self,
        async_client: AsyncClient,
        test_merchant: Merchant,
    ) -> None:
        """Test PATCH updates enabled field only."""
        response = await async_client.patch(
            "/api/v1/merchants/widget-config",
            headers={"X-Merchant-Id": str(test_merchant.id)},
            json={"enabled": False},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["enabled"] is False

    @pytest.mark.asyncio
    async def test_update_widget_config_bot_name(
        self,
        async_client: AsyncClient,
        test_merchant: Merchant,
    ) -> None:
        """Test PATCH updates bot_name field."""
        response = await async_client.patch(
            "/api/v1/merchants/widget-config",
            headers={"X-Merchant-Id": str(test_merchant.id)},
            json={"botName": "Custom Bot Name"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["botName"] == "Custom Bot Name"

    @pytest.mark.asyncio
    async def test_update_widget_config_welcome_message(
        self,
        async_client: AsyncClient,
        test_merchant: Merchant,
    ) -> None:
        """Test PATCH updates welcome_message field."""
        response = await async_client.patch(
            "/api/v1/merchants/widget-config",
            headers={"X-Merchant-Id": str(test_merchant.id)},
            json={"welcomeMessage": "Welcome to our store!"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["welcomeMessage"] == "Welcome to our store!"

    @pytest.mark.asyncio
    async def test_update_widget_config_theme_primary_color(
        self,
        async_client: AsyncClient,
        test_merchant: Merchant,
    ) -> None:
        """Test PATCH updates theme.primary_color field."""
        response = await async_client.patch(
            "/api/v1/merchants/widget-config",
            headers={"X-Merchant-Id": str(test_merchant.id)},
            json={"theme": {"primaryColor": "#ff0000"}},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["theme"]["primaryColor"] == "#ff0000"

    @pytest.mark.asyncio
    async def test_update_widget_config_theme_position(
        self,
        async_client: AsyncClient,
        test_merchant: Merchant,
    ) -> None:
        """Test PATCH updates theme.position field."""
        response = await async_client.patch(
            "/api/v1/merchants/widget-config",
            headers={"X-Merchant-Id": str(test_merchant.id)},
            json={"theme": {"position": "bottom-left"}},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["theme"]["position"] == "bottom-left"

    @pytest.mark.asyncio
    async def test_update_widget_config_multiple_fields(
        self,
        async_client: AsyncClient,
        test_merchant: Merchant,
    ) -> None:
        """Test PATCH updates multiple fields at once."""
        response = await async_client.patch(
            "/api/v1/merchants/widget-config",
            headers={"X-Merchant-Id": str(test_merchant.id)},
            json={
                "enabled": True,
                "botName": "Multi Update Bot",
                "welcomeMessage": "Hello there!",
                "theme": {"primaryColor": "#00ff00", "position": "bottom-right"},
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["enabled"] is True
        assert data["data"]["botName"] == "Multi Update Bot"
        assert data["data"]["welcomeMessage"] == "Hello there!"
        assert data["data"]["theme"]["primaryColor"] == "#00ff00"
        assert data["data"]["theme"]["position"] == "bottom-right"

    @pytest.mark.asyncio
    async def test_update_widget_config_invalid_color_returns_error(
        self,
        async_client: AsyncClient,
        test_merchant: Merchant,
    ) -> None:
        """Test PATCH rejects invalid hex color format."""
        response = await async_client.patch(
            "/api/v1/merchants/widget-config",
            headers={"X-Merchant-Id": str(test_merchant.id)},
            json={"theme": {"primaryColor": "not-a-color"}},
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_widget_config_invalid_position_returns_error(
        self,
        async_client: AsyncClient,
        test_merchant: Merchant,
    ) -> None:
        """Test PATCH rejects invalid position value."""
        response = await async_client.patch(
            "/api/v1/merchants/widget-config",
            headers={"X-Merchant-Id": str(test_merchant.id)},
            json={"theme": {"position": "top-center"}},
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_widget_config_bot_name_max_length_validation(
        self,
        async_client: AsyncClient,
        test_merchant: Merchant,
    ) -> None:
        """Test PATCH rejects bot_name over 50 characters."""
        long_name = "A" * 51
        response = await async_client.patch(
            "/api/v1/merchants/widget-config",
            headers={"X-Merchant-Id": str(test_merchant.id)},
            json={"botName": long_name},
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_widget_config_welcome_message_max_length_validation(
        self,
        async_client: AsyncClient,
        test_merchant: Merchant,
    ) -> None:
        """Test PATCH rejects welcome_message over 500 characters."""
        long_message = "A" * 501
        response = await async_client.patch(
            "/api/v1/merchants/widget-config",
            headers={"X-Merchant-Id": str(test_merchant.id)},
            json={"welcomeMessage": long_message},
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_widget_config_merchant_not_found(
        self,
        async_client: AsyncClient,
    ) -> None:
        """Test PATCH with non-existent merchant returns error."""
        response = await async_client.patch(
            "/api/v1/merchants/widget-config",
            headers={"X-Merchant-Id": "99999"},
            json={"enabled": False},
        )

        assert response.status_code == 404
        data = response.json()
        assert data["error_code"] == ErrorCode.WIDGET_SETTINGS_NOT_FOUND

    @pytest.mark.asyncio
    async def test_update_then_get_returns_updated_values(
        self,
        async_client: AsyncClient,
        test_merchant: Merchant,
    ) -> None:
        """Test update then GET returns updated values."""
        update_response = await async_client.patch(
            "/api/v1/merchants/widget-config",
            headers={"X-Merchant-Id": str(test_merchant.id)},
            json={"enabled": False, "botName": "Persisted Bot"},
        )

        assert update_response.status_code == 200

        get_response = await async_client.get(
            "/api/v1/merchants/widget-config",
            headers={"X-Merchant-Id": str(test_merchant.id)},
        )

        assert get_response.status_code == 200
        data = get_response.json()
        assert data["data"]["enabled"] is False
        assert data["data"]["botName"] == "Persisted Bot"
