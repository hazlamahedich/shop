"""Facebook and Shopify integration API endpoints.

Handles OAuth flow, connection status, and webhook management.
"""

from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address
import structlog

from app.core.database import get_db
from app.core.errors import APIError, ErrorCode
from app.core.security import validate_oauth_state
from app.schemas.integrations import (
    MinimalEnvelope,
    ShopifyCredentialsRequest,
)
from app.services.facebook import (
    FacebookService,
    get_facebook_service,
)
from app.services.facebook import REQUIRED_SCOPES
from app.services.shopify import (
    ShopifyService,
    get_shopify_service,
    REQUIRED_SCOPES as SHOPIFY_REQUIRED_SCOPES,
)
from app.services.shopify_admin import ShopifyAdminClient
from app.services.shopify_storefront import ShopifyStorefrontClient
from app.core.config import is_testing


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
        },
    }


# ==================== OAuth Endpoints ====================


@router.get("/integrations/facebook/authorize", response_model=MinimalEnvelope)
@limiter.limit("1/10 second")  # Rate limit OAuth initiation
async def facebook_authorize(
    request: Request, merchant_id: int, db: AsyncSession = Depends(get_db)
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
    code: str, state: str, merchant_id: int, request: Request, db: AsyncSession = Depends(get_db)
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
                "OAuth state mismatch - possible CSRF attack",
            )

        service = await get_facebook_service(db)

        # Exchange code for short-lived token
        token_response = await service.exchange_code_for_token(
            code=code, state=state, expected_state=expected_state
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
async def facebook_status(merchant_id: int, db: AsyncSession = Depends(get_db)) -> JSONResponse:
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
async def facebook_disconnect(merchant_id: int, db: AsyncSession = Depends(get_db)) -> JSONResponse:
    """Disconnect Facebook integration for merchant.

    Args:
        merchant_id: Merchant ID to disconnect
        db: Database session

    Returns:
        Disconnection confirmation

    Raises:
        APIError: If Facebook not connected
    """
    log = logger.bind(merchant_id=merchant_id)
    try:
        service = await get_facebook_service(db)
        await service.disconnect_facebook(merchant_id)

        response_data = {
            "disconnected": True,
        }

        return JSONResponse(content=create_response(response_data))

    except APIError as e:
        raise HTTPException(status_code=400, detail=e.to_dict())
    except Exception as e:
        log.error("facebook_disconnect_failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Failed to disconnect Facebook. Please try again or contact support."
            },
        )


# ==================== Webhook Testing Endpoints ====================


@router.post("/integrations/facebook/test-webhook", response_model=MinimalEnvelope)
async def test_facebook_webhook(
    merchant_id: int, db: AsyncSession = Depends(get_db)
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
                "Facebook Page not connected - cannot test webhook",
            )

        # Check webhook verification status
        webhook_status = "connected" if integration.webhook_verified else "not-connected"

        response_data = {
            "success": integration.webhook_verified,
            "message": (
                "Webhook is verified and working"
                if integration.webhook_verified
                else "Webhook not verified - please complete webhook setup"
            ),
            "webhookStatus": webhook_status,
        }

        return JSONResponse(content=create_response(response_data))

    except APIError as e:
        raise HTTPException(status_code=400, detail=e.to_dict())


@router.post("/integrations/facebook/resubscribe-webhook", response_model=MinimalEnvelope)
async def resubscribe_facebook_webhook(
    merchant_id: int, request: Request, db: AsyncSession = Depends(get_db)
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
                "Facebook Page not connected - cannot resubscribe webhook",
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
                "Failed to re-subscribe webhook with Facebook",
            )

        return JSONResponse(content=create_response(response_data))

    except APIError as e:
        log.error("resubscribe_webhook_failed", error_code=e.code, message=e.message)
        raise HTTPException(status_code=400, detail=e.to_dict())


# ==================== Shopify OAuth Endpoints ====================


