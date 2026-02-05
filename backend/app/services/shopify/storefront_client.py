"""Shopify Storefront API client for product search.

Provides async GraphQL client for querying Shopify products with filters.
Uses httpx for async HTTP requests with proper error handling and timeout.
"""

from __future__ import annotations

from typing import Any, Optional

import httpx
import structlog

from app.core.config import settings
from app.core.errors import APIError, ErrorCode


class ShopifyStorefrontClient:
    """Async Shopify Storefront API client for product search.

    Uses GraphQL queries with no rate limits (unlike Admin API).

    Attributes:
        access_token: Storefront API access token
        store_url: Shopify store URL
        base_url: Full GraphQL API endpoint URL
        client: httpx async HTTP client
    """

    DEFAULT_TIMEOUT: float = 10.0
    API_VERSION: str = "2024-01"

    def __init__(
        self,
        access_token: Optional[str] = None,
        store_url: Optional[str] = None,
    ) -> None:
        """Initialize Storefront API client.

        Args:
            access_token: Storefront API access token (from settings if not provided)
            store_url: Shopify store URL (from settings if not provided)
        """
        app_settings = settings()
        self.access_token = access_token or app_settings.get("SHOPIFY_STOREFRONT_ACCESS_TOKEN", "")
        self.store_url = store_url or app_settings.get("SHOPIFY_STORE_URL", "")
        self.base_url = f"{self.store_url}/api/{self.API_VERSION}/graphql.json"

        # Check testing mode
        self.is_testing = app_settings.get("IS_TESTING", False)

        self.logger = structlog.get_logger(__name__)

        self.client = httpx.AsyncClient(
            headers={
                "X-Shopify-Storefront-Access-Token": self.access_token,
                "Content-Type": "application/json",
            },
            timeout=self.DEFAULT_TIMEOUT,
        )

    async def search_products(
        self,
        category: Optional[str] = None,
        max_price: Optional[float] = None,
        size: Optional[str] = None,
        first: int = 20,
    ) -> list[dict[str, Any]]:
        """Search for products with filters.

        Args:
            category: Product category/type filter
            max_price: Maximum price filter (USD)
            first: Number of results to return from Shopify

        Returns:
            List of product dicts with variants, images, pricing

        Raises:
            APIError: If Shopify API call fails
        """
        if self.is_testing:
            self.logger.info("returning_mock_products_for_testing")
            return self._get_mock_products()

        query = self._build_product_search_query(category, max_price, first)

        try:
            response = await self.client.post(self.base_url, json={"query": query})
            response.raise_for_status()

            data = response.json()

            # Check for GraphQL errors
            if "errors" in data:
                self.logger.error("shopify_graphql_errors", errors=data["errors"])
                raise APIError(
                    ErrorCode.SHOPIFY_API_ERROR,
                    "Shopify API error",
                    {"errors": data["errors"]},
                )

            products = data.get("data", {}).get("products", {}).get("edges", [])

            # Extract product nodes
            return [edge["node"] for edge in products]

        except httpx.HTTPStatusError as e:
            self.logger.error("shopify_http_error", status_code=e.response.status_code)
            raise APIError(
                ErrorCode.SHOPIFY_API_ERROR,
                f"Shopify API error: {e.response.status_code}",
            ) from e
        except httpx.TimeoutException as e:
            self.logger.error("shopify_timeout")
            raise APIError(
                ErrorCode.SHOPIFY_TIMEOUT,
                "Shopify API timeout",
            ) from e
        except APIError:
            # Re-raise API errors as-is
            raise
        except Exception as e:
            self.logger.error("shopify_client_error", error=str(e))
            raise APIError(
                ErrorCode.SHOPIFY_API_ERROR,
                f"Shopify client error: {str(e)}",
            ) from e

    def _build_product_search_query(
        self,
        category: Optional[str],
        max_price: Optional[float],
        first: int,
    ) -> str:
        """Build GraphQL query for product search.

        Args:
            category: Product category/type
            max_price: Maximum price filter
            first: Number of results

        Returns:
            GraphQL query string
        """
        # Build query filters
        filters = []
        if category:
            filters.append(f'tag:"{category}"')
        if max_price is not None:
            filters.append(f"price:<={max_price}")

        filter_str = ",".join(filters) if filters else ""

        query = f"""{{
            products(first: {first}{', query:"' + filter_str + '"' if filter_str else ''}) {{
                edges {{
                    node {{
                        id
                        title
                        description
                        productType
                        tags
                        vendor
                        priceRangeV2 {{
                            minVariantPrice {{
                                amount
                                currencyCode
                            }}
                        }}
                        images(first: 1) {{
                            edges {{
                                node {{
                                    url
                                    altText
                                    width
                                    height
                                }}
                            }}
                        }}
                        variants(first: 10) {{
                            edges {{
                                node {{
                                    id
                                    productId
                                    title
                                    priceV2 {{
                                        amount
                                        currencyCode
                                    }}
                                    availableForSale
                                    selectedOptions {{
                                        name
                                        value
                                    }}
                                    weight
                                    weightUnit
                                }}
                            }}
                        }}
                    }}
                }}
            }}
        }}"""

        return query

    def _get_mock_products(self) -> list[dict[str, Any]]:
        """Return mock products for testing."""
        return [
            {
                "id": "gid://shopify/Product/1",
                "title": "Performance Running Shoes",
                "description": "High-performance running shoes.",
                "descriptionHtml": "<p>High-performance running shoes.</p>",
                "productType": "Footwear",
                "tags": ["shoes", "running", "sports"],
                "vendor": "Nike",
                "priceRangeV2": {
                    "minVariantPrice": {"amount": "99.99", "currencyCode": "USD"},
                    "maxVariantPrice": {"amount": "129.99", "currencyCode": "USD"},
                },
                "images": {
                    "edges": [
                        {
                            "node": {
                                "url": "https://images.unsplash.com/photo-1542291026-7eec264c27ff",
                                "altText": "Red running shoes",
                                "width": 800,
                                "height": 600,
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
                                "priceV2": {"amount": "99.99", "currencyCode": "USD"},
                                "availableForSale": True,
                                "selectedOptions": [
                                    {"name": "Size", "value": "8"},
                                    {"name": "Color", "value": "Red"},
                                ],
                            }
                        }
                    ]
                },
            },
            {
                "id": "gid://shopify/Product/2",
                "title": "Classic Canvas Sneakers",
                "description": "Casual canvas sneakers for everyday wear.",
                "descriptionHtml": "<p>Casual canvas sneakers.</p>",
                "productType": "Footwear",
                "tags": ["shoes", "casual", "sneakers"],
                "vendor": "Converse",
                "priceRangeV2": {
                    "minVariantPrice": {"amount": "45.00", "currencyCode": "USD"},
                    "maxVariantPrice": {"amount": "45.00", "currencyCode": "USD"},
                },
                "images": {
                    "edges": [
                        {
                            "node": {
                                "url": "https://images.unsplash.com/photo-1525966222134-fcfa99b8ae77",
                                "altText": "White canvas sneakers",
                                "width": 800,
                                "height": 600,
                            }
                        }
                    ]
                },
                "variants": {
                    "edges": [
                        {
                            "node": {
                                "id": "gid://shopify/ProductVariant/2",
                                "title": "Size 9",
                                "priceV2": {"amount": "45.00", "currencyCode": "USD"},
                                "availableForSale": True,
                                "selectedOptions": [
                                    {"name": "Size", "value": "9"},
                                    {"name": "Color", "value": "White"},
                                ],
                            }
                        }
                    ]
                },
            },
        ]

    async def close(self) -> None:
        """Close the HTTP client.

        Should be called when done using the client to properly clean up resources.
        """
        await self.client.aclose()

    async def __aenter__(self) -> ShopifyStorefrontClient:
        """Async context manager entry."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Async context manager exit."""
        await self.close()
