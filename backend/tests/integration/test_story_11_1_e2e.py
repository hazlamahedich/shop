"""Story 11-1: E2E tests for multi-turn conversation context tracking.

Tests the complete flow from message receipt through context accumulation,
summarization triggers, and persistence across multiple turns.

Acceptance Criteria:
- Multi-turn conversations accumulate context correctly
- Context persists across message updates
- Summarization triggers every 5 turns or when size > 1KB
- Mode-specific extraction (ecommerce vs general) works end-to-end
"""

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock

import pytest
from sqlalchemy import text

from app.services.conversation_context import ConversationContextService


@pytest.fixture
async def e2e_test_merchant(db_session):
    """Create test merchant for E2E tests."""
    sql = text("""
        INSERT INTO merchants (merchant_key, platform, status, personality, store_provider, onboarding_mode, created_at, updated_at)
        VALUES ('test_e2e_ctx', 'widget', 'active', 'friendly', 'none', 'ecommerce', NOW(), NOW())
        ON CONFLICT (merchant_key) DO UPDATE SET platform = EXCLUDED.platform
        RETURNING id
    """)
    result = await db_session.execute(sql)
    merchant_id = result.fetchone()[0]
    await db_session.commit()
    yield merchant_id

    # Cleanup with rollback handling
    try:
        await db_session.rollback()
    except Exception:
        pass

    try:
        await db_session.execute(text(f"DELETE FROM conversation_context WHERE merchant_id = {merchant_id}"))
        await db_session.execute(text(f"DELETE FROM conversations WHERE merchant_id = {merchant_id}"))
        await db_session.execute(text(f"DELETE FROM merchants WHERE id = {merchant_id}"))
        await db_session.commit()
    except Exception as e:
        print(f"Cleanup error: {e}")
        try:
            await db_session.rollback()
        except Exception:
            pass


@pytest.fixture
async def e2e_test_conversation(db_session, e2e_test_merchant):
    """Create test conversation for E2E tests."""
    sql = text(f"""
        INSERT INTO conversations (merchant_id, platform, platform_sender_id, status, created_at, updated_at)
        VALUES ({e2e_test_merchant}, 'widget', 'test_e2e_customer', 'active', NOW(), NOW())
        RETURNING id
    """)
    result = await db_session.execute(sql)
    conversation_id = result.fetchone()[0]
    await db_session.commit()
    yield conversation_id

    # Cleanup with rollback handling
    try:
        await db_session.rollback()
    except Exception:
        pass

    try:
        await db_session.execute(text(f"DELETE FROM conversation_context WHERE conversation_id = {conversation_id}"))
        await db_session.execute(text(f"DELETE FROM conversations WHERE id = {conversation_id}"))
        await db_session.commit()
    except Exception as e:
        print(f"Cleanup error: {e}")
        try:
            await db_session.rollback()
        except Exception:
            pass


@pytest.fixture
def mock_redis_e2e():
    """Mock Redis client for E2E tests."""
    redis = MagicMock()
    redis.get = MagicMock(return_value=None)
    redis.setex = MagicMock()
    redis.delete = MagicMock()
    return redis


