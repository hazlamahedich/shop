"""Merchant profile API endpoints.

Provides endpoints for managing merchant profile information including:
- Business information (name, description, hours)
- Email address updates with verification
- Profile data retrieval
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import hash_token
from app.core.database import get_db
from app.core.errors import ErrorCode
from app.core.rate_limiter import RateLimiter
from app.models.merchant import Merchant
from app.schemas.base import MetaData, MinimalEnvelope

router = APIRouter(tags=["Merchant Profile"])
logger = structlog.get_logger(__name__)


# Helper Functions


def _create_meta() -> MetaData:
    """Create metadata for API response.

    Returns:
        MetaData object with request_id and timestamp
    """
    return MetaData(
        request_id=str(uuid4()),
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


async def _get_merchant_id(request: Request) -> int:
    """Get merchant ID from request state.

    Args:
        request: FastAPI request

    Returns:
        Merchant ID

    Raises:
        HTTPException: If authentication fails
    """
    merchant_id = getattr(request.state, "merchant_id", None)
    if not merchant_id:
        # Check X-Merchant-Id header in DEBUG mode for easier testing
        from app.core.config import settings

        if settings()["DEBUG"]:
            merchant_id_header = request.headers.get("X-Merchant-Id")
            if merchant_id_header:
                merchant_id = int(merchant_id_header)
            else:
                merchant_id = 1  # Default for dev/test
        else:
            raise HTTPException(
                status_code=401,
                detail={
                    "error_code": ErrorCode.AUTH_FAILED,
                    "message": "Authentication required",
                },
            )
    return merchant_id


# Request/Response Schemas


class BusinessHours(BaseModel):
    """Business hours configuration."""

    monday: str | None = Field(None, description="Monday hours (e.g., '9:00 AM - 5:00 PM')")
    tuesday: str | None = Field(None, description="Tuesday hours")
    wednesday: str | None = Field(None, description="Wednesday hours")
    thursday: str | None = Field(None, description="Thursday hours")
    friday: str | None = Field(None, description="Friday hours")
    saturday: str | None = Field(None, description="Saturday hours")
    sunday: str | None = Field(None, description="Sunday hours")


class ProfileResponse(BaseModel):
    """Merchant profile information."""

    id: int = Field(description="Merchant ID")
    email: str = Field(description="Merchant email")
    business_name: str | None = Field(None, description="Business name")
    business_description: str | None = Field(None, description="Business description")
    business_hours: BusinessHours | None = Field(None, description="Business hours")
    bot_name: str | None = Field(None, description="Bot name")


class ProfileUpdateRequest(BaseModel):
    """Request schema for updating merchant profile."""

    business_name: str | None = Field(None, max_length=100, description="Business name")
    business_description: str | None = Field(
        None, max_length=500, description="Business description"
    )
    business_hours: BusinessHours | None = Field(None, description="Business hours")
    bot_name: str | None = Field(None, max_length=50, description="Bot name")


class EmailChangeRequest(BaseModel):
    """Request schema for changing email address."""

    new_email: EmailStr = Field(..., description="New email address")
    password: str = Field(..., min_length=8, description="Current password for verification")


class EmailChangeResponse(BaseModel):
    """Response schema for email change request."""

    message: str = Field(
        description="Success message",
        example="Verification email sent to new email address",
    )


class EmailVerificationRequest(BaseModel):
    """Request schema for verifying email change."""

    token: str = Field(..., description="Email verification token")


class EmailVerificationResponse(BaseModel):
    """Response schema for email verification."""

    message: str = Field(description="Success message")


# Endpoint Implementations


@router.get(
    "/profile",
    response_model=MinimalEnvelope,
    status_code=200,
)
async def get_profile(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> MinimalEnvelope:
    """Get merchant profile information.

    Args:
        request: FastAPI request with merchant authentication
        db: Database session

    Returns:
        Merchant profile information

    Raises:
        HTTPException: If authentication fails or merchant not found
    """
    merchant_id = await _get_merchant_id(request)

    result = await db.execute(select(Merchant).where(Merchant.id == merchant_id))
    merchant = result.scalars().first()

    if not merchant:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": ErrorCode.MERCHANT_NOT_FOUND,
                "message": "Merchant not found",
            },
        )

    # Build business hours object
    business_hours = None
    if merchant.business_hours_config:
        business_hours = BusinessHours(**merchant.business_hours_config)

    return MinimalEnvelope(
        data=ProfileResponse(
            id=merchant.id,
            email=merchant.email or "",
            business_name=merchant.business_name,
            business_description=merchant.business_description,
            business_hours=business_hours,
            bot_name=merchant.bot_name,
        ),
        meta=_create_meta(),
    )


@router.patch(
    "/profile",
    response_model=MinimalEnvelope,
    status_code=200,
)
async def update_profile(
    request: Request,
    update: ProfileUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> MinimalEnvelope:
    """Update merchant profile information.

    Args:
        request: FastAPI request with merchant authentication
        update: Profile update data
        db: Database session

    Returns:
        Updated profile information

    Raises:
        HTTPException: If authentication fails or merchant not found
    """
    merchant_id = await _get_merchant_id(request)

    result = await db.execute(select(Merchant).where(Merchant.id == merchant_id))
    merchant = result.scalars().first()

    if not merchant:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": ErrorCode.MERCHANT_NOT_FOUND,
                "message": "Merchant not found",
            },
        )

    # Update fields if provided
    if update.business_name is not None:
        merchant.business_name = update.business_name

    if update.business_description is not None:
        merchant.business_description = update.business_description

    if update.business_hours is not None:
        merchant.business_hours_config = update.business_hours.model_dump()

    if update.bot_name is not None:
        merchant.bot_name = update.bot_name

    try:
        await db.commit()
        await db.refresh(merchant)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": ErrorCode.INTERNAL_ERROR,
                "message": "Failed to update profile",
            },
        ) from e

    logger.info(
        "profile_updated",
        merchant_id=merchant_id,
        business_name=update.business_name,
        bot_name=update.bot_name,
    )

    # Build response
    business_hours = None
    if merchant.business_hours_config:
        business_hours = BusinessHours(**merchant.business_hours_config)

    return MinimalEnvelope(
        data=ProfileResponse(
            id=merchant.id,
            email=merchant.email or "",
            business_name=merchant.business_name,
            business_description=merchant.business_description,
            business_hours=business_hours,
            bot_name=merchant.bot_name,
        ),
        meta=_create_meta(),
    )


@router.post(
    "/profile/change-email",
    response_model=MinimalEnvelope,
    status_code=200,
)
async def request_email_change(
    request: Request,
    body: EmailChangeRequest,
    db: AsyncSession = Depends(get_db),
) -> MinimalEnvelope:
    """Request email address change.

    Verifies current password and sends verification token to new email.
    Old email remains active until verification is complete.

    Args:
        request: FastAPI request with merchant authentication
        body: New email and current password
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If authentication fails or password incorrect
    """
    merchant_id = await _get_merchant_id(request)

    # Check rate limit
    RateLimiter.check_auth_rate_limit(
        request,
        key=f"email_change:{merchant_id}",
        max_requests=3,
        window_seconds=3600,  # 1 hour
    )

    result = await db.execute(select(Merchant).where(Merchant.id == merchant_id))
    merchant = result.scalars().first()

    if not merchant:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": ErrorCode.MERCHANT_NOT_FOUND,
                "message": "Merchant not found",
            },
        )

    # Verify current password
    from app.core.auth import verify_password

    if not verify_password(body.password, merchant.password_hash or ""):
        raise HTTPException(
            status_code=401,
            detail={
                "error_code": ErrorCode.AUTH_FAILED,
                "message": "Current password is incorrect",
            },
        )

    # Generate verification token
    import secrets

    verification_token = secrets.token_hex(32)
    token_hash = hash_token(verification_token)

    # Store token in merchant config (temporary)
    config = merchant.config or {}
    config["pending_email"] = body.new_email
    config["email_verification_token"] = token_hash
    config["email_verification_expires"] = (
        datetime.now(timezone.utc) + timedelta(hours=24)
    ).isoformat()
    merchant.config = config

    await db.commit()

    # Send verification email
    try:
        from app.services.email.email_service import send_email

        await send_email(
            to_email=body.new_email,
            subject="Confirm Your Email Change",
            template_name="email_change_verification",
            template_data={
                "business_name": merchant.business_name or "your account",
                "old_email": merchant.email,
                "verification_link": f"{request.url.scheme}://{request.url.netloc}/settings/profile/verify-email?token={verification_token}",
            },
        )
    except Exception as e:
        logger.error(
            "failed_to_send_email_verification",
            merchant_id=merchant_id,
            new_email=body.new_email,
            error=str(e),
        )
        # Don't fail the request if email fails

    logger.info(
        "email_change_requested",
        merchant_id=merchant_id,
        new_email=body.new_email,
    )

    return MinimalEnvelope(
        data=EmailChangeResponse(
            message="Verification email sent to new email address. Please check your inbox and follow the instructions to confirm."
        ),
        meta=_create_meta(),
    )


@router.post(
    "/profile/verify-email",
    response_model=MinimalEnvelope,
    status_code=200,
)
async def verify_email_change(
    request: Request,
    body: EmailVerificationRequest,
    db: AsyncSession = Depends(get_db),
) -> MinimalEnvelope:
    """Verify email change with token.

    Completes the email change process if token is valid.

    Args:
        request: FastAPI request with merchant authentication
        body: Verification token
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If token is invalid or expired
    """
    merchant_id = await _get_merchant_id(request)

    result = await db.execute(select(Merchant).where(Merchant.id == merchant_id))
    merchant = result.scalars().first()

    if not merchant:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": ErrorCode.MERCHANT_NOT_FOUND,
                "message": "Merchant not found",
            },
        )

    config = merchant.config or {}
    pending_email = config.get("pending_email")
    stored_token = config.get("email_verification_token")
    expires_str = config.get("email_verification_expires")

    # Verify token
    if not pending_email or not stored_token:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": ErrorCode.VALIDATION_ERROR,
                "message": "No pending email change",
                "details": "Please request an email change first",
            },
        )

    token_hash = hash_token(body.token)

    if token_hash != stored_token:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": ErrorCode.VALIDATION_ERROR,
                "message": "Invalid verification token",
            },
        )

    # Check expiration
    if expires_str:
        expires_at = datetime.fromisoformat(expires_str)
        if datetime.now(timezone.utc) > expires_at:
            # Clear pending email change
            config.pop("pending_email", None)
            config.pop("email_verification_token", None)
            config.pop("email_verification_expires", None)
            merchant.config = config
            await db.commit()

            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": ErrorCode.VALIDATION_ERROR,
                    "message": "Verification token has expired",
                    "details": "Please request a new email change",
                },
            )

    # Update email
    old_email = merchant.email
    merchant.email = pending_email

    # Clear verification data
    config.pop("pending_email", None)
    config.pop("email_verification_token", None)
    config.pop("email_verification_expires", None)
    merchant.config = config

    await db.commit()

    logger.info(
        "email_changed",
        merchant_id=merchant_id,
        old_email=old_email,
        new_email=pending_email,
    )

    # Send confirmation to both old and new email
    try:
        from app.services.email.email_service import send_email

        # Send to old email
        await send_email(
            to_email=old_email,
            subject="Email Address Changed",
            template_name="email_change_confirmation_old",
            template_data={
                "business_name": merchant.business_name or "your account",
                "new_email": pending_email,
            },
        )

        # Send to new email
        await send_email(
            to_email=pending_email,
            subject="Email Address Successfully Changed",
            template_name="email_change_confirmation_new",
            template_data={
                "business_name": merchant.business_name or "your account",
            },
        )
    except Exception as e:
        logger.error(
            "failed_to_send_email_confirmation",
            merchant_id=merchant_id,
            error=str(e),
        )
        # Don't fail the request if email fails

    return MinimalEnvelope(
        data=EmailVerificationResponse(
            message="Email address successfully updated. Please log in with your new email address."
        ),
        meta=_create_meta(),
    )
