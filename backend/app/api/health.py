"""Health check API endpoints.

Provides health check endpoints for monitoring and observability.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request

router = APIRouter()


def _is_internal_request(request: Request, x_internal_request: str | None) -> bool:
    """Check if request is from internal source.

    Args:
        request: FastAPI request object
        x_internal_request: X-Internal-Request header value

    Returns:
        True if internal request, False otherwise
    """
    if x_internal_request == "true":
        return True

    client_host = request.client.host if request.client else None
    if client_host in ("127.0.0.1", "::1", "localhost"):
        return True

    return False


@router.get("/polling")
async def polling_health(
    request: Request,
    x_internal_request: str | None = Header(None, alias="X-Internal-Request"),
) -> dict[str, Any]:
    """Get polling service health status.

    Returns scheduler status, last poll timestamp, and per-merchant status.

    Protected by internal-only access check.

    Args:
        request: FastAPI request
        x_internal_request: Header for internal request validation

    Returns:
        Health status dict

    Raises:
        HTTPException: 403 if not internal request
    """
    if not _is_internal_request(request, x_internal_request):
        raise HTTPException(
            status_code=403,
            detail={"error": "Forbidden", "message": "Internal endpoint only"},
        )

    try:
        from app.tasks.polling_scheduler import get_polling_status

        status = get_polling_status()
        return status
    except Exception as e:
        return {
            "scheduler_running": False,
            "error": str(e),
            "last_poll_timestamp": None,
            "merchants_polled": 0,
            "total_orders_synced": 0,
            "errors_last_hour": 0,
            "merchant_status": [],
        }
