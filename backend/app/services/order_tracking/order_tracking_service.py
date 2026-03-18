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
from datetime import UTC, datetime, timedelta
from enum import Enum

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ErrorCode
from app.models.order import Order, OrderStatus

logger = structlog.get_logger(__name__)


PENDING_STATE_KEY = "order_tracking_pending"
PENDING_STATE_TIMESTAMP_KEY = "order_tracking_requested_at"
PENDING_STATE_TIMEOUT_SECONDS = 300


ESTIMATED_DELIVERY_DAYS = {
    OrderStatus.PENDING.value: 7,
    OrderStatus.PROCESSING.value: 5,
    OrderStatus.SHIPPED.value: 3,
    OrderStatus.DELIVERED.value: 0,
    OrderStatus.CANCELLED.value: 0,
    OrderStatus.REFUNDED.value: 0,
}


class OrderLookupType(str, Enum):
    """Type of order lookup performed."""

    BY_CUSTOMER = "by_customer"
    BY_ORDER_NUMBER = "by_order_number"


@dataclass
class OrderTrackingResult:
    """Result of an order tracking lookup."""

    order: Order | None = None
    orders: list[Order] = None  # type: ignore[assignment]  # all orders found by customer lookup
    found: bool = False
    lookup_type: OrderLookupType | None = None
    error_code: ErrorCode | None = None
    error_message: str | None = None

    def __post_init__(self) -> None:
        if self.orders is None:
            self.orders = []


