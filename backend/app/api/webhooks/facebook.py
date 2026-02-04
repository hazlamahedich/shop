"""Facebook webhook endpoint.

Handles incoming Messenger webhooks with signature verification.
"""

from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime
from typing import Optional

import structlog
from fastapi import APIRouter, Request, Response, Header, HTTPException, BackgroundTasks, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verify_webhook_signature
from app.core.errors import APIError, ErrorCode
from app.core.config import settings
from app.services.facebook import FacebookService


router = APIRouter()
logger = structlog.get_logger(__name__)


async def enqueue_failed_webhook(webhook_data: dict, error: str, page_id: str) -> None:
    """Queue failed webhook for retry (3 attempts with exponential backoff).

    Implements Redis Dead Letter Queue pattern per architecture.md.

    Args:
        webhook_data: Original webhook payload
        error: Error message
        page_id: Facebook Page ID for merchant lookup
    """
    try:
        import redis
        redis_url = os.getenv("REDIS_URL")
        if not redis_url:
            logger.warning("redis_not_configured_dlq_skipped")
            return

        redis_client = redis.from_url(redis_url, decode_responses=True)

        retry_data = {
            "webhook_data": webhook_data,
            "error": error,
            "page_id": page_id,
            "attempts": 0,
            "timestamp": datetime.utcnow().isoformat()
        }

        redis_client.rpush("webhook:dlq:facebook", json.dumps(retry_data))
        logger.info("webhook_queued_dlq", page_id=page_id)
    except Exception as e:
        logger.error("dlq_enqueue_failed", error=str(e))


@router.get("/facebook")
async def facebook_webhook_verify(
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token")
) -> Response:
    """Verify Facebook webhook subscription.

    Facebook calls this endpoint when setting up webhook.
    Must return the challenge token to verify ownership.

    Args:
        hub_mode: Hub mode (should be "subscribe")
        hub_verify_token: Verify token
        hub_challenge: Challenge string to echo back

    Returns:
        Plain text response with challenge or 403 error
    """
    config = settings()
    expected_token = config.get("FACEBOOK_WEBHOOK_VERIFY_TOKEN")

    if not expected_token:
        raise HTTPException(
            status_code=500,
            detail="FACEBOOK_WEBHOOK_VERIFY_TOKEN not configured"
        )

    if hub_mode == "subscribe" and hub_verify_token == expected_token:
        return Response(content=hub_challenge, media_type="text/plain")

    raise HTTPException(status_code=403, detail="Webhook verification failed")


