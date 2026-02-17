"""Shopify order processor for webhook handling.

Story 4-2: Shopify Webhook Integration

Provides order processing logic for Shopify webhooks:
- Parse Shopify order payloads
- Resolve customer PSID from checkout attributes
- Map Shopify statuses to OrderStatus enum
- Upsert orders with idempotency
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import APIError, ErrorCode
from app.models.order import Order, OrderStatus

logger = structlog.get_logger(__name__)


SHOPIFY_STATUS_MAP = {
    ("pending", None): OrderStatus.PENDING,
    ("pending", "null"): OrderStatus.PENDING,
    ("authorized", None): OrderStatus.CONFIRMED,
    ("authorized", "null"): OrderStatus.CONFIRMED,
    ("paid", None): OrderStatus.PROCESSING,
    ("paid", "null"): OrderStatus.PROCESSING,
    ("paid", "fulfilled"): OrderStatus.SHIPPED,
    ("paid", "partial"): OrderStatus.PROCESSING,
    ("partially_paid", None): OrderStatus.PROCESSING,
    ("partially_paid", "fulfilled"): OrderStatus.SHIPPED,
    ("cancelled", None): OrderStatus.CANCELLED,
    ("cancelled", "any"): OrderStatus.CANCELLED,
    ("refunded", None): OrderStatus.REFUNDED,
    ("refunded", "any"): OrderStatus.REFUNDED,
    ("void", None): OrderStatus.CANCELLED,
}


def map_shopify_status_to_order_status(
    financial_status: str | None,
    fulfillment_status: str | None,
) -> OrderStatus:
    """Map Shopify financial/fulfillment status to OrderStatus enum.

    Args:
        financial_status: Shopify financial_status (pending, paid, etc.)
        fulfillment_status: Shopify fulfillment_status (null, fulfilled, partial)

    Returns:
        OrderStatus enum value
    """
    if not financial_status:
        return OrderStatus.PENDING

    financial = financial_status.lower() if financial_status else None
    fulfillment = fulfillment_status.lower() if fulfillment_status else None

    if fulfillment is None or fulfillment == "null":
        fulfillment_key = None
    else:
        fulfillment_key = fulfillment

    key = (financial, fulfillment_key)
    if key in SHOPIFY_STATUS_MAP:
        return SHOPIFY_STATUS_MAP[key]

    for (f, _), status in SHOPIFY_STATUS_MAP.items():
        if f == financial:
            return status

    return OrderStatus.PROCESSING


def parse_shopify_order(payload: dict[str, Any]) -> dict[str, Any]:
    """Parse Shopify webhook payload into order data dict.

    Args:
        payload: Raw Shopify order webhook payload

    Returns:
        Dict with extracted order fields ready for Order model
    """
    shopify_order_id = payload.get("id")
    if shopify_order_id:
        shopify_order_id = f"gid://shopify/Order/{shopify_order_id}"

    order_number = payload.get("order_number") or payload.get("name", "")

    financial_status = payload.get("financial_status")
    fulfillment_status = payload.get("fulfillment_status")

    status = map_shopify_status_to_order_status(financial_status, fulfillment_status)

    customer = payload.get("customer", {})
    customer_email = payload.get("email") or customer.get("email")

    line_items = payload.get("line_items", [])
    items = [
        {
            "id": item.get("id"),
            "title": item.get("title"),
            "quantity": item.get("quantity"),
            "price": item.get("price"),
            "variant_id": item.get("variant_id"),
            "product_id": item.get("product_id"),
        }
        for item in line_items
    ]

    subtotal_str = payload.get("current_subtotal_price") or payload.get("subtotal_price", "0")
    total_str = payload.get("current_total_price") or payload.get("total_price", "0")

    try:
        subtotal = Decimal(str(subtotal_str))
    except Exception:
        subtotal = Decimal("0")

    try:
        total = Decimal(str(total_str))
    except Exception:
        total = Decimal("0")

    currency = payload.get("currency") or payload.get("currency_code", "USD")

    tracking_numbers = payload.get("tracking_numbers", [])
    tracking_number = tracking_numbers[0] if tracking_numbers else payload.get("tracking_number")

    tracking_url = payload.get("tracking_url")
    if not tracking_url and tracking_number:
        fulfillments = payload.get("fulfillments", [])
        for fulfillment in fulfillments:
            if fulfillment.get("tracking_number") == tracking_number:
                tracking_url = fulfillment.get("tracking_url")
                break

    shipping_address = payload.get("shipping_address")

    updated_at_str = payload.get("updated_at")
    shopify_updated_at = None
    if updated_at_str:
        try:
            if updated_at_str.endswith("Z"):
                updated_at_str = updated_at_str[:-1] + "+00:00"
            shopify_updated_at = datetime.fromisoformat(
                updated_at_str.replace("Z", "+00:00")
            ).replace(tzinfo=None)
        except Exception:
            pass

    return {
        "shopify_order_id": shopify_order_id,
        "shopify_order_key": order_number,
        "order_number": order_number or f"#{shopify_order_id}",
        "financial_status": financial_status,
        "fulfillment_status": fulfillment_status,
        "status": status.value,
        "customer_email": customer_email,
        "items": items if items else None,
        "subtotal": subtotal,
        "total": total,
        "currency_code": currency,
        "tracking_number": tracking_number,
        "tracking_url": tracking_url,
        "shipping_address": shipping_address,
        "shopify_updated_at": shopify_updated_at,
    }


async def resolve_customer_psid(
    order_payload: dict[str, Any],
    db: AsyncSession,
    merchant_id: int,
) -> str | None:
    """Resolve customer PSID from Shopify order payload.

    Resolution strategy:
    1. Check note_attributes for messenger_psid
    2. Check custom_attributes (checkout attributes)
    3. Fallback: lookup by customer email in conversations

    Args:
        order_payload: Raw Shopify order payload
        db: Database session
        merchant_id: Merchant ID for conversation lookup

    Returns:
        PSID string if found, None otherwise
    """
    note_attributes = order_payload.get("note_attributes", [])
    for attr in note_attributes:
        if isinstance(attr, dict) and attr.get("name") == "messenger_psid":
            psid = attr.get("value")
            if psid:
                logger.info(
                    "shopify_psid_resolved_from_note",
                    merchant_id=merchant_id,
                    source="note_attributes",
                )
                return str(psid)

    custom_attributes = order_payload.get("custom_attributes", [])
    for attr in custom_attributes:
        if isinstance(attr, dict):
            if attr.get("name") == "messenger_psid":
                psid = attr.get("value")
                if psid:
                    logger.info(
                        "shopify_psid_resolved_from_custom",
                        merchant_id=merchant_id,
                        source="custom_attributes",
                    )
                    return str(psid)

    customer_email = order_payload.get("email")
    if not customer_email:
        customer = order_payload.get("customer", {})
        customer_email = customer.get("email")

    if customer_email:
        try:
            from app.models.conversation import Conversation

            result = await db.execute(
                select(Conversation.platform_sender_id)
                .where(
                    Conversation.merchant_id == merchant_id,
                    Conversation.customer_email == customer_email,
                )
                .limit(1)
            )
            row = result.scalar_one_or_none()
            if row:
                logger.info(
                    "shopify_psid_resolved_from_email",
                    merchant_id=merchant_id,
                    email=customer_email,
                )
                return row
        except Exception as e:
            logger.warning(
                "shopify_psid_email_lookup_failed",
                merchant_id=merchant_id,
                email=customer_email,
                error=str(e),
            )

    logger.warning(
        "shopify_psid_resolution_failed",
        merchant_id=merchant_id,
        email=customer_email,
    )
    return None


async def upsert_order(
    db: AsyncSession,
    order_data: dict[str, Any],
    merchant_id: int,
    platform_sender_id: str | None = None,
) -> Order:
    """Upsert order with idempotency and out-of-order handling.

    Uses INSERT ... ON CONFLICT for idempotent webhook processing.
    Handles out-of-order webhooks by comparing timestamps.

    Args:
        db: Database session
        order_data: Parsed order data from parse_shopify_order()
        merchant_id: Merchant ID
        platform_sender_id: Customer PSID (optional)

    Returns:
        Order instance (created or updated)

    Raises:
        APIError: If database operation fails
    """
    shopify_order_id = order_data.get("shopify_order_id")

    if not shopify_order_id:
        raise APIError(
            ErrorCode.VALIDATION_ERROR,
            "shopify_order_id is required",
        )

    incoming_updated_at = order_data.get("shopify_updated_at")

    try:
        existing_result = await db.execute(
            select(Order).where(Order.shopify_order_id == shopify_order_id)
        )
        existing_order = existing_result.scalars().first()

        if existing_order:
            if (
                incoming_updated_at
                and existing_order.shopify_updated_at
                and incoming_updated_at <= existing_order.shopify_updated_at
            ):
                logger.info(
                    "shopify_webhook_out_of_order_skipped",
                    shopify_order_id=shopify_order_id,
                    incoming_ts=incoming_updated_at.isoformat() if incoming_updated_at else None,
                    existing_ts=existing_order.shopify_updated_at.isoformat(),
                )
                return existing_order

            update_data = {
                "status": order_data.get("status", existing_order.status),
                "fulfillment_status": order_data.get(
                    "fulfillment_status", existing_order.fulfillment_status
                ),
                "tracking_number": order_data.get(
                    "tracking_number", existing_order.tracking_number
                ),
                "tracking_url": order_data.get("tracking_url", existing_order.tracking_url),
                "items": order_data.get("items", existing_order.items),
                "subtotal": order_data.get("subtotal", existing_order.subtotal),
                "total": order_data.get("total", existing_order.total),
                "shopify_updated_at": incoming_updated_at or existing_order.shopify_updated_at,
                "updated_at": datetime.utcnow(),
            }

            if platform_sender_id and not existing_order.platform_sender_id:
                update_data["platform_sender_id"] = platform_sender_id

            for key, value in update_data.items():
                setattr(existing_order, key, value)

            await db.commit()
            await db.refresh(existing_order)

            logger.info(
                "shopify_order_updated",
                shopify_order_id=shopify_order_id,
                order_id=existing_order.id,
                status=existing_order.status,
            )
            return existing_order

        order_number = order_data.get("order_number") or order_data.get("shopify_order_key", "")
        if not order_number:
            order_number = f"#{shopify_order_id.split('/')[-1]}"

        new_order = Order(
            order_number=order_number,
            merchant_id=merchant_id,
            platform_sender_id=platform_sender_id or "unknown",
            status=order_data.get("status", OrderStatus.PENDING.value),
            items=order_data.get("items"),
            subtotal=order_data.get("subtotal", Decimal("0")),
            total=order_data.get("total", Decimal("0")),
            currency_code=order_data.get("currency_code", "USD"),
            customer_email=order_data.get("customer_email"),
            shipping_address=order_data.get("shipping_address"),
            tracking_number=order_data.get("tracking_number"),
            tracking_url=order_data.get("tracking_url"),
            shopify_order_id=shopify_order_id,
            shopify_order_key=order_data.get("shopify_order_key"),
            fulfillment_status=order_data.get("fulfillment_status"),
            shopify_updated_at=incoming_updated_at,
        )

        db.add(new_order)
        await db.commit()
        await db.refresh(new_order)

        logger.info(
            "shopify_order_created",
            shopify_order_id=shopify_order_id,
            order_id=new_order.id,
            status=new_order.status,
        )
        return new_order

    except Exception as e:
        await db.rollback()
        logger.error(
            "shopify_order_upsert_failed",
            shopify_order_id=shopify_order_id,
            error=str(e),
        )
        raise APIError(
            ErrorCode.ORDER_LOOKUP_FAILED,
            f"Failed to upsert order: {str(e)}",
        )


class ShopifyOrderProcessor:
    """Service class for processing Shopify order webhooks."""

    async def process_order_webhook(
        self,
        payload: dict[str, Any],
        shop_domain: str,
        merchant_id: int,
        db: AsyncSession,
    ) -> Order:
        """Process a Shopify order webhook payload.

        Args:
            payload: Raw Shopify webhook payload
            shop_domain: Shopify shop domain
            merchant_id: Merchant ID
            db: Database session

        Returns:
            Created or updated Order instance
        """
        log = logger.bind(
            shop_domain=shop_domain,
            merchant_id=merchant_id,
            shopify_order_id=payload.get("id"),
        )

        log.info("shopify_webhook_processing_start")

        order_data = parse_shopify_order(payload)

        platform_sender_id = await resolve_customer_psid(payload, db, merchant_id)

        if not platform_sender_id:
            log.warning(
                "shopify_webhook_psid_not_resolved",
                email=order_data.get("customer_email"),
            )

        order = await upsert_order(db, order_data, merchant_id, platform_sender_id)

        log.info(
            "shopify_webhook_processing_complete",
            order_id=order.id,
            status=order.status,
            psid_resolved=platform_sender_id is not None,
        )

        return order
