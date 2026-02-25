"""Shopify webhook handler.

Receives and processes webhooks from Shopify including orders/create,
orders/updated, orders/fulfilled, orders/cancelled, inventory_levels/update,
products/update, disputes/create.
"""

from __future__ import annotations

import json
import os
from uuid import uuid4

import structlog
from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Request, Response
from sqlalchemy import select

from app.core.config import settings
from app.core.database import async_session
from app.core.security import verify_shopify_webhook_hmac
from app.models.order import Order

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.post("/shopify")
async def shopify_webhook_receive(
    request: Request,
    background_tasks: BackgroundTasks,
    x_shopify_hmac_sha256: str = Header(None, alias="X-Shopify-Hmac-Sha256"),
    x_shopify_topic: str = Header(None, alias="X-Shopify-Topic"),
    x_shopify_shop_domain: str = Header(None, alias="X-Shopify-Shop-Domain"),
    x_shopify_api_version: str = Header(None, alias="X-Shopify-Api-Version"),
) -> Response:
    """Receive Shopify webhook.

    Verifies HMAC signature and processes webhook payload asynchronously.

    Args:
        request: FastAPI request
        x_shopify_hmac_sha256: X-Shopify-Hmac-Sha256 header for signature verification
        x_shopify_topic: Webhook topic (e.g., orders/create)
        x_shopify_shop_domain: Shopify shop domain
        x_shopify_api_version: API version
        background_tasks: FastAPI background tasks

    Returns:
        200 OK response

    Raises:
        HTTPException: If signature verification fails
    """
    from app.core.security import decrypt_access_token
    from app.models.merchant import Merchant
    from app.models.shopify_integration import ShopifyIntegration

    request_id = str(uuid4())
    log = logger.bind(
        request_id=request_id, topic=x_shopify_topic, shop_domain=x_shopify_shop_domain
    )

    raw_payload = await request.body()

    config = settings()
    api_secret = config.get("SHOPIFY_API_SECRET")

    if not api_secret:
        async with async_session() as db:
            result = await db.execute(
                select(ShopifyIntegration).where(
                    ShopifyIntegration.shop_domain == x_shopify_shop_domain
                )
            )
            integration = result.scalars().first()

            if integration:
                merchant_result = await db.execute(
                    select(Merchant).where(Merchant.id == integration.merchant_id)
                )
                merchant = merchant_result.scalars().first()

                if merchant and merchant.config:
                    encrypted_secret = merchant.config.get("shopify_api_secret_encrypted")
                    if encrypted_secret:
                        try:
                            api_secret = decrypt_access_token(encrypted_secret)
                        except Exception as e:
                            log.warning("shopify_webhook_decrypt_secret_failed", error=str(e))

    if api_secret:
        if not verify_shopify_webhook_hmac(raw_payload, x_shopify_hmac_sha256, api_secret):
            log.warning(
                "shopify_webhook_invalid_signature",
                hmac_header=x_shopify_hmac_sha256[:20] + "..." if x_shopify_hmac_sha256 else None,
            )
            debug_mode = config.get("DEBUG", False)
            if not debug_mode:
                raise HTTPException(status_code=403, detail="Invalid webhook signature")
            log.warning("shopify_webhook_skipping_invalid_signature_debug_mode")
    else:
        debug_mode = config.get("DEBUG", False)
        if not debug_mode:
            log.error("shopify_webhook_no_secret")
            raise HTTPException(status_code=500, detail="Shopify API secret not configured")
        log.warning("shopify_webhook_skipping_hmac_no_secret_debug_mode")

    # Parse webhook payload
    try:
        payload = json.loads(raw_payload)
    except json.JSONDecodeError:
        log.error("shopify_webhook_invalid_json")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # Process webhook asynchronously (don't block response)
    if background_tasks:
        background_tasks.add_task(
            process_shopify_webhook, payload, x_shopify_topic, x_shopify_shop_domain, request_id
        )
    else:
        # Fallback: create task directly
        import asyncio

        asyncio.create_task(
            process_shopify_webhook(payload, x_shopify_topic, x_shopify_shop_domain, request_id)
        )

    log.info("shopify_webhook_received", topic=x_shopify_topic)

    # Acknowledge receipt immediately
    return Response(status_code=200, content="OK")


