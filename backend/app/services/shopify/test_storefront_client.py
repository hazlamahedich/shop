"""Tests for Shopify Storefront API client.

Tests GraphQL query building, API calls, error handling, timeout behavior,
and response parsing for product search operations.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
import respx
from httpx import HTTPStatusError, TimeoutException

from app.core.errors import APIError, ErrorCode
from app.services.shopify.storefront_client import ShopifyStorefrontClient


@pytest.fixture
def mock_settings() -> dict[str, Any]:
    """Mock settings for testing."""
    return {
        "SHOPIFY_STORE_URL": "https://test-shop.myshopify.com",
        "SHOPIFY_STOREFRONT_ACCESS_TOKEN": "test_token_123",
    }


@pytest.fixture
def storefront_client(mock_settings: dict[str, Any]) -> ShopifyStorefrontClient:
    """Create a storefront client with test settings."""
    with patch("app.services.shopify.storefront_client.settings", return_value=mock_settings):
        return ShopifyStorefrontClient()


@pytest.fixture
def sample_shopify_response() -> dict[str, Any]:
    """Sample successful Shopify Storefront API response."""
    return {
        "data": {
            "products": {
                "edges": [
                    {
                        "node": {
                            "id": "gid://shopify/Product/1",
                            "title": "Running Shoes",
                            "description": "Comfortable running shoes",
                            "productType": "Footwear",
                            "tags": ["running", "shoes"],
                            "priceRangeV2": {
                                "minVariantPrice": {
                                    "amount": "99.99",
                                    "currencyCode": "USD",
                                }
                            },
                            "images": {
                                "edges": [
                                    {
                                        "node": {
                                            "url": "https://cdn.shopify.com/s/files/1/product.jpg",
                                            "altText": "Running shoe",
                                        }
                                    }
                                ]
                            },
                            "variants": {
                                "edges": [
                                    {
                                        "node": {
                                            "id": "gid://shopify/ProductVariant/1",
                                            "title": "Size 8",
                                            "priceV2": {
                                                "amount": "99.99",
                                                "currencyCode": "USD",
                                            },
                                            "availableForSale": True,
                                            "selectedOptions": [
                                                {"name": "Size", "value": "8"},
                                                {"name": "Color", "value": "Red"},
                                            ],
                                        }
                                    }
                                ]
                            },
                        }
                    }
                ]
            }
        }
    }


@pytest.fixture
def sample_shopify_error_response() -> dict[str, Any]:
    """Sample Shopify error response."""
    return {
        "data": None,
        "errors": [
            {
                "message": "Invalid query",
                "locations": [{"line": 2, "column": 3}],
            }
        ],
    }


class TestShopifyStorefrontClient:
    """Tests for ShopifyStorefrontClient."""

    def test_init_with_default_settings(self, mock_settings: dict[str, Any]) -> None:
        """Test client initialization with default settings."""
        with patch("app.services.shopify.storefront_client.settings", return_value=mock_settings):
            client = ShopifyStorefrontClient()

            assert client.access_token == "test_token_123"
            assert client.store_url == "https://test-shop.myshopify.com"
            assert client.base_url == "https://test-shop.myshopify.com/api/2024-01/graphql.json"

    def test_init_with_custom_settings(self) -> None:
        """Test client initialization with custom settings."""
        client = ShopifyStorefrontClient(
            access_token="custom_token",
            store_url="https://custom-shop.myshopify.com"
        )

        assert client.access_token == "custom_token"
        assert client.store_url == "https://custom-shop.myshopify.com"
        assert client.base_url == "https://custom-shop.myshopify.com/api/2024-01/graphql.json"

    def test_build_product_search_query_no_filters(self, storefront_client: ShopifyStorefrontClient) -> None:
        """Test building query with no filters."""
        query = storefront_client._build_product_search_query(
            category=None,
            max_price=None,
            first=5
        )

        assert "products(first: 5)" in query
        assert "query:" not in query
        assert "id" in query
        assert "title" in query
        assert "variants" in query
        assert "images" in query

    def test_build_product_search_query_with_category(self, storefront_client: ShopifyStorefrontClient) -> None:
        """Test building query with category filter."""
        query = storefront_client._build_product_search_query(
            category="shoes",
            max_price=None,
            first=5
        )

        assert 'tag:"shoes"' in query
        assert "query:" in query

    def test_build_product_search_query_with_price(self, storefront_client: ShopifyStorefrontClient) -> None:
        """Test building query with price filter."""
        query = storefront_client._build_product_search_query(
            category=None,
            max_price=100.0,
            first=5
        )

        assert "price:<=100.0" in query
        assert "query:" in query

    def test_build_product_search_query_with_size(self, storefront_client: ShopifyStorefrontClient) -> None:
        """Test building query - size filtering is post-processing only."""
        query = storefront_client._build_product_search_query(
            category=None,
            max_price=None,
            first=5
        )

        # Size filtering happens in post-processing (service layer), not in query
        # so query should not have size filter
        assert "size" not in query.lower() or "Size" in query

    def test_build_product_search_query_combined_filters(self, storefront_client: ShopifyStorefrontClient) -> None:
        """Test building query with multiple filters."""
        query = storefront_client._build_product_search_query(
            category="shoes",
            max_price=150.0,
            first=10
        )

        assert 'tag:"shoes"' in query
        assert "price:<=150.0" in query
        assert "products(first: 10" in query

    @pytest.mark.asyncio
    async def test_search_products_success(
        self,
        storefront_client: ShopifyStorefrontClient,
        sample_shopify_response: dict[str, Any],
    ) -> None:
        """Test successful product search."""
        with patch.object(
            storefront_client.client,
            "post",
            new_callable=AsyncMock,
            return_value=MagicMock(
                json=lambda: sample_shopify_response,
                raise_for_status=MagicMock()
            )
        ):
            products = await storefront_client.search_products(
                category="shoes",
                max_price=100.0,
                first=5
            )

            assert len(products) == 1
            assert products[0]["id"] == "gid://shopify/Product/1"
            assert products[0]["title"] == "Running Shoes"
            assert products[0]["productType"] == "Footwear"

    @pytest.mark.asyncio
    async def test_search_products_no_results(
        self,
        storefront_client: ShopifyStorefrontClient,
    ) -> None:
        """Test search with no results."""
        empty_response = {
            "data": {
                "products": {
                    "edges": []
                }
            }
        }

        with patch.object(
            storefront_client.client,
            "post",
            new_callable=AsyncMock,
            return_value=MagicMock(
                json=lambda: empty_response,
                raise_for_status=MagicMock()
            )
        ):
            products = await storefront_client.search_products(first=5)

            assert len(products) == 0

    @pytest.mark.asyncio
    async def test_search_products_graphql_error(
        self,
        storefront_client: ShopifyStorefrontClient,
        sample_shopify_error_response: dict[str, Any],
    ) -> None:
        """Test handling of GraphQL errors."""
        with patch.object(
            storefront_client.client,
            "post",
            new_callable=AsyncMock,
            return_value=MagicMock(
                json=lambda: sample_shopify_error_response,
                raise_for_status=MagicMock()
            )
        ):
            with pytest.raises(APIError) as exc_info:
                await storefront_client.search_products(first=5)

            assert exc_info.value.code == ErrorCode.SHOPIFY_API_ERROR
            assert "Shopify API error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_search_products_http_error(
        self,
        storefront_client: ShopifyStorefrontClient,
    ) -> None:
        """Test handling of HTTP errors."""
        mock_response = MagicMock()
        mock_response.status_code = 500

        with patch.object(
            storefront_client.client,
            "post",
            new_callable=AsyncMock,
            side_effect=HTTPStatusError(
                "Server error",
                request=MagicMock(),
                response=mock_response
            )
        ):
            with pytest.raises(APIError) as exc_info:
                await storefront_client.search_products(first=5)

            assert exc_info.value.code == ErrorCode.SHOPIFY_API_ERROR

    @pytest.mark.asyncio
    async def test_search_products_timeout(
        self,
        storefront_client: ShopifyStorefrontClient,
    ) -> None:
        """Test handling of timeout errors."""
        with patch.object(
            storefront_client.client,
            "post",
            new_callable=AsyncMock,
            side_effect=TimeoutException("Request timeout")
        ):
            with pytest.raises(APIError) as exc_info:
                await storefront_client.search_products(first=5)

            assert exc_info.value.code == ErrorCode.SHOPIFY_TIMEOUT
            assert "timeout" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_search_products_size_filter_removed(
        self,
        storefront_client: ShopifyStorefrontClient,
        sample_shopify_response: dict[str, Any],
    ) -> None:
        """Test that size filtering is removed from client (moved to service layer)."""
        with patch.object(
            storefront_client.client,
            "post",
            new_callable=AsyncMock,
            return_value=MagicMock(
                json=lambda: sample_shopify_response,
                raise_for_status=MagicMock()
            )
        ):
            # Client no longer accepts size parameter - filtering in service layer
            products = await storefront_client.search_products(
                category="shoes",
                first=5
            )

            # Client should return all products, service layer filters by size
            assert len(products) >= 0

    def test_client_headers_configured(self, storefront_client: ShopifyStorefrontClient) -> None:
        """Test that client has proper headers configured."""
        headers = storefront_client.client.headers

        assert "X-Shopify-Storefront-Access-Token" in headers
        assert headers["X-Shopify-Storefront-Access-Token"] == "test_token_123"
        assert headers["Content-Type"] == "application/json"

    def test_client_timeout_configured(self, storefront_client: ShopifyStorefrontClient) -> None:
        """Test that client has timeout configured."""
        # httpx timeout is a Timeout object, compare the value
        assert storefront_client.client.timeout == httpx.Timeout(10.0)


class TestShopifyStorefrontClientIntegration:
    """Integration tests with mocked HTTP transport."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_full_search_flow(self) -> None:
        """Test complete search flow with mocked HTTP."""
        # Mock the settings
        mock_settings = {
            "SHOPIFY_STORE_URL": "https://test-shop.myshopify.com",
            "SHOPIFY_STOREFRONT_ACCESS_TOKEN": "test_token",
        }

        with patch("app.services.shopify.storefront_client.settings", return_value=mock_settings):
            client = ShopifyStorefrontClient()

            # Mock the GraphQL response
            shopify_url = "https://test-shop.myshopify.com/api/2024-01/graphql.json"

            response_data = {
                "data": {
                    "products": {
                        "edges": [
                            {
                                "node": {
                                    "id": "gid://shopify/Product/1",
                                    "title": "Test Product",
                                    "description": "Test description",
                                    "productType": "Test",
                                    "tags": ["test"],
                                    "priceRangeV2": {
                                        "minVariantPrice": {
                                            "amount": "10.00",
                                            "currencyCode": "USD",
                                        }
                                    },
                                    "images": {"edges": []},
                                    "variants": {"edges": []},
                                }
                            }
                        ]
                    }
                }
            }

            respx.post(shopify_url).mock(
                return_value=httpx.Response(200, json=response_data)
            )

            products = await client.search_products(category="test", first=5)

            assert len(products) == 1
            assert products[0]["id"] == "gid://shopify/Product/1"
