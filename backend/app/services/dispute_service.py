"""Dispute Service for chargeback and payment issue management.

Handles dispute CRUD, payment issues aggregation for dashboard display.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dispute import Dispute, DisputeStatus
from app.models.order import Order, OrderStatus

logger = structlog.get_logger(__name__)


class DisputeService:
    """Service for dispute and payment issue operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def upsert_dispute(
        self,
        merchant_id: int,
        shopify_dispute_id: str,
        amount: Decimal,
        currency: str,
        reason: str | None = None,
        status: str = DisputeStatus.OPEN.value,
        evidence_due_by: datetime | None = None,
        shopify_order_id: str | None = None,
    ) -> Dispute:
        """Create or update a dispute from Shopify webhook data."""
        existing = await self.db.execute(
            select(Dispute).where(Dispute.shopify_dispute_id == shopify_dispute_id)
        )
        dispute = existing.scalar_one_or_none()

        order_id: int | None = None
        if shopify_order_id:
            order_result = await self.db.execute(
                select(Order).where(
                    Order.shopify_order_id == shopify_order_id,
                    Order.merchant_id == merchant_id,
                )
            )
            order = order_result.scalar_one_or_none()
            if order:
                order_id = order.id

        if dispute:
            dispute.amount = amount
            dispute.currency = currency
            dispute.reason = reason or dispute.reason
            dispute.status = status
            dispute.evidence_due_by = evidence_due_by or dispute.evidence_due_by
            dispute.order_id = order_id or dispute.order_id
            dispute.updated_at = datetime.now(timezone.utc)  # noqa: UP017
            logger.info(
                "dispute_updated",
                dispute_id=dispute.id,
                shopify_dispute_id=shopify_dispute_id,
                status=status,
            )
        else:
            dispute = Dispute(
                merchant_id=merchant_id,
                shopify_dispute_id=shopify_dispute_id,
                amount=amount,
                currency=currency,
                reason=reason,
                status=status,
                evidence_due_by=evidence_due_by,
                order_id=order_id,
            )
            self.db.add(dispute)
            logger.info(
                "dispute_created",
                shopify_dispute_id=shopify_dispute_id,
                merchant_id=merchant_id,
                amount=str(amount),
            )

        await self.db.flush()
        return dispute

    async def get_disputes(
        self,
        merchant_id: int,
        status_filter: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Dispute]:
        """List disputes for a merchant with optional status filter."""
        query = (
            select(Dispute)
            .where(Dispute.merchant_id == merchant_id)
            .order_by(Dispute.created_at.desc())
        )
        if status_filter:
            query = query.where(Dispute.status == status_filter)
        query = query.limit(limit).offset(offset)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_dispute_summary(self, merchant_id: int) -> dict[str, Any]:
        """Get aggregated dispute counts and amounts by status."""
        base_query = select(
            Dispute.status,
            func.count(Dispute.id).label("count"),
            func.coalesce(func.sum(Dispute.amount), Decimal("0")).label("total_amount"),
        ).where(Dispute.merchant_id == merchant_id)

        result = await self.db.execute(base_query.group_by(Dispute.status))
        rows = result.all()

        summary: dict[str, Any] = {
            "open": {"count": 0, "total_amount": Decimal("0")},
            "won": {"count": 0, "total_amount": Decimal("0")},
            "lost": {"count": 0, "total_amount": Decimal("0")},
            "pending": {"count": 0, "total_amount": Decimal("0")},
            "total_count": 0,
            "total_at_risk": Decimal("0"),
        }

        for row in rows:
            status_key = row.status
            if status_key in summary:
                summary[status_key]["count"] = row.count
                summary[status_key]["total_amount"] = row.total_amount
            summary["total_count"] += row.count

        open_result = await self.db.execute(
            select(func.coalesce(func.sum(Dispute.amount), Decimal("0"))).where(
                Dispute.merchant_id == merchant_id,
                Dispute.status.in_([DisputeStatus.OPEN.value, DisputeStatus.PENDING.value]),
            )
        )
        summary["total_at_risk"] = open_result.scalar_one()

        return summary

    async def get_payment_issues_summary(self, merchant_id: int) -> dict[str, Any]:
        """Get unified payment issues summary for the dashboard.

        Combines:
        - Open/pending disputes
        - Orders stuck in 'pending' (unpaid)
        - Payment-related handoff alerts count
        """
        disputes_summary = await self.get_dispute_summary(merchant_id)

        open_disputes_result = await self.db.execute(
            select(Dispute)
            .where(
                Dispute.merchant_id == merchant_id,
                Dispute.status.in_([DisputeStatus.OPEN.value, DisputeStatus.PENDING.value]),
            )
            .order_by(Dispute.created_at.desc())
            .limit(10)
        )
        recent_disputes = list(open_disputes_result.scalars().all())

        pending_orders_result = await self.db.execute(
            select(Order)
            .where(
                Order.merchant_id == merchant_id,
                Order.status == OrderStatus.PENDING,
            )
            .order_by(Order.created_at.desc())
            .limit(10)
        )
        pending_orders = list(pending_orders_result.scalars().all())

        return {
            "disputes": {
                "open_count": disputes_summary["open"]["count"],
                "pending_count": disputes_summary["pending"]["count"],
                "lost_count": disputes_summary["lost"]["count"],
                "total_at_risk": disputes_summary["total_at_risk"],
                "recent": [
                    {
                        "id": d.id,
                        "shopify_dispute_id": d.shopify_dispute_id,
                        "amount": float(d.amount),
                        "currency": d.currency,
                        "reason": d.reason,
                        "status": d.status,
                        "evidence_due_by": d.evidence_due_by.isoformat()
                        if d.evidence_due_by
                        else None,
                        "created_at": d.created_at.isoformat() if d.created_at else None,
                        "order_id": d.order_id,
                    }
                    for d in recent_disputes
                ],
            },
            "pending_orders": {
                "count": len(pending_orders),
                "recent": [
                    {
                        "id": o.id,
                        "shopify_order_id": o.shopify_order_id,
                        "order_name": o.order_number,
                        "total_price": float(o.total) if o.total else None,
                        "currency": o.currency_code,
                        "payment_method": o.payment_method,
                        "created_at": o.created_at.isoformat() if o.created_at else None,
                    }
                    for o in pending_orders
                ],
            },
        }
