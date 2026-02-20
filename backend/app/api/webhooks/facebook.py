"""Facebook Messenger webhook endpoints.

Receives and processes Facebook webhook events for message processing.
Implements webhook signature verification (NFR-S5) and message parsing.
"""

from __future__ import annotations

import hmac
import hashlib
from typing import Any

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


router = APIRouter(prefix="/webhooks", tags=["webhooks"])
logger = structlog.get_logger(__name__)

# Facebook Messenger API base URL
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

    # Facebook sends signature as "sha256=<signature>"
    if not signature.startswith("sha256="):
        return False

    signature_hash = signature.split("=")[1]

    # Compute expected signature
    app_secret = settings()["FACEBOOK_APP_SECRET"]
    expected_signature = hmac.new(
        app_secret.encode(),
        raw_body,
        hashlib.sha256,
    ).digest()

    # Compare signatures
    return hmac.compare_digest(signature_hash, expected_signature.hex())


@router.post("/facebook/messenger")
async def facebook_messenger_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
) -> JSONResponse:
    """Receive Facebook Messenger webhook events.

    Verifies webhook signature (NFR-S5) and processes incoming messages.
    """
    # Get raw body for signature verification
    raw_body = await request.body()

    # Verify X-Hub-Signature (NFR-S5)
    if not verify_facebook_webhook_signature(request, raw_body):
        logger.warning("webhook_signature_verification_failed")
        raise HTTPException(status_code=403, detail="Invalid webhook signature")

    # Parse webhook payload
    try:
        payload_data = await request.json()
        payload = FacebookWebhookPayload(**payload_data)
    except Exception as e:
        logger.error("webhook_payload_parse_failed", error=str(e))
        raise HTTPException(status_code=400, detail="Invalid webhook payload")

    # Process message in background (don't block webhook response)
    processor = MessageProcessor()
    background_tasks.add_task(process_webhook_message, processor, payload)

    # Return 200 OK immediately (Facebook requirement)
    return JSONResponse(content={"status": "received"})


async def process_webhook_message(
    processor: MessageProcessor,
    payload: FacebookWebhookPayload,
) -> None:
    """Process webhook message in background task.

    Args:
        processor: Message processor instance
        payload: Webhook payload
    """
    merchant_id = None
    page_id = payload.page_id
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

                    processor = MessageProcessor(merchant_id=merchant_id, db=db)

                    if payload.postback_payload:
                        response = await processor.process_postback(payload)
                        if response:
                            await send_messenger_response(response)
                    elif payload.message_text:
                        response = await processor.process_message(payload)
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

                # Don't raise for rate limiting - log and continue
                if error_code == 4:  # Rate limit error
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


@router.get("/facebook/messenger")
async def facebook_webhook_verify(request: Request) -> JSONResponse:
    """Verify Facebook webhook during setup.

    Facebook sends a GET request with hub.challenge and hub.verify_token
    to verify webhook ownership.
    """
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    # Verify token matches configured token
    verify_token = settings()["FACEBOOK_WEBHOOK_VERIFY_TOKEN"]
    if token == verify_token and mode == "subscribe":
        return JSONResponse(content={"hub.challenge": challenge})
    else:
        raise HTTPException(status_code=403, detail="Webhook verification failed")
