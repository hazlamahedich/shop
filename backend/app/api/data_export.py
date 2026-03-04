"""Data Export API endpoint for GDPR/CCPA compliance.

Story 6-3: Merchant CSV Export

Provides POST /api/v1/data/export endpoint for complete merchant data export.
Implements rate limiting, concurrent export locks, and consent-based filtering.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, Request, status
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
import structlog
from redis.asyncio import Redis as AsyncRedis
from redis.asyncio import from_url as async_from_url
import os

from app.core.database import get_db
from app.core.errors import APIError, ErrorCode
from app.schemas.base import MinimalEnvelope, MetaData
from app.services.export.merchant_data_export_service import MerchantDataExportService


router = APIRouter()
logger = structlog.get_logger(__name__)

EXPORT_RATE_LIMIT_TTL = 3600
EXPORT_LOCK_TTL = 60


def get_async_redis_client() -> Optional[AsyncRedis]:
    """Get async Redis client for rate limiting.

    Returns:
        Async Redis client or None if Redis not configured
    """
    try:
        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            return async_from_url(redis_url, decode_responses=True)
    except Exception as e:
        logger.warning("redis_connection_failed", error=str(e))
    return None


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
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }


@router.post(
    "/data/export",
    status_code=status.HTTP_200_OK,
)
async def export_merchant_data(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    x_csrf_token: str = Header(..., alias="X-CSRF-Token"),
    merchant_id: int = Header(..., alias="X-Merchant-ID"),
) -> StreamingResponse:
    """Export all merchant data as CSV (GDPR/CCPA compliance).

    Generates a complete CSV export of all merchant data including:
    - Conversations (with consent-based filtering)
    - Messages (content excluded for opted-out users)
    - LLM cost tracking
    - Merchant configuration

    Security:
    - Requires JWT authentication (X-Merchant-ID header)
    - Requires CSRF token validation
    - Rate limited: 1 export per hour per merchant
    - Concurrent export lock: Prevents simultaneous exports

    Args:
        request: FastAPI Request object
        db: Database session
        x_csrf_token: CSRF token from GET /api/v1/csrf-token
        merchant_id: Merchant ID from JWT (X-Merchant-ID header)

    Returns:
        Streaming CSV response with merchant data

    Raises:
        APIError: EXPORT_RATE_LIMITED - If rate limit exceeded
        APIError: EXPORT_ALREADY_IN_PROGRESS - If export already running
        APIError: UNAUTHORIZED - If authentication fails
        APIError: VALIDATION_ERROR - If CSRF token invalid
    """
    request_id = str(uuid4())
    log = logger.bind(
        request_id=request_id,
        merchant_id=merchant_id,
    )

    if not merchant_id or merchant_id <= 0:
        raise APIError(
            ErrorCode.UNAUTHORIZED,
            "Invalid merchant ID",
        )

    redis_client = get_async_redis_client()

    if not redis_client:
        log.warning("redis_not_available", message="Rate limiting disabled")
    else:
        await _check_rate_limit(redis_client, merchant_id, log)
        await _check_concurrent_lock(redis_client, merchant_id, log)
        await _set_concurrent_lock(redis_client, merchant_id, log)

    try:
        log.info("export_started")

        export_service = MerchantDataExportService(db)

        export_date = datetime.now(timezone.utc).strftime("%Y%m%d")
        filename = f"merchant_{merchant_id}_export_{export_date}.csv"

        async def csv_generator():
            """Generate CSV stream."""
            try:
                async for chunk in export_service.export_merchant_data(
                    merchant_id=merchant_id,
                ):
                    yield chunk
            except Exception as e:
                log.error("export_stream_error", error=str(e))
                raise
            finally:
                if redis_client:
                    await _clear_concurrent_lock(redis_client, merchant_id, log)
                    await _set_rate_limit(redis_client, merchant_id, log)

        return StreamingResponse(
            csv_generator(),
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "X-Export-Date": datetime.now(timezone.utc).isoformat(),
                "X-Request-ID": request_id,
            },
        )

    except APIError:
        raise
    except Exception as e:
        log.error("export_error", error=str(e))

        if redis_client:
            await _clear_concurrent_lock(redis_client, merchant_id, log)

        raise APIError(
            ErrorCode.EXPORT_GENERATION_FAILED,
            f"Export generation failed: {str(e)}",
        )


async def _check_rate_limit(
    redis_client: AsyncRedis,
    merchant_id: int,
    log: structlog.BoundLogger,
) -> None:
    """Check if merchant has exceeded export rate limit.

    Args:
        redis_client: Redis client
        merchant_id: Merchant ID
        log: Logger instance

    Raises:
        APIError: EXPORT_RATE_LIMITED if rate limit exceeded
    """
    rate_key = f"export_rate:{merchant_id}"

    try:
        exists = await redis_client.exists(rate_key)
        if exists:
            ttl = await redis_client.ttl(rate_key)
            log.warning(
                "export_rate_limited",
                merchant_id=merchant_id,
                ttl=ttl,
            )
            raise APIError(
                ErrorCode.EXPORT_RATE_LIMITED,
                "Export rate limit: 1 per hour per merchant",
                {"retry_after": ttl if ttl > 0 else EXPORT_RATE_LIMIT_TTL},
            )
    except APIError:
        raise
    except Exception as e:
        log.warning("rate_limit_check_failed", error=str(e))


async def _check_concurrent_lock(
    redis_client: AsyncRedis,
    merchant_id: int,
    log: structlog.BoundLogger,
) -> None:
    """Check if export is already in progress for this merchant.

    Args:
        redis_client: Redis client
        merchant_id: Merchant ID
        log: Logger instance

    Raises:
        APIError: EXPORT_ALREADY_IN_PROGRESS if export running
    """
    lock_key = f"export_lock:{merchant_id}"

    try:
        exists = await redis_client.exists(lock_key)
        if exists:
            ttl = await redis_client.ttl(lock_key)
            log.warning(
                "export_already_in_progress",
                merchant_id=merchant_id,
                ttl=ttl,
            )
            raise APIError(
                ErrorCode.EXPORT_ALREADY_IN_PROGRESS,
                "Export already in progress for this merchant",
                {"retry_after": ttl if ttl > 0 else EXPORT_LOCK_TTL},
            )
    except APIError:
        raise
    except Exception as e:
        log.warning("concurrent_lock_check_failed", error=str(e))


async def _set_concurrent_lock(
    redis_client: AsyncRedis,
    merchant_id: int,
    log: structlog.BoundLogger,
) -> None:
    """Set concurrent export lock for this merchant.

    Args:
        redis_client: Redis client
        merchant_id: Merchant ID
        log: Logger instance
    """
    lock_key = f"export_lock:{merchant_id}"

    try:
        await redis_client.setex(lock_key, EXPORT_LOCK_TTL, "1")
        log.debug("concurrent_lock_set", merchant_id=merchant_id)
    except Exception as e:
        log.warning("concurrent_lock_set_failed", error=str(e))


async def _clear_concurrent_lock(
    redis_client: AsyncRedis,
    merchant_id: int,
    log: structlog.BoundLogger,
) -> None:
    """Clear concurrent export lock for this merchant.

    Args:
        redis_client: Redis client
        merchant_id: Merchant ID
        log: Logger instance
    """
    lock_key = f"export_lock:{merchant_id}"

    try:
        await redis_client.delete(lock_key)
        log.debug("concurrent_lock_cleared", merchant_id=merchant_id)
    except Exception as e:
        log.warning("concurrent_lock_clear_failed", error=str(e))


async def _set_rate_limit(
    redis_client: AsyncRedis,
    merchant_id: int,
    log: structlog.BoundLogger,
) -> None:
    """Set rate limit after successful export.

    Args:
        redis_client: Redis client
        merchant_id: Merchant ID
        log: Logger instance
    """
    rate_key = f"export_rate:{merchant_id}"

    try:
        await redis_client.setex(rate_key, EXPORT_RATE_LIMIT_TTL, "1")
        log.info("rate_limit_set", merchant_id=merchant_id, ttl=EXPORT_RATE_LIMIT_TTL)
    except Exception as e:
        log.warning("rate_limit_set_failed", error=str(e))
