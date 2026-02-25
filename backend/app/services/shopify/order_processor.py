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
from app.models.conversation import Conversation

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

    Story 4-2: Shopify Webhook Integration
    Story 4-13: Payment/Cost Data Enhancement

    Args:
        payload: Raw Shopify order webhook payload

    Returns:
        Dict with extracted order fields ready for Order model
    """
    shopify_order_id = payload.get("id")
    if shopify_order_id:
        shopify_order_id = f"gid://shopify/Order/{shopify_order_id}"

    order_number = payload.get("order_number") or payload.get("name", "")
    if order_number:
        order_number = str(order_number).lstrip("#")

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

    fulfillments = payload.get("fulfillments", [])
    if not tracking_number and fulfillments:
        for fulfillment in fulfillments:
            fulfillment_tracking = fulfillment.get("tracking_number")
            if fulfillment_tracking:
                tracking_number = fulfillment_tracking
                tracking_url = fulfillment.get("tracking_url") or fulfillment.get(
                    "tracking_company_url"
                )
                break

    if not tracking_url and tracking_number:
        for fulfillment in fulfillments:
            if fulfillment.get("tracking_number") == tracking_number:
                tracking_url = fulfillment.get("tracking_url") or fulfillment.get(
                    "tracking_company_url"
                )
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

    # Story 4-13: Payment breakdown extraction
    discount_codes = payload.get("discount_codes", [])
    if discount_codes:
        discount_codes = [
            {
                "code": dc.get("code"),
                "amount": dc.get("amount"),
                "type": dc.get("type"),
            }
            for dc in discount_codes
        ]

    total_discount_str = payload.get("current_total_discounts") or payload.get(
        "total_discounts", "0"
    )
    try:
        total_discount = Decimal(str(total_discount_str))
    except Exception:
        total_discount = Decimal("0")

    total_tax_str = payload.get("total_tax") or "0"
    try:
        total_tax = Decimal(str(total_tax_str))
    except Exception:
        total_tax = Decimal("0")

    total_shipping_str = "0"
    shipping_lines = payload.get("shipping_lines", [])
    if shipping_lines:
        for shipping in shipping_lines:
            price = shipping.get("price") or "0"
            try:
                total_shipping_str = str(Decimal(str(price)) + Decimal(total_shipping_str))
            except Exception:
                pass
    else:
        total_shipping_set = payload.get("total_shipping_price_set", {})
        shop_money = total_shipping_set.get("shop_money", {})
        total_shipping_str = shop_money.get("amount", "0") if shop_money else "0"

    try:
        total_shipping = Decimal(str(total_shipping_str))
    except Exception:
        total_shipping = Decimal("0")

    tax_lines = payload.get("tax_lines", [])
    if tax_lines:
        tax_lines = [
            {
                "title": tl.get("title"),
                "rate": tl.get("rate"),
                "price": tl.get("price"),
            }
            for tl in tax_lines
        ]

    payment_gateway_names = payload.get("payment_gateway_names", [])
    payment_method = payment_gateway_names[0] if payment_gateway_names else None

    transactions = payload.get("transactions", [])
    payment_details = None
    if transactions:
        latest_txn = transactions[0]
        payment_details = {
            "gateway": latest_txn.get("gateway"),
            "kind": latest_txn.get("kind"),
            "status": latest_txn.get("status"),
            "credit_card_company": latest_txn.get("credit_card_company"),
            "credit_card_number": latest_txn.get("credit_card_number"),
        }

    # Story 4-13: Customer identity extraction
    customer_phone = customer.get("phone")
    customer_first_name = customer.get("first_name")
    customer_last_name = customer.get("last_name")

    # Story 4-13: Geographic data extraction
    shipping_city = shipping_address.get("city") if shipping_address else None
    shipping_province = shipping_address.get("province") if shipping_address else None
    shipping_country = shipping_address.get("country_code") if shipping_address else None
    if not shipping_country and shipping_address:
        shipping_country = shipping_address.get("country")
    shipping_postal_code = shipping_address.get("zip") if shipping_address else None

    # Story 4-13: Cancellation data
    cancel_reason = payload.get("cancel_reason")
    cancelled_at_str = payload.get("cancelled_at")
    cancelled_at = None
    if cancelled_at_str:
        try:
            if cancelled_at_str.endswith("Z"):
                cancelled_at_str = cancelled_at_str[:-1] + "+00:00"
            cancelled_at = datetime.fromisoformat(cancelled_at_str.replace("Z", "+00:00")).replace(
                tzinfo=None
            )
        except Exception:
            pass

    return {
        "shopify_order_id": shopify_order_id,
        "shopify_order_key": str(order_number) if order_number else None,
        "order_number": str(order_number) if order_number else f"#{shopify_order_id}",
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
        # Story 4-13: Payment breakdown
        "discount_codes": discount_codes if discount_codes else None,
        "total_discount": total_discount,
        "total_tax": total_tax,
        "total_shipping": total_shipping,
        "tax_lines": tax_lines if tax_lines else None,
        "payment_method": payment_method,
        "payment_details": payment_details,
        # Story 4-13: Customer identity
        "customer_phone": customer_phone,
        "customer_first_name": customer_first_name,
        "customer_last_name": customer_last_name,
        # Story 4-13: Geographic data
        "shipping_city": shipping_city,
        "shipping_province": shipping_province,
        "shipping_country": shipping_country,
        "shipping_postal_code": shipping_postal_code,
        # Story 4-13: Cancellation
        "cancel_reason": cancel_reason,
        "cancelled_at": cancelled_at,
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
            result = await db.execute(
                select(Conversation.platform_sender_id)
                .where(
                    Conversation.merchant_id == merchant_id,
                    Conversation.conversation_data["customer_email"].astext == customer_email,
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
                # Story 4-13: Payment breakdown fields
                "discount_codes": order_data.get("discount_codes", existing_order.discount_codes),
                "total_discount": order_data.get("total_discount", existing_order.total_discount),
                "total_tax": order_data.get("total_tax", existing_order.total_tax),
                "total_shipping": order_data.get("total_shipping", existing_order.total_shipping),
                "tax_lines": order_data.get("tax_lines", existing_order.tax_lines),
                "payment_method": order_data.get("payment_method", existing_order.payment_method),
                "payment_details": order_data.get(
                    "payment_details", existing_order.payment_details
                ),
                # Story 4-13: Customer identity fields
                "customer_phone": order_data.get("customer_phone", existing_order.customer_phone),
                "customer_first_name": order_data.get(
                    "customer_first_name", existing_order.customer_first_name
                ),
                "customer_last_name": order_data.get(
                    "customer_last_name", existing_order.customer_last_name
                ),
                # Story 4-13: Geographic fields
                "shipping_city": order_data.get("shipping_city", existing_order.shipping_city),
                "shipping_province": order_data.get(
                    "shipping_province", existing_order.shipping_province
                ),
                "shipping_country": order_data.get(
                    "shipping_country", existing_order.shipping_country
                ),
                "shipping_postal_code": order_data.get(
                    "shipping_postal_code", existing_order.shipping_postal_code
                ),
                # Story 4-13: Cancellation fields
                "cancel_reason": order_data.get("cancel_reason", existing_order.cancel_reason),
                "cancelled_at": order_data.get("cancelled_at", existing_order.cancelled_at),
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
            is_test=platform_sender_id is None or platform_sender_id == "unknown",
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
            # Story 4-13: Payment breakdown
            discount_codes=order_data.get("discount_codes"),
            total_discount=order_data.get("total_discount"),
            total_tax=order_data.get("total_tax"),
            total_shipping=order_data.get("total_shipping"),
            tax_lines=order_data.get("tax_lines"),
            payment_method=order_data.get("payment_method"),
            payment_details=order_data.get("payment_details"),
            # Story 4-13: Customer identity
            customer_phone=order_data.get("customer_phone"),
            customer_first_name=order_data.get("customer_first_name"),
            customer_last_name=order_data.get("customer_last_name"),
            # Story 4-13: Geographic data
            shipping_city=order_data.get("shipping_city"),
            shipping_province=order_data.get("shipping_province"),
            shipping_country=order_data.get("shipping_country"),
            shipping_postal_code=order_data.get("shipping_postal_code"),
            # Story 4-13: Cancellation
            cancel_reason=order_data.get("cancel_reason"),
            cancelled_at=order_data.get("cancelled_at"),
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
