"""Story 11-1: E2E tests for ecommerce multi-turn context tracking.

Tests multi-turn ecommerce context accumulation, summarization triggers
based on turn count and size, and Redis cache expiry fallback.

Acceptance Criteria:
- Multi-turn conversations accumulate context correctly
- Context persists across Redis cache expiry
- Summarization triggers every 5 turns
- Summarization triggers when size > 1KB
"""

import json

import pytest
from sqlalchemy import text

from app.services.conversation_context import ConversationContextService
from tests.helpers.context_factories import create_mock_redis_client


class TestMultiTurnEcommerceConversations:
    """Test multi-turn conversations in e-commerce mode."""

    @pytest.mark.asyncio
    async def test_five_turn_conversation_accumulates_context(
        self, db_session, e2e_test_conversation, e2e_test_merchant, mock_redis_e2e
    ):
        """5-turn ecommerce flow accumulates products, prices, preferences. [11.1-E2E-001]"""
        # Given: A new conversation with no prior context
        service = ConversationContextService(db=db_session, redis_client=mock_redis_e2e)

        # When: User views product 123
        context1 = await service.update_context(
            conversation_id=e2e_test_conversation,
            merchant_id=e2e_test_merchant,
            message="Show me details for product 123",
            mode="ecommerce",
        )
        # Then: Product 123 is tracked, turn count is 1
        assert context1["turn_count"] == 1
        assert 123 in context1["viewed_products"]
        assert context1["mode"] == "ecommerce"

        # When: User views another product with budget constraint
        context2 = await service.update_context(
            conversation_id=e2e_test_conversation,
            merchant_id=e2e_test_merchant,
            message="I like product 456 but my budget is under $100",
            mode="ecommerce",
        )
        # Then: Both products tracked, budget constraint extracted
        assert context2["turn_count"] == 2
        assert 123 in context2["viewed_products"]
        assert 456 in context2["viewed_products"]
        assert context2["constraints"]["budget_max"] == 100

        # When: User adds size preference
        context3 = await service.update_context(
            conversation_id=e2e_test_conversation,
            merchant_id=e2e_test_merchant,
            message="What about product 789 in medium size?",
            mode="ecommerce",
        )
        # Then: Third product added, budget preserved
        assert context3["turn_count"] == 3
        assert 789 in context3["viewed_products"]
        assert context3["constraints"]["budget_max"] == 100

        # When: User searches for specific products
        context4 = await service.update_context(
            conversation_id=e2e_test_conversation,
            merchant_id=e2e_test_merchant,
            message="Search for red shoes",
            mode="ecommerce",
        )
        # Then: Search history updated
        assert context4["turn_count"] == 4
        assert "red shoes" in context4["search_history"]

        # When: User asks for options (turn 5)
        context5 = await service.update_context(
            conversation_id=e2e_test_conversation,
            merchant_id=e2e_test_merchant,
            message="What are my options?",
            mode="ecommerce",
        )
        # Then: All context from all 5 turns accumulated
        assert context5["turn_count"] == 5
        assert 123 in context5["viewed_products"]
        assert 456 in context5["viewed_products"]
        assert 789 in context5["viewed_products"]
        assert context5["constraints"]["budget_max"] == 100
        assert "red shoes" in context5["search_history"]

    @pytest.mark.asyncio
    async def test_context_persists_across_redis_cache_expiry(
        self, db_session, e2e_test_conversation, e2e_test_merchant
    ):
        """Context survives Redis cache miss by falling back to PostgreSQL. [11.1-E2E-002]"""
        # Given: A Redis client that will cache the context
        redis1 = create_mock_redis_client()
        service1 = ConversationContextService(db=db_session, redis_client=redis1)

        # When: Context is created via first service instance
        context1 = await service1.update_context(
            conversation_id=e2e_test_conversation,
            merchant_id=e2e_test_merchant,
            message="I'm looking for running shoes under $150",
            mode="ecommerce",
        )
        # Then: Turn count and budget are set
        assert context1["turn_count"] == 1
        assert context1["constraints"]["budget_max"] == 150

        # Given: A fresh Redis client simulating cache expiry
        redis2 = create_mock_redis_client()
        service2 = ConversationContextService(db=db_session, redis_client=redis2)

        # When: Context is retrieved after simulated Redis expiry
        context2 = await service2.get_context(e2e_test_conversation)
        # Then: Context is restored from PostgreSQL fallback
        assert context2 is not None
        assert context2["turn_count"] == 1
        assert context2["constraints"]["budget_max"] == 150
        assert context2["mode"] == "ecommerce"

    @pytest.mark.asyncio
    async def test_summarization_trigger_at_five_turns(
        self, db_session, e2e_test_conversation, e2e_test_merchant, mock_redis_e2e
    ):
        """Summarization triggers at turns 5 and 10 but not at other turns. [11.1-E2E-003]"""
        # Given: A new conversation context service
        service = ConversationContextService(db=db_session, redis_client=mock_redis_e2e)

        # When/Then: Turns 1-4 should NOT trigger summarization
        for i in range(1, 5):
            context = await service.update_context(
                conversation_id=e2e_test_conversation,
                merchant_id=e2e_test_merchant,
                message=f"Message {i}",
                mode="ecommerce",
            )
            assert not await service.should_summarize(context), f"Turn {i} should not trigger"

        # When: Turn 5 is reached
        context5 = await service.update_context(
            conversation_id=e2e_test_conversation,
            merchant_id=e2e_test_merchant,
            message="Message 5",
            mode="ecommerce",
        )
        # Then: Summarization SHOULD trigger
        assert await service.should_summarize(context5), "Turn 5 should trigger"

        # When: Turn 6 is reached
        context6 = await service.update_context(
            conversation_id=e2e_test_conversation,
            merchant_id=e2e_test_merchant,
            message="Message 6",
            mode="ecommerce",
        )
        # Then: Summarization should NOT trigger
        assert not await service.should_summarize(context6), "Turn 6 should not trigger"

        # When/Then: Turns 7-9 should NOT trigger
        for i in range(7, 10):
            context = await service.update_context(
                conversation_id=e2e_test_conversation,
                merchant_id=e2e_test_merchant,
                message=f"Message {i}",
                mode="ecommerce",
            )
            assert not await service.should_summarize(context), f"Turn {i} should not trigger"

        # When: Turn 10 is reached
        context10 = await service.update_context(
            conversation_id=e2e_test_conversation,
            merchant_id=e2e_test_merchant,
            message="Message 10",
            mode="ecommerce",
        )
        # Then: Summarization SHOULD trigger again
        assert await service.should_summarize(context10), "Turn 10 should trigger"


