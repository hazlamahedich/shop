"""Cart handler for unified conversation processing.

Story 5-10: Widget Full App Integration
Task 1: Create UnifiedConversationService

Handles CART_VIEW, CART_ADD, CART_REMOVE intents with CartService.
"""

from __future__ import annotations

from typing import Any, Optional

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.merchant import Merchant
from app.services.conversation.schemas import (
    ConversationContext,
    ConversationResponse,
)
from app.services.conversation.handlers.base_handler import BaseHandler
from app.services.llm.base_llm_service import BaseLLMService


logger = structlog.get_logger(__name__)


class CartHandler(BaseHandler):
    """Handler for cart-related intents.

    Manages cart operations using the unified CartKeyStrategy
    for cross-channel cart persistence.
    """

    async def handle(
        self,
        db: AsyncSession,
        merchant: Merchant,
        llm_service: BaseLLMService,
        message: str,
        context: ConversationContext,
        entities: Optional[dict[str, Any]] = None,
    ) -> ConversationResponse:
        """Handle cart intent based on type.

        Args:
            db: Database session
            merchant: Merchant configuration
            llm_service: LLM service for this merchant
            message: User's message
            context: Conversation context
            entities: Extracted entities (product info for add)

        Returns:
            ConversationResponse with cart state
        """
        from app.services.cart.cart_service import CartService
        from app.services.conversation.cart_key_strategy import CartKeyStrategy

        cart_service = CartService()
        cart_key = CartKeyStrategy.get_key_for_context(context)

        intent = entities.get("cart_action", "view") if entities else "view"

        try:
            if intent == "add":
                return await self._handle_add(cart_service, cart_key, entities or {}, merchant)
            elif intent == "remove":
                return await self._handle_remove(cart_service, cart_key, entities or {}, merchant)
            elif intent == "clear":
                return await self._handle_clear(cart_service, cart_key, merchant)
            else:
                return await self._handle_view(cart_service, cart_key, merchant)

        except Exception as e:
            logger.error(
                "cart_handler_failed",
                merchant_id=merchant.id,
                intent=intent,
                error=str(e),
            )
            return ConversationResponse(
                message="I had trouble with your cart. Please try again!",
                intent=f"cart_{intent}",
                confidence=1.0,
                fallback=True,
            )

    async def _handle_view(
        self,
        cart_service: Any,
        cart_key: str,
        merchant: Merchant,
    ) -> ConversationResponse:
        """Handle cart view."""
        cart = await cart_service.get_cart(cart_key)

        if not cart.items:
            return ConversationResponse(
                message="Your cart is empty. Would you like to browse our products?",
                intent="cart_view",
                confidence=1.0,
                cart={"items": [], "subtotal": 0, "currency": "USD"},
            )

        cart_dict = {
            "items": [
                {
                    "title": item.title,
                    "quantity": item.quantity,
                    "price": float(item.price) if item.price else 0,
                }
                for item in cart.items
            ],
            "subtotal": float(cart.subtotal) if cart.subtotal else 0,
            "currency": cart.currency_code.value if cart.currency_code else "USD",
        }

        lines = ["Here's what's in your cart:\n"]
        for item in cart.items:
            lines.append(f"• {item.title} (x{item.quantity}) - ${item.price:.2f}")
        lines.append(f"\nSubtotal: ${cart.subtotal:.2f}")

        return ConversationResponse(
            message="\n".join(lines),
            intent="cart_view",
            confidence=1.0,
            cart=cart_dict,
        )

    async def _handle_add(
        self,
        cart_service: Any,
        cart_key: str,
        entities: dict[str, Any],
        merchant: Merchant,
    ) -> ConversationResponse:
        """Handle add to cart."""
        product_id = entities.get("product_id")
        variant_id = entities.get("variant_id")
        title = entities.get("title", "Product")
        price = entities.get("price", 0)
        quantity = entities.get("quantity", 1)

        if not variant_id:
            return ConversationResponse(
                message="I need to know which product variant to add. Which size or option would you like?",
                intent="cart_add",
                confidence=1.0,
            )

        await cart_service.add_item(
            psid=cart_key,
            variant_id=variant_id,
            title=title,
            price=float(price),
            quantity=int(quantity),
        )

        logger.info(
            "cart_item_added",
            merchant_id=merchant.id,
            variant_id=variant_id,
            title=title,
        )

        return ConversationResponse(
            message=f"Added {title} to your cart! Would you like to continue shopping or checkout?",
            intent="cart_add",
            confidence=1.0,
        )

    async def _handle_remove(
        self,
        cart_service: Any,
        cart_key: str,
        entities: dict[str, Any],
        merchant: Merchant,
    ) -> ConversationResponse:
        """Handle remove from cart."""
        variant_id = entities.get("variant_id")

        if not variant_id:
            return ConversationResponse(
                message="Which item would you like to remove from your cart?",
                intent="cart_remove",
                confidence=1.0,
            )

        await cart_service.remove_item(psid=cart_key, variant_id=variant_id)

        return ConversationResponse(
            message="Item removed from your cart. Anything else I can help with?",
            intent="cart_remove",
            confidence=1.0,
        )

    async def _handle_clear(
        self,
        cart_service: Any,
        cart_key: str,
        merchant: Merchant,
    ) -> ConversationResponse:
        """Handle clear/empty cart."""
        await cart_service.clear_cart(cart_key)

        logger.info(
            "cart_cleared",
            merchant_id=merchant.id,
        )

        return ConversationResponse(
            message="Your cart has been emptied. Would you like to browse our products?",
            intent="cart_clear",
            confidence=1.0,
            cart={"items": [], "subtotal": 0, "currency": "USD"},
        )
