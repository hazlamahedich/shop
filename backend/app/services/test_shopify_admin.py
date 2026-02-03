"""Tests for Shopify Admin API client.

Tests co-located with service per project standards.
"""

from __future__ import annotations

import pytest
from app.services.shopify_admin import ShopifyAdminClient


@pytest.mark.asyncio
async def test_create_storefront_access_token_testing_mode() -> None:
    """Test Storefront token creation in testing mode."""
    client = ShopifyAdminClient(
        shop_domain="test.myshopify.com",
        access_token="test_admin_token",
        is_testing=True
    )

    token = await client.create_storefront_access_token(title="test-token")

    assert token == "test_storefront_token"


@pytest.mark.asyncio
async def test_subscribe_webhook_testing_mode() -> None:
    """Test webhook subscription in testing mode."""
    client = ShopifyAdminClient(
        shop_domain="test.myshopify.com",
        access_token="test_admin_token",
        is_testing=True
    )

    result = await client.subscribe_webhook(
        topic="orders/create",
        webhook_url="https://example.com/webhooks/shopify"
    )

    assert result is True


@pytest.mark.asyncio
async def test_verify_webhook_subscription_testing_mode() -> None:
    """Test webhook subscription verification in testing mode."""
    client = ShopifyAdminClient(
        shop_domain="test.myshopify.com",
        access_token="test_admin_token",
        is_testing=True
    )

    result = await client.verify_webhook_subscription(topic="orders/create")

    assert result is True


@pytest.mark.asyncio
async def test_verify_shop_access_testing_mode() -> None:
    """Test shop access verification in testing mode."""
    client = ShopifyAdminClient(
        shop_domain="test.myshopify.com",
        access_token="test_admin_token",
        is_testing=True
    )

    shop_details = await client.verify_shop_access()

    assert shop_details["id"] == 123456789
    assert shop_details["name"] == "Test Store"
    assert shop_details["domain"] == "test-store.myshopify.com"


@pytest.mark.asyncio
async def test_close_client() -> None:
    """Test closing the HTTP client."""
    client = ShopifyAdminClient(
        shop_domain="test.myshopify.com",
        access_token="test_admin_token",
        is_testing=True
    )

    # Access client to create it
    _ = client.async_client
    assert client._async_client is not None

    # Close client
    await client.close()
    assert client._async_client is None
