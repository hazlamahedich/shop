"""Test helper endpoints for automated testing.

These endpoints provide utilities for test setup:
- Create test merchant accounts
- Reset rate limiters
- Clear test data

Only accessible when DEBUG=True or with X-Test-Mode header.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.config import settings
from app.core.auth import hash_password
from app.core.rate_limiter import RateLimiter
from app.models.merchant import Merchant
from app.models.session import Session


router = APIRouter(tags=["test"])


class CreateMerchantRequest(BaseModel):
    """Request to create a test merchant."""

    email: EmailStr
    password: str


class CreateMerchantResponse(BaseModel):
    """Response from merchant creation."""

    success: bool
    merchant_id: Optional[int] = None
    message: str


def is_test_mode(request: Request) -> bool:
    """Check if request is in test mode.

    Test mode is enabled if:
    - DEBUG=True in settings, OR
    - X-Test-Mode header is present

    Args:
        request: FastAPI request

    Returns:
        True if test mode is enabled
    """
    if settings()["DEBUG"]:
        return True

    test_mode = request.headers.get("X-Test-Mode", "false").lower()
    return test_mode in ("true", "1", "yes")


@router.post(
    "/create-merchant",
    response_model=CreateMerchantResponse,
    status_code=status.HTTP_200_OK,
    responses={
        403: {"description": "Not in test mode"},
        409: {"description": "Merchant already exists"},
    },
)
async def create_test_merchant(
    request: Request,
    data: CreateMerchantRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> CreateMerchantResponse:
    """Create a test merchant account for automated testing.

    Only accessible in test mode (DEBUG=True or X-Test-Mode header).

    Args:
        request: FastAPI request
        data: Merchant email and password
        response: FastAPI response
        db: Database session

    Returns:
        Success status and merchant ID

    Raises:
        HTTPException: If not in test mode
    """
    if not is_test_mode(request):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error_code": "FORBIDDEN",
                "message": "Test endpoints only available in test mode",
            },
        )

    # Check if merchant already exists
    result = await db.execute(
        select(Merchant).where(Merchant.email == data.email)
    )
    existing = result.scalars().first()

    if existing:
        response.status_code = status.HTTP_409_CONFLICT
        return CreateMerchantResponse(
            success=False,
            merchant_id=existing.id,
            message="Merchant already exists",
        )

    # Create new merchant
    merchant = Merchant(
        email=data.email,
        password_hash=hash_password(data.password),
        merchant_key=f"test_key_{data.email.split('@')[0]}",
        platform="test",
    )

    db.add(merchant)
    await db.commit()
    await db.refresh(merchant)

    return CreateMerchantResponse(
        success=True,
        merchant_id=merchant.id,
        message="Test merchant created successfully",
    )


@router.post(
    "/reset-rate-limits",
    status_code=status.HTTP_200_OK,
    responses={
        403: {"description": "Not in test mode"},
    },
)
async def reset_rate_limits(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Reset rate limit counters for testing.

    Only accessible in test mode (DEBUG=True or X-Test-Mode header).

    Args:
        request: FastAPI request
        db: Database session

    Returns:
        Success message
    """
    if not is_test_mode(request):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error_code": "FORBIDDEN",
                "message": "Test endpoints only available in test mode",
            },
        )

    # Reset rate limit counters
    RateLimiter.reset_all()

    return {"status": "success", "message": "Rate limits reset"}


@router.post(
    "/clear-sessions",
    status_code=status.HTTP_200_OK,
    responses={
        403: {"description": "Not in test mode"},
    },
)
async def clear_test_sessions(
    request: Request,
    email: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Clear test sessions for a merchant or all merchants.

    Only accessible in test mode (DEBUG=True or X-Test-Mode header).

    Args:
        request: FastAPI request
        email: Optional email to filter sessions
        db: Database session

    Returns:
        Success message
    """
    if not is_test_mode(request):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error_code": "FORBIDDEN",
                "message": "Test endpoints only available in test mode",
            },
        )

    if email:
        # Delete sessions for specific merchant
        result = await db.execute(
            select(Merchant).where(Merchant.email == email)
        )
        merchant = result.scalars().first()

        if merchant:
            await db.execute(
                delete(Session).where(Session.merchant_id == merchant.id)
            )
    else:
        # Delete all sessions (use with caution)
        await db.execute(delete(Session))

    await db.commit()

    return {
        "status": "success",
        "message": f"Sessions cleared for {email if email else 'all merchants'}",
    }


@router.delete(
    "/cleanup",
    status_code=status.HTTP_200_OK,
    responses={
        403: {"description": "Not in test mode"},
    },
)
async def cleanup_test_data(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Clean up all test data (merchants, sessions, etc.).

    Only accessible in test mode (DEBUG=True or X-Test-Mode header).
    USE WITH CAUTION - This deletes all test data.

    Args:
        request: FastAPI request
        db: Database session

    Returns:
        Success message
    """
    if not is_test_mode(request):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error_code": "FORBIDDEN",
                "message": "Test endpoints only available in test mode",
            },
        )

    # Delete all sessions
    await db.execute(delete(Session))

    # Delete all test merchants (those with test_ prefix in merchant_key)
    await db.execute(
        delete(Merchant).where(Merchant.merchant_key.like("test_%"))
    )

    await db.commit()

    return {"status": "success", "message": "Test data cleaned up"}
