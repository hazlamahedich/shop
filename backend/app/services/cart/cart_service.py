"""Cart service for managing shopping carts in Redis.

Provides CRUD operations for cart items with automatic quantity
increment, validation, and 24-hour TTL.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Optional

import structlog

from app.core.errors import APIError, ErrorCode
from app.core.config import settings
from app.schemas.cart import Cart, CartItem, CurrencyCode


class CartService:
    """Service for managing shopper carts in Redis sessions.

    Cart Operations:
    1. Add item (increment quantity if exists)
    2. Remove item
    3. Update quantity
    4. Get cart (with subtotal calculation)
    5. Clear cart

    Cart Persistence:
    - Redis session key: cart:{psid}
    - TTL: 24 hours (same as conversation context)
    - Stored alongside conversation context
    """

    MAX_QUANTITY = 10  # Maximum quantity per item
    CART_TTL_SECONDS = 24 * 60 * 60  # 24 hours

    def __init__(self, redis_client: Optional[Any] = None) -> None:
        """Initialize cart service.

        Args:
            redis_client: Redis client instance (creates default if not provided)
        """
        if redis_client is None:
            # Create default Redis client
            import redis
            config = settings()
            redis_url = config.get("REDIS_URL", "redis://localhost:6379/0")
            self.redis = redis.from_url(redis_url, decode_responses=True)
        else:
            self.redis = redis_client

        self.logger = structlog.get_logger(__name__)

    def _get_cart_key(self, psid: str) -> str:
        """Generate Redis key for cart.

        Args:
            psid: Facebook Page-Scoped ID

        Returns:
            Redis cart key
        """
        return f"cart:{psid}"

    async def get_cart(self, psid: str) -> Cart:
        """Get cart for shopper.

        Args:
            psid: Facebook Page-Scoped ID

        Returns:
            Cart object (empty if no cart exists)
        """
        cart_key = self._get_cart_key(psid)
        data = None  # Initialize for exception handling

        try:
            data = self.redis.get(cart_key)
            if data:
                cart_dict = json.loads(data)
                return Cart(**cart_dict)
            else:
                # Return empty cart
                return Cart(
                    items=[],
                    subtotal=0.0,
                    currency_code=CurrencyCode.USD
                )

        except json.JSONDecodeError as e:
            self.logger.error(
                "cart_data_corrupted",
                psid=psid,
                error=str(e),
                data_preview=data[:200] if data else None
            )
            raise APIError(
                ErrorCode.CART_DATA_CORRUPTED,
                "Cart data is corrupted. Please try clearing your cart."
            )
        except Exception as e:
            self.logger.error("cart_retrieval_failed", psid=psid, error=str(e))
            raise APIError(
                ErrorCode.CART_RETRIEVAL_FAILED,
                "Failed to retrieve cart"
            )

    async def add_item(
        self,
        psid: str,
        product_id: str,
        variant_id: str,
        title: str,
        price: float,
        image_url: str,
        currency_code: str = "USD",
        quantity: int = 1,
    ) -> Cart:
        """Add item to cart (increment quantity if exists).

        Args:
            psid: Facebook Page-Scoped ID
            product_id: Shopify product ID
            variant_id: Shopify variant ID
            title: Product title
            price: Product price
            image_url: Product image URL
            currency_code: Price currency (default USD)
            quantity: Quantity to add (default 1)

        Returns:
            Updated cart object

        Raises:
            APIError: If add operation fails
        """
        cart_key = self._get_cart_key(psid)

        try:
            # Get existing cart or create new one
            cart = await self.get_cart(psid)

            # Validate currency matches cart (unless cart is empty)
            item_currency = CurrencyCode(currency_code)
            if cart.items and cart.currency_code != item_currency:
                self.logger.warning(
                    "cart_currency_mismatch",
                    psid=psid,
                    cart_currency=cart.currency_code.value,
                    item_currency=item_currency.value
                )
                raise APIError(
                    ErrorCode.CART_CURRENCY_MISMATCH,
                    f"Cannot add {item_currency.value} item to {cart.currency_code.value} cart. "
                    f"Please clear your cart first or add items in the same currency."
                )

            # Check if item already exists
            existing_item: Optional[CartItem] = None
            for item in cart.items:
                if item.variant_id == variant_id:
                    existing_item = item
                    break

            if existing_item:
                # Increment quantity (with max check)
                new_quantity = min(
                    existing_item.quantity + quantity,
                    self.MAX_QUANTITY
                )
                existing_item.quantity = new_quantity

                self.logger.info(
                    "cart_item_incremented",
                    psid=psid,
                    variant_id=variant_id,
                    old_quantity=existing_item.quantity,
                    new_quantity=new_quantity
                )
            else:
                # Add new item
                new_item = CartItem(
                    product_id=product_id,
                    variant_id=variant_id,
                    title=title,
                    price=price,
                    image_url=image_url,
                    currency_code=CurrencyCode(currency_code),
                    quantity=quantity,
                    added_at=datetime.now(timezone.utc).isoformat()
                )
                cart.items.append(new_item)

                self.logger.info(
                    "cart_item_added",
                    psid=psid,
                    variant_id=variant_id,
                    quantity=quantity
                )

            # Update subtotal
            cart.subtotal = sum(item.price * item.quantity for item in cart.items)
            cart.currency_code = CurrencyCode(currency_code)
            cart.updated_at = datetime.now(timezone.utc).isoformat()

            # Set created_at if new cart
            if cart.created_at is None:
                cart.created_at = datetime.now(timezone.utc).isoformat()

            # Save to Redis with TTL
            cart_dict = cart.model_dump(exclude_none=True, mode="json")
            self.redis.setex(
                cart_key,
                self.CART_TTL_SECONDS,
                json.dumps(cart_dict)
            )

            return cart

        except APIError:
            raise
        except Exception as e:
            self.logger.error("cart_add_item_failed", psid=psid, error=str(e))
            raise APIError(
                ErrorCode.CART_ADD_FAILED,
                "Failed to add item to cart"
            )

    async def remove_item(self, psid: str, variant_id: str) -> Cart:
        """Remove item from cart.

        Args:
            psid: Facebook Page-Scoped ID
            variant_id: Variant ID to remove

        Returns:
            Updated cart object
        """
        cart_key = self._get_cart_key(psid)

        try:
            cart = await self.get_cart(psid)

            # Remove item with matching variant_id
            cart.items = [item for item in cart.items if item.variant_id != variant_id]

            # Update subtotal
            cart.subtotal = sum(item.price * item.quantity for item in cart.items)
            cart.updated_at = datetime.now(timezone.utc).isoformat()

            # Save to Redis
            cart_dict = cart.model_dump(exclude_none=True, mode="json")
            self.redis.setex(
                cart_key,
                self.CART_TTL_SECONDS,
                json.dumps(cart_dict)
            )

            self.logger.info("cart_item_removed", psid=psid, variant_id=variant_id)

            return cart

        except Exception as e:
            self.logger.error("cart_remove_item_failed", psid=psid, error=str(e))
            raise APIError(
                ErrorCode.CART_REMOVE_FAILED,
                "Failed to remove item from cart"
            )

    async def update_quantity(
        self,
        psid: str,
        variant_id: str,
        quantity: int,
    ) -> Cart:
        """Update item quantity in cart.

        Args:
            psid: Facebook Page-Scoped ID
            variant_id: Variant ID to update
            quantity: New quantity (1-10)

        Returns:
            Updated cart object

        Raises:
            APIError: If quantity is invalid or item not found
        """
        if not (1 <= quantity <= self.MAX_QUANTITY):
            raise APIError(
                ErrorCode.INVALID_QUANTITY,
                f"Quantity must be between 1 and {self.MAX_QUANTITY}"
            )

        cart_key = self._get_cart_key(psid)

        try:
            cart = await self.get_cart(psid)

            # Find and update item
            found = False
            for item in cart.items:
                if item.variant_id == variant_id:
                    item.quantity = quantity
                    found = True
                    break

            if not found:
                raise APIError(
                    ErrorCode.ITEM_NOT_FOUND,
                    f"Item with variant_id {variant_id} not found in cart"
                )

            # Update subtotal
            cart.subtotal = sum(item.price * item.quantity for item in cart.items)
            cart.updated_at = datetime.now(timezone.utc).isoformat()

            # Save to Redis
            cart_dict = cart.model_dump(exclude_none=True, mode="json")
            self.redis.setex(
                cart_key,
                self.CART_TTL_SECONDS,
                json.dumps(cart_dict)
            )

            self.logger.info(
                "cart_quantity_updated",
                psid=psid,
                variant_id=variant_id,
                quantity=quantity
            )

            return cart

        except APIError:
            raise
        except Exception as e:
            self.logger.error("cart_update_quantity_failed", psid=psid, error=str(e))
            raise APIError(
                ErrorCode.CART_UPDATE_FAILED,
                "Failed to update cart quantity"
            )

    async def clear_cart(self, psid: str) -> None:
        """Clear all items from cart.

        Args:
            psid: Facebook Page-Scoped ID
        """
        cart_key = self._get_cart_key(psid)

        try:
            self.redis.delete(cart_key)
            self.logger.info("cart_cleared", psid=psid)

        except Exception as e:
            self.logger.error("cart_clear_failed", psid=psid, error=str(e))
            raise APIError(
                ErrorCode.CART_CLEAR_FAILED,
                "Failed to clear cart"
            )
