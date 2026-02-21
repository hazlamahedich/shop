"""Order handler for unified conversation processing.

Story 5-10: Widget Full App Integration
Task 1: Create UnifiedConversationService

Handles ORDER_TRACKING intent with OrderTrackingService.
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


class OrderHandler(BaseHandler):
    """Handler for ORDER_TRACKING intent.

    Looks up orders by customer ID or order number,
    filtering out test orders (is_test=False).
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

        tracking_service = OrderTrackingService()

        order_number = None
        if entities:
            order_number = entities.get("order_number")

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
            response_text = tracking_service.format_order_not_found_response(
                lookup_type=result.lookup_type,
                order_number=order_number,
            )
            return ConversationResponse(
                message=response_text,
                intent="order_tracking",
                confidence=1.0,
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
