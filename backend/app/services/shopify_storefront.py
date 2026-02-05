"""Shopify Storefront API client for product search and checkout generation.

Uses GraphQL to query products and generate checkout URLs via Storefront API.
"""

from __future__ import annotations

from typing import Optional, Dict, Any, List
import structlog

from app.services.shopify_base import ShopifyBaseClient
from app.core.errors import APIError, ErrorCode

SHOPIFY_STOREFRONT_API_URL = "https://{shop}.myshopify.com/api/2024-01/graphql"

logger = structlog.get_logger(__name__)


class ShopifyStorefrontClient(ShopifyBaseClient):
    """Shopify Storefront API client for product search and checkout generation."""

    async def verify_access(self) -> bool:
        """Verify Storefront API access with test query.

        Returns:
            True if access token is valid
        """
        query = """
        query {
            shop {
                name
            }
        }
        """

        try:
            if self.is_testing:
                return True

            response = await self.async_client.post(
                SHOPIFY_STOREFRONT_API_URL.format(shop=self.shop_domain),
                json={"query": query},
                headers={"X-Shopify-Storefront-Access-Token": self.access_token}
            )
            response.raise_for_status()
            data = response.json()

            # Check for errors
            if "errors" in data:
                return False

            return data.get("data", {}).get("shop") is not None

        except Exception:
            return False

    async def search_products(
        self,
        query: str = "",
        first: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search products via Storefront API.

        Args:
            query: Search query string
            first: Number of results to return
            filters: Optional filters (price range, category, availability)

        Returns:
            List of products with id, title, description, images, price_range

        Raises:
            APIError: If product search fails
        """
        # Build GraphQL query
        graphql_query = """
        query ($query: String, $first: Int) {
            search(query: $query, first: $first, types: PRODUCT) {
                edges {
                    node {
                        ... on Product {
                            id
                            title
                            description
                            descriptionHtml
                            priceRangeV2 {
                                minVariantPrice {
                                    amount
                                    currencyCode
                                }
                                maxVariantPrice {
                                    amount
                                    currencyCode
                                }
                            }
                            images(first: 1) {
                                edges {
                                    node {
                                        url
                                        altText
                                    }
                                }
                            }
                            variants(first: 1) {
                                edges {
                                    node {
                                        id
                                        availableForSale
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        """

        variables = {"query": query, "first": first}

        try:
            if self.is_testing:
                # Return mock products in test mode
                return self._get_mock_products()

            response = await self.async_client.post(
                SHOPIFY_STOREFRONT_API_URL.format(shop=self.shop_domain),
                json={"query": graphql_query, "variables": variables},
                headers={"X-Shopify-Storefront-Access-Token": self.access_token}
            )
            response.raise_for_status()
            data = response.json()

            # Check for errors
            if "errors" in data:
                raise APIError(
                    ErrorCode.SHOPIFY_API_ERROR,
                    f"Storefront API error: {data['errors']}"
                )

            # Extract products
            edges = data.get("data", {}).get("search", {}).get("edges", [])
            products = []
            for edge in edges:
                product = edge.get("node", {})
                images = product.get("images", {}).get("edges", [])
                variants = product.get("variants", {}).get("edges", [])

                products.append({
                    "id": product.get("id"),
                    "title": product.get("title"),
                    "description": product.get("description"),
                    "priceRange": product.get("priceRangeV2"),
                    "imageUrl": images[0].get("node", {}).get("url") if images else None,
                    "availableForSale": variants[0].get("node", {}).get("availableForSale", False) if variants else False
                })

            return products

        except Exception as e:
            if isinstance(e, APIError):
                raise
            raise APIError(
                ErrorCode.SHOPIFY_PRODUCT_SEARCH_FAILED,
                f"Failed to search products: {str(e)}"
            )

    async def create_checkout_url(
        self,
        items: List[Dict[str, Any]]
    ) -> str:
        """Generate Shopify checkout URL.

        Args:
            items: List of cart items (variant_id, quantity)

        Returns:
            Checkout URL

        Raises:
            APIError: If checkout creation fails
        """
        # Build line items from cart items
        line_items = []
        for item in items:
            line_items.append({
                "quantity": item["quantity"],
                "variantId": item["variant_id"]
            })

        mutation = """
        mutation ($checkoutInput: CheckoutCreateInput!) {
            checkoutCreate(input: $checkoutInput) {
                checkout {
                    id
                    webUrl
                }
                checkoutUserErrors {
                    code
                    field
                    message
                }
            }
        }
        """

        variables = {
            "checkoutInput": {
                "lineItems": line_items
            }
        }

        try:
            if self.is_testing:
                # Return mock checkout URL in test mode
                return "https://checkout.shopify.com/test"

            response = await self.async_client.post(
                SHOPIFY_STOREFRONT_API_URL.format(shop=self.shop_domain),
                json={"query": mutation, "variables": variables},
                headers={"X-Shopify-Storefront-Access-Token": self.access_token}
            )
            response.raise_for_status()
            data = response.json()

            # Check for errors
            if "errors" in data:
                raise APIError(
                    ErrorCode.SHOPIFY_CHECKOUT_CREATE_FAILED,
                    f"Checkout creation error: {data['errors']}"
                )

            # Check for user errors
            user_errors = data.get("data", {}).get("checkoutCreate", {}).get("checkoutUserErrors", [])
            if user_errors:
                raise APIError(
                    ErrorCode.SHOPIFY_CHECKOUT_CREATE_FAILED,
                    f"Checkout user errors: {[e['message'] for e in user_errors]}"
                )

            # Extract checkout URL
            checkout_url = data.get("data", {}).get("checkoutCreate", {}).get("checkout", {}).get("webUrl")

            if not checkout_url:
                raise APIError(
                    ErrorCode.SHOPIFY_CHECKOUT_CREATE_FAILED,
                    "Failed to create checkout - no URL returned"
                )

            # Validate checkout URL via HTTP HEAD before returning
            if not await self._validate_checkout_url(checkout_url):
                raise APIError(
                    ErrorCode.SHOPIFY_CHECKOUT_URL_INVALID,
                    "Generated checkout URL is invalid"
                )

            return checkout_url

        except Exception as e:
            if isinstance(e, APIError):
                raise
            raise APIError(
                ErrorCode.SHOPIFY_CHECKOUT_CREATE_FAILED,
                f"Failed to create checkout: {str(e)}"
            )

    async def _validate_checkout_url(self, checkout_url: str) -> bool:
        """Validate checkout URL via HTTP HEAD request.

        Args:
            checkout_url: Checkout URL to validate

        Returns:
            True if URL is valid (returns 200 OK)
        """
        try:
            # Issue #2: Follow redirects (302/307) and set timeout
            response = await self.async_client.head(
                checkout_url,
                follow_redirects=True,
                timeout=5.0
            )
            return response.status_code == 200
        except Exception:
            return False

    def _get_mock_products(self) -> List[Dict[str, Any]]:
        """Get mock products for testing.

        Returns:
            List of mock product dictionaries
        """
        return [
            {
                "id": "gid://shopify/Product/1",
                "title": "Test Product 1",
                "description": "Test description",
                "priceRange": {
                    "minVariantPrice": {"amount": "100.00", "currencyCode": "USD"},
                    "maxVariantPrice": {"amount": "100.00", "currencyCode": "USD"}
                },
                "imageUrl": "https://example.com/product1.jpg",
                "availableForSale": True
            }
        ]
