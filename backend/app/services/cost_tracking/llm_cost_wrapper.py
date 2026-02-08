"""LLM Cost Tracking wrapper.

Provides automatic cost tracking for LLM requests by wrapping
LLM service calls and recording token usage and costs.

Example:
    # Wrap the LLM router with cost tracking
    llm_router = LLMRouter(config)
    cost_tracking_router = CostTrackingLLMWrapper(llm_router, db, merchant_id, conversation_id)
    response = await cost_tracking_router.chat(messages)  # Automatically tracked
"""

from __future__ import annotations

from typing import Any, List, Optional
import time
import structlog

from app.services.llm.base_llm_service import (
    BaseLLMService,
    LLMMessage,
    LLMResponse,
)
from app.services.llm.llm_router import LLMRouter
from app.services.cost_tracking.cost_tracking_service import track_llm_request
from sqlalchemy.ext.asyncio import AsyncSession


logger = structlog.get_logger(__name__)


class CostTrackingLLMWrapper(BaseLLMService):
    """Wrapper around LLM services that automatically tracks costs.

    Wraps any BaseLLMService or LLMRouter and automatically records
    cost data after each successful LLM request.

    Attributes:
        llm_service: The underlying LLM service to wrap
        db: Database session for cost tracking
        merchant_id: Merchant ID for cost isolation
        conversation_id: Conversation ID for cost association
        track_costs: Whether to track costs (default: True)
    """

    def __init__(
        self,
        llm_service: BaseLLMService,
        db: AsyncSession,
        merchant_id: int,
        conversation_id: str,
        track_costs: bool = True,
    ) -> None:
        """Initialize cost tracking wrapper.

        Args:
            llm_service: The LLM service or router to wrap
            db: Database session for cost tracking
            merchant_id: Merchant ID for cost isolation
            conversation_id: Conversation ID for cost association
            track_costs: Whether to track costs (can be disabled for testing)
        """
        self.llm_service = llm_service
        self.db = db
        self.merchant_id = merchant_id
        self.conversation_id = conversation_id
        self.track_costs = track_costs
        self.config = getattr(llm_service, "config", {})

    @property
    def provider_name(self) -> str:
        """Return provider name from wrapped service."""
        return self.llm_service.provider_name

    async def test_connection(self) -> bool:
        """Test LLM connectivity (delegated to wrapped service)."""
        return await self.llm_service.test_connection()

    async def chat(
        self,
        messages: List[LLMMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> LLMResponse:
        """Send chat completion with automatic cost tracking.

        Wraps the underlying service's chat method and records
        cost data after successful responses.

        Args:
            messages: Conversation history
            model: Model override (optional)
            temperature: Response randomness (0.0-1.0)
            max_tokens: Maximum tokens in response

        Returns:
            LLM response with content and metadata

        Raises:
            Exception: If LLM request fails (cost tracking skipped)
        """
        start_time = time.time()

        # Make the actual LLM request
        response = await self.llm_service.chat(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000

        # Track costs automatically if enabled
        if self.track_costs:
            try:
                await track_llm_request(
                    db=self.db,
                    llm_response=response,
                    conversation_id=self.conversation_id,
                    merchant_id=self.merchant_id,
                    processing_time_ms=processing_time_ms,
                )
            except Exception as e:
                # Log tracking error but don't fail the request
                logger.warning(
                    "cost_tracking_failed",
                    conversation_id=self.conversation_id,
                    merchant_id=self.merchant_id,
                    error=str(e),
                )

        return response

    def count_tokens(self, text: str) -> int:
        """Count tokens (delegated to wrapped service)."""
        return self.llm_service.count_tokens(text)

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost (delegated to wrapped service)."""
        return self.llm_service.estimate_cost(input_tokens, output_tokens)

    async def health_check(self) -> dict[str, Any]:
        """Health check (delegated to wrapped service)."""
        return await self.llm_service.health_check()


class CostTrackingLLMRouter:
    """Cost-aware wrapper for LLMRouter.

    Wraps an LLMRouter with automatic cost tracking for all requests.
    This is the recommended way to add cost tracking to existing
    LLM router configurations.

    Example:
        # Create standard LLM router
        router = LLMRouter(config)

        # Wrap with cost tracking
        cost_router = CostTrackingLLMRouter(router, db, merchant_id, conversation_id)

        # Use normally - costs tracked automatically
        response = await cost_router.chat(messages)
    """

    def __init__(
        self,
        llm_router: LLMRouter,
        db: AsyncSession,
        merchant_id: int,
        conversation_id: str,
        track_costs: bool = True,
    ) -> None:
        """Initialize cost tracking router wrapper.

        Args:
            llm_router: The LLMRouter instance to wrap
            db: Database session for cost tracking
            merchant_id: Merchant ID for cost isolation
            conversation_id: Conversation ID for cost association
            track_costs: Whether to track costs (default: True)
        """
        self.llm_router = llm_router
        self.db = db
        self.merchant_id = merchant_id
        self.conversation_id = conversation_id
        self.track_costs = track_costs

        # Wrap the primary and backup providers with cost tracking
        self._primary_provider = CostTrackingLLMWrapper(
            llm_service=llm_router.primary_provider,
            db=db,
            merchant_id=merchant_id,
            conversation_id=conversation_id,
            track_costs=track_costs,
        )

        if llm_router.backup_provider:
            self._backup_provider = CostTrackingLLMWrapper(
                llm_service=llm_router.backup_provider,
                db=db,
                merchant_id=merchant_id,
                conversation_id=conversation_id,
                track_costs=track_costs,
            )
        else:
            self._backup_provider = None

    async def chat(
        self,
        messages: List[LLMMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        use_backup: bool = False,
    ) -> LLMResponse:
        """Send chat completion with automatic cost tracking.

        Follows the same failover logic as LLMRouter but tracks
        costs for both primary and backup provider requests.

        Args:
            messages: Conversation history
            model: Model override (optional)
            temperature: Response randomness
            max_tokens: Maximum tokens in response
            use_backup: Force use of backup provider

        Returns:
            LLM response with content and metadata

        Raises:
            APIError: If both primary and backup providers fail
        """
        provider = self._backup_provider if use_backup else self._primary_provider
        provider_name = "backup" if use_backup else "primary"

        try:
            logger.info(
                "llm_cost_router_attempt",
                provider=provider_name,
                use_backup=use_backup,
                conversation_id=self.conversation_id,
            )

            response = await provider.chat(messages, model, temperature, max_tokens)

            logger.info(
                "llm_cost_router_success",
                provider=provider_name,
                tokens_used=response.tokens_used,
                model=response.model,
                conversation_id=self.conversation_id,
            )

            return response

        except Exception as e:
            logger.warning(
                "llm_cost_router_primary_failed",
                error=str(e),
                backup_available=self._backup_provider is not None,
                conversation_id=self.conversation_id,
            )

            if self._backup_provider and not use_backup:
                logger.info(
                    "llm_cost_router_fallback",
                    fallback_to="backup",
                    conversation_id=self.conversation_id,
                )

                try:
                    response = await self._backup_provider.chat(
                        messages, model, temperature, max_tokens
                    )

                    logger.info(
                        "llm_cost_router_backup_success",
                        tokens_used=response.tokens_used,
                        model=response.model,
                        conversation_id=self.conversation_id,
                    )

                    return response

                except Exception as backup_error:
                    logger.error(
                        "llm_cost_router_both_failed",
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
