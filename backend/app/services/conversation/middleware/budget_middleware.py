"""Budget middleware for unified conversation processing.

Story 5-10 Task 20: Budget Alert Middleware

Checks merchant's LLM budget before processing messages.
Returns graceful message when budget is exceeded.

This middleware provides a user-facing interface to the
BudgetAwareLLMWrapper for the unified conversation service.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.models.merchant import Merchant
from app.services.conversation.schemas import ConversationContext, ConversationResponse
from app.services.cost_tracking.budget_alert_service import BudgetAlertService
from app.services.cost_tracking.cost_tracking_service import CostTrackingService


logger = structlog.get_logger(__name__)


class BudgetMiddleware:
    """Middleware for checking budget before LLM calls.

    Checks if the merchant's LLM budget is exceeded and returns
    a graceful message instead of processing the message.

    This middleware wraps the BudgetAwareLLMWrapper functionality
    for the unified conversation service.

    Usage:
        middleware = BudgetMiddleware()

        # Check budget before processing
        is_ok, message = await middleware.check_budget(
            db=db,
            merchant_id=merchant.id,
        )

        if not is_ok:
            return ConversationResponse(message=message, ...)
    """

    BUDGET_EXCEEDED_MESSAGE = (
        "I'm taking a short break while we review our chat budget. "
        "A team member will be with you shortly!"
    )
    ZERO_BUDGET_MESSAGE = (
        "Our chat service is being configured. Please contact us directly for assistance!"
    )
    PAUSED_MESSAGE = "I'm currently unavailable. A team member will assist you soon!"

    def __init__(self, redis_client: Any = None) -> None:
        """Initialize budget middleware.

        Args:
            redis_client: Optional Redis client for pause state
        """
        self.redis_client = redis_client
        self.logger = structlog.get_logger(__name__)
        self.cost_service = CostTrackingService()

    async def check_budget(
        self,
        db: AsyncSession,
        merchant_id: int,
    ) -> tuple[bool, Optional[str]]:
        """Check if merchant has budget available.

        Args:
            db: Database session
            merchant_id: Merchant ID to check

        Returns:
            Tuple of (is_ok, message_if_not)
            - (True, None) if budget is OK
            - (False, message) if budget exceeded
        """
        merchant = await self._get_merchant(db, merchant_id)

        if not merchant:
            return True, None

        budget_cap = self._get_budget_cap(merchant)

        if budget_cap is None:
            return True, None

        budget_service = BudgetAlertService(db, self.redis_client)

        is_paused, pause_reason = await budget_service.get_bot_paused_state(merchant_id)

        if is_paused:
            self.logger.info(
                "budget_middleware_paused",
                merchant_id=merchant_id,
                pause_reason=pause_reason,
            )
            return False, self.PAUSED_MESSAGE

        if budget_cap == Decimal("0"):
            self.logger.info(
                "budget_middleware_zero_budget",
                merchant_id=merchant_id,
            )
            await budget_service.set_bot_paused_state(merchant_id, True, "Zero budget")
            return False, self.ZERO_BUDGET_MESSAGE

        monthly_spend = Decimal(str(await self.cost_service.get_monthly_spend(db, merchant_id)))

        if monthly_spend >= budget_cap:
            self.logger.info(
                "budget_middleware_exceeded",
                merchant_id=merchant_id,
                monthly_spend=float(monthly_spend),
                budget_cap=float(budget_cap),
            )
            await budget_service.set_bot_paused_state(merchant_id, True, "Budget exceeded")
            return False, self.BUDGET_EXCEEDED_MESSAGE

        return True, None

    async def get_budget_status(
        self,
        db: AsyncSession,
        merchant_id: int,
    ) -> dict:
        """Get current budget status for a merchant.

        Args:
            db: Database session
            merchant_id: Merchant ID

        Returns:
            Dict with budget status information
        """
        merchant = await self._get_merchant(db, merchant_id)

        if not merchant:
            return {
                "has_budget": False,
                "budget_cap": None,
                "monthly_spend": 0,
                "remaining": None,
                "is_paused": False,
            }

        budget_cap = self._get_budget_cap(merchant)

        if budget_cap is None:
            return {
                "has_budget": False,
                "budget_cap": None,
                "monthly_spend": 0,
                "remaining": None,
                "is_paused": False,
            }

        monthly_spend = Decimal(str(await self.cost_service.get_monthly_spend(db, merchant_id)))
        remaining = max(Decimal("0"), budget_cap - monthly_spend)

        budget_service = BudgetAlertService(db, self.redis_client)
        is_paused, pause_reason = await budget_service.get_bot_paused_state(merchant_id)

        return {
            "has_budget": True,
            "budget_cap": float(budget_cap),
            "monthly_spend": float(monthly_spend),
            "remaining": float(remaining),
            "is_paused": is_paused,
            "pause_reason": pause_reason,
            "percentage_used": float(monthly_spend / budget_cap * 100) if budget_cap > 0 else 0,
        }

    async def _get_merchant(
        self,
        db: AsyncSession,
        merchant_id: int,
    ) -> Optional[Merchant]:
        """Get merchant by ID.

        Args:
            db: Database session
            merchant_id: Merchant ID

        Returns:
            Merchant or None
        """
        result = await db.execute(select(Merchant).where(Merchant.id == merchant_id))
        return result.scalars().first()

    def _get_budget_cap(self, merchant: Merchant) -> Optional[Decimal]:
        """Get budget cap from merchant config.

        Args:
            merchant: Merchant instance

        Returns:
            Budget cap as Decimal or None if not set
        """
        if not merchant.config:
            return None

        budget_cap = merchant.config.get("budget_cap")
        if budget_cap is None:
            return None

        return Decimal(str(budget_cap))