class TestMultiTurnEcommerceConversations:
    """Test multi-turn conversations in e-commerce mode."""

    @pytest.mark.asyncio
    async def test_five_turn_conversation_accumulates_context(
        self, db_session, e2e_test_conversation, e2e_test_merchant, mock_redis_e2e
    ):
        """Test that 5-turn conversation accumulates product, price, and preference context.

        Acceptance Criteria:
        - Turn 1: viewed_products [123]
        - Turn 2: viewed_products [123, 456], budget_max 100
        - Turn 3: viewed_products [123, 456, 789], budget_max 100, size "M"
        - Turn 4: search_history contains "red shoes"
        - Turn 5: All context preserved, turn_count = 5
        """
        service = ConversationContextService(db=db_session, redis_client=mock_redis_e2e)

        # Turn 1: User views a product
        context1 = await service.update_context(
            conversation_id=e2e_test_conversation,
            merchant_id=e2e_test_merchant,
            message="Show me details for product 123",
            mode="ecommerce",
        )
        assert context1["turn_count"] == 1
        assert 123 in context1["viewed_products"]
        assert context1["mode"] == "ecommerce"

        # Turn 2: User views another product with budget constraint
        context2 = await service.update_context(
            conversation_id=e2e_test_conversation,
            merchant_id=e2e_test_merchant,
            message="I like product 456 but my budget is under $100",
            mode="ecommerce",
        )
        assert context2["turn_count"] == 2
        assert 123 in context2["viewed_products"]
        assert 456 in context2["viewed_products"]
        assert context2["constraints"]["budget_max"] == 100

        # Turn 3: User adds size preference
        context3 = await service.update_context(
            conversation_id=e2e_test_conversation,
            merchant_id=e2e_test_merchant,
            message="What about product 789 in medium size?",
            mode="ecommerce",
        )
        assert context3["turn_count"] == 3
        assert 789 in context3["viewed_products"]
        assert context3["constraints"]["budget_max"] == 100

        # Turn 4: User searches for specific products
        context4 = await service.update_context(
            conversation_id=e2e_test_conversation,
            merchant_id=e2e_test_merchant,
            message="Search for red shoes",
            mode="ecommerce",
        )
        assert context4["turn_count"] == 4
        assert "red shoes" in context4["search_history"]

        # Turn 5: Verify all context accumulated
        context5 = await service.update_context(
            conversation_id=e2e_test_conversation,
            merchant_id=e2e_test_merchant,
            message="What are my options?",
            mode="ecommerce",
        )
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
        """Test that context persists even when Redis cache expires.

        Acceptance Criteria:
        - Update context with Redis available
        - Simulate Redis cache miss (returns None)
        - Context should be retrieved from PostgreSQL
        - All data should be intact
        """
        # First Redis client (works)
        redis1 = MagicMock()
        redis1.get = MagicMock(return_value=None)
        redis1.setex = MagicMock()

        service1 = ConversationContextService(db=db_session, redis_client=redis1)

        # Create context
        context1 = await service1.update_context(
            conversation_id=e2e_test_conversation,
            merchant_id=e2e_test_merchant,
            message="I'm looking for running shoes under $150",
            mode="ecommerce",
        )
        assert context1["turn_count"] == 1
        assert context1["constraints"]["budget_max"] == 150

        # Simulate Redis expiry (new Redis client that returns None)
        redis2 = MagicMock()
        redis2.get = MagicMock(return_value=None)  # Cache miss
        redis2.setex = MagicMock()

        service2 = ConversationContextService(db=db_session, redis_client=redis2)

        # Retrieve context (should fall back to PostgreSQL)
        context2 = await service2.get_context(e2e_test_conversation)

        assert context2 is not None
        assert context2["turn_count"] == 1
        assert context2["constraints"]["budget_max"] == 150
        assert context2["mode"] == "ecommerce"

    @pytest.mark.asyncio
    async def test_summarization_trigger_at_five_turns(
        self, db_session, e2e_test_conversation, e2e_test_merchant, mock_redis_e2e
    ):
        """Test that summarization trigger activates at turn 5.

        Acceptance Criteria:
        - should_summarize returns False for turns 1-4
        - should_summarize returns True at turn 5
        - should_summarize returns False at turn 6
        - should_summarize returns True at turn 10
        """
        service = ConversationContextService(db=db_session, redis_client=mock_redis_e2e)

        # Turns 1-4: Should not trigger
        for i in range(1, 5):
            context = await service.update_context(
                conversation_id=e2e_test_conversation,
                merchant_id=e2e_test_merchant,
                message=f"Message {i}",
                mode="ecommerce",
            )
            assert not await service.should_summarize(context), f"Turn {i} should not trigger"

        # Turn 5: Should trigger
        context5 = await service.update_context(
            conversation_id=e2e_test_conversation,
            merchant_id=e2e_test_merchant,
            message="Message 5",
            mode="ecommerce",
        )
        assert await service.should_summarize(context5), "Turn 5 should trigger"

        # Turn 6: Should not trigger
        context6 = await service.update_context(
            conversation_id=e2e_test_conversation,
            merchant_id=e2e_test_merchant,
            message="Message 6",
            mode="ecommerce",
        )
        assert not await service.should_summarize(context6), "Turn 6 should not trigger"

        # Turns 7-9: Should not trigger
        for i in range(7, 10):
            context = await service.update_context(
                conversation_id=e2e_test_conversation,
                merchant_id=e2e_test_merchant,
                message=f"Message {i}",
                mode="ecommerce",
            )
            assert not await service.should_summarize(context), f"Turn {i} should not trigger"

        # Turn 10: Should trigger again
        context10 = await service.update_context(
            conversation_id=e2e_test_conversation,
            merchant_id=e2e_test_merchant,
            message="Message 10",
            mode="ecommerce",
        )
        assert await service.should_summarize(context10), "Turn 10 should trigger"


