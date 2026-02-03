"""Shopify Admin API client for webhook management and token creation.

Uses REST API to manage webhooks and create Storefront access tokens.
"""

from __future__ import annotations

from typing import Optional, Dict, Any
import httpx
import asyncio
import structlog

from app.services.shopify_base import ShopifyBaseClient
from app.core.errors import APIError, ErrorCode

SHOPIFY_ADMIN_API_URL = "https://{shop}.myshopify.com/admin/api/2024-01"

logger = structlog.get_logger(__name__)


class ShopifyAdminClient(ShopifyBaseClient):
    """Shopify Admin API client for webhook management."""

    async def _handle_rate_limit(self, response: httpx.Response) -> None:
        """Check and handle rate limit headers from Shopify.

        Shopify Admin API has 40 calls/sec leaky bucket rate limit.

        Args:
            response: HTTP response from Shopify
        """
        retry_after = response.headers.get('Retry-After')
        if retry_after:
            # Wait for specified seconds before retrying
            await asyncio.sleep(int(retry_after))

    async def create_storefront_access_token(
        self,
        title: str
    ) -> str:
        """Create Storefront API access token via Admin API.

        Args:
            title: Token title for identification

        Returns:
            Storefront access token

        Raises:
            APIError: If token creation fails
        """
        url = f"{SHOPIFY_ADMIN_API_URL.format(shop=self.shop_domain)}/storefront_access_tokens/create.json"

        payload = {
            "storefront_access_token": {
                "title": title
            }
        }

        try:
            if self.is_testing:
                return "test_storefront_token"

            response = await self.async_client.post(
                url,
                json=payload,
                headers={"X-Shopify-Access-Token": self.access_token},
                timeout=30.0  # 30 second timeout
            )

            await self._handle_rate_limit(response)
            response.raise_for_status()
            data = response.json()

            # Check for errors
            if "errors" in data:
                raise APIError(
                    ErrorCode.SHOPIFY_STOREFRONT_TOKEN_FAILED,
                    f"Failed to create Storefront token: {data['errors']}"
                )

            # Extract access token
            token = data.get("storefront_access_token", {}).get("access_token")

            if not token:
                raise APIError(
                    ErrorCode.SHOPIFY_STOREFRONT_TOKEN_FAILED,
                    "No access token returned"
                )

            return token

        except APIError:
            raise
        except httpx.HTTPStatusError as e:
            raise APIError(
                ErrorCode.SHOPIFY_STOREFRONT_TOKEN_FAILED,
                f"Failed to create Storefront token: {e.response.text}"
            )
        except Exception as e:
            raise APIError(
                ErrorCode.SHOPIFY_STOREFRONT_TOKEN_FAILED,
                f"Failed to create Storefront token: {str(e)}"
            )

    async def subscribe_webhook(
        self,
        topic: str,
        webhook_url: str
    ) -> bool:
        """Subscribe to Shopify webhook topic.

        Args:
            topic: Webhook topic (e.g., "orders/create")
            webhook_url: Webhook endpoint URL

        Returns:
            True if subscription successful
        """
        url = f"{SHOPIFY_ADMIN_API_URL.format(shop=self.shop_domain)}/webhooks.json"

        payload = {
            "webhook": {
                "topic": topic,
                "address": webhook_url,
                "format": "json"
            }
        }

        try:
            if self.is_testing:
                return True

            response = await self.async_client.post(
                url,
                json=payload,
                headers={"X-Shopify-Access-Token": self.access_token}
            )

            await self._handle_rate_limit(response)
            response.raise_for_status()
            data = response.json()

            # Check for errors
            if "errors" in data:
                logger.warning("webhook_subscription_failed", topic=topic, errors=data['errors'])
                return False

            return data.get("webhook") is not None

        except httpx.HTTPStatusError:
            return False
        except Exception:
            return False

    async def verify_webhook_subscription(self, topic: str) -> bool:
        """Verify that a webhook subscription exists for a topic.

        Args:
            topic: Webhook topic to verify (e.g., "orders/create")

        Returns:
            True if webhook subscription exists
        """
        url = f"{SHOPIFY_ADMIN_API_URL.format(shop=self.shop_domain)}/webhooks.json"

        try:
            if self.is_testing:
                return True

            response = await self.async_client.get(
                url,
                headers={"X-Shopify-Access-Token": self.access_token}
            )

            await self._handle_rate_limit(response)
            response.raise_for_status()
            data = response.json()

            # Check if any webhook matches the topic
            return any(
                wh.get('topic') == topic
                for wh in data.get('webhooks', [])
            )

        except Exception:
            return False

    async def verify_shop_access(self) -> Dict[str, Any]:
        """Verify Admin API access and fetch shop details.

        Returns:
            Shop details dict

        Raises:
            APIError: If verification fails
        """
        url = f"{SHOPIFY_ADMIN_API_URL.format(shop=self.shop_domain)}/shop.json"

        try:
            if self.is_testing:
                return {
                    "id": 123456789,
                    "name": "Test Store",
                    "domain": "test-store.myshopify.com"
                }

            response = await self.async_client.get(
                url,
                headers={"X-Shopify-Access-Token": self.access_token}
            )

            await self._handle_rate_limit(response)
            response.raise_for_status()
            data = response.json()

            # Check for errors
            if "errors" in data:
                raise APIError(
                    ErrorCode.SHOPIFY_ADMIN_API_ACCESS_DENIED,
                    f"Admin API access denied: {data['errors']}"
                )

            return data.get("shop", {})

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401 or e.response.status_code == 403:
                raise APIError(
                    ErrorCode.SHOPIFY_ADMIN_API_ACCESS_DENIED,
                    "Insufficient permissions - please grant required OAuth scopes"
                )
            raise APIError(
                ErrorCode.SHOPIFY_API_ERROR,
                f"Failed to verify shop access: {e.response.text}"
            )
        except APIError:
            raise
        except Exception as e:
            raise APIError(
                ErrorCode.SHOPIFY_API_ERROR,
                f"Failed to verify shop access: {str(e)}"
            )
