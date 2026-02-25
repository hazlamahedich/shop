"""Facebook Messenger webhook endpoints.

Receives and processes Facebook webhook events for message processing.
Implements webhook signature verification (NFR-S5) and message parsing.

Story 5-11: Messenger Unified Service Migration
- INT-2: Updated to use UnifiedConversationService via MessengerAdapter
- GAP-4.3: Added consent postback handler (platform-specific)
- MessageProcessor kept for fallback postback handling (deprecated)
"""

from __future__ import annotations

import hmac
import hashlib
import json
from typing import Any, Optional

import httpx
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from fastapi.responses import JSONResponse

import structlog

from app.core.config import settings
from app.schemas.messaging import FacebookWebhookPayload, MessengerResponse
from app.services.messaging.message_processor import MessageProcessor
from app.core.database import async_session
from app.models.facebook_integration import FacebookIntegration
from sqlalchemy import select
from app.services.conversation.unified_conversation_service import UnifiedConversationService
from app.services.conversation.messenger_adapter import MessengerAdapter
from app.services.cart import CartService
from app.services.consent import ConsentService
import redis.asyncio as redis


router = APIRouter(prefix="/webhooks", tags=["webhooks"])
logger = structlog.get_logger(__name__)

FACEBOOK_API_BASE = "https://graph.facebook.com"


def verify_facebook_webhook_signature(request: Request, raw_body: bytes) -> bool:
    """Verify Facebook X-Hub-Signature header (NFR-S5).

    Args:
        request: FastAPI request
        raw_body: Raw request body

    Returns:
        True if signature is valid
    """
    signature = request.headers.get("x-hub-signature-256")
    if not signature:
        return False

    if not signature.startswith("sha256="):
        return False

    signature_hash = signature.split("=")[1]

    app_secret = settings()["FACEBOOK_APP_SECRET"]
    expected_signature = hmac.new(
        app_secret.encode(),
        raw_body,
        hashlib.sha256,
    ).digest()

    return hmac.compare_digest(signature_hash, expected_signature.hex())


@router.post("/facebook/messenger")
async def facebook_messenger_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
) -> JSONResponse:
    """Receive Facebook Messenger webhook events.

    Verifies webhook signature (NFR-S5) and processes incoming messages.
    """
    raw_body = await request.body()

    if not verify_facebook_webhook_signature(request, raw_body):
        logger.warning("webhook_signature_verification_failed")
        raise HTTPException(status_code=403, detail="Invalid webhook signature")

    try:
        payload_data = await request.json()
        payload = FacebookWebhookPayload(**payload_data)
    except Exception as e:
        logger.error("webhook_payload_parse_failed", error=str(e))
        raise HTTPException(status_code=400, detail="Invalid webhook payload")

    processor = MessageProcessor()
    background_tasks.add_task(process_webhook_message, processor, payload)

    return JSONResponse(content={"status": "received"})


async def process_webhook_message(
    processor: MessageProcessor,
    payload: FacebookWebhookPayload,
) -> None:
    """Process webhook message using UnifiedConversationService.

    Story 5-11: Updated to use UnifiedConversationService via MessengerAdapter.
    Falls back to MessageProcessor for postbacks and on error.

    Args:
        processor: Message processor instance (for fallback)
        payload: Webhook payload
    """
    merchant_id = None
    page_id = payload.page_id
    psid = payload.sender_id

    if page_id:
        try:
            async with async_session() as db:
                result = await db.execute(
                    select(FacebookIntegration.merchant_id).where(
                        FacebookIntegration.page_id == page_id
                    )
                )
                row = result.first()
                if row:
                    merchant_id = row[0]
                    logger.info("merchant_lookup_success", page_id=page_id, merchant_id=merchant_id)

                    if payload.postback_payload:
                        consent_response = await handle_consent_postback(
                            psid=psid,
                            postback_payload=payload.postback_payload,
                        )
                        if consent_response:
                            await send_messenger_response(consent_response)
                            return

                        response = await processor.process_postback(payload)
                        if response:
                            await send_messenger_response(response)
                        return

                    if payload.message_text:
                        try:
                            adapter = MessengerAdapter()
                            context = adapter.create_context(
                                psid=psid,
                                merchant_id=merchant_id,
                            )

                            service = UnifiedConversationService(db=db)
                            conv_response = await service.process_message(
                                db=db,
                                context=context,
                                message=payload.message_text,
                            )

                            messenger_response = await adapter.convert_response(
                                response=conv_response,
                                psid=psid,
                            )

                            if messenger_response.text:
                                await send_messenger_response(messenger_response)

                            await adapter.close()

                            logger.info(
                                "unified_conversation_processed",
                                psid=psid,
                                merchant_id=merchant_id,
                                intent=conv_response.intent,
                            )
                            return

                        except Exception as e:
                            logger.warning(
                                "unified_conversation_fallback_to_processor",
                                psid=psid,
                                merchant_id=merchant_id,
                                error=str(e),
                            )
                            processor_with_merchant = MessageProcessor(
                                merchant_id=merchant_id, db=db
                            )
                            response = await processor_with_merchant.process_message(payload)
                            await send_messenger_response(response)
                            return

        except Exception as e:
            logger.warning("merchant_lookup_failed", page_id=page_id, error=str(e))

    if payload.postback_payload:
        response = await processor.process_postback(payload)
        if response:
            await send_messenger_response(response)
    elif payload.message_text:
        response = await processor.process_message(payload)
        await send_messenger_response(response)


