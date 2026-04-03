"""Password Reset API endpoints.

Implements forgot password, token verification, and password reset functionality.
Added as separate module to avoid conflicts with existing auth.py structure.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import hash_password, hash_token, validate_password_requirements
from app.core.config import settings
from app.core.database import get_db
from app.core.errors import ErrorCode
from app.core.rate_limiter import RateLimiter
from app.models.merchant import Merchant
from app.models.password_reset_token import PasswordResetToken
from app.models.session import Session
from app.schemas.base import MetaData, MinimalEnvelope

router = APIRouter(tags=["Password Reset"])
security = HTTPBearer(auto_error=False)

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


# Request/Response Schemas


class ForgotPasswordRequest(BaseModel):
    """Request schema for forgot password."""

    email: EmailStr = Field(..., description="Merchant email address")


class ForgotPasswordResponse(BaseModel):
    """Response schema for forgot password."""

    message: str = Field(
        description="Success message",
        example="If an account exists with this email, a password reset link has been sent.",
    )


class VerifyResetTokenRequest(BaseModel):
    """Request schema for verifying reset token."""

    token: str = Field(..., description="Password reset token")


class VerifyResetTokenResponse(BaseModel):
    """Response schema for verifying reset token."""

    valid: bool = Field(description="Whether token is valid")
    email: str | None = Field(None, description="Email associated with token (only if valid)")


class ResetPasswordRequest(BaseModel):
    """Request schema for resetting password."""

    token: str = Field(..., description="Password reset token")
    new_password: str = Field(
        ...,
        min_length=8,
        description="New password (must be at least 8 characters)",
    )


class ResetPasswordResponse(BaseModel):
    """Response schema for resetting password."""

    message: str = Field(
        description="Success message",
        example="Password has been reset successfully. Please log in with your new password.",
    )


# Endpoint Implementations


@router.post(
    "/forgot-password",
    response_model=MinimalEnvelope,
    status_code=status.HTTP_200_OK,
)
async def forgot_password(
    request: Request,
    body: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> MinimalEnvelope:
    """Initiate password reset flow.

    Generates a secure reset token and emails it to the merchant.
    Token expires after 1 hour.
    Rate limits requests (3 per hour per email/IP).

    Args:
        request: FastAPI request
        body: Email address
        db: Database session

    Returns:
        Success message (always returns success for security)
    """
    # Check rate limit
    RateLimiter.check_auth_rate_limit(
        request,
        key=f"forgot_password:{body.email}",
        max_requests=3,
        window_seconds=3600,  # 1 hour
    )

    # Always return success to prevent email enumeration
    # But only actually send email if account exists
    result = await db.execute(
        select(Merchant).where(Merchant.email == body.email)
    )
    merchant = result.scalars().first()

    if merchant:
        # Generate secure token (32 bytes = 64 hex chars)
        import secrets

        reset_token = secrets.token_hex(32)
        token_hash = hash_token(reset_token)

        # Calculate expiration (1 hour from now)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        # Create token record
        reset_record = PasswordResetToken(
            merchant_id=merchant.id,
            token=token_hash,
            expires_at=expires_at,
        )
        db.add(reset_record)

        # Delete any old unused tokens for this merchant
        old_tokens = await db.execute(
            select(PasswordResetToken).where(
                PasswordResetToken.merchant_id == merchant.id,
                PasswordResetToken.used_at.is_(None),
                PasswordResetToken.id != reset_record.id,
            )
        )
        for old_token in old_tokens.scalars():
            await db.delete(old_token)

        await db.commit()

        # Send reset email
        try:
            # Get frontend URL from settings or default to localhost
            frontend_url = settings().get("FRONTEND_URL", "http://localhost:5173")
            reset_link = f"{frontend_url}/reset-password/{reset_token}"

            # Import email service here to avoid circular import
            from app.services.email.email_service import send_email

            await send_email(
                to_email=merchant.email,
                subject="Password Reset Request",
                template_name="password_reset",
                template_data={
                    "reset_link": reset_link,
                    "expires_in": "1 hour",
                    "business_name": merchant.business_name or "your account",
                },
            )
        except Exception as e:
            logger.error(
                "failed_to_send_reset_email",
                merchant_id=merchant.id,
                email=merchant.email,
                error=str(e),
            )
            # Don't fail the request if email fails
            # The token is still created and can be used

    return MinimalEnvelope(
        data=ForgotPasswordResponse(
            message="If an account exists with this email, a password reset link has been sent."
        ),
        meta=_create_meta(),
    )


@router.post(
    "/verify-reset-token",
    response_model=MinimalEnvelope,
    status_code=status.HTTP_200_OK,
)
async def verify_reset_token(
    body: VerifyResetTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> MinimalEnvelope:
    """Verify password reset token validity.

    Checks if token exists, is not expired, and has not been used.

    Args:
        body: Reset token
        db: Database session

    Returns:
        Token validity and associated email (if valid)
    """
    # Hash the provided token to match against stored hash
    token_hash = hash_token(body.token)

    # Find token record
    result = await db.execute(
        select(PasswordResetToken)
        .where(PasswordResetToken.token == token_hash)
        .where(PasswordResetToken.used_at.is_(None))
    )
    reset_record = result.scalars().first()

    is_valid = reset_record is not None and reset_record.is_valid()
    email = None

    if is_valid and reset_record:
        # Get merchant email
        merchant_result = await db.execute(
            select(Merchant).where(Merchant.id == reset_record.merchant_id)
        )
        merchant = merchant_result.scalars().first()
        if merchant:
            email = merchant.email

    return MinimalEnvelope(
        data=VerifyResetTokenResponse(valid=is_valid, email=email),
        meta=_create_meta(),
    )


@router.post(
    "/reset-password",
    response_model=MinimalEnvelope,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"description": "Invalid or expired token"},
    },
)
async def reset_password(
    body: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> MinimalEnvelope:
    """Reset password using valid token.

    Validates token, updates password, marks token as used,
    invalidates all existing sessions, and sends confirmation email.

    Args:
        body: Reset token and new password
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If token is invalid, expired, or already used
    """
    # Validate password requirements
    validate_password_requirements(body.new_password)

    # Hash the provided token to match against stored hash
    token_hash = hash_token(body.token)

    # Find token record
    result = await db.execute(
        select(PasswordResetToken)
        .where(PasswordResetToken.token == token_hash)
        .where(PasswordResetToken.used_at.is_(None))
    )
    reset_record = result.scalars().first()

    if not reset_record or not reset_record.is_valid():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": ErrorCode.VALIDATION_ERROR,
                "message": "Invalid or expired reset token",
                "details": "Please request a new password reset link",
            },
        )

    # Get merchant
    merchant_result = await db.execute(
        select(Merchant).where(Merchant.id == reset_record.merchant_id)
    )
    merchant = merchant_result.scalars().first()

    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": ErrorCode.MERCHANT_NOT_FOUND,
                "message": "Account not found",
                "details": "Please contact support",
            },
        )

    # Update password
    merchant.password_hash = hash_password(body.new_password)

    # Mark token as used
    reset_record.used_at = datetime.now(timezone.utc)

    # Invalidate all existing sessions for security
    sessions_result = await db.execute(
        select(Session).where(
            Session.merchant_id == merchant.id, Session.revoked.is_(False)
        )
    )
    for session in sessions_result.scalars():
        session.revoke()

    await db.commit()

    # Send confirmation email
    try:
        from app.services.email.email_service import send_email

        await send_email(
            to_email=merchant.email,
            subject="Password Successfully Reset",
            template_name="password_reset_confirmation",
            template_data={
                "business_name": merchant.business_name or "your account",
                "reset_time": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            },
        )
    except Exception as e:
        logger.error(
            "failed_to_send_reset_confirmation_email",
            merchant_id=merchant.id,
            email=merchant.email,
            error=str(e),
        )
        # Don't fail the request if email fails

    return MinimalEnvelope(
        data=ResetPasswordResponse(
            message="Password has been reset successfully. Please log in with your new password."
        ),
        meta=_create_meta(),
    )
