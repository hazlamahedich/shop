"""Unit tests for ShopifyAdminClient.

Story 4-4 Task 1 & 5: Admin API client with authentication, rate limiting, and 429 handling
"""

from __future__ import annotations

import os
import re
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import ClientResponseError, ClientSession
from aioresponses import aioresponses

from app.services.shopify.admin_client import (
    ShopifyAdminClient,
    ShopifyRateLimitError,
    ShopifyAuthError,
    ShopifyAPIError,
)


class TestShopifyAdminClient:
    """Tests for ShopifyAdminClient."""

    @pytest.fixture
    async def admin_client(self):
        """Create admin client instance with proper cleanup."""
        client = ShopifyAdminClient(
            shop_domain="test-shop.myshopify.com",
            access_token="test_admin_token_123",
        )
        yield client
        await client.close()

    @pytest.fixture
    def mock_orders_response(self):
        """Sample orders response from Shopify Admin API."""
        return {
            "orders": [
                {
                    "id": 123456789,
                    "order_number": 1001,
                    "email": "customer@example.com",
                    "financial_status": "paid",
                    "fulfillment_status": None,
                    "created_at": (datetime.utcnow() - timedelta(hours=1)).isoformat() + "Z",
                    "updated_at": datetime.utcnow().isoformat() + "Z",
                    "customer": {
                        "id": 987654321,
                        "email": "customer@example.com",
                    },
                    "line_items": [
                        {
                            "id": 111,
                            "title": "Test Product",
                            "quantity": 1,
                            "price": "29.99",
                        }
                    ],
                    "note_attributes": [{"name": "messenger_psid", "value": "test_psid_123"}],
                },
            ]
        }

    def test_client_initialization(self, admin_client):
        """Test client initialization with credentials."""
        assert admin_client.shop_domain == "test-shop.myshopify.com"
        assert admin_client.access_token == "test_admin_token_123"
        assert admin_client.api_version == "2024-01"
        assert admin_client.base_url == "https://test-shop.myshopify.com/admin/api/2024-01"

    def test_client_with_custom_api_version(self):
        """Test client with custom API version."""
        client = ShopifyAdminClient(
            shop_domain="custom.myshopify.com",
            access_token="token",
            api_version="2023-10",
        )
        assert client.api_version == "2023-10"
        assert "2023-10" in client.base_url

    @pytest.mark.asyncio
    async def test_get_orders_updated_since_success(self, admin_client, mock_orders_response):
        """Test successful order retrieval."""
        with aioresponses() as m:
            m.get(
                re.compile(r"https://test-shop\.myshopify\.com/admin/api/2024-01/orders\.json.*"),
                payload=mock_orders_response,
                headers={"X-Shopify-Shop-Api-Call-Limit": "5/1000"},
            )

            orders = await admin_client.get_orders_updated_since(minutes=5)

            assert len(orders) == 1
            assert orders[0]["id"] == 123456789
            assert orders[0]["order_number"] == 1001

    @pytest.mark.asyncio
    async def test_get_orders_with_empty_response(self, admin_client):
        """Test handling of empty orders response."""
        with aioresponses() as m:
            m.get(
                re.compile(r"https://test-shop\.myshopify\.com/admin/api/2024-01/orders\.json.*"),
                payload={"orders": []},
                headers={"X-Shopify-Shop-Api-Call-Limit": "5/1000"},
            )

            orders = await admin_client.get_orders_updated_since(minutes=5)

            assert orders == []

    @pytest.mark.asyncio
    async def test_authentication_header_set(self, admin_client, mock_orders_response):
        """Test that X-Shopify-Access-Token header is set correctly."""
        with aioresponses() as m:
            m.get(
                re.compile(r"https://test-shop\.myshopify\.com/admin/api/2024-01/orders\.json.*"),
                payload=mock_orders_response,
                headers={"X-Shopify-Shop-Api-Call-Limit": "5/1000"},
            )

            await admin_client.get_orders_updated_since(minutes=5)

            assert m.requests
            for key, requests in m.requests.items():
                if key[0] == "GET":
                    request = requests[0]
                    assert (
                        request.kwargs["headers"]["X-Shopify-Access-Token"]
                        == "test_admin_token_123"
                    )
                    break

    @pytest.mark.asyncio
    async def test_rate_limit_tracking(self, admin_client, mock_orders_response):
        """Test rate limit header parsing and tracking."""
        with aioresponses() as m:
            m.get(
                re.compile(r"https://test-shop\.myshopify\.com/admin/api/2024-01/orders\.json.*"),
                payload=mock_orders_response,
                headers={"X-Shopify-Shop-Api-Call-Limit": "850/1000"},
            )

            await admin_client.get_orders_updated_since(minutes=5)

            assert admin_client.rate_limit_used == 850
            assert admin_client.rate_limit_max == 1000

    @pytest.mark.asyncio
    async def test_rate_limit_backoff_triggers(self, admin_client, mock_orders_response):
        """Test backoff when approaching rate limit (>800)."""
        with aioresponses() as m:
            m.get(
                re.compile(r"https://test-shop\.myshopify\.com/admin/api/2024-01/orders\.json.*"),
                payload=mock_orders_response,
                headers={"X-Shopify-Shop-Api-Call-Limit": "850/1000"},
            )

            await admin_client.get_orders_updated_since(minutes=5)

            assert admin_client.should_backoff() is True

    @pytest.mark.asyncio
    async def test_429_response_handling_with_retry(self, admin_client, mock_orders_response):
        """Test HTTP 429 rate limit response with exponential backoff retry."""
        with aioresponses() as m:
            m.get(
                re.compile(r"https://test-shop\.myshopify\.com/admin/api/2024-01/orders\.json.*"),
                status=429,
                headers={"Retry-After": "1"},
            )
            m.get(
                re.compile(r"https://test-shop\.myshopify\.com/admin/api/2024-01/orders\.json.*"),
                payload=mock_orders_response,
                headers={"X-Shopify-Shop-Api-Call-Limit": "10/1000"},
            )

            orders = await admin_client.get_orders_updated_since(minutes=5, max_retries=3)

            assert len(orders) == 1

    @pytest.mark.asyncio
    async def test_429_max_retries_exceeded(self, admin_client):
        """Test that 429 raises error after max retries."""
        with aioresponses() as m:
            m.get(
                re.compile(r"https://test-shop\.myshopify\.com/admin/api/2024-01/orders\.json.*"),
                status=429,
                headers={"Retry-After": "1"},
                repeat=True,
            )

            with pytest.raises(ShopifyRateLimitError) as exc_info:
                await admin_client.get_orders_updated_since(minutes=5, max_retries=2)

            assert "rate limit" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_401_authentication_failure(self, admin_client):
        """Test HTTP 401 authentication failure."""
        with aioresponses() as m:
            m.get(
                re.compile(r"https://test-shop\.myshopify\.com/admin/api/2024-01/orders\.json.*"),
                status=401,
            )

            with pytest.raises(ShopifyAuthError):
                await admin_client.get_orders_updated_since(minutes=5)

    @pytest.mark.asyncio
    async def test_500_server_error(self, admin_client):
        """Test HTTP 500 server error handling."""
        with aioresponses() as m:
            m.get(
                re.compile(r"https://test-shop\.myshopify\.com/admin/api/2024-01/orders\.json.*"),
                status=500,
            )

            with pytest.raises(ShopifyAPIError):
                await admin_client.get_orders_updated_since(minutes=5)

    @pytest.mark.asyncio
    async def test_timeout_handling(self, admin_client):
        """Test request timeout handling."""
        with aioresponses() as m:
            m.get(
                re.compile(r"https://test-shop\.myshopify\.com/admin/api/2024-01/orders\.json.*"),
                exception=TimeoutError(),
            )

            with pytest.raises(ShopifyAPIError):
                await admin_client.get_orders_updated_since(minutes=5)

    @pytest.mark.asyncio
    async def test_context_manager(self, admin_client, mock_orders_response):
        """Test async context manager usage."""
        with aioresponses() as m:
            m.get(
                re.compile(r"https://test-shop\.myshopify\.com/admin/api/2024-01/orders\.json.*"),
                payload=mock_orders_response,
                headers={"X-Shopify-Shop-Api-Call-Limit": "5/1000"},
            )

            async with ShopifyAdminClient(
                shop_domain="test-shop.myshopify.com",
                access_token="test_admin_token_123",
            ) as client:
                orders = await client.get_orders_updated_since(minutes=5)
                assert len(orders) == 1

    @pytest.mark.asyncio
    async def test_updated_at_min_parameter_included(self, admin_client, mock_orders_response):
        """Test that updated_at_min parameter is included in request."""
        with aioresponses() as m:
            m.get(
                re.compile(r"https://test-shop\.myshopify\.com/admin/api/2024-01/orders\.json.*"),
                payload=mock_orders_response,
                headers={"X-Shopify-Shop-Api-Call-Limit": "5/1000"},
            )

            await admin_client.get_orders_updated_since(minutes=5)

            assert m.requests
            for key, requests in m.requests.items():
                if key[0] == "GET":
                    request = requests[0]
                    params = request.kwargs.get("params", {})
                    assert "updated_at_min" in params
                    break

    def test_rate_limit_percentage(self, admin_client):
        """Test rate limit percentage calculation."""
        admin_client.rate_limit_used = 500
        admin_client.rate_limit_max = 1000
        assert admin_client.rate_limit_percentage() == 50.0

    def test_rate_limit_percentage_when_zero(self, admin_client):
        """Test rate limit percentage when no calls made."""
        admin_client.rate_limit_used = 0
        admin_client.rate_limit_max = 1000
        assert admin_client.rate_limit_percentage() == 0.0

    @pytest.mark.asyncio
    async def test_close_session(self, admin_client):
        """Test session cleanup."""
        await admin_client.close()
        assert admin_client._session is None or admin_client._session.closed
