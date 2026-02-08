"""Unit tests for LLM Cost Tracking integration.

Tests automatic cost tracking integration with LLM services.
"""

from __future__ import annotations

import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.llm_conversation_cost import LLMConversationCost
from app.services.llm.base_llm_service import LLMResponse, LLMMessage
from app.services.llm.openai_service import OpenAIService
from app.services.llm.ollama_service import OllamaService
from app.services.llm.llm_router import LLMRouter
from app.services.cost_tracking.cost_tracking_service import (
    CostTrackingService,
    track_llm_request,
)
from app.services.cost_tracking.llm_cost_wrapper import (
    CostTrackingLLMWrapper,
    CostTrackingLLMRouter,
)


@pytest.mark.asyncio
class TestLLMCostTrackingIntegration:
    """Test automatic LLM cost tracking integration."""

    async def test_track_llm_request_openai(
        self, async_session: AsyncSession
    ) -> None:
        """Test tracking OpenAI LLM request."""
        # Create a mock LLM response (OpenAI)
        response = LLMResponse(
            content="Test response",
            tokens_used=150,
            model="gpt-4o-mini",
            provider="openai",
            metadata={
                "input_tokens": 100,
                "output_tokens": 50,
            },
        )

        # Track the request
        cost_record = await track_llm_request(
            db=async_session,
            llm_response=response,
            conversation_id="test-conv-123",
            merchant_id=1,
        )

        # Verify cost record was created
        assert cost_record is not None
        assert cost_record.conversation_id == "test-conv-123"
        assert cost_record.merchant_id == 1
        assert cost_record.provider == "openai"
        assert cost_record.model == "gpt-4o-mini"
        assert cost_record.prompt_tokens == 100
        assert cost_record.completion_tokens == 50
        assert cost_record.total_tokens == 150

        # Verify cost calculation (gpt-4o-mini: $0.15/M input, $0.60/M output)
        # input: 100/1M * $0.15 = $0.000015
        # output: 50/1M * $0.60 = $0.00003
        # total: $0.000045
        assert cost_record.total_cost_usd > 0
        assert cost_record.total_cost_usd < 0.001  # Should be very small

        await async_session.flush()

    async def test_track_llm_request_ollama(
        self, async_session: AsyncSession
    ) -> None:
        """Test tracking Ollama LLM request (should be free)."""
        # Create a mock LLM response (Ollama)
        response = LLMResponse(
            content="Test response",
            tokens_used=1000,
            model="llama3",
            provider="ollama",
            metadata={
                "prompt_eval_count": 500,
                "eval_count": 500,
            },
        )

        # Track the request
        cost_record = await track_llm_request(
            db=async_session,
            llm_response=response,
            conversation_id="test-conv-ollama",
            merchant_id=1,
        )

        # Verify cost record was created
        assert cost_record is not None
        assert cost_record.provider == "ollama"
        assert cost_record.total_cost_usd == 0.0  # Ollama is free

        await async_session.flush()

    async def test_track_llm_request_anthropic(
        self, async_session: AsyncSession
    ) -> None:
        """Test tracking Anthropic LLM request."""
        response = LLMResponse(
            content="Test response",
            tokens_used=200,
            model="claude-3-haiku",
            provider="anthropic",
            metadata={
                "input_tokens": 150,
                "output_tokens": 50,
            },
        )

        cost_record = await track_llm_request(
            db=async_session,
            llm_response=response,
            conversation_id="test-conv-anthropic",
            merchant_id=1,
        )

        assert cost_record is not None
        assert cost_record.provider == "anthropic"
        assert cost_record.model == "claude-3-haiku"
        assert cost_record.total_cost_usd > 0

        await async_session.flush()

    async def test_track_llm_request_no_metadata_fallback(
        self, async_session: AsyncSession
    ) -> None:
        """Test tracking with missing metadata (50/50 token split)."""
        # Response without input/output token metadata
        response = LLMResponse(
            content="Test response",
            tokens_used=100,
            model="gpt-4o-mini",
            provider="openai",
            metadata={},  # No token breakdown
        )

        cost_record = await track_llm_request(
            db=async_session,
            llm_response=response,
            conversation_id="test-conv-no-meta",
            merchant_id=1,
        )

        # Should estimate 50/50 split
        assert cost_record is not None
        assert cost_record.prompt_tokens == 50  # 100 // 2
        assert cost_record.completion_tokens == 50  # 100 - 50
        assert cost_record.total_tokens == 100

        await async_session.flush()

    async def test_cost_tracking_wrapper(
        self, async_session: AsyncSession
    ) -> None:
        """Test CostTrackingLLMWrapper with actual LLM service."""
        # Create OpenAI service in test mode
        config = {"api_key": "test-key", "model": "gpt-4o-mini"}
        openai_service = OpenAIService(config, is_testing=True)

        # Wrap with cost tracking
        cost_wrapper = CostTrackingLLMWrapper(
            llm_service=openai_service,
            db=async_session,
            merchant_id=1,
            conversation_id="test-wrapper-conv",
        )

        # Make a chat request
        messages = [LLMMessage(role="user", content="Hello")]
        response = await cost_wrapper.chat(messages)

        # Verify response
        assert response.content == "Test response from OpenAI"
        assert response.provider == "openai"

        # Verify cost was tracked
        service = CostTrackingService()
        costs = await service.get_conversation_costs(
            db=async_session,
            merchant_id=1,
            conversation_id="test-wrapper-conv",
        )

        assert costs["requestCount"] == 1
        assert costs["totalCostUsd"] >= 0  # Test responses have minimal tokens

    async def test_cost_tracking_router(
        self, async_session: AsyncSession
    ) -> None:
        """Test CostTrackingLLMRouter with failover."""
        # Create LLM router config
        config = {
            "primary_provider": "ollama",
            "primary_config": {"ollama_url": "http://localhost:11434", "model": "llama3"},
            "backup_provider": "openai",
            "backup_config": {"api_key": "test-key", "model": "gpt-4o-mini"},
        }

        # Create router (is_testing=True uses MockService)
        llm_router = LLMRouter(config, is_testing=True)

        # Wrap with cost tracking
        cost_router = CostTrackingLLMRouter(
            llm_router=llm_router,
            db=async_session,
            merchant_id=1,
            conversation_id="test-router-conv",
        )

        # Make a chat request
        messages = [LLMMessage(role="user", content="Hello")]
        response = await cost_router.chat(messages)

        # Verify response
        assert response.content is not None

        # Verify cost was tracked (primary provider used)
        service = CostTrackingService()
        costs = await service.get_conversation_costs(
            db=async_session,
            merchant_id=1,
            conversation_id="test-router-conv",
        )

        assert costs["requestCount"] == 1
        # Note: is_testing=True uses MockService which reports provider="mock"
        assert costs["provider"] == "mock"
        assert costs["totalCostUsd"] == 0.0  # Mock has no cost

    async def test_track_llm_request_with_processing_time(
        self, async_session: AsyncSession
    ) -> None:
        """Test tracking with processing time."""
        response = LLMResponse(
            content="Test response",
            tokens_used=100,
            model="gpt-4o-mini",
            provider="openai",
            metadata={"input_tokens": 70, "output_tokens": 30},
        )

        cost_record = await track_llm_request(
            db=async_session,
            llm_response=response,
            conversation_id="test-conv-time",
            merchant_id=1,
            processing_time_ms=250.5,
        )

        assert cost_record is not None
        assert cost_record.processing_time_ms == 250.5

        await async_session.flush()

    async def test_track_llm_request_merchant_isolation(
        self, async_session: AsyncSession
    ) -> None:
        """Test that cost tracking respects merchant isolation."""
        response = LLMResponse(
            content="Test response",
            tokens_used=50,
            model="gpt-4o-mini",
            provider="openai",
            metadata={"input_tokens": 30, "output_tokens": 20},
        )

        # Track for merchant 1
        await track_llm_request(
            db=async_session,
            llm_response=response,
            conversation_id="test-conv-isolation",
            merchant_id=1,
        )

        # Track for merchant 2 (same conversation ID)
        await track_llm_request(
            db=async_session,
            llm_response=response,
            conversation_id="test-conv-isolation",
            merchant_id=2,
        )

        await async_session.flush()

        # Verify merchant isolation
        service = CostTrackingService()

        # Merchant 1 should see only their costs
        costs_1 = await service.get_conversation_costs(
            db=async_session,
            merchant_id=1,
            conversation_id="test-conv-isolation",
        )
        assert costs_1["requestCount"] == 1

        # Merchant 2 should see only their costs
        costs_2 = await service.get_conversation_costs(
            db=async_session,
            merchant_id=2,
            conversation_id="test-conv-isolation",
        )
        assert costs_2["requestCount"] == 1

    async def test_cost_tracking_wrapper_disabled(
        self, async_session: AsyncSession
    ) -> None:
        """Test CostTrackingLLMWrapper with tracking disabled."""
        config = {"api_key": "test-key", "model": "gpt-4o-mini"}
        openai_service = OpenAIService(config, is_testing=True)

        # Wrap with tracking DISABLED
        cost_wrapper = CostTrackingLLMWrapper(
            llm_service=openai_service,
            db=async_session,
            merchant_id=1,
            conversation_id="test-disabled-conv",
            track_costs=False,
        )

        # Make a chat request
        messages = [LLMMessage(role="user", content="Hello")]
        response = await cost_wrapper.chat(messages)

        # Verify response still works
        assert response.content == "Test response from OpenAI"

        # Verify NO cost was tracked
        service = CostTrackingService()
        with pytest.raises(ValueError, match="No cost data found"):
            await service.get_conversation_costs(
                db=async_session,
                merchant_id=1,
                conversation_id="test-disabled-conv",
            )
