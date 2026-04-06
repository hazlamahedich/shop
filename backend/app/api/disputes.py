"""Dispute and Payment Issues API endpoints.

Provides dispute listing, summary, and unified payment issues data
for the merchant dashboard.
"""

from __future__ import annotations

from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.dispute import DisputeStatus
from app.services.dispute_service import DisputeService

router = APIRouter(prefix="/disputes", tags=["disputes"])
logger = structlog.get_logger(__name__)


def _get_merchant_id(request: Request) -> int:
    """Extract merchant_id from authenticated request."""
    merchant_id = getattr(request.state, "merchant_id", None)
    if merchant_id:
        return merchant_id
    from app.core.config import settings

    if settings()["DEBUG"]:
        header = request.headers.get("X-Merchant-Id")
        if header:
            try:
                return int(header)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid X-Merchant-Id header",
                )
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
    )


@router.get("")
async def list_disputes(
    request: Request,
    db: AsyncSession = Depends(get_db),
    status_filter: str | None = Query(None, alias="status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    """List disputes for the authenticated merchant."""
    merchant_id = _get_merchant_id(request)

    if status_filter and status_filter not in [s.value for s in DisputeStatus]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status filter. Must be one of: {[s.value for s in DisputeStatus]}",
        )

    service = DisputeService(db)
    disputes = await service.get_disputes(
        merchant_id=merchant_id,
        status_filter=status_filter,
        limit=limit,
        offset=offset,
    )

    return {
        "data": [
            {
                "id": d.id,
                "shopify_dispute_id": d.shopify_dispute_id,
                "amount": float(d.amount),
                "currency": d.currency,
                "reason": d.reason,
                "status": d.status,
                "evidence_due_by": d.evidence_due_by.isoformat() if d.evidence_due_by else None,
                "created_at": d.created_at.isoformat() if d.created_at else None,
                "updated_at": d.updated_at.isoformat() if d.updated_at else None,
                "order_id": d.order_id,
            }
            for d in disputes
        ],
        "meta": {"merchant_id": merchant_id, "limit": limit, "offset": offset},
    }


@router.get("/summary")
async def get_dispute_summary(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get aggregated dispute summary for the authenticated merchant."""
    merchant_id = _get_merchant_id(request)
    service = DisputeService(db)
    summary = await service.get_dispute_summary(merchant_id)

    return {
        "data": {
            k: float(v)
            if isinstance(v, (int,))
            else (
                {sk: (float(sv) if isinstance(sv, (int,)) else sv) for sk, sv in v.items()}
                if isinstance(v, dict)
                else v
            )
            for k, v in summary.items()
        },
    }


@router.get("/payment-issues")
async def get_payment_issues(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get unified payment issues summary for the dashboard.

    Returns disputes, pending orders, and payment-related alerts.
    """
    merchant_id = _get_merchant_id(request)
    service = DisputeService(db)
    issues = await service.get_payment_issues_summary(merchant_id)

    return {"data": issues}
