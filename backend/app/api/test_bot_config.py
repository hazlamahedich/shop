"""Tests for Bot Configuration API endpoints.

Story 1.12: Bot Naming

Tests bot configuration CRUD operations.
"""

from __future__ import annotations

import pytest


class TestBotConfigApi:
    """Tests for bot configuration API endpoints."""

    @pytest.fixture
    def merchant_headers(self):
        """Get merchant authentication headers for DEBUG mode."""
        return {"X-Merchant-Id": "1"}

    @pytest.mark.asyncio
    async def test_get_bot_config_success(
        self,
        async_client,
        merchant,
        merchant_headers: dict,
    ):
        """Test GET /api/v1/merchant/bot-config returns bot configuration (Story 1.12 AC 5)."""
        response = await async_client.get(
            "/api/v1/merchant/bot-config",
            headers=merchant_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "meta" in data
        assert "requestId" in data["meta"]
        assert "timestamp" in data["meta"]

    @pytest.mark.asyncio
    async def test_get_bot_config_returns_merchant_data(
        self,
        async_client,
        merchant,
        merchant_headers: dict,
    ):
        """Test GET returns merchant's bot configuration (Story 1.12 AC 5)."""
        response = await async_client.get(
            "/api/v1/merchant/bot-config",
            headers=merchant_headers,
        )

        assert response.status_code == 200
        data = response.json()["data"]
        # Fields may be None initially
        assert "botName" in data
        assert "personality" in data
        assert "customGreeting" in data

    @pytest.mark.asyncio
    async def test_update_bot_config_success(
        self,
        async_client,
        merchant,
        merchant_headers: dict,
    ):
        """Test PUT /api/v1/merchant/bot-config updates bot name (Story 1.12 AC 2, 5)."""
        update_data = {
            "bot_name": "GearBot",
        }

        response = await async_client.put(
            "/api/v1/merchant/bot-config",
            headers=merchant_headers,
            json=update_data,
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["botName"] == "GearBot"

    @pytest.mark.asyncio
    async def test_update_bot_config_whitespace_stripped(
        self,
        async_client,
        merchant,
        merchant_headers: dict,
    ):
        """Test PUT strips whitespace from bot name (Story 1.12 AC 2)."""
        update_data = {
            "bot_name": "  GearBot  ",
        }

        response = await async_client.put(
            "/api/v1/merchant/bot-config",
            headers=merchant_headers,
            json=update_data,
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["botName"] == "GearBot"

    @pytest.mark.asyncio
    async def test_update_bot_config_empty_string_clears(
        self,
        async_client,
        merchant,
        merchant_headers: dict,
    ):
        """Test PUT with empty string clears bot name (Story 1.12 AC 2)."""
        # First set a bot name
        await async_client.put(
            "/api/v1/merchant/bot-config",
            headers=merchant_headers,
            json={"bot_name": "GearBot"},
        )

        # Then clear with empty string (whitespace only)
        response = await async_client.put(
            "/api/v1/merchant/bot-config",
            headers=merchant_headers,
            json={"bot_name": "   "},
        )

        assert response.status_code == 200
        data = response.json()["data"]
        # Empty string after stripping becomes None
        assert data.get("botName") is None or data.get("botName") == ""

    @pytest.mark.asyncio
    async def test_update_bot_config_validation_max_length(
        self,
        async_client,
        merchant,
        merchant_headers: dict,
    ):
        """Test PUT validates bot name max length of 50 characters (Story 1.12 AC 2)."""
        update_data = {
            "bot_name": "A" * 51,  # Max is 50
        }

        response = await async_client.put(
            "/api/v1/merchant/bot-config",
            headers=merchant_headers,
            json=update_data,
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_update_bot_config_various_names(
        self,
        async_client,
        merchant,
        merchant_headers: dict,
    ):
        """Test PUT accepts various valid bot name formats (Story 1.12 AC 2)."""
        valid_names = [
            "GearBot",
            "ShopAssistant",
            "StoreBot123",
            "The-Helpful-Bot",
            "Alex's Bot",
            "A",  # Single character
            "A" * 50,  # Max length
        ]

        for name in valid_names:
            response = await async_client.put(
                "/api/v1/merchant/bot-config",
                headers=merchant_headers,
                json={"bot_name": name},
            )
            assert response.status_code == 200, f"Failed for name: {name}"
            data = response.json()["data"]
            assert data["botName"] == name

    @pytest.mark.asyncio
    async def test_get_bot_config_persisted_value(
        self,
        async_client,
        merchant,
        merchant_headers: dict,
    ):
        """Test GET returns previously set bot name (Story 1.12 AC 2, 5)."""
        # First set a bot name
        await async_client.put(
            "/api/v1/merchant/bot-config",
            headers=merchant_headers,
            json={"bot_name": "TestBot"},
        )

        # Then get the config
        response = await async_client.get(
            "/api/v1/merchant/bot-config",
            headers=merchant_headers,
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["botName"] == "TestBot"
