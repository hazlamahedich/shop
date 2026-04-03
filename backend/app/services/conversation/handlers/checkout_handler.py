"""Checkout handler for unified conversation processing.

Story 5-10: Widget Full App Integration
Task 1: Create UnifiedConversationService
Task 15: Circuit Breaker for Shopify

Story 5-12: Bot Personality Consistency
Task 2.3: Update CheckoutHandler to use PersonalityAwareResponseFormatter

Handles CHECKOUT intent with Shopify checkout URL generation.
Implements circuit breaker for resilience.
"""

from __future__ import annotations

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
from app.services.shopify.circuit_breaker import (
    CircuitOpenError,
    ShopifyCircuitBreaker,
)

logger = structlog.get_logger(__name__)


_MODE = "ecommerce"


class CheckoutHandler(BaseHandler):
    """Handler for CHECKOUT intent.

    Generates Shopify checkout URLs from cart contents.
    Implements graceful degradation for failures.
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
        """Handle checkout intent.

        Args:
            db: Database session
            merchant: Merchant configuration
            llm_service: LLM service for this merchant
            message: User's message
            context: Conversation context
            entities: Extracted entities (not used for checkout)

        Returns:
            ConversationResponse with checkout URL or fallback
        """
        from app.services.cart.cart_service import CartService
        from app.services.conversation.cart_key_strategy import CartKeyStrategy

        cart_service = CartService()
        cart_key = CartKeyStrategy.get_key_for_context(context)

        cart = await cart_service.get_cart(cart_key)

        if not cart.items:
            return ConversationResponse(
                message=PersonalityAwareResponseFormatter.format_response(
                    "checkout",
                    "empty_cart",
                    merchant.personality,
                ),
                intent="checkout",
                confidence=1.0,
                metadata={"error": "cart_empty"},
            )

        try:
            checkout_url = await ShopifyCircuitBreaker.execute(
                merchant.id,
                self._create_shopify_checkout,
                db,
                merchant,
                cart,
            )

            logger.info(
                "checkout_url_generated",
                merchant_id=merchant.id,
                item_count=len(cart.items),
            )

            return ConversationResponse(
                message=PersonalityAwareResponseFormatter.format_response(
                    "checkout",
                    "ready",
                    merchant.personality,
                    include_transition=True,
                    conversation_id=str(context.session_id),
                    mode=_MODE,
                    checkout_url=checkout_url,
                ),
                intent="checkout",
                confidence=1.0,
                checkout_url=checkout_url,
            )

        except CircuitOpenError as e:
            logger.warning(
                "checkout_circuit_open",
                merchant_id=merchant.id,
                retry_after=e.retry_after,
            )
            from app.services.conversation.error_recovery_service import (
                ErrorType,
                NaturalErrorRecoveryService,
            )

            return await NaturalErrorRecoveryService().recover(
                error_type=ErrorType.CHECKOUT_FAILED,
                merchant=merchant,
                context=context,
                error=e,
                intent="checkout",
                conversation_id=str(context.session_id),
            )

        except Exception as e:
            logger.warning(
                "checkout_degraded",
                merchant_id=merchant.id,
                error=str(e),
            )
            from app.services.conversation.error_recovery_service import (
                ErrorType,
                NaturalErrorRecoveryService,
            )

            return await NaturalErrorRecoveryService().recover(
                error_type=ErrorType.CHECKOUT_FAILED,
                merchant=merchant,
                context=context,
                error=e,
                intent="checkout",
                conversation_id=str(context.session_id),
            )

    async def _create_shopify_checkout(
        self,
        db: AsyncSession,
        merchant: Merchant,
        cart: Any,
    ) -> str:
        """Create Shopify checkout URL from cart.

        Args:
            db: Database session
            merchant: Merchant configuration
            cart: Cart with items

        Returns:
            Shopify checkout URL
        """
        from sqlalchemy import select

        from app.models.shopify_integration import ShopifyIntegration

        result = await db.execute(
            select(ShopifyIntegration).where(ShopifyIntegration.merchant_id == merchant.id)
        )
        integration = result.scalars().first()

        if not integration or integration.status != "active":
            raise ValueError("No active Shopify integration")

        shop_domain = integration.shop_domain
        if not shop_domain:
            raise ValueError("No shop domain configured")

        line_items = []
        for item in cart.items:
            line_items.append(
                {
                    "variant_id": item.variant_id,
                    "quantity": item.quantity,
                }
            )

        checkout_url = f"https://{shop_domain}/cart/"

        variant_ids = []
        for item in cart.items:
            if item.variant_id:
                variant_ids.append(f"{item.variant_id}:{item.quantity}")

        if variant_ids:
            checkout_url += ",".join(variant_ids)

        return checkout_url