async def process_shopify_webhook(
    payload: dict,
    topic: str,
    shop_domain: str,
    request_id: str,
) -> None:
    """Process Shopify webhook payload asynchronously.

    Args:
        payload: Webhook payload
        topic: Webhook topic (orders/create, orders/updated, etc.)
        shop_domain: Shopify shop domain
        request_id: Request ID for logging
    """
    log = logger.bind(request_id=request_id, topic=topic, shop_domain=shop_domain)

    try:
        if topic == "orders/create":
            await handle_order_created(payload, shop_domain, log)
        elif topic == "orders/updated":
            await handle_order_updated(payload, shop_domain, log)
        elif topic == "orders/fulfilled":
            await handle_order_fulfilled(payload, shop_domain, log)
        elif topic == "fulfillments/create" or topic == "fulfillments/update":
            await handle_fulfillment_event(payload, shop_domain, log, topic)
        elif topic == "refunds/create":
            await handle_refund_created(payload, shop_domain, log)
        else:
            log.warning("shopify_webhook_unknown_topic", topic=topic)

    except Exception as e:
        # Enqueue failed webhook to Dead Letter Queue
        await enqueue_failed_shopify_webhook(payload, topic, str(e), log)
        log.error("shopify_webhook_processing_failed", error=str(e))


async def handle_order_created(payload: dict, shop_domain: str, log) -> None:
    """Handle orders/create webhook.

    Story 2.9: Process order confirmation, send message to shopper, clear cart.
    Story 4-2: Store order in database for tracking.

    Args:
        payload: Order payload
        shop_domain: Shopify shop domain
        log: Structlog logger
    """
    from app.models.shopify_integration import ShopifyIntegration
    from app.services.shopify import ShopifyOrderProcessor

    order_id = payload.get("id")
    email = payload.get("email")
    financial_status = payload.get("financial_status")

    log.info(
        "shopify_order_created",
        order_id=order_id,
        email=email,
        financial_status=financial_status,
    )

    try:
        async with async_session() as db:
            result = await db.execute(
                select(ShopifyIntegration.merchant_id).where(
                    ShopifyIntegration.shop_domain == shop_domain
                )
            )
            integration = result.scalar_one_or_none()

            if integration:
                merchant_id = integration
                processor = ShopifyOrderProcessor()
                order = await processor.process_order_webhook(payload, shop_domain, merchant_id, db)
                log.info(
                    "shopify_order_created_stored",
                    order_id=order_id,
                    db_order_id=order.id,
                )

    except Exception as e:
        log.error(
            "shopify_order_storage_failed",
            order_id=order_id,
            error=str(e),
        )

    try:
        from app.services.order_confirmation import OrderConfirmationService

        confirmation_service = OrderConfirmationService()
        result = await confirmation_service.process_order_confirmation(payload)

        log.info(
            "order_confirmation_processed",
            order_id=order_id,
            status=result.status,
            psid=result.psid,
        )

        await confirmation_service.send_service.close()

    except Exception as e:
        log.error(
            "order_confirmation_processing_error",
            order_id=order_id,
            error=str(e),
        )
        raise


async def handle_order_updated(payload: dict, shop_domain: str, log) -> None:
    """Handle orders/updated webhook.

    Story 4-2: Process order updates with PSID resolution and database storage.

    Args:
        payload: Order payload
        shop_domain: Shopify shop domain
        log: Structlog logger
    """
    from app.models.shopify_integration import ShopifyIntegration
    from app.services.shopify import ShopifyOrderProcessor

    order_id = payload.get("id")
    financial_status = payload.get("financial_status")

    log.info("shopify_order_updated", order_id=order_id, financial_status=financial_status)

    try:
        async with async_session() as db:
            result = await db.execute(
                select(ShopifyIntegration.merchant_id).where(
                    ShopifyIntegration.shop_domain == shop_domain
                )
            )
            integration = result.scalar_one_or_none()

            if not integration:
                log.warning(
                    "shopify_order_update_no_merchant",
                    shop_domain=shop_domain,
                    order_id=order_id,
                )
                return

            merchant_id = integration
            processor = ShopifyOrderProcessor()
            order = await processor.process_order_webhook(payload, shop_domain, merchant_id, db)

            log.info(
                "shopify_order_updated_stored",
                order_id=order_id,
                db_order_id=order.id,
                status=order.status,
            )

    except Exception as e:
        log.error(
            "shopify_order_update_failed",
            order_id=order_id,
            error=str(e),
        )
        raise