async def send_messenger_response(response: MessengerResponse) -> None:
    """Send response to Facebook Messenger.

    Args:
        response: Messenger response to send

    Raises:
        HTTPException: If sending fails due to configuration or API errors
    """
    page_access_token = settings()["FACEBOOK_PAGE_ACCESS_TOKEN"]
    api_version = settings()["FACEBOOK_API_VERSION"]

    if not page_access_token:
        logger.error("facebook_page_access_token_missing")
        raise HTTPException(status_code=500, detail="Facebook Page Access Token not configured")

    url = f"{FACEBOOK_API_BASE}/{api_version}/me/messages"

    payload = {"recipient": {"id": response.recipient_id}, "message": {"text": response.text}}

    headers = {
        "Content-Type": "application/json",
    }

    params = {"access_token": page_access_token}

    try:
        async with httpx.AsyncClient() as client:
            fb_response = await client.post(
                url, json=payload, headers=headers, params=params, timeout=10.0
            )

            if fb_response.status_code == 200:
                logger.info(
                    "messenger_response_sent",
                    recipient_id=response.recipient_id,
                    message_id=fb_response.json().get("message_id"),
                    text=response.text,
                )
            else:
                error_data = fb_response.json()
                error_code = error_data.get("error", {}).get("code", "unknown")
                error_message = error_data.get("error", {}).get("message", "Unknown error")

                logger.error(
                    "messenger_send_failed",
                    status_code=fb_response.status_code,
                    error_code=error_code,
                    error_message=error_message,
                    recipient_id=response.recipient_id,
                )

                if error_code == 4:
                    logger.warning("messenger_rate_limited", recipient_id=response.recipient_id)
                else:
                    raise HTTPException(
                        status_code=502, detail=f"Failed to send message: {error_message}"
                    )

    except httpx.TimeoutException:
        logger.error("messenger_send_timeout", recipient_id=response.recipient_id)
        raise HTTPException(status_code=504, detail="Facebook API timeout")

    except httpx.RequestError as e:
        logger.error(
            "messenger_send_network_error", error=str(e), recipient_id=response.recipient_id
        )
        raise HTTPException(status_code=503, detail="Failed to connect to Facebook API")


async def handle_consent_postback(
    psid: str,
    postback_payload: str,
) -> Optional[MessengerResponse]:
    """Handle consent postback directly without MessageProcessor.

    Story 5-11 GAP-4.3: Consent postback handling (platform-specific).

    Args:
        psid: Facebook Page-Scoped ID
        postback_payload: Postback payload (format: CONSENT:YES/NO:product_id:variant_id)

    Returns:
        MessengerResponse if handled, None if not a consent postback
    """
    parts = postback_payload.split(":")
    if len(parts) < 3 or parts[0] != "CONSENT":
        return None

    consent_choice = parts[1]
    product_id = parts[2] if len(parts) > 2 else None
    variant_id = parts[3] if len(parts) > 3 else None

    consent_granted = consent_choice == "YES"

    try:
        config = settings()
        redis_url = config.get("REDIS_URL", "redis://localhost:6379/0")
        redis_client = redis.from_url(redis_url, decode_responses=True)

        consent_service = ConsentService(redis_client=redis_client)
        await consent_service.record_consent(psid, consent_granted=consent_granted)

        logger.info(
            "consent_response_handled",
            psid=psid,
            consent_granted=consent_granted,
            product_id=product_id,
            variant_id=variant_id,
        )

        if consent_granted and product_id and variant_id:
            pending_key = f"pending_cart:{psid}"
            pending_data = await redis_client.get(pending_key)

            if pending_data:
                await redis_client.delete(pending_key)
                pending = json.loads(pending_data)

                cart_service = CartService(redis_client=redis_client)
                cart = await cart_service.add_item(
                    psid=psid,
                    product_id=pending["product_id"],
                    variant_id=pending["variant_id"],
                    title=pending["title"],
                    price=pending["price"],
                    image_url=pending["image_url"],
                    currency_code=pending.get("currency_code", "USD"),
                    quantity=1,
                )

                logger.info(
                    "cart_add_after_consent",
                    psid=psid,
                    product_id=pending["product_id"],
                    item_count=cart.item_count,
                )

                await redis_client.close()
                return MessengerResponse(
                    text=f"Great! I've added {pending['title']} (${pending['price']}) to your cart. Your cart will be saved for 24 hours.",
                    recipient_id=psid,
                )
            else:
                await redis_client.close()
                return MessengerResponse(
                    text="Your cart session expired. Please search for the product again and add it.",
                    recipient_id=psid,
                )
        else:
            await redis_client.close()
            return MessengerResponse(
                text="No problem! Let me know if you'd like to search for something else.",
                recipient_id=psid,
            )

    except Exception as e:
        logger.error("consent_postback_failed", psid=psid, error=str(e))
        return MessengerResponse(
            text="Sorry, I encountered an error. Please try again.",
            recipient_id=psid,
        )


@router.get("/facebook/messenger")
async def facebook_webhook_verify(request: Request) -> JSONResponse:
    """Verify Facebook webhook during setup.

    Facebook sends a GET request with hub.challenge and hub.verify_token
    to verify webhook ownership.
    """
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    verify_token = settings()["FACEBOOK_WEBHOOK_VERIFY_TOKEN"]
    if token == verify_token and mode == "subscribe":
        return JSONResponse(content={"hub.challenge": challenge})
    else:
        raise HTTPException(status_code=403, detail="Webhook verification failed")
