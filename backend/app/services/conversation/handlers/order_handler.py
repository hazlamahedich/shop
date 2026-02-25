"""Order handler for unified conversation processing.

Story 5-10: Widget Full App Integration
Task 1: Create UnifiedConversationService
Story 4-13: Cross-device order lookup with email fallback

Handles ORDER_TRACKING intent with OrderTrackingService.
"""

from __future__ import annotations

import re
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

EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
PENDING_CROSS_DEVICE_KEY = "pending_cross_device_lookup"


class OrderHandler(BaseHandler):
    """Handler for ORDER_TRACKING intent.

    Looks up orders by customer ID or order number,
    filtering out test orders (is_test=False).

    Story 4-13: Cross-device lookup with email/order number fallback.
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
        """Handle order tracking intent.

        Args:
            db: Database session
            merchant: Merchant configuration
            llm_service: LLM service for this merchant
            message: User's message
            context: Conversation context
            entities: Extracted entities (order_number if provided)

        Returns:
            ConversationResponse with order status
        """
        from app.services.order_tracking.order_tracking_service import OrderTrackingService
        from app.services.customer_lookup_service import CustomerLookupService

        tracking_service = OrderTrackingService()
        customer_service = CustomerLookupService()

        order_number = None
        if entities:
            order_number = entities.get("order_number")

        conversation_data = context.conversation_data or {}
        pending_lookup = conversation_data.get(PENDING_CROSS_DEVICE_KEY)

        if pending_lookup and not order_number:
            email_match = EMAIL_PATTERN.match(message.strip())
            if email_match:
                return await self._handle_cross_device_email_lookup(
                    db=db,
                    merchant=merchant,
                    customer_service=customer_service,
                    tracking_service=tracking_service,
                    email=message.strip(),
                    context=context,
                )

            if self._looks_like_order_number(message):
                order_number = message.strip()

        if order_number:
            result = await tracking_service.track_order_by_number(
                db=db,
                merchant_id=merchant.id,
                order_number=order_number,
            )
        else:
            platform_sender_id = context.platform_sender_id or context.session_id
            result = await tracking_service.track_order_by_customer(
                db=db,
                merchant_id=merchant.id,
                platform_sender_id=platform_sender_id,
            )

        if not result.found or not result.order:
            return await self._handle_order_not_found(
                db=db,
                merchant=merchant,
                tracking_service=tracking_service,
                customer_service=customer_service,
                result=result,
                order_number=order_number,
                context=context,
            )

        order = result.order
        response_text = tracking_service.format_order_response(order)

        order_dict = {
            "order_number": order.order_number,
            "status": order.status,
            "tracking_number": order.tracking_number,
            "tracking_url": order.tracking_url,
        }

        logger.info(
            "order_tracking_success",
            merchant_id=merchant.id,
            order_number=order.order_number,
            lookup_type=result.lookup_type.value if result.lookup_type else "unknown",
        )

        return ConversationResponse(
            message=response_text,
            intent="order_tracking",
            confidence=1.0,
            order=order_dict,
        )

    async def _handle_cross_device_email_lookup(
        self,
        db: AsyncSession,
        merchant: Merchant,
        customer_service: CustomerLookupService,
        tracking_service,
        email: str,
        context: ConversationContext,
    ) -> ConversationResponse:
        """Handle cross-device lookup by email.

        Story 4-13: Smart cross-device order lookup flow.

        Args:
            db: Database session
            merchant: Merchant configuration
            customer_service: Customer lookup service
            tracking_service: Order tracking service
            email: Customer email to lookup
            context: Conversation context

        Returns:
            ConversationResponse with order status or error
        """
        profile = await customer_service.find_by_email(
            db=db,
            merchant_id=merchant.id,
            email=email,
        )

        if not profile:
            return ConversationResponse(
                message=f"I couldn't find any orders for {email}. Please check the email or provide your order number.",
                intent="order_tracking",
                confidence=1.0,
            )

        orders = await customer_service.get_customer_orders(
            db=db,
            customer_profile_id=profile.id,
            limit=1,
        )

        if not orders:
            return ConversationResponse(
                message=f"I found your account, {profile.first_name or 'there'}! But no orders yet. Would you like to browse our products?",
                intent="order_tracking",
                confidence=1.0,
            )

        order = orders[0]
        response_text = tracking_service.format_order_response(order)

        greeting = customer_service.get_personalized_greeting(profile)
        device_link_message = f"\n\n🎉 {greeting} This device is now linked to your account!"

        conversation_data = context.conversation_data or {}
        updated_data = await customer_service.link_device_to_profile(
            db=db,
            profile=profile,
            platform_sender_id=context.platform_sender_id or context.session_id,
            conversation_data=conversation_data,
        )

        logger.info(
            "cross_device_lookup_success",
            merchant_id=merchant.id,
            email=email,
            profile_id=profile.id,
            order_number=order.order_number,
        )

        order_dict = {
            "order_number": order.order_number,
            "status": order.status,
            "tracking_number": order.tracking_number,
            "tracking_url": order.tracking_url,
        }

        return ConversationResponse(
            message=response_text + device_link_message,
            intent="order_tracking",
            confidence=1.0,
            order=order_dict,
            conversation_data_update=updated_data,
        )

    async def _handle_order_not_found(
        self,
        db: AsyncSession,
        merchant: Merchant,
        tracking_service,
        customer_service: CustomerLookupService,
        result,
        order_number: Optional[str],
        context: ConversationContext,
    ) -> ConversationResponse:
        """Handle order not found with cross-device fallback prompt.

        Story 4-13: Prompt for email or order number.

        Args:
            db: Database session
            merchant: Merchant configuration
            tracking_service: Order tracking service
            customer_service: Customer lookup service
            result: Order tracking result
            order_number: Order number if provided
            context: Conversation context

        Returns:
            ConversationResponse with prompt for email/order number
        """
        response_text = tracking_service.format_order_not_found_response(
            lookup_type=result.lookup_type,
            order_number=order_number,
        )

        cross_device_prompt = (
            "\n\n😊 I can look it up! What's easier:\n"
            "• Your order number (from confirmation email)\n"
            "• Or your email address"
        )

        conversation_data = context.conversation_data or {}
        conversation_data[PENDING_CROSS_DEVICE_KEY] = True

        return ConversationResponse(
            message=response_text + cross_device_prompt,
            intent="order_tracking",
            confidence=1.0,
            conversation_data_update=conversation_data,
        )

    def _looks_like_order_number(self, message: str) -> bool:
        """Check if message looks like an order number.

        Args:
            message: User message

        Returns:
            True if message looks like an order number
        """
        cleaned = message.strip().lstrip("#")
        if len(cleaned) < 4 or len(cleaned) > 20:
            return False
        return bool(re.match(r"^[A-Za-z0-9\-]+$", cleaned))
