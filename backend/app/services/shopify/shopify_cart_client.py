"""Shopify Storefront Cart API client for real-time cart sync.

Provides async GraphQL mutations for Shopify Cart API:
- cartCreate: Create a new cart with optional line items
- cartLinesAdd: Add items to existing cart
- cartLinesRemove: Remove items from cart
- cartLinesUpdate: Update item quantities
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import structlog

from app.core.errors import APIError, ErrorCode
from app.services.shopify_base import ShopifyBaseClient

SHOPIFY_STOREFRONT_API_URL = "https://{shop}/api/2024-01/graphql"

logger = structlog.get_logger(__name__)


class ShopifyCartClient(ShopifyBaseClient):
    """Shopify Storefront Cart API client for real-time cart synchronization.

    Multi-tenant aware - each instance is configured with a specific merchant's
    Shopify credentials.
    """

    async def create_cart(
        self,
        lines: Optional[List[Dict[str, Any]]] = None,
        buyer_identity: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a new Shopify cart.

        Args:
            lines: Optional list of line items [{'merchandiseId': variant_gid, 'quantity': 1}]
            buyer_identity: Optional buyer identity for personalized pricing

        Returns:
            Dict with cart_id, checkout_url, and lines with their IDs

        Raises:
            APIError: If cart creation fails
        """
        mutation = """
        mutation cartCreate($input: CartInput!) {
            cartCreate(input: $input) {
                cart {
                    id
                    checkoutUrl
                    lines(first: 100) {
                        edges {
                            node {
                                id
                                merchandise {
                                    ... on ProductVariant {
                                        id
                                    }
                                }
                                quantity
                            }
                        }
                    }
                }
                userErrors {
                    code
                    field
                    message
                }
            }
        }
        """

        cart_input: Dict[str, Any] = {}
        if lines:
            cart_input["lines"] = lines
        if buyer_identity:
            cart_input["buyerIdentity"] = buyer_identity

        variables = {"input": cart_input}

        try:
            if self.is_testing:
                return self._mock_create_cart(lines)

            response = await self.async_client.post(
                SHOPIFY_STOREFRONT_API_URL.format(shop=self.shop_domain),
                json={"query": mutation, "variables": variables},
                headers={"X-Shopify-Storefront-Access-Token": self.access_token},
            )
            response.raise_for_status()
            data = response.json()

            if "errors" in data:
                logger.error("shopify_cart_create_graphql_errors", errors=data["errors"])
                raise APIError(
                    ErrorCode.SHOPIFY_API_ERROR,
                    f"Shopify cart create error: {data['errors']}",
                )

            result = data.get("data", {}).get("cartCreate", {})
            user_errors = result.get("userErrors", [])

            if user_errors:
                logger.error("shopify_cart_create_user_errors", errors=user_errors)
                raise APIError(
                    ErrorCode.SHOPIFY_API_ERROR,
                    f"Shopify cart user errors: {[e['message'] for e in user_errors]}",
                )

            cart = result.get("cart", {})
            if not cart:
                raise APIError(
                    ErrorCode.SHOPIFY_API_ERROR,
                    "No cart returned from Shopify",
                )

            line_mapping = {}
            for edge in cart.get("lines", {}).get("edges", []):
                node = edge.get("node", {})
                variant_id = node.get("merchandise", {}).get("id", "")
                line_id = node.get("id", "")
                if variant_id and line_id:
                    line_mapping[variant_id] = line_id

            logger.info(
                "shopify_cart_created",
                cart_id=cart.get("id"),
                line_count=len(line_mapping),
            )

            return {
                "cart_id": cart.get("id"),
                "checkout_url": cart.get("checkoutUrl"),
                "line_ids": line_mapping,
            }

        except APIError:
            raise
        except Exception as e:
            logger.error("shopify_cart_create_failed", error=str(e))
            raise APIError(
                ErrorCode.SHOPIFY_API_ERROR,
                f"Failed to create Shopify cart: {str(e)}",
            )

    async def add_lines(
        self,
        cart_id: str,
        lines: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Add line items to an existing Shopify cart.

        Args:
            cart_id: Shopify cart GID
            lines: List of line items [{'merchandiseId': variant_gid, 'quantity': 1}]

        Returns:
            Dict with updated line_ids mapping

        Raises:
            APIError: If add operation fails
        """
        mutation = """
        mutation cartLinesAdd($cartId: ID!, $lines: [CartLineInput!]!) {
            cartLinesAdd(cartId: $cartId, lines: $lines) {
                cart {
                    id
                    lines(first: 100) {
                        edges {
                            node {
                                id
                                merchandise {
                                    ... on ProductVariant {
                                        id
                                    }
                                }
                                quantity
                            }
                        }
                    }
                }
                userErrors {
                    code
                    field
                    message
                }
            }
        }
        """

        variables = {"cartId": cart_id, "lines": lines}

        try:
            if self.is_testing:
                return self._mock_add_lines(lines)

            response = await self.async_client.post(
                SHOPIFY_STOREFRONT_API_URL.format(shop=self.shop_domain),
                json={"query": mutation, "variables": variables},
                headers={"X-Shopify-Storefront-Access-Token": self.access_token},
            )
            response.raise_for_status()
            data = response.json()

            if "errors" in data:
                logger.error("shopify_cart_add_graphql_errors", errors=data["errors"])
                raise APIError(
                    ErrorCode.SHOPIFY_API_ERROR,
                    f"Shopify cart add error: {data['errors']}",
                )

            result = data.get("data", {}).get("cartLinesAdd", {})
            user_errors = result.get("userErrors", [])

            if user_errors:
                logger.error("shopify_cart_add_user_errors", errors=user_errors, cart_id=cart_id)
                raise APIError(
                    ErrorCode.SHOPIFY_API_ERROR,
                    f"Shopify cart add user errors: {[e['message'] for e in user_errors]}",
                )

            cart = result.get("cart", {})
            line_mapping = {}
            for edge in cart.get("lines", {}).get("edges", []):
                node = edge.get("node", {})
                variant_id = node.get("merchandise", {}).get("id", "")
                line_id = node.get("id", "")
                if variant_id and line_id:
                    line_mapping[variant_id] = line_id

            logger.info(
                "shopify_cart_lines_added",
                cart_id=cart_id,
                added_count=len(lines),
                total_lines=len(line_mapping),
            )

            return {"line_ids": line_mapping}

        except APIError:
            raise
        except Exception as e:
            logger.error("shopify_cart_add_failed", cart_id=cart_id, error=str(e))
            raise APIError(
                ErrorCode.SHOPIFY_API_ERROR,
                f"Failed to add to Shopify cart: {str(e)}",
            )

    async def remove_lines(
        self,
        cart_id: str,
        line_ids: List[str],
    ) -> Dict[str, Any]:
        """Remove line items from a Shopify cart.

        Args:
            cart_id: Shopify cart GID
            line_ids: List of Shopify line item GIDs to remove

        Returns:
            Dict with remaining line_ids mapping

        Raises:
            APIError: If remove operation fails
        """
        mutation = """
        mutation cartLinesRemove($cartId: ID!, $lineIds: [ID!]!) {
            cartLinesRemove(cartId: $cartId, lineIds: $lineIds) {
                cart {
                    id
                    lines(first: 100) {
                        edges {
                            node {
                                id
                                merchandise {
                                    ... on ProductVariant {
                                        id
                                    }
                                }
                                quantity
                            }
                        }
                    }
                }
                userErrors {
                    code
                    field
                    message
                }
            }
        }
        """

        variables = {"cartId": cart_id, "lineIds": line_ids}

        try:
            if self.is_testing:
                return self._mock_remove_lines(line_ids)

            response = await self.async_client.post(
                SHOPIFY_STOREFRONT_API_URL.format(shop=self.shop_domain),
                json={"query": mutation, "variables": variables},
                headers={"X-Shopify-Storefront-Access-Token": self.access_token},
            )
            response.raise_for_status()
            data = response.json()

            if "errors" in data:
                logger.error("shopify_cart_remove_graphql_errors", errors=data["errors"])
                raise APIError(
                    ErrorCode.SHOPIFY_API_ERROR,
                    f"Shopify cart remove error: {data['errors']}",
                )

            result = data.get("data", {}).get("cartLinesRemove", {})
            user_errors = result.get("userErrors", [])

            if user_errors:
                logger.error(
                    "shopify_cart_remove_user_errors",
                    errors=user_errors,
                    cart_id=cart_id,
                    line_ids=line_ids,
                )
                raise APIError(
                    ErrorCode.SHOPIFY_API_ERROR,
                    f"Shopify cart remove user errors: {[e['message'] for e in user_errors]}",
                )

            cart = result.get("cart", {})
            line_mapping = {}
            for edge in cart.get("lines", {}).get("edges", []):
                node = edge.get("node", {})
                variant_id = node.get("merchandise", {}).get("id", "")
                line_id = node.get("id", "")
                if variant_id and line_id:
                    line_mapping[variant_id] = line_id

            logger.info(
                "shopify_cart_lines_removed",
                cart_id=cart_id,
                removed_count=len(line_ids),
                remaining_lines=len(line_mapping),
            )

            return {"line_ids": line_mapping}

        except APIError:
            raise
        except Exception as e:
            logger.error(
                "shopify_cart_remove_failed",
                cart_id=cart_id,
                line_ids=line_ids,
                error=str(e),
            )
            raise APIError(
                ErrorCode.SHOPIFY_API_ERROR,
                f"Failed to remove from Shopify cart: {str(e)}",
            )

    async def update_lines(
        self,
        cart_id: str,
        lines: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Update line item quantities in a Shopify cart.

        Args:
            cart_id: Shopify cart GID
            lines: List of line updates [{'id': line_gid, 'quantity': 2}]

        Returns:
            Dict with updated line_ids mapping

        Raises:
            APIError: If update operation fails
        """
        mutation = """
        mutation cartLinesUpdate($cartId: ID!, $lines: [CartLineUpdateInput!]!) {
            cartLinesUpdate(cartId: $cartId, lines: $lines) {
                cart {
                    id
                    lines(first: 100) {
                        edges {
                            node {
                                id
                                merchandise {
                                    ... on ProductVariant {
                                        id
                                    }
                                }
                                quantity
                            }
                        }
                    }
                }
                userErrors {
                    code
                    field
                    message
                }
            }
        }
        """

        variables = {"cartId": cart_id, "lines": lines}

        try:
            if self.is_testing:
                return self._mock_update_lines(lines)

            response = await self.async_client.post(
                SHOPIFY_STOREFRONT_API_URL.format(shop=self.shop_domain),
                json={"query": mutation, "variables": variables},
                headers={"X-Shopify-Storefront-Access-Token": self.access_token},
            )
            response.raise_for_status()
            data = response.json()

            if "errors" in data:
                logger.error("shopify_cart_update_graphql_errors", errors=data["errors"])
                raise APIError(
                    ErrorCode.SHOPIFY_API_ERROR,
                    f"Shopify cart update error: {data['errors']}",
                )

            result = data.get("data", {}).get("cartLinesUpdate", {})
            user_errors = result.get("userErrors", [])

            if user_errors:
                logger.error(
                    "shopify_cart_update_user_errors",
                    errors=user_errors,
                    cart_id=cart_id,
                )
                raise APIError(
                    ErrorCode.SHOPIFY_API_ERROR,
                    f"Shopify cart update user errors: {[e['message'] for e in user_errors]}",
                )

            cart = result.get("cart", {})
            line_mapping = {}
            for edge in cart.get("lines", {}).get("edges", []):
                node = edge.get("node", {})
                variant_id = node.get("merchandise", {}).get("id", "")
                line_id = node.get("id", "")
                if variant_id and line_id:
                    line_mapping[variant_id] = line_id

            logger.info(
                "shopify_cart_lines_updated",
                cart_id=cart_id,
                updated_count=len(lines),
            )

            return {"line_ids": line_mapping}

        except APIError:
            raise
        except Exception as e:
            logger.error("shopify_cart_update_failed", cart_id=cart_id, error=str(e))
            raise APIError(
                ErrorCode.SHOPIFY_API_ERROR,
                f"Failed to update Shopify cart: {str(e)}",
            )

    def _mock_create_cart(
        self,
        lines: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Return mock cart for testing."""
        import uuid

        cart_id = f"gid://shopify/Cart/{uuid.uuid4().hex}"
        checkout_url = f"https://{self.shop_domain}/cart/c/{uuid.uuid4().hex}"

        line_mapping = {}
        if lines:
            for i, line in enumerate(lines):
                variant_id = line.get("merchandiseId", "")
                if variant_id:
                    line_mapping[variant_id] = f"gid://shopify/CartLine/{i}"

        return {
            "cart_id": cart_id,
            "checkout_url": checkout_url,
            "line_ids": line_mapping,
        }

    def _mock_add_lines(
        self,
        lines: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Return mock response for adding lines."""
        import uuid

        line_mapping = {}
        for i, line in enumerate(lines):
            variant_id = line.get("merchandiseId", "")
            if variant_id:
                line_mapping[variant_id] = f"gid://shopify/CartLine/{uuid.uuid4().hex[:8]}{i}"

        return {"line_ids": line_mapping}

    def _mock_remove_lines(
        self,
        line_ids: List[str],
    ) -> Dict[str, Any]:
        """Return mock response for removing lines."""
        return {"line_ids": {}}

    def _mock_update_lines(
        self,
        lines: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Return mock response for updating lines."""
        line_mapping = {}
        for line in lines:
            line_id = line.get("id", "")
            line_mapping[line_id] = line_id

        return {"line_ids": line_mapping}