async def handle_order_fulfilled(payload: dict, shop_domain: str, log) -> None:
    """Handle orders/fulfilled webhook.

    Story 4-2: Process fulfillment with tracking info and database storage.
    Story 4-3: Send shipping notification to shopper.

    Args:
        payload: Order payload
        shop_domain: Shopify shop domain
        log: Structlog logger
    """
    from app.models.shopify_integration import ShopifyIntegration
    from app.services.shopify import ShopifyOrderProcessor

    order_id = payload.get("id")
    tracking_numbers = payload.get("tracking_numbers", [])
    fulfillments = payload.get("fulfillments", [])

    fulfillment_id = None
    if fulfillments:
        fulfillment_id = fulfillments[0].get("id")

    log.info("shopify_order_fulfilled", order_id=order_id, tracking_numbers=tracking_numbers)

    try:
        async with async_session() as db:
            result = await db.execute(
                select(ShopifyIntegration.merchant_id).where(
                    ShopifyIntegration.shop_domain == shop_domain
                )
            )
            integration = result.scalar_one_or_none()

            if not integration:
                log.warning(
                    "shopify_order_fulfillment_no_merchant",
                    shop_domain=shop_domain,
                    order_id=order_id,
                )
                return

            merchant_id = integration
            processor = ShopifyOrderProcessor()
            order = await processor.process_order_webhook(payload, shop_domain, merchant_id, db)

            log.info(
                "shopify_order_fulfilled_stored",
                order_id=order_id,
                db_order_id=order.id,
                tracking_number=order.tracking_number,
            )

            try:
                from app.services.shipping_notification import ShippingNotificationService

                notification_service = ShippingNotificationService()
                notification_result = await notification_service.send_shipping_notification(
                    order=order,
                    db=db,
                    fulfillment_id=str(fulfillment_id) if fulfillment_id else None,
                )

                log.info(
                    "shipping_notification_result",
                    order_id=order_id,
                    status=notification_result.status.value,
                    error_code=notification_result.error_code,
                )

                await notification_service.close()

            except Exception as notification_error:
                log.error(
                    "shipping_notification_error",
                    order_id=order_id,
                    error=str(notification_error),
                )

    except Exception as e:
        log.error(
            "shopify_order_fulfillment_failed",
            order_id=order_id,
            error=str(e),
        )
        raise


async def handle_fulfillment_event(payload: dict, shop_domain: str, log, topic: str) -> None:
    """Handle fulfillments/create and fulfillments/update webhooks.

    These events are triggered when a fulfillment is created or updated,
    including when tracking info is added/modified.

    Args:
        payload: Fulfillment payload
        shop_domain: Shopify shop domain
        log: Structlog logger
        topic: Webhook topic (fulfillments/create or fulfillments/update)
    """
    from app.models.shopify_integration import ShopifyIntegration

    fulfillment_id = payload.get("id")
    order_id = payload.get("order_id")
    tracking_number = payload.get("tracking_number")
    tracking_url = payload.get("tracking_url")

    log.info(
        "shopify_fulfillment_event",
        fulfillment_id=fulfillment_id,
        order_id=order_id,
        tracking_number=tracking_number,
        topic=topic,
    )

    if not order_id:
        log.warning("shopify_fulfillment_no_order_id", fulfillment_id=fulfillment_id)
        return

    try:
        async with async_session() as db:
            result = await db.execute(
                select(ShopifyIntegration.merchant_id).where(
                    ShopifyIntegration.shop_domain == shop_domain
                )
            )
            integration = result.scalar_one_or_none()

            if not integration:
                log.warning(
                    "shopify_fulfillment_no_merchant",
                    shop_domain=shop_domain,
                    order_id=order_id,
                )
                return

            merchant_id = integration

            shopify_order_id = f"gid://shopify/Order/{order_id}"

            order_result = await db.execute(
                select(Order).where(
                    Order.merchant_id == merchant_id,
                    Order.shopify_order_id == shopify_order_id,
                )
            )
            order = order_result.scalars().first()

            if order:
                order.tracking_number = tracking_number
                order.tracking_url = tracking_url
                if tracking_number:
                    order.status = "shipped"
                    order.fulfillment_status = "fulfilled"
                await db.commit()

                log.info(
                    "shopify_fulfillment_tracking_updated",
                    order_id=order.id,
                    order_number=order.order_number,
                    tracking_number=tracking_number,
                    tracking_url=tracking_url,
                )
            else:
                log.warning(
                    "shopify_fulfillment_order_not_found",
                    shopify_order_id=shopify_order_id,
                    merchant_id=merchant_id,
                )

    except Exception as e:
        log.error(
            "shopify_fulfillment_event_failed",
            fulfillment_id=fulfillment_id,
            order_id=order_id,
            error=str(e),
        )
        raise


