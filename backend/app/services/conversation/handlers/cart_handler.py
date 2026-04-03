"""Cart handler for unified conversation processing.

Story 5-10: Widget Full App Integration
Task 1: Create UnifiedConversationService

Story 5-12: Bot Personality Consistency
Task 2.2: Update CartHandler to use PersonalityAwareResponseFormatter

Handles CART_VIEW, CART_ADD, CART_REMOVE intents with CartService.
Syncs cart changes to Shopify for widget/preview channels.

Enhanced to handle anaphoric references ("add that to cart").
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.merchant import Merchant
from app.services.conversation.handlers.base_handler import BaseHandler
from app.services.conversation.schemas import (
    ConversationContext,
    ConversationResponse,
)
from app.services.llm.base_llm_service import BaseLLMService
from app.services.personality.response_formatter import PersonalityAwareResponseFormatter

logger = structlog.get_logger(__name__)

_MODE = "ecommerce"


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
        entities: dict[str, Any] | None = None,
    ) -> ConversationResponse:
        from app.services.cart.cart_service import CartService
        from app.services.conversation.cart_key_strategy import CartKeyStrategy

        cart_service = CartService()
        cart_key = CartKeyStrategy.get_key_for_context(context)

        intent = entities.get("cart_action", "view") if entities else "view"
        conversation_id = str(context.session_id)

        try:
            if intent == "add":
                return await self._handle_add(
                    cart_service=cart_service,
                    cart_key=cart_key,
                    entities=entities or {},
                    merchant=merchant,
                    context=context,
                    conversation_id=conversation_id,
                )
            elif intent == "remove":
                return await self._handle_remove(cart_service, cart_key, entities or {}, merchant)
            elif intent == "clear":
                return await self._handle_clear(cart_service, cart_key, merchant)
            else:
                return await self._handle_view(
                    cart_service,
                    cart_key,
                    merchant,
                    conversation_id=conversation_id,
                )

        except Exception as e:
            logger.error(
                "cart_handler_failed",
                merchant_id=merchant.id,
                intent=intent,
                error=str(e),
            )
            from app.services.conversation.error_recovery_service import (
                ErrorType,
                NaturalErrorRecoveryService,
            )

            return await NaturalErrorRecoveryService().recover(
                error_type=ErrorType.CART_FAILED,
                merchant=merchant,
                context=context,
                error=e,
                intent=f"cart_{intent}",
                conversation_id=str(context.session_id),
            )

    async def _handle_view(
        self,
        cart_service: Any,
        cart_key: str,
        merchant: Merchant,
        conversation_id: str | None = None,
    ) -> ConversationResponse:
        cart = await cart_service.get_cart(cart_key)

        if not cart.items:
            return ConversationResponse(
                message=PersonalityAwareResponseFormatter.format_response(
                    "cart",
                    "view_empty",
                    merchant.personality,
                    include_transition=True,
                    conversation_id=conversation_id,
                    mode=_MODE,
                ),
                intent="cart_view",
                confidence=1.0,
                cart={"items": [], "subtotal": 0, "currency": "USD"},
            )

        cart_dict = self._cart_to_dict(cart)

        item_lines = []
        for item in cart.items:
            item_lines.append(f"• {item.title} (x{item.quantity}) - ${item.price:.2f}")
        items_str = "\n".join(item_lines)

        message = PersonalityAwareResponseFormatter.format_response(
            "cart",
            "view_items",
            merchant.personality,
            include_transition=True,
            conversation_id=conversation_id,
            mode=_MODE,
            items=items_str,
            subtotal=f"{cart.subtotal:.2f}",
        )

        return ConversationResponse(
            message=message,
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
        context: ConversationContext | None = None,
        conversation_id: str | None = None,
    ) -> ConversationResponse:
        variant_id = entities.get("variant_id")
        title = entities.get("title", "Product")
        price = entities.get("price", 0)
        quantity = entities.get("quantity", 1)
        image_url = entities.get("image_url", "")
        product_reference = entities.get("product_reference")

        if context and context.consent_status == "pending":
            context.pending_consent_product = {
                "variant_id": variant_id,
                "title": title,
                "price": price,
                "quantity": quantity,
                "image_url": image_url,
            }
            return ConversationResponse(
                message=PersonalityAwareResponseFormatter.format_response(
                    "cart",
                    "consent_required",
                    merchant.personality,
                ),
                intent="cart_add",
                confidence=1.0,
                metadata={
                    "consent_required": True,
                    "pending_product": context.pending_consent_product,
                },
            )

        if not variant_id and context and product_reference:
            resolved_product = context.shopping_state.find_product_by_reference(product_reference)
            if resolved_product:
                variant_id = resolved_product.get("variant_id") or resolved_product.get("id")
                title = resolved_product.get("title", title)
                price = resolved_product.get("price", price)
                image_url = resolved_product.get("image_url", image_url)
                logger.info(
                    "cart_anaphoric_reference_resolved",
                    merchant_id=merchant.id,
                    reference=product_reference,
                    resolved_to=title,
                )

        if not variant_id and context:
            last_product = context.shopping_state.get_last_viewed_product()
            if last_product:
                variant_id = last_product.get("variant_id") or last_product.get("id")
                title = last_product.get("title", title)
                price = last_product.get("price", price)
                image_url = last_product.get("image_url", image_url)
                logger.info(
                    "cart_last_viewed_product_used",
                    merchant_id=merchant.id,
                    product_title=title,
                )

        if not variant_id:
            return ConversationResponse(
                message=PersonalityAwareResponseFormatter.format_response(
                    "cart",
                    "add_needs_selection",
                    merchant.personality,
                ),
                intent="cart_add",
                confidence=1.0,
            )

        await cart_service.add_item(
            psid=cart_key,
            product_id=variant_id,
            variant_id=variant_id,
            title=title,
            price=float(price),
            image_url=image_url,
            quantity=int(quantity),
        )

        logger.info(
            "cart_item_added",
            merchant_id=merchant.id,
            variant_id=variant_id,
            title=title,
        )

        cart = await cart_service.get_cart(cart_key)

        cart = await self._sync_add_to_shopify(
            cart_key=cart_key,
            merchant_id=merchant.id,
            variant_id=variant_id,
            title=title,
            price=float(price),
            quantity=int(quantity),
            cart=cart,
        )

        cart_state = self._cart_to_dict(cart)

        await self._track_pinned_cart_add(db, merchant.id, variant_id)

        return ConversationResponse(
            message=PersonalityAwareResponseFormatter.format_response(
                "cart",
                "add_success",
                merchant.personality,
                include_transition=True,
                conversation_id=conversation_id,
                mode=_MODE,
                title=title,
            ),
            intent="cart_add",
            confidence=1.0,
            cart=cart_state,
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
                message=PersonalityAwareResponseFormatter.format_response(
                    "cart",
                    "remove_needs_selection",
                    merchant.personality,
                ),
                intent="cart_remove",
                confidence=1.0,
            )

        await cart_service.remove_item(psid=cart_key, variant_id=variant_id)

        cart = await cart_service.get_cart(cart_key)

        cart = await self._sync_remove_from_shopify(
            cart_key=cart_key,
            merchant_id=merchant.id,
            variant_id=variant_id,
            cart=cart,
        )

        cart_state = self._cart_to_dict(cart)

        return ConversationResponse(
            message=PersonalityAwareResponseFormatter.format_response(
                "cart",
                "remove_success",
                merchant.personality,
            ),
            intent="cart_remove",
            confidence=1.0,
            cart=cart_state,
        )

    async def _handle_clear(
        self,
        cart_service: Any,
        cart_key: str,
        merchant: Merchant,
    ) -> ConversationResponse:
        """Handle clear/empty cart."""
        cart = await cart_service.get_cart(cart_key)

        await self._sync_clear_shopify(
            cart_key=cart_key,
            merchant_id=merchant.id,
            cart=cart,
        )

        await cart_service.clear_cart(cart_key)

        logger.info(
            "cart_cleared",
            merchant_id=merchant.id,
        )

        return ConversationResponse(
            message=PersonalityAwareResponseFormatter.format_response(
                "cart",
                "clear_success",
                merchant.personality,
            ),
            intent="cart_clear",
            confidence=1.0,
            cart={"items": [], "subtotal": 0, "currency": "USD"},
        )

    def _cart_to_dict(self, cart: Any) -> dict:
        """Convert Cart object to dictionary for response."""
        return {
            "items": [
                {
                    "variant_id": item.variant_id,
                    "title": item.title,
                    "quantity": item.quantity,
                    "price": float(item.price) if item.price else 0,
                }
                for item in cart.items
            ],
            "subtotal": float(cart.subtotal) if cart.subtotal else 0,
            "currency": cart.currency_code.value if cart.currency_code else "USD",
            "item_count": sum(item.quantity for item in cart.items),
        }

    async def _sync_add_to_shopify(
        self,
        cart_key: str,
        merchant_id: int,
        variant_id: str,
        title: str,
        price: float,
        quantity: int,
        cart: Any,
    ) -> Any:
        """Sync add item to Shopify cart.

        Args:
            cart_key: Local cart key
            merchant_id: Merchant ID for Shopify integration
            variant_id: Product variant ID
            title: Product title
            price: Product price
            quantity: Quantity to add
            cart: Current local cart state

        Returns:
            Updated cart (with shopify_cart_url if sync succeeded)
        """
        try:
            from app.schemas.cart import CartItem
            from app.services.cart.shopify_cart_sync import ShopifyCartSync

            sync_service = ShopifyCartSync(merchant_id=merchant_id)
            new_item = CartItem(
                product_id=variant_id,
                variant_id=variant_id,
                title=title,
                price=price,
                image_url="",
                quantity=quantity,
                added_at=datetime.now(UTC).isoformat(),
            )
            cart = await sync_service.sync_add_item(cart_key, new_item)
            logger.info(
                "cart_shopify_sync_add_success",
                merchant_id=merchant_id,
                variant_id=variant_id,
            )
        except Exception as e:
            logger.warning(
                "cart_shopify_sync_add_failed",
                merchant_id=merchant_id,
                variant_id=variant_id,
                error=str(e),
            )

        return cart

    async def _sync_remove_from_shopify(
        self,
        cart_key: str,
        merchant_id: int,
        variant_id: str,
        cart: Any,
    ) -> Any:
        """Sync remove item from Shopify cart.

        Args:
            cart_key: Local cart key
            merchant_id: Merchant ID for Shopify integration
            variant_id: Product variant ID to remove
            cart: Current local cart state

        Returns:
            Updated cart
        """
        try:
            from app.services.cart.shopify_cart_sync import ShopifyCartSync

            sync_service = ShopifyCartSync(merchant_id=merchant_id)
            cart = await sync_service.sync_remove_item(cart_key, variant_id)
            logger.info(
                "cart_shopify_sync_remove_success",
                merchant_id=merchant_id,
                variant_id=variant_id,
            )
        except Exception as e:
            logger.warning(
                "cart_shopify_sync_remove_failed",
                merchant_id=merchant_id,
                variant_id=variant_id,
                error=str(e),
            )

        return cart

    async def _sync_clear_shopify(
        self,
        cart_key: str,
        merchant_id: int,
        cart: Any,
    ) -> None:
        """Sync clear cart to Shopify.

        Args:
            cart_key: Local cart key
            merchant_id: Merchant ID for Shopify integration
            cart: Current cart state (must have shopify_cart_id)
        """
        try:
            from app.services.cart.shopify_cart_sync import ShopifyCartSync

            if not cart.shopify_cart_id:
                logger.debug(
                    "cart_shopify_sync_clear_skipped_no_id",
                    merchant_id=merchant_id,
                )
                return

            sync_service = ShopifyCartSync(merchant_id=merchant_id)
            await sync_service.sync_clear_cart(cart_key)
            logger.info(
                "cart_shopify_sync_clear_success",
                merchant_id=merchant_id,
            )
        except Exception as e:
            logger.warning(
                "cart_shopify_sync_clear_failed",
                merchant_id=merchant_id,
                error=str(e),
            )

    async def _track_pinned_cart_add(
        self,
        db: AsyncSession,
        merchant_id: int,
        variant_id: str,
    ) -> None:
        """Track cart addition for pinned product analytics.

        Only tracks if the product is actually pinned.

        Args:
            db: Database session
            merchant_id: Merchant ID
            variant_id: Product variant ID that was added
        """
        try:
            from app.services.product_pin_analytics_service import track_pinned_product_cart_add
            from app.services.product_pin_service import get_pinned_product_ids

            pinned_ids = await get_pinned_product_ids(db, merchant_id)
            pinned_ids_set = {str(pid) for pid in pinned_ids}

            # Check if the variant_id or its product_id is pinned
            # Note: variant_id might be different from product_id, but for simplicity
            # we check if any pinned product matches this variant
            if str(variant_id) in pinned_ids_set:
                await track_pinned_product_cart_add(db, merchant_id, variant_id)
        except Exception as e:
            logger.warning(
                "track_pinned_cart_add_failed",
                merchant_id=merchant_id,
                error=str(e),
            )
