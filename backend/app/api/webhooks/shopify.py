"""Shopify webhook handler.

Receives and processes webhooks from Shopify including orders/create, orders/updated, orders/fulfilled.
"""

from __future__ import annotations

import json
import os
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Request, Response, Header, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.core.database import get_db
from app.core.errors import APIError, ErrorCode
from app.core.security import verify_shopify_webhook_hmac
from app.core.config import settings


router = APIRouter()
logger = structlog.get_logger(__name__)


@router.post("/shopify")
async def shopify_webhook_receive(
    request: Request,
    x_shopify_hmac_sha256: str = Header(None),
    x_shopify_topic: str = Header(None),
    x_shopify_shop_domain: str = Header(None),
    x_shopify_api_version: str = Header(None),
    background_tasks: BackgroundTasks = None,
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
        db: Database session

    Returns:
        200 OK response

    Raises:
        HTTPException: If signature verification fails
    """
    request_id = str(uuid4())
    log = logger.bind(
        request_id=request_id,
        topic=x_shopify_topic,
        shop_domain=x_shopify_shop_domain
    )

    # Read raw payload for signature verification
    raw_payload = await request.body()

    # Verify webhook signature (HMAC)
    config = settings()
    api_secret = config.get("SHOPIFY_API_SECRET")

    if not api_secret:
        log.error("shopify_webhook_no_secret")
        raise HTTPException(
            status_code=500,
            detail="Shopify API secret not configured"
        )

    if not verify_shopify_webhook_hmac(raw_payload, x_shopify_hmac_sha256, api_secret):
        log.warning("shopify_webhook_invalid_signature")
        raise HTTPException(status_code=403, detail="Invalid webhook signature")

    # Parse webhook payload
    try:
        payload = json.loads(raw_payload)
    except json.JSONDecodeError:
        log.error("shopify_webhook_invalid_json")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # Process webhook asynchronously (don't block response)
    if background_tasks:
        background_tasks.add_task(
            process_shopify_webhook,
            payload,
            x_shopify_topic,
            x_shopify_shop_domain,
            request_id
        )
    else:
        # Fallback: create task directly
        import asyncio
        asyncio.create_task(
            process_shopify_webhook(
                payload,
                x_shopify_topic,
                x_shopify_shop_domain,
                request_id
            )
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
    log = logger.bind(
        request_id=request_id,
        topic=topic,
        shop_domain=shop_domain
    )

    try:
        # Handle different webhook topics
        if topic == "orders/create":
            await handle_order_created(payload, shop_domain, log)
        elif topic == "orders/updated":
            await handle_order_updated(payload, shop_domain, log)
        elif topic == "orders/fulfilled":
            await handle_order_fulfilled(payload, shop_domain, log)
        else:
            log.warning("shopify_webhook_unknown_topic")

    except Exception as e:
        # Enqueue failed webhook to Dead Letter Queue
        await enqueue_failed_shopify_webhook(payload, topic, str(e), log)
        log.error("shopify_webhook_processing_failed", error=str(e))


async def handle_order_created(payload: dict, shop_domain: str, log) -> None:
    """Handle orders/create webhook.

    Story 2.9: Process order confirmation, send message to shopper, clear cart.

    Args:
        payload: Order payload
        shop_domain: Shopify shop domain
        log: Structlog logger
    """
    order_id = payload.get("id")
    email = payload.get("email")
    financial_status = payload.get("financial_status")

    log.info(
        "shopify_order_created",
        order_id=order_id,
        email=email,
        financial_status=financial_status,
    )

    # Story 2.9: Process order confirmation
    try:
        from app.services.order_confirmation import OrderConfirmationService

        # Create order confirmation service
        confirmation_service = OrderConfirmationService()

        # Process the order confirmation
        result = await confirmation_service.process_order_confirmation(payload)

        log.info(
            "order_confirmation_processed",
            order_id=order_id,
            status=result.status,
            psid=result.psid,
        )

        # Close the service's HTTP client
        await confirmation_service.send_service.close()

    except Exception as e:
        log.error(
            "order_confirmation_processing_error",
            order_id=order_id,
            error=str(e),
        )
        # Re-raise to enqueue to DLQ
        raise


async def handle_order_updated(payload: dict, shop_domain: str, log) -> None:
    """Handle orders/updated webhook.

    Args:
        payload: Order payload
        shop_domain: Shopify shop domain
        log: Structlog logger
    """
    order_id = payload.get("id")
    financial_status = payload.get("financial_status")

    log.info("shopify_order_updated", order_id=order_id, financial_status=financial_status)

    # TODO: Implement order update logic
    # This will be implemented in Epic 4 (Order Tracking & Support)


async def handle_order_fulfilled(payload: dict, shop_domain: str, log) -> None:
    """Handle orders/fulfilled webhook.

    Args:
        payload: Order payload
        shop_domain: Shopify shop domain
        log: Structlog logger
    """
    order_id = payload.get("id")
    tracking_numbers = payload.get("tracking_numbers", [])

    log.info("shopify_order_fulfilled", order_id=order_id, tracking_numbers=tracking_numbers)

    # TODO: Implement fulfillment logic
    # This will be implemented in Epic 4 (Order Tracking & Support)


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
        import redis
        from datetime import datetime

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
            "timestamp": datetime.utcnow().isoformat()
        }
        redis_client.rpush("webhook:dlq:shopify", json.dumps(retry_data))
        log.info("shopify_webhook_enqueued_dlq", topic=topic)

    except Exception as e:
        log.error("shopify_webhook_dlq_failed", error=str(e))