RESPONSE_TEMPLATES: dict[str, str] = {
    OrderStatus.PENDING.value: """📦 Order #{order_number}
Status: Pending
We're processing your order and will notify you when it ships.
{fulfillment_status}
{product_details}
{payment_breakdown}
Need help? Just ask!
""",
    OrderStatus.PROCESSING.value: """📦 Order #{order_number}
Status: Processing
{fulfillment_status}
{tracking_info}
Estimated Delivery: {estimated_delivery}
{product_details}
{payment_breakdown}
Need help? Just ask!
""",
    OrderStatus.SHIPPED.value: """📦 Order #{order_number}
Status: Shipped
{fulfillment_status}
{tracking_info}
Estimated Delivery: {estimated_delivery}
{product_details}
{payment_breakdown}
""",
    OrderStatus.DELIVERED.value: """📦 Order #{order_number}
Status: Delivered
{fulfillment_status}
{tracking_info}
{product_details}
{payment_breakdown}
Enjoy! 🎉
""",
    OrderStatus.CANCELLED.value: """📦 Order #{order_number}
Status: Cancelled
Your order has been cancelled.
Reason: {cancel_reason}

{product_details}
{payment_breakdown}
Need help? Just ask!
""",
    OrderStatus.REFUNDED.value: """📦 Order #{order_number}
Status: Refunded
Your refund has been processed.
{payment_breakdown}
Need help? Just ask!
""",
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
        limit: int = 5,
        customer_email: str | None = None,
    ) -> OrderTrackingResult:
        """Track recent orders for a customer (up to `limit`).

        Returns all recent non-test orders so the bot can display all of
        them when a customer asks about their order status.

        Args:
            db: Database session
            merchant_id: Merchant ID to scope the search
            platform_sender_id: Customer's platform sender ID (Facebook PSID)
            limit: Maximum number of recent orders to return (default 5)

        Returns:
            OrderTrackingResult with orders list if found, or error details.
            `order` is set to the most recent order for backward compatibility.
        """
        start_time = datetime.now(UTC)

        try:
            stmt = (
                select(Order)
                .where(Order.merchant_id == merchant_id)
                .where(Order.platform_sender_id == platform_sender_id)
                .where(Order.is_test == False)
                .order_by(Order.created_at.desc())
                .limit(limit)
            )

            result = await db.execute(stmt)
            orders = list(result.scalars().all())

            # Fallback to customer email if no orders found by PSID
            if not orders and customer_email:
                email_stmt = (
                    select(Order)
                    .where(Order.merchant_id == merchant_id)
                    .where(Order.customer_email == customer_email)
                    .where(Order.is_test == False)
                    .order_by(Order.created_at.desc())
                    .limit(limit)
                )
                email_result = await db.execute(email_stmt)
                orders = list(email_result.scalars().all())

            response_time_ms = (datetime.now(UTC) - start_time).total_seconds() * 1000

            if orders:
                logger.info(
                    "order_tracking_lookup",
                    merchant_id=merchant_id,
                    platform_sender_id=platform_sender_id,
                    order_count=len(orders),
                    order_numbers=[o.order_number for o in orders],
                    found=True,
                    lookup_type=OrderLookupType.BY_CUSTOMER.value,
                    response_time_ms=round(response_time_ms, 2),
                )
                return OrderTrackingResult(
                    order=orders[0],  # most recent, for backward compat
                    orders=orders,
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
        start_time = datetime.now(UTC)

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

            response_time_ms = (datetime.now(UTC) - start_time).total_seconds() * 1000

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

    def format_order_response(
        self, order: Order, product_images: dict[str, str] | None = None
    ) -> str:
        """Format an order for Messenger response.

        Story 4-13: Added payment breakdown to response.
        Story 5-13: Enhanced with product details and images.
        Bug fix: Added fulfillment_status display from Shopify webhook data.

        Args:
            order: Order to format
            product_images: Dictionary mapping product ID to image URL

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

        estimated_delivery_date = self.calculate_estimated_delivery(order)
        estimated_delivery = "Not available"
        if estimated_delivery_date:
            estimated_delivery = estimated_delivery_date.strftime("%B %d, %Y")

        product_details = self._format_product_details(order, product_images or {})

        payment_breakdown = self._format_payment_breakdown(order)

        fulfillment_status = self._format_fulfillment_status(order)

        # CANCELLED and REFUNDED templates don't include fulfillment_status placeholder
        if order.status in (OrderStatus.CANCELLED.value, OrderStatus.REFUNDED.value):
            formatted = template.format(
                order_number=order.order_number,
                tracking_info=tracking_info,
                estimated_delivery=estimated_delivery,
                product_details=product_details,
                payment_breakdown=payment_breakdown,
                cancel_reason=getattr(order, "cancel_reason", "") or "",
            )
        else:
            formatted = template.format(
                order_number=order.order_number,
                tracking_info=tracking_info,
                estimated_delivery=estimated_delivery,
                product_details=product_details,
                payment_breakdown=payment_breakdown,
                fulfillment_status=fulfillment_status,
            )
        return formatted

    def _format_product_details(self, order: Order, product_images: dict[str, str] = None) -> str:
        """Format product details with images for order response.

        Story 5-13: Product details with images.

        Args:
            order: Order to format products for
            product_images: Dictionary mapping product ID to image URL

        Returns:
            Formatted product details string with images
        """
        if not order.items:
            return ""

        product_images = product_images or {}
        lines = ["\n📦 Order Items:"]

        for idx, item in enumerate(order.items, 1):
            title = item.get("title", "Unknown Product")
            quantity = item.get("quantity", 1)
            price = item.get("price", "0.00")
            product_id = str(item.get("product_id") or item.get("id", ""))

            try:
                price_float = float(price)
                formatted_price = f"${price_float:.2f}"
            except (ValueError, TypeError):
                formatted_price = f"${price}"

            lines.append(f"\n{idx}. {title}")
            lines.append(f"   Quantity: {quantity}")
            lines.append(f"   Price: {formatted_price}")

            if product_id and product_id in product_images:
                lines.append(f"   📷 Image: {product_images[product_id]}")

        return "\n".join(lines)

    def _format_payment_breakdown(self, order: Order) -> str:
        """Format payment breakdown for order response.

        Story 4-13: Payment breakdown display.

        Args:
            order: Order to format payment for

        Returns:
            Formatted payment breakdown string
        """
        lines = ["\n💰 Payment Summary:"]

        if order.subtotal:
            lines.append(f"Items: ${order.subtotal:.2f}")

        if order.total_shipping:
            lines.append(f"Shipping: ${order.total_shipping:.2f}")

        if order.total_tax:
            lines.append(f"Tax: ${order.total_tax:.2f}")

        if order.total_discount and order.total_discount > 0:
            lines.append(f"Discount: -${order.total_discount:.2f}")

        lines.append("─────────")
        lines.append(f"Total: ${order.total:.2f}")

        if order.payment_method:
            lines.append(f"Paid via: {order.payment_method}")

        return "\n".join(lines)

    def _format_fulfillment_status(self, order: Order) -> str:
        """Format Shopify fulfillment status for order response.

        Bug fix: Surface fulfillment_status from Shopify webhook data
        so the bot can tell customers when their order has been fulfilled.

        Shopify fulfillment_status values:
            None / null  - not yet fulfilled (show nothing extra)
            "fulfilled"  - all items fulfilled
            "partial"    - some items fulfilled
            "restocked"  - items restocked (after cancellation)

        Args:
            order: Order to format fulfillment status for

        Returns:
            Formatted fulfillment status line, or empty string if not set
        """
        fulfillment = getattr(order, "fulfillment_status", None)
        if not fulfillment:
            return ""

        fulfillment_lower = fulfillment.lower()
        if fulfillment_lower == "fulfilled":
            return "✅ Fulfillment: Fulfilled\n"
        elif fulfillment_lower == "partial":
            return "⚡ Fulfillment: Partially Fulfilled\n"
        elif fulfillment_lower == "restocked":
            return "🔄 Fulfillment: Restocked\n"
        else:
            return f"Fulfillment: {fulfillment}\n"

    def format_order_not_found_response(
        self,
        lookup_type: OrderLookupType,
        order_number: str | None = None,
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

    def get_pending_state(self, conversation_data: dict | None) -> bool:
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
            elapsed = (datetime.now(UTC) - requested_at).total_seconds()
            return elapsed < PENDING_STATE_TIMEOUT_SECONDS
        except (ValueError, TypeError):
            return False

    def set_pending_state(self, conversation_data: dict | None) -> dict:
        """Set the pending order number request state.

        Args:
            conversation_data: Current conversation_data (can be None)

        Returns:
            Updated conversation_data with pending state set
        """
        data = conversation_data.copy() if conversation_data else {}
        data[PENDING_STATE_KEY] = True
        data[PENDING_STATE_TIMESTAMP_KEY] = datetime.now(UTC).isoformat()
        return data

    def clear_pending_state(self, conversation_data: dict | None) -> dict:
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

    def calculate_estimated_delivery(self, order: Order) -> datetime | None:
        """Calculate estimated delivery date based on order status.

        Story 5-13: Estimated delivery calculation.

        Args:
            order: Order to calculate delivery for

        Returns:
            Estimated delivery date or None if already delivered/cancelled
        """
        if order.status in (
            OrderStatus.DELIVERED.value,
            OrderStatus.CANCELLED.value,
            OrderStatus.REFUNDED.value,
        ):
            return None

        effective_status = order.status
        if order.fulfillment_status == "fulfilled":
            if effective_status not in (
                OrderStatus.DELIVERED.value,
                OrderStatus.CANCELLED.value,
                OrderStatus.REFUNDED.value,
            ):
                effective_status = OrderStatus.SHIPPED.value
        elif order.fulfillment_status == "partial":
            if effective_status == OrderStatus.PENDING.value:
                effective_status = OrderStatus.PROCESSING.value

        days_to_add = ESTIMATED_DELIVERY_DAYS.get(effective_status, 7)
        if days_to_add == 0:
            return None

        if order.fulfillment_status == "fulfilled":
            base_date = order.updated_at or order.created_at
        elif order.estimated_delivery:
            return order.estimated_delivery
        else:
            base_date = order.created_at

        if base_date.tzinfo is None:
            base_date = base_date.replace(tzinfo=UTC)

        return base_date + timedelta(days=days_to_add)