async def handle_refund_created(payload: dict, shop_domain: str, log) -> None:
    """Handle refunds/create webhook.

    Args:
        payload: Refund payload
        shop_domain: Shopify shop domain
        log: Structlog logger
    """
    from app.models.shopify_integration import ShopifyIntegration

    refund_id = payload.get("id")
    order_id = payload.get("order_id")

    log.info(
        "shopify_refund_created",
        refund_id=refund_id,
        order_id=order_id,
    )

    if not order_id:
        log.warning("shopify_refund_no_order_id", refund_id=refund_id)
        return

    try:
        async with async_session() as db:
            result = await db.execute(
                select(ShopifyIntegration.merchant_id).where(
                    ShopifyIntegration.shop_domain == shop_domain
                )
            )
            integration = result.scalar_one_or_none()

            if not integration:
                log.warning(
                    "shopify_refund_no_merchant",
                    shop_domain=shop_domain,
                    order_id=order_id,
                )
                return

            merchant_id = integration
            shopify_order_id = f"gid://shopify/Order/{order_id}"

            order_result = await db.execute(
                select(Order).where(
                    Order.merchant_id == merchant_id,
                    Order.shopify_order_id == shopify_order_id,
                )
            )
            order = order_result.scalars().first()

            if order:
                order.status = "refunded"
                order.fulfillment_status = "restocked"
                await db.commit()

                log.info(
                    "shopify_refund_order_updated",
                    order_id=order.id,
                    order_number=order.order_number,
                )
            else:
                log.warning(
                    "shopify_refund_order_not_found",
                    shopify_order_id=shopify_order_id,
                    merchant_id=merchant_id,
                )

    except Exception as e:
        log.error(
            "shopify_refund_event_failed",
            refund_id=refund_id,
            order_id=order_id,
            error=str(e),
        )
        raise


async def enqueue_failed_shopify_webhook(
    webhook_data: dict,
    topic: str,
    error: str,
    log,
) -> None:
    """Queue failed Shopify webhook for retry.

    Per architecture: Redis lists as temporary DLQ with 3 retry attempts.

    NOTE: DLQ retry worker implementation is deferred to Epic 4 (Order Tracking & Support).
    Current implementation stores webhooks for manual inspection and recovery.

    Args:
        webhook_data: Webhook payload
        topic: Webhook topic
        error: Error message
        log: Structlog logger
    """
    try:
        from datetime import datetime

        import redis

        redis_url = os.getenv("REDIS_URL")
        if not redis_url:
            log.warning("shopify_webhook_dlq_no_redis")
            return

        redis_client = redis.from_url(redis_url, decode_responses=True)
        retry_data = {
            "webhook_data": webhook_data,
            "topic": topic,
            "error": error,
            "attempts": 0,
            "max_attempts": 3,
            "timestamp": datetime.utcnow().isoformat(),
        }
        redis_client.rpush("webhook:dlq:shopify", json.dumps(retry_data))
        log.info("shopify_webhook_enqueued_dlq", topic=topic)

    except Exception as e:
        log.error("shopify_webhook_dlq_failed", error=str(e))