class TestContextSizeBasedSummarization:
    """Test summarization triggers based on context size."""

    @pytest.mark.asyncio
    async def test_large_context_triggers_summarization(
        self, db_session, e2e_test_conversation, e2e_test_merchant, mock_redis_e2e
    ):
        """Context exceeding 1KB triggers size-based summarization. [11.1-E2E-004]"""
        # Given: A new context service
        service = ConversationContextService(db=db_session, redis_client=mock_redis_e2e)

        # When: Accumulating enough context data to exceed 1KB
        context = None
        for i in range(50):
            context = await service.update_context(
                conversation_id=e2e_test_conversation,
                merchant_id=e2e_test_merchant,
                message=f"Show me product {i} with very long detailed description that adds size",
                mode="ecommerce",
            )

        # Then: Context exceeds 1KB and triggers summarization
        context_size = len(json.dumps(context).encode("utf-8"))
        assert context_size > service.SUMMARIZE_SIZE_TRIGGER_BYTES, "Context should exceed 1KB"
        assert await service.should_summarize(context), "Large context should trigger"

    @pytest.mark.asyncio
    async def test_summarization_boundary_at_exact_threshold(
        self, db_session, e2e_test_conversation, e2e_test_merchant, mock_redis_e2e
    ):
        """Context at exactly the size threshold triggers summarization. [11.1-E2E-005]"""
        # Given: A context service
        service = ConversationContextService(db=db_session, redis_client=mock_redis_e2e)

        # When: Context exceeds the size boundary
        target_size = service.SUMMARIZE_SIZE_TRIGGER_BYTES
        boundary_context = {
            "turn_count": 2,
            "data": "x" * (target_size + 100),
        }

        # Then: Should trigger because it exceeds the threshold
        assert await service.should_summarize(boundary_context), "Boundary context should trigger"