@router.post("/facebook")
async def facebook_webhook_receive(
    request: Request,
    background_tasks: BackgroundTasks,
    x_hub_signature_256: Optional[str] = Header(None, alias="X-Hub-Signature-256"),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Receive Facebook Messenger webhook.

    Processes incoming messages from Facebook Messenger.
    Verifies webhook signature before processing.

    Args:
        request: FastAPI request object
        background_tasks: FastAPI background tasks
        x_hub_signature_256: X-Hub-Signature-256 header for verification
        db: Database session

    Returns:
        Acknowledgment response

    Raises:
        HTTPException: If signature verification fails
    """
    request_id = str(hash(datetime.utcnow().timestamp()))
    log = logger.bind(request_id=request_id)

    # Read raw payload for signature verification
    raw_payload = await request.body()

    # Verify webhook signature
    app_secret = settings().get("FACEBOOK_APP_SECRET")
    if not app_secret:
        log.error("facebook_app_secret_not_configured")
        raise HTTPException(
            status_code=500,
            detail="FACEBOOK_APP_SECRET not configured"
        )

    if not verify_webhook_signature(raw_payload, x_hub_signature_256, app_secret):
        log.warning("invalid_webhook_signature")
        raise HTTPException(status_code=403, detail="Invalid webhook signature")

    # Parse webhook payload
    try:
        payload = json.loads(raw_payload.decode())
    except json.JSONDecodeError:
        log.error("invalid_webhook_json")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # Process webhook asynchronously in background (don't block response)
    background_tasks.add_task(process_webhook_background, payload, db, request_id, log)

    # Acknowledge receipt within 1 second
    return {"status": "ok"}


async def process_webhook_background(
    payload: dict,
    db: AsyncSession,
    request_id: str,
    log: structlog.BoundLogger
) -> None:
    """Process webhook in background task.

    Args:
        payload: Webhook payload
        db: Database session
        request_id: Request ID for logging
        log: Bound logger
    """
    try:
        await process_facebook_webhook(payload, db)
        log.info("webhook_processed_success")
    except Exception as e:
        log.error("webhook_processing_failed", error=str(e), exc_info=True)

        # Enqueue to DLQ for retry
        page_id = payload.get("entry", [{}])[0].get("id", "")
        await enqueue_failed_webhook(payload, str(e), page_id)


async def process_facebook_webhook(payload: dict, db: AsyncSession) -> None:
    """Process Facebook webhook payload.

    Extracts messages and stores in database.
    Handles both text messages and postbacks.

    Args:
        payload: Webhook payload from Facebook
        db: Database session
    """
    # Check if this is a message or standby event
    if payload.get("object") != "page":
        return

    # Get merchant_id from page_id
    # In production, query by page_id to find merchant
    entry = payload.get("entry", [])
    if not entry:
        return

    for entry_item in entry:
        # Get messaging events
        messaging = entry_item.get("messaging", [])
        if not messaging:
            continue

        for event in messaging:
            await process_messaging_event(event, db, logger.bind(page_id=entry_item.get("id")))


async def process_messaging_event(event: dict, db: AsyncSession, log: structlog.BoundLogger) -> None:
    """Process a single messaging event.

    Args:
        event: Messaging event from Facebook
        db: Database session
        log: Bound logger
    """
    # Get sender and recipient IDs
    sender_id = event.get("sender", {}).get("id")
    recipient_id = event.get("recipient", {}).get("id")

    if not sender_id:
        return

    # Find merchant by page_id (recipient_id)
    from sqlalchemy import select
    from app.models.facebook_integration import FacebookIntegration

    result = await db.execute(
        select(FacebookIntegration).where(
            FacebookIntegration.page_id == recipient_id
        )
    )
    integration = result.scalars().first()

    if not integration:
        log.warning("merchant_not_found_for_page", page_id=recipient_id)
        return

    merchant_id = integration.merchant_id

    # Create or update conversation
    service = FacebookService(db, is_testing=settings()["IS_TESTING"])
    conversation = await service.create_or_update_conversation(
        merchant_id=merchant_id,
        platform="facebook",
        sender_id=sender_id
    )

    # Extract message content
    message = event.get("message", {})
    postback = event.get("postback", {})

    if message:
        # Handle message
        await process_message(message, conversation.id, "customer", service, sender_id)
    elif postback:
        # Handle postback
        await process_postback(postback, conversation.id, "customer", service)


async def process_message(
    message: dict,
    conversation_id: int,
    sender: str,
    service: FacebookService,
    sender_id: str = None,
) -> None:
    """Process a message event.

    Args:
        message: Message object from Facebook
        conversation_id: Conversation ID
        sender: Message sender (customer/bot)
        service: Facebook service
        sender_id: Platform sender ID for deletion requests
    """
    # Check for text message
    text = message.get("text")
    if text:
        # Check for data deletion commands (GDPR/CCPA compliance)
        deletion_commands = [
            "forget my preferences",
            "delete my data",
            "delete my information",
            "forget me",
        ]
        text_lower = text.strip().lower()

        if text_lower in deletion_commands:
            # Store the message first
            await service.store_message(
                conversation_id=conversation_id,
                sender=sender,
                content=text,
                message_type="text",
            )
            # Trigger data deletion flow
            await handle_data_deletion_request(sender_id, "facebook", service)
            return

        await service.store_message(
            conversation_id=conversation_id,
            sender=sender,
            content=text,
            message_type="text",
        )
        return

    # Check for attachment
    attachments = message.get("attachments", [])
    if attachments:
        attachment = attachments[0]
        attachment_type = attachment.get("type")
        payload_data = attachment.get("payload", {})

        if attachment_type == "image":
            url = payload_data.get("url")
            await service.store_message(
                conversation_id=conversation_id,
                sender=sender,
                content="Image",
                message_type="attachment",
                message_metadata={
                    "attachment_type": "image",
                    "attachment_url": url,
                }
            )
        elif attachment_type == "audio":
            url = payload_data.get("url")
            await service.store_message(
                conversation_id=conversation_id,
                sender=sender,
                content="Audio",
                message_type="attachment",
                message_metadata={
                    "attachment_type": "audio",
                    "attachment_url": url,
                }
            )


async def handle_data_deletion_request(
    customer_id: str,
    platform: str,
    facebook_service: FacebookService,
) -> None:
    """Handle data deletion request from messaging platform.

    Creates deletion request and sends confirmation message.

    Args:
        customer_id: Platform customer ID
        platform: Platform name
        facebook_service: Facebook service instance
    """
    import asyncio
    from app.services.data_deletion import DataDeletionService
    from app.core.database import async_session

    # Create deletion request
    async with async_session() as db:
        try:
            service = DataDeletionService(db)
            request = await service.request_deletion(customer_id, platform)

            # Start background processing
            asyncio.create_task(
                process_deletion_background(request.id)
            )

            logger.info(
                "data_deletion_requested_via_messaging",
                customer_id=customer_id,
                platform=platform,
                request_id=request.id,
            )

            # TODO: Send confirmation message to user via Facebook Send API
            # This would require implementing the send_message functionality

        except Exception as e:
            logger.error(
                "data_deletion_request_failed",
                customer_id=customer_id,
                error=str(e),
            )


async def process_deletion_background(request_id: int) -> None:
    """Background task to process deletion request from messaging.

    Args:
        request_id: Deletion request ID
    """
    from app.services.data_deletion import DataDeletionService
    from app.core.database import async_session

    async with async_session() as db:
        try:
            service = DataDeletionService(db)
            deleted = await service.process_deletion(request_id)

            logger.info(
                "messaging_deletion_completed",
                request_id=request_id,
                deleted_items=deleted,
            )

            # TODO: Send completion notification to user

        except Exception as e:
            logger.error(
                "messaging_deletion_failed",
                request_id=request_id,
                error=str(e),
            )


async def process_postback(
    postback: dict,
    conversation_id: int,
    sender: str,
    service: FacebookService
) -> None:
    """Process a postback event.

    Args:
        postback: Postback object from Facebook
        conversation_id: Conversation ID
        sender: Message sender (customer/bot)
        service: Facebook service
    """
    payload = postback.get("payload", "")
    await service.store_message(
        conversation_id=conversation_id,
        sender=sender,
        content=payload,
        message_type="postback",
        message_metadata={"postback_payload": payload}
    )