async def _upsert_customer_profile_and_link(
    db,
    payload: dict,
    order,
    merchant_id: int,
    log,
) -> None:
    """Upsert customer profile and link conversation on purchase.

    Story 4-13: AC 10 - Conversation linking with customer identity.

    Args:
        db: Database session
        payload: Shopify order payload
        order: Order model instance
        merchant_id: Merchant ID
        log: Structlog logger
    """
    from decimal import Decimal

    from app.services.customer_lookup_service import CustomerLookupService

    customer_email = payload.get("email")
    customer = payload.get("customer", {})
    first_name = customer.get("first_name")
    last_name = customer.get("last_name")
    phone = customer.get("phone")

    if not customer_email:
        return

    try:
        customer_service = CustomerLookupService()
        profile = await customer_service.upsert_customer_profile(
            db=db,
            merchant_id=merchant_id,
            email=customer_email,
            phone=phone,
            first_name=first_name,
            last_name=last_name,
            order_total=Decimal(str(order.total)) if order.total else None,
        )

        if order.platform_sender_id and order.platform_sender_id != "unknown":
            from app.models.conversation import Conversation

            result = await db.execute(
                select(Conversation).where(
                    Conversation.merchant_id == merchant_id,
                    Conversation.platform_sender_id == order.platform_sender_id,
                )
            )
            conversation = result.scalars().first()

            if conversation:
                conversation_data = conversation.conversation_data or {}
                updated_data = await customer_service.link_device_to_profile(
                    db=db,
                    profile=profile,
                    platform_sender_id=order.platform_sender_id,
                    conversation_data=conversation_data,
                )
                conversation.conversation_data = updated_data
                await db.commit()

                log.info(
                    "customer_profile_linked_to_conversation",
                    profile_id=profile.id,
                    conversation_id=conversation.id,
                    email=customer_email,
                )

    except Exception as e:
        log.warning(
            "customer_profile_upsert_failed",
            email=customer_email,
            error=str(e),
        )


async def _fetch_cogs_async(
    shop_domain: str,
    items: list,
    order_id: int,
    log,
) -> None:
    """Fetch COGS for order items asynchronously.

    Story 4-13: AC 9 - COGS tracking with Redis caching.

    Args:
        shop_domain: Shopify shop domain
        items: List of order items with variant_id
        order_id: Database order ID
        log: Structlog logger
    """
    from datetime import datetime, timezone
    from decimal import Decimal

    from app.core.security import decrypt_access_token
    from app.models.shopify_integration import ShopifyIntegration
    from app.services.shopify.cogs_cache import COGSCache
    from app.services.shopify_admin import ShopifyAdminClient

    variant_ids = []
    for item in items:
        variant_id = item.get("variant_id")
        if variant_id:
            variant_ids.append(f"gid://shopify/ProductVariant/{variant_id}")

    if not variant_ids:
        return

    try:
        async with async_session() as db:
            result = await db.execute(
                select(ShopifyIntegration).where(ShopifyIntegration.shop_domain == shop_domain)
            )
            integration = result.scalars().first()

            if not integration:
                log.warning("cogs_fetch_no_integration", shop_domain=shop_domain)
                return

            decrypted_token = decrypt_access_token(integration.admin_token_encrypted)
            admin_client = ShopifyAdminClient(
                shop_domain=shop_domain,
                access_token=decrypted_token,
            )

            costs = await admin_client.fetch_variant_costs_batch(variant_ids)

            if not costs:
                return

            cogs_cache = COGSCache()
            await cogs_cache.set_batch(costs)

            total_cogs = Decimal("0") * sum(costs.values())

            order_result = await db.execute(select(Order).where(Order.id == order_id))
            order = order_result.scalars().first()

            if order:
                order.cogs_total = Decimal(str(total_cogs))
                order.cogs_fetched_at = datetime.now(timezone.utc).replace(tzinfo=None)
                await db.commit()

                log.info(
                    "cogs_fetched_for_order",
                    order_id=order_id,
                    total_cogs=str(total_cogs),
                    variant_count=len(costs),
                )

    except Exception as e:
        log.warning(
            "cogs_fetch_failed_enqueue_dlq",
            order_id=order_id,
            error=str(e),
        )

        try:
            from datetime import datetime

            import redis

            redis_url = os.getenv("REDIS_URL")
            if redis_url:
                redis_client = redis.from_url(redis_url, decode_responses=True)
                retry_data = {
                    "order_id": order_id,
                    "variant_ids": variant_ids,
                    "shop_domain": shop_domain,
                    "error": str(e),
                    "attempts": 0,
                    "max_attempts": 3,
                    "timestamp": datetime.utcnow().isoformat(),
                }
                redis_client.rpush("cogs:dlq", json.dumps(retry_data))
                log.info("cogs_fetch_enqueued_dlq", order_id=order_id)
        except Exception as dlq_error:
            log.error("cogs_dlq_enqueue_failed", error=str(dlq_error))
