"""Shopify Cart Synchronization Service.

Provides bidirectional sync between local Redis cart and Shopify Storefront Cart API.

Architecture:
- Fail-open: Local cart operations succeed immediately, Shopify sync happens async
- Background retry: Failed sync operations are queued for retry
- Multi-tenant: Each merchant syncs to their own Shopify store

Cart Flow:
1. Local cart operation (add/remove/update/clear) succeeds immediately
2. Shopify sync triggered asynchronously
3. On sync success: Update cart with shopify_cart_id, shopify_cart_url, shopify_line_ids
4. On sync failure: Log error, queue for retry, cart still works locally
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import structlog
import redis.asyncio as redis

from app.core.config import settings
from app.core.errors import APIError, ErrorCode
from app.schemas.cart import Cart, CartItem
from app.services.cart.cart_service import CartService
from app.services.shopify.shopify_cart_client import ShopifyCartClient

logger = structlog.get_logger(__name__)

SYNC_QUEUE_PREFIX = "shopify_cart_sync_queue:"
SYNC_QUEUE_TTL = 3600  # 1 hour
MAX_RETRY_ATTEMPTS = 3


class ShopifyCartSync:
    """Bidirectional sync between Redis cart and Shopify Cart API.

    Usage:
        sync_service = ShopifyCartSync(merchant_id=123)

        # Sync add operation
        await sync_service.sync_add_item(cart_key, item)

        # Sync remove operation
        await sync_service.sync_remove_item(cart_key, variant_id)

        # Sync update operation
        await sync_service.sync_update_quantity(cart_key, variant_id, quantity)

        # Sync clear operation
        await sync_service.sync_clear_cart(cart_key)
    """

    def __init__(
        self,
        merchant_id: int,
        redis_client: Optional[redis.Redis] = None,
        cart_service: Optional[CartService] = None,
    ) -> None:
        """Initialize Shopify cart sync service.

        Args:
            merchant_id: Merchant ID for multi-tenant support
            redis_client: Optional Redis client (creates default if not provided)
            cart_service: Optional cart service (creates default if not provided)
        """
        self.merchant_id = merchant_id
        self._redis = redis_client
        self._cart_service = cart_service
        self._shopify_client: Optional[ShopifyCartClient] = None
        self._shop_domain: Optional[str] = None
        self._access_token: Optional[str] = None
        self._initialized = False

    async def _ensure_initialized(self) -> bool:
        """Initialize Shopify client with merchant credentials.

        Returns:
            True if initialized successfully, False otherwise
        """
        if self._initialized:
            return self._shopify_client is not None

        try:
            from app.core.database import async_session
            from app.services.shopify_oauth import ShopifyService

            async with async_session() as session:
                shopify_service = ShopifyService(session)
                integration = await shopify_service.get_shopify_integration(self.merchant_id)

                if not integration:
                    logger.warning(
                        "shopify_cart_sync_no_integration",
                        merchant_id=self.merchant_id,
                    )
                    self._initialized = True
                    return False

                self._shop_domain = integration.shop_domain
                self._access_token = await shopify_service.get_storefront_token(self.merchant_id)

                if not self._access_token:
                    logger.warning(
                        "shopify_cart_sync_no_token",
                        merchant_id=self.merchant_id,
                    )
                    self._initialized = True
                    return False

                self._shopify_client = ShopifyCartClient(
                    access_token=self._access_token,
                    shop_domain=self._shop_domain,
                )

                self._initialized = True
                logger.info(
                    "shopify_cart_sync_initialized",
                    merchant_id=self.merchant_id,
                    shop_domain=self._shop_domain,
                )
                return True

        except Exception as e:
            logger.error(
                "shopify_cart_sync_init_failed",
                merchant_id=self.merchant_id,
                error=str(e),
            )
            self._initialized = True
            return False

    @property
    def redis(self) -> redis.Redis:
        """Get Redis client."""
        if self._redis is None:
            config = settings()
            redis_url = config.get("REDIS_URL", "redis://localhost:6379/0")
            self._redis = redis.from_url(redis_url, decode_responses=True)
        return self._redis

    @property
    def cart_service(self) -> CartService:
        """Get cart service."""
        if self._cart_service is None:
            self._cart_service = CartService(self.redis)
        return self._cart_service

    async def sync_add_item(
        self,
        cart_key: str,
        item: CartItem,
    ) -> Cart:
        """Sync add item to Shopify cart.

        Fail-open: Local cart succeeds immediately, Shopify sync happens async.

        Args:
            cart_key: Redis cart key
            item: Cart item to add

        Returns:
            Updated cart with Shopify sync info
        """
        cart = await self.cart_service.get_cart(cart_key)

        try:
            if not await self._ensure_initialized():
                logger.warning(
                    "shopify_sync_add_skipped_no_client",
                    cart_key=cart_key,
                    variant_id=item.variant_id,
                )
                return cart

            shopify_cart = await self._get_or_create_shopify_cart(cart)

            if shopify_cart:
                variant_gid = self._to_variant_gid(item.variant_id)
                lines = [{"merchandiseId": variant_gid, "quantity": item.quantity}]

                result = await self._shopify_client.add_lines(
                    cart_id=shopify_cart["cart_id"],
                    lines=lines,
                )

                cart.shopify_cart_id = shopify_cart["cart_id"]
                cart.shopify_cart_url = shopify_cart["checkout_url"]
                cart.shopify_line_ids.update(result.get("line_ids", {}))
                cart.shopify_sync_error = None

                await self._save_cart(cart_key, cart)

                logger.info(
                    "shopify_sync_add_success",
                    cart_key=cart_key,
                    variant_id=item.variant_id,
                    shopify_cart_id=cart.shopify_cart_id,
                )

        except Exception as e:
            await self._handle_sync_error(cart_key, cart, f"add_item: {str(e)}")

        return cart

    async def sync_remove_item(
        self,
        cart_key: str,
        variant_id: str,
    ) -> Cart:
        """Sync remove item from Shopify cart.

        Args:
            cart_key: Redis cart key
            variant_id: Variant ID to remove

        Returns:
            Updated cart
        """
        cart = await self.cart_service.get_cart(cart_key)

        try:
            if not await self._ensure_initialized():
                return cart

            if not cart.shopify_cart_id:
                logger.debug(
                    "shopify_sync_remove_no_cart",
                    cart_key=cart_key,
                )
                return cart

            line_id = cart.shopify_line_ids.get(variant_id)
            if not line_id:
                logger.debug(
                    "shopify_sync_remove_no_line_id",
                    cart_key=cart_key,
                    variant_id=variant_id,
                )
                return cart

            result = await self._shopify_client.remove_lines(
                cart_id=cart.shopify_cart_id,
                line_ids=[line_id],
            )

            if variant_id in cart.shopify_line_ids:
                del cart.shopify_line_ids[variant_id]

            cart.shopify_line_ids = result.get("line_ids", {})
            cart.shopify_sync_error = None

            await self._save_cart(cart_key, cart)

            logger.info(
                "shopify_sync_remove_success",
                cart_key=cart_key,
                variant_id=variant_id,
            )

        except Exception as e:
            await self._handle_sync_error(cart_key, cart, f"remove_item: {str(e)}")

        return cart

    async def sync_update_quantity(
        self,
        cart_key: str,
        variant_id: str,
        quantity: int,
    ) -> Cart:
        """Sync update quantity in Shopify cart.

        Args:
            cart_key: Redis cart key
            variant_id: Variant ID to update
            quantity: New quantity

        Returns:
            Updated cart
        """
        cart = await self.cart_service.get_cart(cart_key)

        try:
            if not await self._ensure_initialized():
                return cart

            if not cart.shopify_cart_id:
                return cart

            line_id = cart.shopify_line_ids.get(variant_id)
            if not line_id:
                logger.debug(
                    "shopify_sync_update_no_line_id",
                    cart_key=cart_key,
                    variant_id=variant_id,
                )
                return cart

            result = await self._shopify_client.update_lines(
                cart_id=cart.shopify_cart_id,
                lines=[{"id": line_id, "quantity": quantity}],
            )

            cart.shopify_line_ids = result.get("line_ids", {})
            cart.shopify_sync_error = None

            await self._save_cart(cart_key, cart)

            logger.info(
                "shopify_sync_update_success",
                cart_key=cart_key,
                variant_id=variant_id,
                quantity=quantity,
            )

        except Exception as e:
            await self._handle_sync_error(cart_key, cart, f"update_quantity: {str(e)}")

        return cart

    async def sync_clear_cart(
        self,
        cart_key: str,
    ) -> Cart:
        """Sync clear cart - creates a new empty Shopify cart.

        Args:
            cart_key: Redis cart key

        Returns:
            Updated cart with new Shopify cart ID
        """
        cart = await self.cart_service.get_cart(cart_key)

        try:
            if not await self._ensure_initialized():
                return cart

            if not cart.shopify_cart_id:
                return cart

            result = await self._shopify_client.create_cart(lines=[])

            cart.shopify_cart_id = result["cart_id"]
            cart.shopify_cart_url = result["checkout_url"]
            cart.shopify_line_ids = {}
            cart.shopify_sync_error = None

            await self._save_cart(cart_key, cart)

            logger.info(
                "shopify_sync_clear_success",
                cart_key=cart_key,
                new_shopify_cart_id=cart.shopify_cart_id,
            )

        except Exception as e:
            await self._handle_sync_error(cart_key, cart, f"clear_cart: {str(e)}")

        return cart

    async def sync_rebuild_cart(
        self,
        cart_key: str,
    ) -> Cart:
        """Rebuild Shopify cart from local cart.

        Used when Shopify cart is expired or corrupted.

        Args:
            cart_key: Redis cart key

        Returns:
            Updated cart with rebuilt Shopify cart
        """
        cart = await self.cart_service.get_cart(cart_key)

        try:
            if not await self._ensure_initialized():
                return cart

            lines = []
            for item in cart.items:
                variant_gid = self._to_variant_gid(item.variant_id)
                lines.append({"merchandiseId": variant_gid, "quantity": item.quantity})

            result = await self._shopify_client.create_cart(lines=lines)

            cart.shopify_cart_id = result["cart_id"]
            cart.shopify_cart_url = result["checkout_url"]
            cart.shopify_line_ids = result.get("line_ids", {})
            cart.shopify_sync_error = None

            await self._save_cart(cart_key, cart)

            logger.info(
                "shopify_sync_rebuild_success",
                cart_key=cart_key,
                shopify_cart_id=cart.shopify_cart_id,
                item_count=len(cart.items),
            )

        except Exception as e:
            await self._handle_sync_error(cart_key, cart, f"rebuild_cart: {str(e)}")

        return cart

    async def _get_or_create_shopify_cart(
        self,
        cart: Cart,
    ) -> Optional[Dict[str, Any]]:
        """Get existing Shopify cart or create new one.

        Args:
            cart: Local cart

        Returns:
            Dict with cart_id and checkout_url, or None on failure
        """
        if cart.shopify_cart_id:
            return {
                "cart_id": cart.shopify_cart_id,
                "checkout_url": cart.shopify_cart_url,
            }

        lines = []
        for item in cart.items:
            variant_gid = self._to_variant_gid(item.variant_id)
            lines.append({"merchandiseId": variant_gid, "quantity": item.quantity})

        result = await self._shopify_client.create_cart(lines=lines)

        return {
            "cart_id": result["cart_id"],
            "checkout_url": result["checkout_url"],
            "line_ids": result.get("line_ids", {}),
        }

    async def _save_cart(
        self,
        cart_key: str,
        cart: Cart,
    ) -> None:
        """Save cart to Redis.

        Args:
            cart_key: Redis cart key
            cart: Cart to save
        """
        cart.updated_at = datetime.now(timezone.utc).isoformat()
        cart_dict = cart.model_dump(exclude_none=True, mode="json")
        await self.redis.setex(
            cart_key,
            CartService.CART_TTL_SECONDS,
            json.dumps(cart_dict),
        )

    async def _handle_sync_error(
        self,
        cart_key: str,
        cart: Cart,
        error_message: str,
    ) -> None:
        """Handle sync error with logging and queue for retry.

        Args:
            cart_key: Redis cart key
            cart: Cart that had sync error
            error_message: Error message
        """
        logger.error(
            "shopify_cart_sync_error",
            cart_key=cart_key,
            error=error_message,
            merchant_id=self.merchant_id,
        )

        cart.shopify_sync_error = error_message
        await self._save_cart(cart_key, cart)

        await self._queue_retry(cart_key, error_message)

    async def _queue_retry(
        self,
        cart_key: str,
        error_message: str,
    ) -> None:
        """Queue cart for background retry.

        Args:
            cart_key: Redis cart key
            error_message: Error that caused the retry
        """
        queue_key = f"{SYNC_QUEUE_PREFIX}{cart_key}"
        retry_entry = {
            "cart_key": cart_key,
            "merchant_id": self.merchant_id,
            "error": error_message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "attempts": 1,
        }

        try:
            existing = await self.redis.get(queue_key)
            if existing:
                data = json.loads(existing)
                data["attempts"] += 1
                data["last_error"] = error_message
                if data["attempts"] >= MAX_RETRY_ATTEMPTS:
                    logger.warning(
                        "shopify_sync_max_retries_reached",
                        cart_key=cart_key,
                        attempts=data["attempts"],
                    )
                    await self.redis.delete(queue_key)
                    return
                retry_entry = data

            await self.redis.setex(
                queue_key,
                SYNC_QUEUE_TTL,
                json.dumps(retry_entry),
            )

        except Exception as e:
            logger.error(
                "shopify_sync_queue_retry_failed",
                cart_key=cart_key,
                error=str(e),
            )

    def _to_variant_gid(self, variant_id: str) -> str:
        """Convert variant ID to Shopify GID format.

        Args:
            variant_id: Variant ID (may or may not have gid:// prefix)

        Returns:
            Full Shopify GID
        """
        if variant_id.startswith("gid://"):
            return variant_id
        return f"gid://shopify/ProductVariant/{variant_id}"
