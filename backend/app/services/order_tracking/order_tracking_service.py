"""Order Tracking Service (Story 4-1).

Provides order lookup and response formatting for customer order tracking queries.
Orders can be looked up by customer ID (platform_sender_id) or order number.

Usage:
    service = OrderTrackingService()

    # Lookup by customer
    result = await service.track_order_by_customer(db, merchant_id, psid)
    if result.order:
        response = service.format_order_response(result.order)

    # Lookup by order number
    result = await service.track_order_by_number(db, merchant_id, "ORD-12345")
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ErrorCode
from app.models.order import Order, OrderStatus

logger = structlog.get_logger(__name__)


PENDING_STATE_KEY = "order_tracking_pending"
PENDING_STATE_TIMESTAMP_KEY = "order_tracking_requested_at"
PENDING_STATE_TIMEOUT_SECONDS = 300


class OrderLookupType(str, Enum):
    """Type of order lookup performed."""

    BY_CUSTOMER = "by_customer"
    BY_ORDER_NUMBER = "by_order_number"


@dataclass
class OrderTrackingResult:
    """Result of an order tracking lookup."""

    order: Optional[Order] = None
    found: bool = False
    lookup_type: Optional[OrderLookupType] = None
    error_code: Optional[ErrorCode] = None
    error_message: Optional[str] = None


RESPONSE_TEMPLATES: dict[str, str] = {
    OrderStatus.PENDING.value: (
        "📦 Order #{order_number}\n"
        "Status: Pending\n"
        "Your order has been received and will be processed soon.\n\n"
        "Need help? Just ask!"
    ),
    OrderStatus.CONFIRMED.value: (
        "📦 Order #{order_number}\n"
        "Status: Confirmed\n"
        "Your order is confirmed and being prepared.\n\n"
        "Need help? Just ask!"
    ),
    OrderStatus.PROCESSING.value: (
        "📦 Order #{order_number}\n"
        "Status: Processing\n"
        "Your order is being prepared for shipment.\n\n"
        "Need help? Just ask!"
    ),
    OrderStatus.SHIPPED.value: (
        "📦 Order #{order_number}\n"
        "Status: Shipped 🚚\n"
        "{tracking_info}"
        "Estimated delivery: {estimated_delivery}\n\n"
        "Need help? Just ask!"
    ),
    OrderStatus.DELIVERED.value: (
        "📦 Order #{order_number}\n"
        "Status: Delivered ✅\n"
        "Your order was delivered.\n\n"
        "Need help? Just ask!"
    ),
    OrderStatus.CANCELLED.value: (
        "📦 Order #{order_number}\n"
        "Status: Cancelled\n"
        "This order has been cancelled.\n\n"
        "Need help? Just ask!"
    ),
    OrderStatus.REFUNDED.value: (
        "📦 Order #{order_number}\n"
        "Status: Refunded\n"
        "Your refund has been processed.\n\n"
        "Need help? Just ask!"
    ),
}

ORDER_NOT_FOUND_CUSTOMER = (
    "I couldn't find any orders linked to your account. "
    "What's your order number? You can find it in your confirmation email."
)

ORDER_NOT_FOUND_NUMBER = (
    "I couldn't find order #{order_number}. Please double-check the number and try again."
)


class OrderTrackingService:
    """Service for tracking customer orders.

    Provides order lookup by customer ID or order number, with formatted
    responses suitable for Messenger delivery.

    Story 4-2 will add Shopify webhook integration to populate orders.
    """

    def __init__(self) -> None:
        """Initialize the order tracking service."""
        pass

    async def track_order_by_customer(
        self,
        db: AsyncSession,
        merchant_id: int,
        platform_sender_id: str,
    ) -> OrderTrackingResult:
        """Track the most recent order for a customer.

        Args:
            db: Database session
            merchant_id: Merchant ID to scope the search
            platform_sender_id: Customer's platform sender ID (Facebook PSID)

        Returns:
            OrderTrackingResult with order if found, or error details
        """
        start_time = datetime.now(timezone.utc)

        try:
            stmt = (
                select(Order)
                .where(Order.merchant_id == merchant_id)
                .where(Order.platform_sender_id == platform_sender_id)
                .order_by(Order.created_at.desc())
                .limit(1)
            )

            result = await db.execute(stmt)
            order = result.scalars().first()

            response_time_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000

            if order:
                logger.info(
                    "order_tracking_lookup",
                    merchant_id=merchant_id,
                    platform_sender_id=platform_sender_id,
                    order_id=order.id,
                    order_number=order.order_number,
                    found=True,
                    lookup_type=OrderLookupType.BY_CUSTOMER.value,
                    response_time_ms=round(response_time_ms, 2),
                )
                return OrderTrackingResult(
                    order=order,
                    found=True,
                    lookup_type=OrderLookupType.BY_CUSTOMER,
                )

            logger.info(
                "order_tracking_lookup",
                merchant_id=merchant_id,
                platform_sender_id=platform_sender_id,
                found=False,
                lookup_type=OrderLookupType.BY_CUSTOMER.value,
                response_time_ms=round(response_time_ms, 2),
            )
            return OrderTrackingResult(
                found=False,
                lookup_type=OrderLookupType.BY_CUSTOMER,
            )

        except Exception as e:
            logger.error(
                "order_tracking_lookup_failed",
                merchant_id=merchant_id,
                platform_sender_id=platform_sender_id,
                error=str(e),
            )
            return OrderTrackingResult(
                found=False,
                lookup_type=OrderLookupType.BY_CUSTOMER,
                error_code=ErrorCode.ORDER_LOOKUP_FAILED,
                error_message="Failed to lookup order by customer",
            )

    async def track_order_by_number(
        self,
        db: AsyncSession,
        merchant_id: int,
        order_number: str,
    ) -> OrderTrackingResult:
        """Track an order by its order number.

        Args:
            db: Database session
            merchant_id: Merchant ID to scope the search
            order_number: Human-readable order number (e.g., "ORD-12345")

        Returns:
            OrderTrackingResult with order if found, or error details
        """
        start_time = datetime.now(timezone.utc)

        sanitized_order_number = self._sanitize_order_number(order_number)

        try:
            stmt = (
                select(Order)
                .where(Order.merchant_id == merchant_id)
                .where(Order.order_number == sanitized_order_number)
                .limit(1)
            )

            result = await db.execute(stmt)
            order = result.scalars().first()

            response_time_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000

            if order:
                logger.info(
                    "order_tracking_lookup",
                    merchant_id=merchant_id,
                    order_number=sanitized_order_number,
                    order_id=order.id,
                    found=True,
                    lookup_type=OrderLookupType.BY_ORDER_NUMBER.value,
                    response_time_ms=round(response_time_ms, 2),
                )
                return OrderTrackingResult(
                    order=order,
                    found=True,
                    lookup_type=OrderLookupType.BY_ORDER_NUMBER,
                )

            logger.info(
                "order_tracking_lookup",
                merchant_id=merchant_id,
                order_number=sanitized_order_number,
                found=False,
                lookup_type=OrderLookupType.BY_ORDER_NUMBER.value,
                response_time_ms=round(response_time_ms, 2),
            )
            return OrderTrackingResult(
                found=False,
                lookup_type=OrderLookupType.BY_ORDER_NUMBER,
            )

        except Exception as e:
            logger.error(
                "order_tracking_lookup_failed",
                merchant_id=merchant_id,
                order_number=sanitized_order_number,
                error=str(e),
            )
            return OrderTrackingResult(
                found=False,
                lookup_type=OrderLookupType.BY_ORDER_NUMBER,
                error_code=ErrorCode.ORDER_LOOKUP_FAILED,
                error_message="Failed to lookup order by number",
            )

    def format_order_response(self, order: Order) -> str:
        """Format an order for Messenger response.

        Args:
            order: Order to format

        Returns:
            Formatted message string for Messenger
        """
        template = RESPONSE_TEMPLATES.get(
            order.status,
            RESPONSE_TEMPLATES[OrderStatus.PENDING.value],
        )

        tracking_info = ""
        if order.tracking_url:
            tracking_info = f"Track it here: {order.tracking_url}\n"
        elif order.tracking_number:
            tracking_info = f"Tracking #: {order.tracking_number}\n"

        estimated_delivery = "Not available"
        if order.estimated_delivery:
            estimated_delivery = order.estimated_delivery.strftime("%B %d, %Y")

        return template.format(
            order_number=order.order_number,
            tracking_info=tracking_info,
            estimated_delivery=estimated_delivery,
        )

    def format_order_not_found_response(
        self,
        lookup_type: OrderLookupType,
        order_number: Optional[str] = None,
    ) -> str:
        """Format a 'not found' response.

        Args:
            lookup_type: Type of lookup that was attempted
            order_number: Order number if lookup was by number

        Returns:
            Formatted message string asking for order number or suggesting retry
        """
        if lookup_type == OrderLookupType.BY_CUSTOMER:
            return ORDER_NOT_FOUND_CUSTOMER

        if order_number:
            return ORDER_NOT_FOUND_NUMBER.format(order_number=order_number)

        return ORDER_NOT_FOUND_CUSTOMER

    def get_pending_state(self, conversation_data: Optional[dict]) -> bool:
        """Check if conversation has a pending order number request state.

        Args:
            conversation_data: Conversation's conversation_data JSONB field

        Returns:
            True if pending state is active and not expired
        """
        if not conversation_data:
            return False

        pending = conversation_data.get(PENDING_STATE_KEY, False)
        if not pending:
            return False

        requested_at_str = conversation_data.get(PENDING_STATE_TIMESTAMP_KEY)
        if not requested_at_str:
            return False

        try:
            requested_at = datetime.fromisoformat(requested_at_str.replace("Z", "+00:00"))
            elapsed = (datetime.now(timezone.utc) - requested_at).total_seconds()
            return elapsed < PENDING_STATE_TIMEOUT_SECONDS
        except (ValueError, TypeError):
            return False

    def set_pending_state(self, conversation_data: Optional[dict]) -> dict:
        """Set the pending order number request state.

        Args:
            conversation_data: Current conversation_data (can be None)

        Returns:
            Updated conversation_data with pending state set
        """
        data = conversation_data.copy() if conversation_data else {}
        data[PENDING_STATE_KEY] = True
        data[PENDING_STATE_TIMESTAMP_KEY] = datetime.now(timezone.utc).isoformat()
        return data

    def clear_pending_state(self, conversation_data: Optional[dict]) -> dict:
        """Clear the pending order number request state.

        Args:
            conversation_data: Current conversation_data (can be None)

        Returns:
            Updated conversation_data with pending state cleared
        """
        data = conversation_data.copy() if conversation_data else {}
        data.pop(PENDING_STATE_KEY, None)
        data.pop(PENDING_STATE_TIMESTAMP_KEY, None)
        return data

    def _sanitize_order_number(self, order_number: str) -> str:
        """Sanitize order number input.

        Args:
            order_number: Raw order number input

        Returns:
            Sanitized order number (trimmed, max 50 chars)
        """
        sanitized = order_number.strip()
        return sanitized[:50]
