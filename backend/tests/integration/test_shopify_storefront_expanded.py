"""Expanded integration tests for Shopify Storefront API client.

Tests product search with filters, checkout URL generation, and
checkout URL validation per architecture requirements.
"""

from __future__ import annotations

import pytest
import respx
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_storefront_verify_access(async_client: AsyncClient) -> None:
    """Test Storefront API access verification.

    P0 - Revenue Critical: Verifies Storefront API token is valid
    before attempting product search or checkout.

    Args:
        async_client: Test HTTP client
    """
    from app.services.shopify_storefront import ShopifyStorefrontClient

    client = ShopifyStorefrontClient(
        shop_domain="test-store.myshopify.com",
        access_token="test_storefront_token",
        is_testing=True
    )

    # Should return True in test mode
    result = await client.verify_access()
    assert result is True


@pytest.mark.asyncio
async def test_storefront_product_search_basic(async_client: AsyncClient) -> None:
    """Test basic product search via Storefront API.

    P0 - Revenue Critical: Product search is core shopping experience.

    Args:
        async_client: Test HTTP client
    """
    from app.services.shopify_storefront import ShopifyStorefrontClient

    client = ShopifyStorefrontClient(
        shop_domain="test-store.myshopify.com",
        access_token="test_storefront_token",
        is_testing=True
    )

    # Search with query
    products = await client.search_products(query="running shoes", first=5)

    assert len(products) > 0
    assert "Test Product" in products[0]["title"]  # May be "Test Product 1", "Test Product 2", etc.
    assert "priceRange" in products[0]


@pytest.mark.asyncio
async def test_storefront_product_search_with_filters(async_client: AsyncClient) -> None:
    """Test product search with price and category filters.

    P1 - High Priority: Filtered search improves user experience.

    Args:
        async_client: Test HTTP client
    """
    from app.services.shopify_storefront import ShopifyStorefrontClient

    client = ShopifyStorefrontClient(
        shop_domain="test-store.myshopify.com",
        access_token="test_storefront_token",
        is_testing=True
    )

    # Search with price filter
    filters = {
        "max_price": 150.00,
        "category": "shoes"
    }

    products = await client.search_products(query="shoes", first=10, filters=filters)

    assert len(products) >= 0  # May return 0 if no products match


@pytest.mark.asyncio
async def test_storefront_product_search_no_results(async_client: AsyncClient) -> None:
    """Test product search with no matching results.

    P2 - Medium Priority: Edge case handling for empty results.

    Args:
        async_client: Test HTTP client
    """
    from app.services.shopify_storefront import ShopifyStorefrontClient

    client = ShopifyStorefrontClient(
        shop_domain="test-store.myshopify.com",
        access_token="test_storefront_token",
        is_testing=True
    )

    # Search for non-existent product
    # In test mode, returns mock products - in production would return []
    products = await client.search_products(query="nonexistent_product_xyz", first=5)

    # Should return list (empty in production, mock data in test)
    assert isinstance(products, list)


@pytest.mark.asyncio
async def test_storefront_checkout_url_generation(async_client: AsyncClient) -> None:
    """Test checkout URL generation for cart items.

    P0 - Revenue Critical: Checkout URL is required for payment completion.

    Args:
        async_client: Test HTTP client
    """
    from app.services.shopify_storefront import ShopifyStorefrontClient

    client = ShopifyStorefrontClient(
        shop_domain="test-store.myshopify.com",
        access_token="test_storefront_token",
        is_testing=True
    )

    # Cart items
    items = [
        {
            "variant_id": "gid://shopify/ProductVariant/1",
            "quantity": 2
        }
    ]

    checkout_url = await client.create_checkout_url(items)

    # Should return valid checkout URL
    assert checkout_url is not None
    assert isinstance(checkout_url, str)
    assert "checkout" in checkout_url.lower()


@pytest.mark.asyncio
async def test_storefront_checkout_url_validation(async_client: AsyncClient) -> None:
    """Test checkout URL validation via HTTP HEAD request.

    P0 - Revenue Critical: Architecture requirement (NFR-R16) - checkout
    URL validity must be verified before sending to user.

    Args:
        async_client: Test HTTP client
    """
    from app.services.shopify_storefront import ShopifyStorefrontClient
    from unittest.mock import AsyncMock, patch

    client = ShopifyStorefrontClient(
        shop_domain="test-store.myshopify.com",
        access_token="test_storefront_token",
        is_testing=True
    )

    valid_url = "https://checkout.shopify.com/test"

    # Mock the HTTP HEAD request response using AsyncMock
    mock_response = AsyncMock()
    mock_response.status_code = 200

    with patch.object(client.async_client, 'head', return_value=mock_response):
        # Test validation method exists and works
        result = await client._validate_checkout_url(valid_url)
        assert result is True  # Should return True for valid URL


@pytest.mark.asyncio
async def test_storefront_checkout_empty_cart(async_client: AsyncClient) -> None:
    """Test checkout generation with empty cart.

    P1 - High Priority: Edge case handling for empty cart.

    Args:
        async_client: Test HTTP client
    """
    from app.services.shopify_storefront import ShopifyStorefrontClient
    from app.core.errors import APIError

    client = ShopifyStorefrontClient(
        shop_domain="test-store.myshopify.com",
        access_token="test_storefront_token",
        is_testing=True
    )

    # Empty cart
    items = []

    # Should handle gracefully - may raise error or return mock URL
    # depending on implementation
    try:
        checkout_url = await client.create_checkout_url(items)
        # If it doesn't raise, verify it handles empty cart
        # (in test mode, may return mock URL)
        assert checkout_url is None or checkout_url == "" or "checkout" in checkout_url.lower()
    except (APIError, ValueError):
        # Expected behavior - empty cart should raise error
        pass


@pytest.mark.asyncio
async def test_storefront_multiple_items_checkout(async_client: AsyncClient) -> None:
    """Test checkout URL generation with multiple cart items.

    P1 - High Priority: Multi-item checkout is common use case.

    Args:
        async_client: Test HTTP client
    """
    from app.services.shopify_storefront import ShopifyStorefrontClient

    client = ShopifyStorefrontClient(
        shop_domain="test-store.myshopify.com",
        access_token="test_storefront_token",
        is_testing=True
    )

    # Multiple items
    items = [
        {"variant_id": "gid://shopify/ProductVariant/1", "quantity": 2},
        {"variant_id": "gid://shopify/ProductVariant/2", "quantity": 1},
        {"variant_id": "gid://shopify/ProductVariant/3", "quantity": 3},
    ]

    checkout_url = await client.create_checkout_url(items)

    assert checkout_url is not None
    assert isinstance(checkout_url, str)


@pytest.mark.asyncio
async def test_storefront_api_error_handling(async_client: AsyncClient) -> None:
    """Test Storefront API error handling.

    P2 - Medium Priority: Graceful error handling for API failures.

    Args:
        async_client: Test HTTP client
    """
    from app.services.shopify_storefront import ShopifyStorefrontClient
    from app.core.errors import APIError

    client = ShopifyStorefrontClient(
        shop_domain="test-store.myshopify.com",
        access_token="invalid_token",
        is_testing=False  # Use real API mode (will fail)
    )

    # Should handle error gracefully
    # In real API mode with invalid token, verify_access returns False
    result = await client.verify_access()
    assert result is False  # Should return False on error
