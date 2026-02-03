"""Facebook integration API endpoints.

Handles OAuth flow, connection status, and webhook management.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address
from pydantic import ValidationError
import structlog

from app.core.database import get_db
from app.core.errors import APIError, ErrorCode
from app.core.config import settings
from app.core.security import validate_oauth_state
from app.schemas.integrations import (
    MinimalEnvelope,
    MetaData,
    FacebookAuthorizeResponse,
    FacebookCallbackResponse,
    FacebookStatusResponse,
    FacebookDisconnectResponse,
    WebhookTestResponse,
    WebhookResubscribeResponse,
)
from app.services.facebook import (
    FacebookService,
    get_facebook_service,
)
from app.services.facebook import REQUIRED_SCOPES


# Rate limiter for OAuth endpoints (1 request per 10 seconds)
limiter = Limiter(key_func=get_remote_address)
router = APIRouter()

# Structlog configuration
logger = structlog.get_logger(__name__)


def create_response(data: dict) -> dict:
    """Create standard API response envelope.

    Args:
        data: Response data

    Returns:
        Dict with data and meta fields
    """
    return {
        "data": data,
        "meta": {
            "requestId": str(uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
        }
    }


# ==================== OAuth Endpoints ====================


@router.get("/integrations/facebook/authorize", response_model=MinimalEnvelope)
@limiter.limit("1/10 second")  # Rate limit OAuth initiation
async def facebook_authorize(
    merchant_id: int,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """Initiate Facebook OAuth flow.

    Generates OAuth URL with state parameter for CSRF protection.
    Frontend should open this URL in a popup window.

    Args:
        merchant_id: Merchant ID initiating OAuth
        db: Database session

    Returns:
        OAuth URL and state token

    Raises:
        APIError: If configuration is missing
    """
    try:
        service = await get_facebook_service(db)
        auth_url, state = await service.generate_oauth_url(merchant_id)

        response_data = {
            "authUrl": auth_url,
            "state": state,
        }

        return JSONResponse(content=create_response(response_data))

    except APIError as e:
        raise HTTPException(status_code=400, detail=e.to_dict())


@router.get("/integrations/facebook/callback", response_model=MinimalEnvelope)
async def facebook_callback(
    code: str,
    state: str,
    merchant_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """Handle Facebook OAuth callback.

    Exchanges authorization code for access token and verifies page access.
    Creates Facebook integration record on success.

    Args:
        code: Authorization code from Facebook
        state: State parameter for CSRF validation
        merchant_id: Merchant ID from session
        request: FastAPI request for logging
        db: Database session

    Returns:
        Page connection details

    Raises:
        APIError: If OAuth flow fails
    """
    request_id = str(uuid4())
    log = logger.bind(request_id=request_id, merchant_id=merchant_id)

    try:
        # Validate state from session (CSRF protection)
        expected_state = validate_oauth_state(state)
        if not expected_state:
            log.warning("oauth_state_mismatch", state=state)
            raise APIError(
                ErrorCode.FACEBOOK_OAUTH_STATE_MISMATCH,
                "OAuth state mismatch - possible CSRF attack"
            )

        service = await get_facebook_service(db)

        # Exchange code for short-lived token
        token_response = await service.exchange_code_for_token(
            code=code,
            state=state,
            expected_state=expected_state
        )
        short_lived_token = token_response["access_token"]

        # Exchange for long-lived token (60 days)
        long_lived_token = await service.get_long_lived_token(short_lived_token)

        # Verify page access and get page details
        page_details = await service.verify_page_access(long_lived_token)

        # Create Facebook integration record
        integration = await service.create_facebook_integration(
            merchant_id=merchant_id,
            page_id=page_details["id"],
            page_name=page_details["name"],
            page_picture_url=page_details["picture"]["data"]["url"],
            access_token=long_lived_token,
            scopes=REQUIRED_SCOPES,
        )

        response_data = {
            "pageId": integration.page_id,
            "pageName": integration.page_name,
            "pagePictureUrl": integration.page_picture_url,
            "connectedAt": integration.connected_at.isoformat(),
        }

        log.info("facebook_connection_success", page_id=integration.page_id)
        return JSONResponse(content=create_response(response_data))

    except APIError as e:
        log.error("facebook_callback_failed", error_code=e.code, message=e.message)
        raise HTTPException(status_code=400, detail=e.to_dict())


@router.get("/integrations/facebook/status", response_model=MinimalEnvelope)
async def facebook_status(
    merchant_id: int,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """Get Facebook connection status for merchant.

    Args:
        merchant_id: Merchant ID to check
        db: Database session

    Returns:
        Connection status with page details if connected
    """
    try:
        service = await get_facebook_service(db)
        integration = await service.get_facebook_integration(merchant_id)

        if not integration:
            response_data = {
                "connected": False,
            }
        else:
            response_data = {
                "connected": True,
                "pageId": integration.page_id,
                "pageName": integration.page_name,
                "pagePictureUrl": integration.page_picture_url,
                "connectedAt": integration.connected_at.isoformat(),
                "webhookVerified": integration.webhook_verified,
            }

        return JSONResponse(content=create_response(response_data))

    except APIError as e:
        raise HTTPException(status_code=400, detail=e.to_dict())


@router.delete("/integrations/facebook/disconnect", response_model=MinimalEnvelope)
async def facebook_disconnect(
    merchant_id: int,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """Disconnect Facebook integration for merchant.

    Args:
        merchant_id: Merchant ID to disconnect
        db: Database session

    Returns:
        Disconnection confirmation

    Raises:
        APIError: If Facebook not connected
    """
    try:
        service = await get_facebook_service(db)
        await service.disconnect_facebook(merchant_id)

        response_data = {
            "disconnected": True,
        }

        return JSONResponse(content=create_response(response_data))

    except APIError as e:
        raise HTTPException(status_code=400, detail=e.to_dict())


# ==================== Webhook Testing Endpoints ====================


@router.post("/integrations/facebook/test-webhook", response_model=MinimalEnvelope)
async def test_facebook_webhook(
    merchant_id: int,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """Test Facebook webhook connection.

    Sends a test message to verify webhook is working.

    Args:
        merchant_id: Merchant ID to test
        db: Database session

    Returns:
        Test result with status message

    Raises:
        APIError: If webhook test fails
    """
    try:
        service = await get_facebook_service(db)
        integration = await service.get_facebook_integration(merchant_id)

        if not integration:
            raise APIError(
                ErrorCode.FACEBOOK_NOT_CONNECTED,
                "Facebook Page not connected - cannot test webhook"
            )

        # Check webhook verification status
        webhook_status = "connected" if integration.webhook_verified else "not-connected"

        response_data = {
            "success": integration.webhook_verified,
            "message": "Webhook is verified and working" if integration.webhook_verified else "Webhook not verified - please complete webhook setup",
            "webhookStatus": webhook_status,
        }

        return JSONResponse(content=create_response(response_data))

    except APIError as e:
        raise HTTPException(status_code=400, detail=e.to_dict())


@router.post("/integrations/facebook/resubscribe-webhook", response_model=MinimalEnvelope)
async def resubscribe_facebook_webhook(
    merchant_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """Re-subscribe to Facebook webhook.

    Re-establishes webhook subscription if disconnected.

    Args:
        merchant_id: Merchant ID to resubscribe
        request: FastAPI request for logging
        db: Database session

    Returns:
        Resubscription result

    Raises:
        APIError: If resubscription fails
    """
    request_id = str(uuid4())
    log = logger.bind(request_id=request_id, merchant_id=merchant_id)

    try:
        service = await get_facebook_service(db)
        integration = await service.get_facebook_integration(merchant_id)

        if not integration:
            log.warning("resubscribe_failed_not_connected")
            raise APIError(
                ErrorCode.FACEBOOK_NOT_CONNECTED,
                "Facebook Page not connected - cannot resubscribe webhook"
            )

        # Get page access token and call Graph API to resubscribe
        success = await service.resubscribe_webhook(integration)

        if success:
            integration.webhook_verified = True
            await db.commit()

            log.info("webhook_resubscribed_success", page_id=integration.page_id)
            response_data = {
                "success": True,
                "message": "Webhook re-subscribed successfully",
            }
        else:
            log.error("webhook_resubscribe_failed", page_id=integration.page_id)
            raise APIError(
                ErrorCode.FACEBOOK_WEBHOOK_VERIFY_FAILED,
                "Failed to re-subscribe webhook with Facebook"
            )

        return JSONResponse(content=create_response(response_data))

    except APIError as e:
        log.error("resubscribe_webhook_failed", error_code=e.code, message=e.message)
        raise HTTPException(status_code=400, detail=e.to_dict())
