"""Webhook Verification API endpoints.

Provides webhook verification, testing, and re-subscription endpoints for merchants.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.errors import APIError, ErrorCode
from app.schemas.webhook_verification import (
    WebhookStatusResponse,
    WebhookTestResponse,
    WebhookResubscribeResponse,
    MinimalEnvelope,
    MetaData,
)
from app.services.webhook_verification import WebhookVerificationService


router = APIRouter()


def create_meta(request_id: str) -> MetaData:
    """Create metadata for API response.

    Args:
        request_id: Request ID

    Returns:
        MetaData object
    """
    return MetaData(
        request_id=request_id,
        timestamp=datetime.utcnow().isoformat(),
    )


@router.get(
    "/webhooks/verification/status",
    response_model=MinimalEnvelope[WebhookStatusResponse],
    tags=["webhooks"],
)
async def get_webhook_verification_status(
    merchant_id: int,
    db: AsyncSession = Depends(get_db),
) -> MinimalEnvelope[WebhookStatusResponse]:
    """Get webhook connection status for all platforms.

    Returns comprehensive status including:
    - Facebook webhook connection status
    - Shopify webhook connection status
    - Overall verification status
    - Whether bot is ready to go live

    Args:
        merchant_id: Merchant ID from query parameter
        db: Database session

    Returns:
        Webhook status for all platforms

    Note: Authentication/Tenant isolation is not implemented yet.
    TODO: Implement proper authentication with Depends(get_current_merchant)
    """
    request_id = str(uuid4())

    try:
        service = WebhookVerificationService(merchant_id=merchant_id, db=db)
        status_data = await service.get_verification_status()

        return MinimalEnvelope(
            data=status_data,
            meta=create_meta(request_id),
        )
    except APIError as e:
        raise HTTPException(
            status_code=400,
            detail=e.to_dict(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": int(ErrorCode.UNKNOWN_ERROR),
                "message": str(e),
            },
        )


@router.post(
    "/webhooks/verification/test-facebook",
    response_model=MinimalEnvelope[WebhookTestResponse],
    tags=["webhooks"],
)
async def test_facebook_webhook(
    merchant_id: int,
    db: AsyncSession = Depends(get_db),
) -> MinimalEnvelope[WebhookTestResponse]:
    """Send test message via Facebook Messenger.

    Verifies Facebook webhook is working by sending a test message.
    Returns test results with diagnostic information on failure.

    Args:
        merchant_id: Merchant ID from query parameter
        db: Database session

    Returns:
        Test result with status and details

    Note: Authentication/Tenant isolation is not implemented yet.
    TODO: Implement proper authentication with Depends(get_current_merchant)
    """
    request_id = str(uuid4())

    try:
        service = WebhookVerificationService(merchant_id=merchant_id, db=db)
        test_result = await service.test_facebook_webhook()

        return MinimalEnvelope(
            data=test_result,
            meta=create_meta(request_id),
        )
    except APIError as e:
        # Include troubleshooting steps in error response
        service = WebhookVerificationService(merchant_id=merchant_id, db=db)
        diagnosis = await service.diagnose_webhook_failure(
            "facebook", str(e.message)
        )

        raise HTTPException(
            status_code=400,
            detail={
                **e.to_dict(),
                "troubleshooting": diagnosis["troubleshootingSteps"],
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": int(ErrorCode.UNKNOWN_ERROR),
                "message": str(e),
            },
        )


@router.post(
    "/webhooks/verification/test-shopify",
    response_model=MinimalEnvelope[WebhookTestResponse],
    tags=["webhooks"],
)
async def test_shopify_webhook(
    merchant_id: int,
    db: AsyncSession = Depends(get_db),
) -> MinimalEnvelope[WebhookTestResponse]:
    """Trigger test Shopify webhook.

    Verifies Shopify webhook subscription is active and working.
    Returns test results with diagnostic information on failure.

    Args:
        merchant_id: Merchant ID from query parameter
        db: Database session

    Returns:
        Test result with status and details

    Note: Authentication/Tenant isolation is not implemented yet.
    TODO: Implement proper authentication with Depends(get_current_merchant)
    """
    request_id = str(uuid4())

    try:
        service = WebhookVerificationService(merchant_id=merchant_id, db=db)
        test_result = await service.test_shopify_webhook()

        return MinimalEnvelope(
            data=test_result,
            meta=create_meta(request_id),
        )
    except APIError as e:
        # Include troubleshooting steps in error response
        service = WebhookVerificationService(merchant_id=merchant_id, db=db)
        diagnosis = await service.diagnose_webhook_failure(
            "shopify", str(e.message)
        )

        raise HTTPException(
            status_code=400,
            detail={
                **e.to_dict(),
                "troubleshooting": diagnosis["troubleshootingSteps"],
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": int(ErrorCode.UNKNOWN_ERROR),
                "message": str(e),
            },
        )


@router.post(
    "/webhooks/verification/resubscribe-facebook",
    response_model=MinimalEnvelope[WebhookResubscribeResponse],
    tags=["webhooks"],
)
async def resubscribe_facebook_webhook(
    merchant_id: int,
    db: AsyncSession = Depends(get_db),
) -> MinimalEnvelope[WebhookResubscribeResponse]:
    """Re-subscribe to Facebook Messenger webhooks.

    Re-establishes webhook subscription via Facebook Graph API.
    Useful if webhook subscription was lost or needs renewal.

    Args:
        merchant_id: Merchant ID from query parameter
        db: Database session

    Returns:
        Re-subscription result with status

    Note: Authentication/Tenant isolation is not implemented yet.
    TODO: Implement proper authentication with Depends(get_current_merchant)
    """
    request_id = str(uuid4())

    try:
        service = WebhookVerificationService(merchant_id=merchant_id, db=db)
        result = await service.resubscribe_facebook_webhook()

        return MinimalEnvelope(
            data=result,
            meta=create_meta(request_id),
        )
    except APIError as e:
        raise HTTPException(
            status_code=400,
            detail=e.to_dict(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": int(ErrorCode.UNKNOWN_ERROR),
                "message": str(e),
            },
        )


@router.post(
    "/webhooks/verification/resubscribe-shopify",
    response_model=MinimalEnvelope[WebhookResubscribeResponse],
    tags=["webhooks"],
)
async def resubscribe_shopify_webhook(
    merchant_id: int,
    db: AsyncSession = Depends(get_db),
) -> MinimalEnvelope[WebhookResubscribeResponse]:
    """Re-subscribe to Shopify webhooks.

    Re-establishes webhook subscriptions via Shopify Admin API.
    Useful if webhook subscriptions were lost or need renewal.

    Args:
        merchant_id: Merchant ID from query parameter
        db: Database session

    Returns:
        Re-subscription result with status

    Note: Authentication/Tenant isolation is not implemented yet.
    TODO: Implement proper authentication with Depends(get_current_merchant)
    """
    request_id = str(uuid4())

    try:
        service = WebhookVerificationService(merchant_id=merchant_id, db=db)
        result = await service.resubscribe_shopify_webhook()

        return MinimalEnvelope(
            data=result,
            meta=create_meta(request_id),
        )
    except APIError as e:
        raise HTTPException(
            status_code=400,
            detail=e.to_dict(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": int(ErrorCode.UNKNOWN_ERROR),
                "message": str(e),
            },
        )