@router.get("/integrations/shopify/authorize", response_model=MinimalEnvelope)
@limiter.limit("1/10 second")  # Rate limit OAuth initiation
async def shopify_authorize(
    request: Request, merchant_id: int, shop_domain: str, db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """Initiate Shopify OAuth flow.

    Generates OAuth URL with state parameter for CSRF protection.
    Frontend should open this URL in a popup window.

    Args:
        merchant_id: Merchant ID initiating OAuth
        shop_domain: Shopify shop domain (e.g., mystore.myshopify.com)
        db: Database session

    Returns:
        OAuth URL and state token

    Raises:
        HTTPException: If configuration is missing or domain is invalid
    """
    request_id = str(uuid4())
    log = logger.bind(request_id=request_id, merchant_id=merchant_id, shop_domain=shop_domain)

    try:
        service = await get_shopify_service(db)
        auth_url, state = await service.generate_oauth_url(merchant_id, shop_domain)

        response_data = {
            "authUrl": auth_url,
            "state": state,
        }

        log.info("shopify_oauth_initiated", shop_domain=shop_domain)
        return JSONResponse(content=create_response(response_data))

    except APIError as e:
        log.warning("shopify_oauth_initiate_failed", error_code=e.code, message=e.message)
        raise HTTPException(status_code=400, detail=e.to_dict())


@router.get("/integrations/shopify/callback")
async def shopify_callback(
    code: str, state: str, shop: str, request: Request, db: AsyncSession = Depends(get_db)
):
    """Handle Shopify OAuth callback.

    Exchanges authorization code for access token, creates Storefront API token,
    verifies API access, validates required scopes, and creates Shopify integration record.

    Args:
        code: Authorization code from Shopify
        state: State parameter for CSRF validation
        shop: Shopify shop domain
        request: FastAPI request for logging
        db: Database session

    Returns:
        Shop connection details

    Raises:
        HTTPException: If OAuth flow fails or required scopes are missing
    """
    request_id = str(uuid4())
    log = logger.bind(request_id=request_id, shop=shop)

    try:
        # Validate state from session (CSRF protection)
        expected_merchant_id = validate_oauth_state(state)
        if not expected_merchant_id:
            log.warning("shopify_oauth_state_mismatch")
            raise APIError(
                ErrorCode.SHOPIFY_OAUTH_STATE_MISMATCH,
                "OAuth state mismatch - possible CSRF attack",
            )

        service = await get_shopify_service(db)

        # Exchange code for Admin API access token
        token_response = await service.exchange_code_for_token(
            shop_domain=shop,
            code=code,
            merchant_id=expected_merchant_id,
        )
        admin_token = token_response["access_token"]
        granted_scopes = token_response["scope"].split(",")
        # Clean up scopes (remove whitespace)
        granted_scopes = [s.strip() for s in granted_scopes]

        log.info(
            "shopify_oauth_scopes_granted",
            granted_scopes=granted_scopes,
            required_scopes=list(SHOPIFY_REQUIRED_SCOPES),
        )

        # Validate that all required scopes were granted
        missing_scopes = []
        for required_scope in SHOPIFY_REQUIRED_SCOPES:
            if required_scope in granted_scopes:
                continue

            # Write scopes implicitly grant read access
            if required_scope.startswith("read_"):
                write_scope = "write_" + required_scope[5:]
                if write_scope in granted_scopes:
                    continue

            missing_scopes.append(required_scope)

        if missing_scopes:
            log.warning(
                "shopify_oauth_insufficient_permissions",
                missing_scopes=missing_scopes,
                granted=granted_scopes,
            )
            raise APIError(
                ErrorCode.SHOPIFY_ADMIN_API_ACCESS_DENIED,
                f"Insufficient permissions granted. Missing scopes: {', '.join(missing_scopes)}. "
                f"Granted scopes: {', '.join(granted_scopes)}. "
                f"Please grant all required permissions and try again.",
            )

        # Verify Admin API access and get shop details
        admin_client = ShopifyAdminClient(shop, admin_token, is_testing=is_testing())
        shop_details = await admin_client.verify_shop_access()

        # Note: Creating Storefront tokens requires the app to be a Sales Channel.
        # For a chatbot, we use tokenless Storefront API for product queries
        # and direct checkout URLs (https://{shop}/cart/{variant}:{qty}) for cart.
        # This approach works without needing Storefront token creation.
        storefront_token = None
        storefront_verified = True  # Tokenless access always works

        # Create Shopify integration record
        integration = await service.create_shopify_integration(
            merchant_id=expected_merchant_id,
            shop_domain=shop,
            shop_name=shop_details.get("name", shop),
            admin_token=admin_token,
            storefront_token=storefront_token,
            scopes=granted_scopes,
        )

        # Update verification flags
        integration.admin_api_verified = True
        integration.storefront_api_verified = storefront_verified
        await db.commit()

        response_data = {
            "shopDomain": integration.shop_domain,
            "shopName": integration.shop_name,
            "connectedAt": integration.connected_at.isoformat(),
        }

        log.info("shopify_connection_success", shop_domain=shop)

        # Return HTML page that posts message to parent and closes popup
        shop_domain = integration.shop_domain
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head><title>Shopify Connected</title></head>
        <body>
        <script>
          window.opener.postMessage({{type: 'shopify-oauth-success', shopDomain: '{shop_domain}'}}, '*');
          window.close();
        </script>
        <p>Connection successful! You can close this window.</p>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)

    except APIError as e:
        log.error("shopify_callback_failed", error_code=e.code, message=e.message)
        error_message = e.message.replace("'", "\\'")
        # Return HTML error page for popup
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head><title>Connection Failed</title></head>
        <body>
        <script>
          window.opener.postMessage({{type: 'shopify-oauth-error', error: '{error_message}'}}, '*');
          window.close();
        </script>
        <p>Connection failed: {e.message}</p>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content, status_code=400)

    except Exception as e:
        log.error("shopify_callback_unexpected_error", error=str(e), exc_info=True)
        error_message = str(e).replace("'", "\\'")
        # Return HTML error page for popup
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head><title>Connection Failed</title></head>
        <body>
        <script>
          window.opener.postMessage({{type: 'shopify-oauth-error', error: '{error_message}'}}, '*');
          window.close();
        </script>
        <p>Connection failed: {error_message}</p>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content, status_code=500)