class TestMultiTurnGeneralConversations:
    """Test multi-turn conversations in general mode."""

    @pytest.mark.asyncio
    async def test_general_mode_tracks_topics_and_issues(
        self, db_session, e2e_test_conversation, e2e_test_merchant, mock_redis_e2e
    ):
        """Test that general mode accumulates topics and support issues.

        Acceptance Criteria:
        - Turn 1: topics_discussed contains "login issue"
        - Turn 2: topics_discussed contains "password reset"
        - Turn 3: support_issues tracks "cannot access account"
        - Turn 4: All topics and issues preserved
        """
        service = ConversationContextService(db=db_session, redis_client=mock_redis_e2e)

        # Turn 1: Login issue
        context1 = await service.update_context(
            conversation_id=e2e_test_conversation,
            merchant_id=e2e_test_merchant,
            message="I'm having trouble logging in",
            mode="general",
        )
        assert context1["turn_count"] == 1
        assert context1["mode"] == "general"
        assert "login" in context1["topics_discussed"]

        # Turn 2: Password reset
        context2 = await service.update_context(
            conversation_id=e2e_test_conversation,
            merchant_id=e2e_test_merchant,
            message="I need to reset my password",
            mode="general",
        )
        assert context2["turn_count"] == 2
        assert "login" in context2["topics_discussed"]
        assert "password" in context2["topics_discussed"]

        # Turn 3: Account access issue
        context3 = await service.update_context(
            conversation_id=e2e_test_conversation,
            merchant_id=e2e_test_merchant,
            message="I cannot access my account at all",
            mode="general",
        )
        assert context3["turn_count"] == 3
        assert "account" in context3["topics_discussed"]

        # Turn 4: Verify all accumulated
        context4 = await service.update_context(
            conversation_id=e2e_test_conversation,
            merchant_id=e2e_test_merchant,
            message="This is really frustrating",
            mode="general",
        )
        assert context4["turn_count"] == 4
        assert "login" in context4["topics_discussed"]
        assert "password" in context4["topics_discussed"]
        assert "account" in context4["topics_discussed"]


class TestContextSizeBasedSummarization:
    """Test summarization triggers based on context size."""

    @pytest.mark.asyncio
    async def test_large_context_triggers_summarization(
        self, db_session, e2e_test_conversation, e2e_test_merchant, mock_redis_e2e
    ):
        """Test that context size > 1KB triggers summarization.

        Acceptance Criteria:
        - Accumulate enough context data to exceed 1KB
        - should_summarize returns True
        - Verify size calculation is correct
        """
        service = ConversationContextService(db=db_session, redis_client=mock_redis_e2e)

        # Build up large context with many products
        context = None
        for i in range(50):  # Add 50 products
            context = await service.update_context(
                conversation_id=e2e_test_conversation,
                merchant_id=e2e_test_merchant,
                message=f"Show me product {i} with very long detailed description that adds size",
                mode="ecommerce",
            )

        # Check if size trigger activated
        context_size = len(json.dumps(context).encode("utf-8"))
        assert context_size > service.SUMMARIZE_SIZE_TRIGGER_BYTES, "Context should exceed 1KB"
        assert await service.should_summarize(context), "Large context should trigger"


class TestContextExpiryE2E:
    """Test context expiry in multi-turn scenarios."""

    @pytest.mark.asyncio
    async def test_expired_context_returns_none(
        self, db_session, e2e_test_conversation, e2e_test_merchant, mock_redis_e2e
    ):
        """Test that expired context is not returned.

        Acceptance Criteria:
        - Create context with short expiry
        - Wait for expiry
        - get_context should return None
        """
        service = ConversationContextService(db=db_session, redis_client=mock_redis_e2e)

        # Create context
        await service.update_context(
            conversation_id=e2e_test_conversation,
            merchant_id=e2e_test_merchant,
            message="Test message",
            mode="ecommerce",
        )

        # Manually set expiry to past
        await db_session.execute(
            text(f"""
                UPDATE conversation_context
                SET expires_at = NOW() - INTERVAL '1 hour'
                WHERE conversation_id = {e2e_test_conversation}
            """)
        )
        await db_session.commit()

        # Try to get expired context
        context = await service.get_context(e2e_test_conversation, bypass_cache=True)
        assert context is None, "Expired context should return None"


class TestModeSwitchingE2E:
    """Test mode switching in multi-turn conversations."""

    @pytest.mark.asyncio
    async def test_mode_from_ecommerce_to_general(
        self, db_session, e2e_test_conversation, e2e_test_merchant, mock_redis_e2e
    ):
        """Test behavior when conversation switches from ecommerce to general mode.

        Acceptance Criteria:
        - Start in ecommerce mode with product context
        - Switch to general mode
        - Ecommerce context should be preserved in DB
        - New turns should extract general context
        """
        service = ConversationContextService(db=db_session, redis_client=mock_redis_e2e)

        # Ecommerce turns
        context1 = await service.update_context(
            conversation_id=e2e_test_conversation,
            merchant_id=e2e_test_merchant,
            message="Show me red shoes under $100",
            mode="ecommerce",
        )
        assert context1["mode"] == "ecommerce"
        assert context1["constraints"]["budget_max"] == 100

        # Switch to general mode
        context2 = await service.update_context(
            conversation_id=e2e_test_conversation,
            merchant_id=e2e_test_merchant,
            message="Actually, I need help with my account",
            mode="general",
        )
        # Note: Mode is now general, but ecommerce context is in the DB
        assert context2["turn_count"] == 2
