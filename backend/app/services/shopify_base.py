"""Base client for Shopify API integrations.

Provides shared functionality for Shopify Storefront and Admin API clients.
"""

from __future__ import annotations

from typing import Optional
import httpx

from app.core.http_client import get_ssl_context


class ShopifyBaseClient:
    """Base class for Shopify API clients with common patterns."""

    def __init__(
        self,
        shop_domain: Optional[str] = None,
        access_token: Optional[str] = None,
        is_testing: bool = False,
    ) -> None:
        """Initialize Shopify base client.

        Args:
            shop_domain: Shopify shop domain (e.g., mystore.myshopify.com)
            access_token: Shopify access token
            is_testing: Whether running in test mode (uses mock client)
        """
        from app.core.config import settings

        app_settings = settings()

        self.shop_domain = shop_domain or app_settings.get("SHOPIFY_STORE_URL", "").replace(
            "https://", ""
        ).replace("http://", "").strip("/")
        self.access_token = access_token or app_settings.get("SHOPIFY_STOREFRONT_ACCESS_TOKEN", "")
        self.is_testing = is_testing or app_settings.get("IS_TESTING", False)
        self._async_client: Optional[httpx.AsyncClient] = None

    @property
    def async_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client with testing support.

        Returns:
            Configured httpx.AsyncClient
        """
        if self._async_client is None:
            if self.is_testing:
                from httpx import ASGITransport

                # For testing, use a mock client that raises errors on actual calls
                # The subclasses override methods to return mock data
                from app.main import app

                self._async_client = httpx.AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                )
            else:
                # Use SSL context with certifi for macOS compatibility
                ssl_context = get_ssl_context()
                self._async_client = httpx.AsyncClient(verify=ssl_context, timeout=30.0)
        return self._async_client

    async def close(self) -> None:
        """Close HTTP client."""
        if self._async_client:
            await self._async_client.aclose()
            self._async_client = None
