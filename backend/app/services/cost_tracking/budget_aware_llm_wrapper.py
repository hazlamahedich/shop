"""Budget-aware LLM wrapper.

Extends cost tracking with budget validation BEFORE LLM calls.
Blocks requests when budget is exceeded and returns configured message.
"""

from __future__ import annotations

import time
from decimal import Decimal
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.merchant import Merchant
from app.services.cost_tracking.budget_alert_service import BudgetAlertService
from app.services.cost_tracking.cost_tracking_service import (
    CostTrackingService,
    track_llm_request,
)
from app.services.llm.base_llm_service import (
    BaseLLMService,
    LLMMessage,
    LLMResponse,
)
from app.services.llm.llm_router import LLMRouter

logger = structlog.get_logger(__name__)


class BudgetAwareLLMWrapper(BaseLLMService):
    """Budget-aware LLM wrapper that checks budget BEFORE making LLM calls.

    Flow:
    1. Check if bot is paused (Redis-first check)
    2. Check budget threshold
    3. If exceeded -> return pause message WITHOUT calling LLM (no cost recorded)
    4. If OK -> make LLM call
    5. Track cost after successful call
    6. Check if cost pushed to threshold -> create alert or pause
    """

    PAUSED_BOT_MESSAGE = "I've reached my message limit. Please contact support."
    ZERO_BUDGET_MESSAGE = "Budget is $0. Please set a budget to enable the bot."

    def __init__(
        self,
        llm_service: BaseLLMService,
        db: AsyncSession,
        merchant_id: int,
        conversation_id: str,
        track_costs: bool = True,
        redis_client: Any | None = None,
    ) -> None:
        """Initialize budget-aware wrapper.

        Args:
            llm_service: The LLM service to wrap
            db: Database session
            merchant_id: Merchant ID for cost isolation
            conversation_id: Conversation ID for cost association
            track_costs: Whether to track costs
            redis_client: Optional Redis client for pause state
        """
        self.llm_service = llm_service
        self.db = db
        self.merchant_id = merchant_id
        self.conversation_id = conversation_id
        self.track_costs = track_costs
        self.config = getattr(llm_service, "config", {})
        self.budget_service = BudgetAlertService(db, redis_client)
        self.cost_service = CostTrackingService()

    @property
    def provider_name(self) -> str:
        """Return provider name from wrapped service."""
        return self.llm_service.provider_name

    async def test_connection(self) -> bool:
        """Test LLM connectivity (delegated to wrapped service)."""
        return await self.llm_service.test_connection()

    async def chat(
        self,
        messages: list[LLMMessage],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> LLMResponse:
        """Send chat completion with budget check BEFORE call.

        CRITICAL: Check budget BEFORE making LLM API call to prevent
        any cost when budget is exceeded.

        Args:
            messages: Conversation history
            model: Model override (optional)
            temperature: Response randomness (0.0-1.0)
            max_tokens: Maximum tokens in response

        Returns:
            LLM response with content and metadata
            OR paused message if budget exceeded (without calling LLM)
        """
        merchant = await self._get_merchant()
        if not merchant:
            raise ValueError(f"Merchant {self.merchant_id} not found")

        budget_cap = self._get_budget_cap(merchant)

        if budget_cap is not None:
            is_paused, pause_reason = await self.budget_service.get_bot_paused_state(
                self.merchant_id
            )

            if is_paused:
                logger.info(
                    "llm_request_blocked_bot_paused",
                    merchant_id=self.merchant_id,
                    conversation_id=self.conversation_id,
                    pause_reason=pause_reason,
                )
                return self._create_paused_response(self.PAUSED_BOT_MESSAGE)

            if budget_cap == Decimal("0"):
                logger.info(
                    "llm_request_blocked_zero_budget",
                    merchant_id=self.merchant_id,
                    conversation_id=self.conversation_id,
                )
                await self.budget_service.set_bot_paused_state(
                    self.merchant_id, True, "Zero budget"
                )
                return self._create_paused_response(self.ZERO_BUDGET_MESSAGE)

        start_time = time.time()

        response = await self.llm_service.chat(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        processing_time_ms = (time.time() - start_time) * 1000

        if self.track_costs:
            try:
                await track_llm_request(
                    db=self.db,
                    llm_response=response,
                    conversation_id=self.conversation_id,
                    merchant_id=self.merchant_id,
                    processing_time_ms=processing_time_ms,
                )

                if budget_cap is not None:
                    monthly_spend = Decimal(
                        str(await self.cost_service.get_monthly_spend(self.db, self.merchant_id))
                    )

                    status, _ = await self.budget_service.check_and_handle_budget_state(
                        self.merchant_id,
                        monthly_spend,
                        budget_cap,
                    )

                    if status == "exceeded":
                        logger.info(
                            "budget_exceeded_after_call",
                            merchant_id=self.merchant_id,
                            monthly_spend=float(monthly_spend),
                            budget_cap=float(budget_cap),
                        )

            except Exception as e:
                logger.warning(
                    "cost_tracking_failed",
                    conversation_id=self.conversation_id,
                    merchant_id=self.merchant_id,
                    error=str(e),
                )

        return response

    def _create_paused_response(self, message: str) -> LLMResponse:
        """Create a response for when bot is paused.

        Args:
            message: Paused message to return

        Returns:
            LLMResponse with paused message (no actual LLM call made)
        """
        return LLMResponse(
            content=message,
            tokens_used=0,
            provider="budget_paused",
            model="none",
            metadata={
                "budget_paused": True,
                "no_cost_recorded": True,
            },
        )

    async def _get_merchant(self) -> Merchant | None:
        """Get merchant by ID.

        Returns:
            Merchant or None
        """
        query = select(Merchant).where(Merchant.id == self.merchant_id)
        result = await self.db.execute(query)
        return result.scalars().first()

    def _get_budget_cap(self, merchant: Merchant) -> Decimal | None:
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

    def count_tokens(self, text: str) -> int:
        """Count tokens (delegated to wrapped service)."""
        return self.llm_service.count_tokens(text)

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost (delegated to wrapped service)."""
        return self.llm_service.estimate_cost(input_tokens, output_tokens)

    async def health_check(self) -> dict[str, Any]:
        """Health check (delegated to wrapped service)."""
        return await self.llm_service.health_check()


class BudgetAwareLLMRouter:
    """Budget-aware wrapper for LLMRouter with failover support.

    Wraps an LLMRouter with budget checking for all requests.
    Supports primary/backup failover pattern.
    """

    def __init__(
        self,
        llm_router: LLMRouter,
        db: AsyncSession,
        merchant_id: int,
        conversation_id: str,
        track_costs: bool = True,
        redis_client: Any | None = None,
    ) -> None:
        """Initialize budget-aware router wrapper.

        Args:
            llm_router: The LLMRouter instance to wrap
            db: Database session
            merchant_id: Merchant ID
            conversation_id: Conversation ID
            track_costs: Whether to track costs
            redis_client: Optional Redis client
        """
        self.llm_router = llm_router
        self.db = db
        self.merchant_id = merchant_id
        self.conversation_id = conversation_id
        self.track_costs = track_costs

        self._primary_provider = BudgetAwareLLMWrapper(
            llm_service=llm_router.primary_provider,
            db=db,
            merchant_id=merchant_id,
            conversation_id=conversation_id,
            track_costs=track_costs,
            redis_client=redis_client,
        )

        if llm_router.backup_provider:
            self._backup_provider = BudgetAwareLLMWrapper(
                llm_service=llm_router.backup_provider,
                db=db,
                merchant_id=merchant_id,
                conversation_id=conversation_id,
                track_costs=track_costs,
                redis_client=redis_client,
            )
        else:
            self._backup_provider = None

    async def chat(
        self,
        messages: list[LLMMessage],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        use_backup: bool = False,
    ) -> LLMResponse:
        """Send chat completion with budget awareness and failover.

        Args:
            messages: Conversation history
            model: Model override (optional)
            temperature: Response randomness
            max_tokens: Maximum tokens in response
            use_backup: Force use of backup provider

        Returns:
            LLM response

        Raises:
            APIError: If both providers fail
        """
        provider = self._backup_provider if use_backup else self._primary_provider
        provider_name = "backup" if use_backup else "primary"

        try:
            logger.info(
                "budget_aware_llm_router_attempt",
                provider=provider_name,
                conversation_id=self.conversation_id,
            )

            response = await provider.chat(messages, model, temperature, max_tokens)

            if response.metadata and response.metadata.get("budget_paused"):
                return response

            logger.info(
                "budget_aware_llm_router_success",
                provider=provider_name,
                tokens_used=response.tokens_used,
                model=response.model,
                conversation_id=self.conversation_id,
            )

            return response

        except Exception as e:
            logger.warning(
                "budget_aware_llm_router_failed",
                error=str(e),
                backup_available=self._backup_provider is not None,
                conversation_id=self.conversation_id,
            )

            if self._backup_provider and not use_backup:
                logger.info(
                    "budget_aware_llm_router_fallback",
                    fallback_to="backup",
                    conversation_id=self.conversation_id,
                )

                try:
                    response = await self._backup_provider.chat(
                        messages, model, temperature, max_tokens
                    )
                    return response

                except Exception as backup_error:
                    logger.error(
                        "budget_aware_llm_router_both_failed",
                        primary_error=str(e),
                        backup_error=str(backup_error),
                        conversation_id=self.conversation_id,
                    )

                    from app.core.errors import APIError, ErrorCode

                    raise APIError(
                        ErrorCode.LLM_ROUTER_BOTH_FAILED,
                        f"Both LLM providers failed. "
                        f"Primary: {str(e)}, Backup: {str(backup_error)}",
                    )
            else:
                from app.core.errors import APIError, ErrorCode

                raise APIError(
                    ErrorCode.LLM_SERVICE_UNAVAILABLE,
                    f"LLM provider failed: {str(e)}",
                )

    async def health_check(self) -> dict[str, Any]:
        """Health check (delegated to wrapped router)."""
        return await self.llm_router.health_check()
