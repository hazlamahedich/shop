"""Tests for Shopify Storefront API client.

Tests co-located with service per project standards.
"""

from __future__ import annotations

import pytest
from app.services.shopify_storefront import ShopifyStorefrontClient


@pytest.mark.asyncio
async def test_verify_access_testing_mode() -> None:
    """Test verify_access returns True in testing mode.

    In testing mode, the client uses ASGITransport and should return True.
    """
    client = ShopifyStorefrontClient(
        shop_domain="test.myshopify.com",
        access_token="test_token",
        is_testing=True
    )

    result = await client.verify_access()
    assert result is True


@pytest.mark.asyncio
async def test_search_products_testing_mode() -> None:
    """Test product search returns mock products in testing mode."""
    client = ShopifyStorefrontClient(
        shop_domain="test.myshopify.com",
        access_token="test_token",
        is_testing=True
    )

    products = await client.search_products(query="test")

    assert len(products) == 1
    assert products[0]["id"] == "gid://shopify/Product/1"
    assert products[0]["title"] == "Test Product 1"
    assert products[0]["description"] == "Test description"
    assert products[0]["availableForSale"] is True
    assert products[0]["imageUrl"] == "https://example.com/product1.jpg"


@pytest.mark.asyncio
async def test_search_products_with_query() -> None:
    """Test product search with query parameter."""
    client = ShopifyStorefrontClient(
        shop_domain="test.myshopify.com",
        access_token="test_token",
        is_testing=True
    )

    products = await client.search_products(query="shoes", first=5)

    assert len(products) == 1
    assert products[0]["title"] == "Test Product 1"


@pytest.mark.asyncio
async def test_create_checkout_url_testing_mode() -> None:
    """Test checkout URL generation in testing mode."""
    client = ShopifyStorefrontClient(
        shop_domain="test.myshopify.com",
        access_token="test_token",
        is_testing=True
    )

    items = [
        {"variant_id": "gid://shopify/ProductVariant/1", "quantity": 2}
    ]

    checkout_url = await client.create_checkout_url(items)

    assert checkout_url == "https://checkout.shopify.com/test"


@pytest.mark.asyncio
async def test_create_checkout_url_multiple_items() -> None:
    """Test checkout URL generation with multiple items."""
    client = ShopifyStorefrontClient(
        shop_domain="test.myshopify.com",
        access_token="test_token",
        is_testing=True
    )

    items = [
        {"variant_id": "gid://shopify/ProductVariant/1", "quantity": 1},
        {"variant_id": "gid://shopify/ProductVariant/2", "quantity": 3}
    ]

    checkout_url = await client.create_checkout_url(items)

    assert checkout_url == "https://checkout.shopify.com/test"


@pytest.mark.asyncio
async def test_close_client() -> None:
    """Test closing the HTTP client."""
    client = ShopifyStorefrontClient(
        shop_domain="test.myshopify.com",
        access_token="test_token",
        is_testing=True
    )

    # Access client to create it
    _ = client.async_client
    assert client._async_client is not None

    # Close client
    await client.close()
    assert client._async_client is None
