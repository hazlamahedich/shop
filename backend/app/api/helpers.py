"""Shared helper functions for API endpoints.

This module provides common utility functions used across multiple API
endpoints to reduce code duplication and ensure consistency.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import APIError, ErrorCode
from app.schemas.base import MetaData


def create_meta() -> MetaData:
    """Create metadata for API response.

    Returns:
        MetaData object with request_id and timestamp

    Note:
        Uses timezone-aware datetime (UTC) to avoid Python 3.12+ deprecation
        warnings about datetime.utcnow().
    """
    return MetaData(
        request_id=str(uuid4()),
        timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    )


def get_merchant_id(request: Request) -> int:
    """Get merchant ID from request state with fallback for testing.

    In production, merchant_id should be set by authentication middleware
    in request.state. In DEBUG mode, X-Merchant-Id header is supported
    for easier API testing.

    Args:
        request: FastAPI request

    Returns:
        Merchant ID

    Raises:
        APIError: If authentication fails and not in DEBUG mode

    Note:
        The X-Merchant-Id header fallback should only be used in development/
        testing. Production endpoints should rely on proper authentication.
    """
    merchant_id = getattr(request.state, "merchant_id", None)
    if not merchant_id:
        # Check X-Merchant-Id header in DEBUG mode for easier testing
        if settings()["DEBUG"]:
            merchant_id_header = request.headers.get("X-Merchant-Id")
            if merchant_id_header:
                merchant_id = int(merchant_id_header)
            else:
                merchant_id = 1  # Default for dev/test
        else:
            raise APIError(
                ErrorCode.AUTH_FAILED,
                "Authentication required",
            )
    return merchant_id


async def verify_merchant_exists(
    merchant_id: int,
    db: AsyncSession,
) -> Any:
    """Verify that a merchant exists in the database.

    Args:
        merchant_id: The merchant ID to verify
        db: Database session

    Returns:
        The Merchant object if found

    Raises:
        APIError: If merchant is not found (ErrorCode.MERCHANT_NOT_FOUND)

    Note:
        This function encapsulates the common pattern of verifying merchant
        existence across multiple endpoints.
    """
    from sqlalchemy import select
    from app.models.merchant import Merchant

    result = await db.execute(select(Merchant).where(Merchant.id == merchant_id))
    merchant = result.scalars().first()

    if not merchant:
        raise APIError(
            ErrorCode.MERCHANT_NOT_FOUND,
            f"Merchant with ID {merchant_id} not found",
        )

    return merchant
