"""Shopify Admin API client for order polling.

Story 4-4 Task 1 & 5: Admin API client with authentication and rate limiting

Provides authenticated access to Shopify Admin API for:
- Fetching orders updated since a given time
- Rate limit tracking and backoff
- 429 response handling with exponential backoff retry
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import aiohttp
import structlog

logger = structlog.get_logger(__name__)


class ShopifyAPIError(Exception):
    """Base exception for Shopify Admin API errors."""

    def __init__(
        self, message: str, status_code: int | None = None, error_code: int | None = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(message)


class ShopifyAuthError(ShopifyAPIError):
    """Authentication failed (401)."""

    def __init__(self, message: str = "Shopify authentication failed"):
        super().__init__(message, status_code=401, error_code=7052)


class ShopifyRateLimitError(ShopifyAPIError):
    """Rate limit exceeded (429)."""

    def __init__(
        self, message: str = "Shopify rate limit exceeded", retry_after: int | None = None
    ):
        self.retry_after = retry_after
        super().__init__(message, status_code=429, error_code=7051)


@dataclass
class RateLimitInfo:
    """Rate limit tracking info."""

    used: int = 0
    max: int = 1000

    @property
    def percentage(self) -> float:
        if self.max == 0:
            return 0.0
        return (self.used / self.max) * 100


class ShopifyAdminClient:
    """Client for Shopify Admin API operations.

    Features:
    - OAuth access token authentication
    - Rate limit tracking via X-Shopify-Shop-Api-Call-Limit header
    - Automatic backoff when approaching rate limit (>80%)
    - Exponential backoff retry for 429 responses
    - Request timeout handling

    Usage:
        async with ShopifyAdminClient(shop_domain, access_token) as client:
            orders = await client.get_orders_updated_since(minutes=5)
    """

    DEFAULT_TIMEOUT = 30
    BACKOFF_THRESHOLD_PERCENT = 80.0

    def __init__(
        self,
        shop_domain: str,
        access_token: str,
        api_version: str = "2024-01",
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        """Initialize Shopify Admin API client.

        Args:
            shop_domain: Shopify shop domain (e.g., "myshop.myshopify.com")
            access_token: Shopify Admin API access token
            api_version: Shopify API version (default: 2024-01)
            timeout: Request timeout in seconds
        """
        self.shop_domain = shop_domain
        self.access_token = access_token
        self.api_version = api_version
        self.timeout = timeout
        self.base_url = f"https://{shop_domain}/admin/api/{api_version}"

        self._session: aiohttp.ClientSession | None = None
        self._rate_limit_info = RateLimitInfo()

    @property
    def rate_limit_used(self) -> int:
        return self._rate_limit_info.used

    @rate_limit_used.setter
    def rate_limit_used(self, value: int) -> None:
        self._rate_limit_info.used = value

    @property
    def rate_limit_max(self) -> int:
        return self._rate_limit_info.max

    @rate_limit_max.setter
    def rate_limit_max(self, value: int) -> None:
        self._rate_limit_info.max = value

    def rate_limit_percentage(self) -> float:
        return self._rate_limit_info.percentage

    def should_backoff(self) -> bool:
        return self._rate_limit_info.percentage >= self.BACKOFF_THRESHOLD_PERCENT

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def __aenter__(self) -> ShopifyAdminClient:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    def _get_headers(self) -> dict[str, str]:
        return {
            "X-Shopify-Access-Token": self.access_token,
            "Content-Type": "application/json",
        }

    def _update_rate_limit_from_headers(self, headers: dict) -> None:
        header_value = headers.get("X-Shopify-Shop-Api-Call-Limit", "")
        if header_value and "/" in header_value:
            try:
                used, max_limit = header_value.split("/")
                self.rate_limit_used = int(used)
                self.rate_limit_max = int(max_limit)

                logger.debug(
                    "shopify_rate_limit_updated",
                    used=self.rate_limit_used,
                    max=self.rate_limit_max,
                    percentage=self.rate_limit_percentage(),
                )
            except (ValueError, TypeError):
                pass

    async def get_orders_updated_since(
        self,
        minutes: int = 5,
        status: str = "any",
        limit: int = 250,
        max_retries: int = 3,
    ) -> list[dict[str, Any]]:
        """Get orders updated in the last N minutes.

        Args:
            minutes: Number of minutes to look back
            status: Order status filter (default: "any")
            limit: Maximum number of orders to return (max 250)
            max_retries: Maximum retry attempts for 429 responses

        Returns:
            List of order dictionaries

        Raises:
            ShopifyAuthError: If authentication fails (401)
            ShopifyRateLimitError: If rate limit exceeded after retries
            ShopifyAPIError: For other API errors
        """
        updated_at_min = (datetime.now(UTC) - timedelta(minutes=minutes)).isoformat()

        params = {
            "updated_at_min": updated_at_min,
            "status": status,
            "limit": min(limit, 250),
            "fields": ",".join(
                [
                    "id",
                    "order_number",
                    "updated_at",
                    "created_at",
                    "financial_status",
                    "fulfillment_status",
                    "customer",
                    "email",
                    "tracking_numbers",
                    "tracking_urls",
                    "note_attributes",
                    "line_items",
                    "current_subtotal_price",
                    "current_total_price",
                    "subtotal_price",
                    "total_price",
                    "currency",
                    "currency_code",
                    "shipping_address",
                    "fulfillments",
                ]
            ),
        }

        url = f"{self.base_url}/orders.json"
        retry_count = 0
        base_delay = 1.0

        while True:
            session = await self._get_session()

            try:
                async with session.get(
                    url,
                    headers=self._get_headers(),
                    params=params,
                ) as response:
                    self._update_rate_limit_from_headers(dict(response.headers))

                    if response.status == 200:
                        data = await response.json()
                        orders = data.get("orders", [])

                        logger.info(
                            "shopify_admin_orders_fetched",
                            shop_domain=self.shop_domain,
                            count=len(orders),
                            rate_limit_used=self.rate_limit_used,
                            rate_limit_max=self.rate_limit_max,
                        )

                        return orders

                    elif response.status == 401:
                        logger.error(
                            "shopify_admin_auth_failed",
                            shop_domain=self.shop_domain,
                            status_code=401,
                            error_code=7052,
                        )
                        raise ShopifyAuthError()

                    elif response.status == 429:
                        retry_after = int(
                            response.headers.get("Retry-After", base_delay * (2**retry_count))
                        )

                        if retry_count >= max_retries:
                            logger.error(
                                "shopify_admin_rate_limit_exceeded",
                                shop_domain=self.shop_domain,
                                retry_count=retry_count,
                                max_retries=max_retries,
                                error_code=7051,
                            )
                            raise ShopifyRateLimitError(retry_after=retry_after)

                        logger.warning(
                            "shopify_admin_rate_limited_retrying",
                            shop_domain=self.shop_domain,
                            retry_after=retry_after,
                            retry_count=retry_count + 1,
                            max_retries=max_retries,
                            error_code=7051,
                        )

                        await asyncio.sleep(retry_after)
                        retry_count += 1
                        continue

                    else:
                        error_text = await response.text()
                        logger.error(
                            "shopify_admin_api_error",
                            shop_domain=self.shop_domain,
                            status_code=response.status,
                            error=error_text[:500],
                            error_code=7050,
                        )
                        raise ShopifyAPIError(
                            f"Shopify API error: {response.status}",
                            status_code=response.status,
                            error_code=7050,
                        )

            except TimeoutError:
                logger.error(
                    "shopify_admin_timeout",
                    shop_domain=self.shop_domain,
                    error_code=7050,
                )
                raise ShopifyAPIError("Shopify API request timed out", error_code=7050)

            except aiohttp.ClientError as e:
                logger.error(
                    "shopify_admin_client_error",
                    shop_domain=self.shop_domain,
                    error=str(e),
                    error_code=7050,
                )
                raise ShopifyAPIError(f"Shopify API client error: {str(e)}", error_code=7050)

    async def wait_for_rate_limit_if_needed(self, min_headroom: int = 200) -> None:
        """Wait if approaching rate limit.

        Args:
            min_headroom: Minimum remaining calls before proceeding
        """
        remaining = self.rate_limit_max - self.rate_limit_used

        if remaining < min_headroom:
            wait_time = 60
            logger.warning(
                "shopify_admin_rate_limit_backoff",
                shop_domain=self.shop_domain,
                remaining=remaining,
                min_headroom=min_headroom,
                wait_seconds=wait_time,
            )
            await asyncio.sleep(wait_time)