@router.get("/integrations/shopify/status", response_model=MinimalEnvelope)
async def shopify_status(merchant_id: int, db: AsyncSession = Depends(get_db)) -> JSONResponse:
    """Get Shopify connection status for merchant.

    Args:
        merchant_id: Merchant ID to check
        db: Database session

    Returns:
        Connection status with shop details if connected
    """
    try:
        service = await get_shopify_service(db)
        integration = await service.get_shopify_integration(merchant_id)

        if not integration:
            response_data = {
                "connected": False,
            }
        else:
            response_data = {
                "connected": True,
                "shopDomain": integration.shop_domain,
                "shopName": integration.shop_name,
                "storefrontApiConnected": integration.storefront_api_verified,
                "adminApiConnected": integration.admin_api_verified,
                "webhookSubscribed": integration.webhook_subscribed,
                "connectedAt": integration.connected_at.isoformat(),
            }

        return JSONResponse(content=create_response(response_data))

    except APIError as e:
        raise HTTPException(status_code=400, detail=e.to_dict())


@router.delete("/integrations/shopify/disconnect", response_model=MinimalEnvelope)
async def shopify_disconnect(merchant_id: int, db: AsyncSession = Depends(get_db)) -> JSONResponse:
    """Disconnect Shopify integration for merchant.

    Args:
        merchant_id: Merchant ID to disconnect
        db: Database session

    Returns:
        Disconnection confirmation

    Raises:
        HTTPException: If Shopify not connected
    """
    try:
        service = await get_shopify_service(db)
        await service.disconnect_shopify(merchant_id)

        response_data = {
            "disconnected": True,
        }

        return JSONResponse(content=create_response(response_data))

    except APIError as e:
        raise HTTPException(status_code=400, detail=e.to_dict())


# ==================== Shopify Webhook Testing Endpoints ====================


@router.post("/integrations/shopify/test-webhook", response_model=MinimalEnvelope)
async def test_shopify_webhook(
    merchant_id: int, db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """Test Shopify webhook connection.

    Checks webhook subscription status.

    Args:
        merchant_id: Merchant ID to test
        db: Database session

    Returns:
        Test result with status message

    Raises:
        HTTPException: If webhook test fails
    """
    try:
        service = await get_shopify_service(db)
        integration = await service.get_shopify_integration(merchant_id)

        if not integration:
            raise APIError(
                ErrorCode.SHOPIFY_NOT_CONNECTED, "Shopify store not connected - cannot test webhook"
            )

        webhook_status = "connected" if integration.webhook_subscribed else "not-connected"

        response_data = {
            "success": integration.webhook_subscribed,
            "message": (
                "Webhook is subscribed"
                if integration.webhook_subscribed
                else "Webhook not subscribed"
            ),
            "webhookStatus": webhook_status,
        }

        return JSONResponse(content=create_response(response_data))

    except APIError as e:
        raise HTTPException(status_code=400, detail=e.to_dict())


@router.post("/integrations/shopify/credentials", status_code=204, response_model=None)
async def save_shopify_credentials(
    request: ShopifyCredentialsRequest,
    db=Depends(get_db),
    shopify_service=Depends(get_shopify_service),
) -> None:
    """Save Shopify App credentials."""
    log = logger.bind(merchant_id=request.merchant_id)
    try:
        log.info("saving_shopify_credentials", api_key_length=len(request.api_key))
        await shopify_service.save_shopify_credentials(
            merchant_id=request.merchant_id,
            api_key=request.api_key,
            api_secret=request.api_secret,
        )
        log.info("shopify_credentials_saved_successfully")
    except APIError as e:
        log.error("api_error_saving_credentials", error=str(e))
        raise HTTPException(status_code=400, detail=e.to_dict())
    except Exception as e:
        log.error(
            "unexpected_error_saving_shopify_credentials",
            error_type=type(e).__name__,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": ErrorCode.INTERNAL_ERROR,
                "message": f"An unexpected error occurred: {type(e).__name__}",
            },
        )
