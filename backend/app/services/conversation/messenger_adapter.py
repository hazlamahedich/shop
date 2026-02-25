"""Messenger adapter for UnifiedConversationService.

Story 5-11: Messenger Unified Service Migration
INT-1: Create Messenger adapter for UnifiedConversationService

Provides an adapter layer that:
1. Maps PSID to session_id
2. Uses CartKeyStrategy.for_messenger(psid) for cart operations
3. Converts ConversationResponse to MessengerResponse
4. Integrates with MessengerSendService for carousel/button templates
"""

from __future__ import annotations

from typing import Any, Optional

import structlog

from app.schemas.messaging import MessengerResponse
from app.services.conversation.schemas import (
    Channel,
    ConversationContext,
    ConversationResponse,
)
from app.services.conversation.cart_key_strategy import CartKeyStrategy
from app.services.messenger import MessengerSendService


logger = structlog.get_logger(__name__)


class MessengerAdapter:
    """Adapter for using UnifiedConversationService with Facebook Messenger.

    This adapter bridges the gap between the channel-agnostic
    UnifiedConversationService and the Messenger-specific webhook handler.

    Responsibilities:
    - Convert Facebook webhook payloads to ConversationContext
    - Convert ConversationResponse to MessengerResponse
    - Handle Messenger-specific features (carousels, buttons)
    - Use CartKeyStrategy for cart operations
    """

    def __init__(self) -> None:
        """Initialize Messenger adapter."""
        self.logger = structlog.get_logger(__name__)
        self._send_service: Optional[MessengerSendService] = None

    @property
    def send_service(self) -> MessengerSendService:
        """Get or create MessengerSendService (lazy initialization)."""
        if self._send_service is None:
            self._send_service = MessengerSendService()
        return self._send_service

    def create_context(
        self,
        psid: str,
        merchant_id: int,
        conversation_history: Optional[list[dict[str, Any]]] = None,
        metadata: Optional[dict[str, Any]] = None,
        is_returning_shopper: bool = False,
        consent_status: Optional[str] = None,
    ) -> ConversationContext:
        """Create ConversationContext from Messenger webhook data.

        Args:
            psid: Facebook Page-Scoped ID
            merchant_id: Merchant ID
            conversation_history: Recent conversation messages
            metadata: Additional context metadata
            is_returning_shopper: Whether this is a returning shopper
            consent_status: Current consent status

        Returns:
            ConversationContext configured for Messenger channel
        """
        return ConversationContext(
            session_id=psid,
            merchant_id=merchant_id,
            channel=Channel.MESSENGER,
            conversation_history=conversation_history or [],
            platform_sender_id=psid,
            is_returning_shopper=is_returning_shopper,
            consent_status=consent_status,
            hybrid_mode_enabled=False,
            hybrid_mode_expires_at=None,
            last_activity_at=None,
            metadata=metadata or {},
        )

    def get_cart_key(self, psid: str) -> str:
        """Generate cart key for Messenger using CartKeyStrategy.

        Args:
            psid: Facebook Page-Scoped ID

        Returns:
            Cart key in format: cart:messenger:{psid}
        """
        return CartKeyStrategy.for_messenger(psid)

    async def convert_response(
        self,
        response: ConversationResponse,
        psid: str,
    ) -> MessengerResponse:
        """Convert ConversationResponse to MessengerResponse.

        Args:
            response: Response from UnifiedConversationService
            psid: Facebook Page-Scoped ID

        Returns:
            MessengerResponse ready to send
        """
        if response.products and len(response.products) > 0:
            await self._send_product_carousel(response.products, psid)
            return MessengerResponse(
                text=response.message,
                recipient_id=psid,
            )

        if response.cart and response.cart.get("items"):
            await self._send_cart_template(response.cart, psid)
            return MessengerResponse(
                text=response.message,
                recipient_id=psid,
            )

        if response.checkout_url:
            return MessengerResponse(
                text=f"{response.message}\n\nCheckout: {response.checkout_url}",
                recipient_id=psid,
            )

        return MessengerResponse(
            text=response.message,
            recipient_id=psid,
        )

    async def _send_product_carousel(
        self,
        products: list[dict[str, Any]],
        psid: str,
    ) -> None:
        """Send product carousel to Messenger.

        Args:
            products: List of product dicts
            psid: Facebook Page-Scoped ID
        """
        try:
            from app.services.messenger import MessengerProductFormatter

            formatter = MessengerProductFormatter()
            payload = formatter.format_product_results_from_list(products)

            await self.send_service.send_message(psid, payload)
            await self.send_service.close()

            self.logger.info(
                "messenger_carousel_sent",
                psid=psid,
                product_count=len(products),
            )
        except Exception as e:
            self.logger.warning(
                "messenger_carousel_failed",
                psid=psid,
                error=str(e),
            )

    async def _send_cart_template(
        self,
        cart: dict[str, Any],
        psid: str,
    ) -> None:
        """Send cart template to Messenger.

        Args:
            cart: Cart dict with items
            psid: Facebook Page-Scoped ID
        """
        try:
            from app.services.messenger import CartFormatter
            from app.core.config import settings

            config = settings()
            shop_domain = (
                config.get("STORE_URL", "https://shop.example.com")
                .replace("https://", "")
                .replace("http://", "")
            )
            formatter = CartFormatter(shop_domain=shop_domain)
            payload = formatter.format_cart_from_dict(cart, psid)

            await self.send_service.send_message(psid, payload)
            await self.send_service.close()

            self.logger.info(
                "messenger_cart_sent",
                psid=psid,
                item_count=cart.get("item_count", 0),
            )
        except Exception as e:
            self.logger.warning(
                "messenger_cart_failed",
                psid=psid,
                error=str(e),
            )

    async def send_welcome_back(
        self,
        psid: str,
        item_count: int,
    ) -> None:
        """Send welcome back message for returning shopper.

        Args:
            psid: Facebook Page-Scoped ID
            item_count: Number of items in cart
        """
        message = (
            f"Welcome back! You have {item_count} "
            f"item{'s' if item_count != 1 else ''} in your cart. "
            "Type 'cart' to view."
        )
        try:
            await self.send_service.send_message(psid, {"text": message})
            await self.send_service.close()

            self.logger.info(
                "messenger_welcome_back_sent",
                psid=psid,
                item_count=item_count,
            )
        except Exception as e:
            self.logger.warning(
                "messenger_welcome_back_failed",
                psid=psid,
                error=str(e),
            )

    async def close(self) -> None:
        """Close the send service connection."""
        if self._send_service:
            await self._send_service.close()
            self._send_service = None


__all__ = ["MessengerAdapter"]
