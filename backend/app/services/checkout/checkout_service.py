"""Checkout service for generating Shopify checkout URLs from cart items.

Follows red-green-refactor TDD cycle with CartService encapsulation and
checkout token tracking for order confirmation.
"""

from __future__ import annotations

import json
import asyncio
from datetime import datetime, timezone
from urllib.parse import urlparse
from typing import Any, Dict, Optional

import structlog
import redis.asyncio as redis

from app.core.errors import APIError, ErrorCode
from app.schemas.cart import Cart
from app.services.cart import CartService
from app.services.checkout.checkout_schema import CheckoutStatus
from app.services.shopify_storefront import ShopifyStorefrontClient


class CheckoutService:
    """Service for generating checkout URLs from cart items.

    Checkout Flow:
    1. Retrieve cart using CartService (encapsulated)
    2. Build Shopify line items from Cart object
    3. Call checkoutCreate mutation (client handles validation)
    4. Retry on failure (max 3 attempts with backoff)
    5. Store checkout token for cart preservation
    6. Retain local cart (do NOT clear) until order confirmation

    Data Storage:
    - Checkout Token: checkout_token:{psid} with 24-hour TTL
    - Local Cart: Retained until order confirmation (Story 2.9)
    """

    MAX_RETRY_ATTEMPTS = 3
    CHECKOUT_TOKEN_TTL_HOURS = 24
    RETRY_BACKOFF_SECONDS = 1.0

    def __init__(
        self,
        redis_client: Optional[Any] = None,
        shopify_client: Optional[ShopifyStorefrontClient] = None,
        cart_service: Optional[CartService] = None,
    ) -> None:
        """Initialize checkout service.

        Args:
            redis_client: Redis client instance
            shopify_client: Shopify Storefront API client (REQUIRED)
            cart_service: Cart service instance
        """
        if redis_client is None:
            # Create default Redis client (Async)
            from app.core.config import settings
            config = settings()
            redis_url = config.get("REDIS_URL", "redis://localhost:6379/0")
            self.redis = redis.from_url(redis_url, decode_responses=True)
        else:
            self.redis = redis_client

        # Initialization Guard (Issue #1)
        if shopify_client is None:
            raise ValueError("CheckoutService requires a valid shopify_client instance")
        self.shopify_client = shopify_client

        # Reuse Redis client for CartService
        self.cart_service = cart_service or CartService(self.redis)
        self.logger = structlog.get_logger(__name__)

    def _get_checkout_token_key(self, psid: str) -> str:
        """Generate Redis key for checkout token.

        Args:
            psid: Facebook Page-Scoped ID

        Returns:
            Redis key for checkout token storage
        """
        return f"checkout_token:{psid}"

    async def generate_checkout_url(
        self,
        psid: str,
    ) -> Dict[str, Any]:
        """Generate Shopify checkout URL from cart items.

        Args:
            psid: Facebook Page-Scoped ID

        Returns:
            Dict with status, checkout_url, and message
        """
        # Get cart using CartService (Encapsulation)
        try:
            cart = await self.cart_service.get_cart(psid)
        except APIError:
            self.logger.error("checkout_cart_retrieval_failed", psid=psid)
            return {
                "status": CheckoutStatus.FAILED,
                "checkout_url": None,
                "checkout_token": None,
                "message": "Failed to retrieve your cart.",
                "retry_count": 0,
            }

        # Check if cart has items
        if not cart.items:
            self.logger.info("checkout_empty_cart", psid=psid)
            return {
                "status": CheckoutStatus.EMPTY_CART,
                "checkout_url": None,
                "checkout_token": None,
                "message": "Your cart is empty. Add items before checkout.",
                "retry_count": 0,
            }

        # Build line items for Shopify
        line_items = []
        for item in cart.items:
            line_items.append({
                "variant_id": item.variant_id,
                "quantity": item.quantity
            })

        self.logger.info(
            "checkout_generation_started",
            psid=psid,
            item_count=len(line_items),
        )

        # Retry Loop (Issue #4)
        last_error = None
        for attempt in range(self.MAX_RETRY_ATTEMPTS + 1):
            try:
                # Generate checkout URL via Shopify
                # Note: client.create_checkout_url performs HTTP HEAD validation
                checkout_url = await self.shopify_client.create_checkout_url(line_items)

                # Store checkout token for cart preservation
                checkout_token = self._extract_checkout_token(checkout_url)

                if checkout_token:
                    await self._store_checkout_token(
                        psid=psid,
                        checkout_token=checkout_token,
                        checkout_url=checkout_url,
                        cart=cart,
                    )

                # Mask token for logging (Issue #6)
                masked_token = f"{checkout_token[:4]}...{checkout_token[-4:]}" if checkout_token and len(checkout_token) > 8 else "tok_***"

                self.logger.info(
                    "checkout_generation_success",
                    psid=psid,
                    retry_count=attempt,
                    checkout_token_masked=masked_token,
                )

                return {
                    "status": CheckoutStatus.SUCCESS,
                    "checkout_url": checkout_url,
                    "checkout_token": checkout_token,
                    "message": f"Complete your purchase here: {checkout_url}",
                    "retry_count": attempt,
                }

            except APIError as e:
                last_error = e
                if e.code == ErrorCode.SHOPIFY_CHECKOUT_URL_INVALID and attempt < self.MAX_RETRY_ATTEMPTS:
                    # Retry on validation failure with backoff
                    self.logger.warning(
                        "checkout_validation_failed_retry",
                        psid=psid,
                        retry_count=attempt,
                        max_retries=self.MAX_RETRY_ATTEMPTS,
                        backoff=self.RETRY_BACKOFF_SECONDS
                    )
                    await asyncio.sleep(self.RETRY_BACKOFF_SECONDS)
                    continue
                else:
                    # Break immediately for non-retryable errors or max attempts
                    break

        # If we get here, all retries failed
        self.logger.error(
            "checkout_generation_failed",
            psid=psid,
            error=str(last_error) if last_error else "Unknown error",
            error_code=last_error.code.value if last_error and isinstance(last_error.code, ErrorCode) else None,
            retry_count=attempt,
        )

        return {
            "status": CheckoutStatus.FAILED,
            "checkout_url": None,
            "checkout_token": None,
            "message": "Sorry, checkout failed. Please try again later.",
            "retry_count": attempt,
        }

    def _extract_checkout_token(self, checkout_url: str) -> Optional[str]:
        """Extract checkout token from Shopify checkout URL.

        Handles custom domains by extracting the last path segment.

        Args:
            checkout_url: Shopify checkout URL

        Returns:
            Checkout token or None if not found
        """
        try:
            # Issue #3: Robust extraction using urlparse
            path = urlparse(checkout_url).path
            # Handle potential trailing slashes
            path = path.rstrip('/')
            token = path.split('/')[-1]

            # Basic validation: Token should be reasonably long
            if len(token) > 5:
                return token
            return None
        except Exception:
            return None

    async def _store_checkout_token(
        self,
        psid: str,
        checkout_token: str,
        checkout_url: str,
        cart: Cart,
    ) -> None:
        """Store checkout token in Redis for order confirmation.

        Args:
            psid: Facebook Page-Scoped ID
            checkout_token: Checkout token from URL
            checkout_url: Full checkout URL
            cart: Cart object for reference
        """
        checkout_token_key = self._get_checkout_token_key(psid)
        ttl_seconds = self.CHECKOUT_TOKEN_TTL_HOURS * 60 * 60

        token_data = {
            "token": checkout_token,
            "url": checkout_url,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "psid": psid,
            "item_count": cart.item_count,
            "subtotal": cart.subtotal,
            "currency_code": cart.currency_code.value,
        }

        # Issue #5: Async Redis call
        await self.redis.setex(
            checkout_token_key,
            ttl_seconds,
            json.dumps(token_data),
        )

        # Issue #6: Mask token in logs
        masked_token = f"{checkout_token[:4]}...{checkout_token[-4:]}" if len(checkout_token) > 8 else "tok_***"
        self.logger.info(
            "checkout_token_stored",
            psid=psid,
            token_masked=masked_token,
            ttl_hours=self.CHECKOUT_TOKEN_TTL_HOURS,
        )

    async def get_checkout_token(self, psid: str) -> Optional[Dict[str, Any]]:
        """Retrieve checkout token data for order confirmation.

        Args:
            psid: Facebook Page-Scoped ID

        Returns:
            Checkout token data or None if not found
        """
        checkout_token_key = self._get_checkout_token_key(psid)
        # Issue #5: Async Redis call
        token_data = await self.redis.get(checkout_token_key)

        if token_data:
            return json.loads(token_data)

        return None