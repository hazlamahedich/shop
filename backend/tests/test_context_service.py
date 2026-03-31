"""Story 11-1: Unit tests for ConversationContextService.

Tests Redis+PostgreSQL hybrid storage, context CRUD, summarization,
and TTL behavior with mocked dependencies.

Acceptance Criteria:
- Context CRUD with Redis cache and PostgreSQL fallback
- Summarization triggers at correct intervals
- 24-hour TTL on Redis keys
- Context merges with existing data
"""

import json
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.conversation_context import ConversationContext
from app.services.conversation_context import ConversationContextService
from tests.helpers.context_factories import (
    create_mock_context,
    create_mock_context_model,
    create_mock_db_session,
    create_mock_redis_client,
)


@pytest.fixture
def mock_redis():
    return create_mock_redis_client()


@pytest.fixture
def mock_db_session():
    return create_mock_db_session()


class TestConversationContextService:
    @pytest.mark.asyncio
    async def test_get_context_from_redis(self, mock_redis, mock_db_session):
        """Context retrieved from Redis cache when available. [11.1-SVC-001]"""
        # Given: Context data cached in Redis
        context_data = create_mock_context(
            mode="ecommerce",
            turn_count=5,
            viewed_products=[123, 456],
            constraints={"budget_max": 100},
        )
        mock_redis.get.return_value = json.dumps(context_data)
        # When: Retrieving context
        service = ConversationContextService(db=mock_db_session, redis_client=mock_redis)
        result = await service.get_context(123)
        # Then: Redis cache is used
        assert result is not None
        assert result["mode"] == "ecommerce"
        assert result["turn_count"] == 5
        assert result["viewed_products"] == [123, 456]
        assert result["constraints"]["budget_max"] == 100
        mock_redis.get.assert_called_once_with("conversation_context:123")

    @pytest.mark.asyncio
    async def test_get_context_fallback_to_postgres(self, mock_redis, mock_db_session):
        """Falls back to PostgreSQL when Redis cache misses. [11.1-SVC-002]"""
        mock_redis.get.return_value = None
        mock_context_model = create_mock_context_model(
            mode="ecommerce", turn_count=3, viewed_products=[789]
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_context_model
        mock_db_session.execute = lambda stmt: mock_result.__class__(mock_result._mock_name)
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        service = ConversationContextService(db=mock_db_session, redis_client=mock_redis)
        result = await service.get_context(123)
        assert result is not None
        assert result["mode"] == "ecommerce"
        assert result["viewed_products"] == [789]

    @pytest.mark.asyncio
    async def test_get_context_expired(self, mock_redis, mock_db_session):
        """Expired contexts return None. [11.1-SVC-003]"""
        mock_redis.get.return_value = None
        mock_context_model = create_mock_context_model(
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1)
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_context_model
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        service = ConversationContextService(db=mock_db_session, redis_client=mock_redis)
        result = await service.get_context(123)
        assert result is None

    @pytest.mark.asyncio
    async def test_update_context_ecommerce_mode(self, mock_redis, mock_db_session):
        """Ecommerce mode update extracts products and constraints. [11.1-SVC-004]"""
        mock_redis.get.return_value = None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        mock_db_session.add = MagicMock()
        mock_db_session.commit = AsyncMock()
        service = ConversationContextService(db=mock_db_session, redis_client=mock_redis)
        result = await service.update_context(
            conversation_id=123,
            merchant_id=1,
            message="Show me red shoes under $100",
            mode="ecommerce",
        )
        assert result["mode"] == "ecommerce"
        assert result["turn_count"] == 1
        assert "constraints" in result
        assert "search_history" in result
        mock_redis.setex.assert_called_once()
        assert "conversation_context:123" in str(mock_redis.setex.call_args)

    @pytest.mark.asyncio
    async def test_update_context_general_mode(self, mock_redis, mock_db_session):
        """General mode update extracts topics discussed. [11.1-SVC-005]"""
        mock_redis.get.return_value = None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        mock_db_session.add = MagicMock()
        mock_db_session.commit = AsyncMock()
        service = ConversationContextService(db=mock_db_session, redis_client=mock_redis)
        result = await service.update_context(
            conversation_id=456, merchant_id=1, message="I'm having login issues", mode="general"
        )
        assert result["mode"] == "general"
        assert result["turn_count"] == 1
        assert "topics_discussed" in result

    @pytest.mark.asyncio
    async def test_update_context_merges_with_existing(self, mock_redis, mock_db_session):
        """Updates merge with existing context, preserving prior data. [11.1-SVC-006]"""
        existing = create_mock_context(
            mode="ecommerce", turn_count=2, viewed_products=[123], constraints={"budget_max": 100}
        )
        mock_redis.get.return_value = json.dumps(existing)
        mock_result = MagicMock()
        mock_model = create_mock_context_model(
            mode="ecommerce", turn_count=2, viewed_products=[123], constraints={"budget_max": 100}
        )
        mock_result.scalar_one_or_none.return_value = mock_model
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        mock_db_session.commit = AsyncMock()
        service = ConversationContextService(db=mock_db_session, redis_client=mock_redis)
        result = await service.update_context(
            conversation_id=123, merchant_id=1, message="What about in blue?", mode="ecommerce"
        )
        assert result["turn_count"] == 3
        assert 123 in result["viewed_products"]

    @pytest.mark.asyncio
    async def test_should_summarize_every_5_turns(self, mock_redis, mock_db_session):
        """Summarization triggers when turn_count is divisible by 5. [11.1-SVC-007]"""
        service = ConversationContextService(db=mock_db_session, redis_client=mock_redis)
        assert await service.should_summarize({"turn_count": 5}) is True
        assert await service.should_summarize({"turn_count": 4}) is False

    @pytest.mark.asyncio
    async def test_should_summarize_when_size_exceeds_1kb(self, mock_redis, mock_db_session):
        """Summarization triggers when context size exceeds 1KB. [11.1-SVC-008]"""
        service = ConversationContextService(db=mock_db_session, redis_client=mock_redis)
        large_context = {"turn_count": 2, "data": "x" * 2000}
        assert await service.should_summarize(large_context) is True

    @pytest.mark.asyncio
    async def test_summarize_context_with_llm(self, mock_redis, mock_db_session):
        """Summarization produces key points and preserves constraints. [11.1-SVC-009]"""
        service = ConversationContextService(db=mock_db_session, redis_client=mock_redis)
        context = create_mock_context(
            mode="ecommerce",
            turn_count=10,
            viewed_products=[123, 456, 789],
            constraints={"budget_max": 100, "color": "red"},
        )
        summary = await service.summarize_context(123, context)
        assert summary["original_turns"] == 10
        assert "summarized_at" in summary
        assert isinstance(summary["key_points"], list)
        assert summary["active_constraints"]["budget_max"] == 100

    @pytest.mark.asyncio
    async def test_delete_context(self, mock_redis, mock_db_session):
        """Delete removes context from both Redis and PostgreSQL. [11.1-SVC-010]"""
        mock_model = MagicMock(spec=ConversationContext)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_model
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        mock_db_session.delete = AsyncMock()
        mock_db_session.commit = AsyncMock()
        service = ConversationContextService(db=mock_db_session, redis_client=mock_redis)
        await service.delete_context(123)
        mock_redis.delete.assert_called_once_with("conversation_context:123")
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_redis_24h_ttl(self, mock_redis, mock_db_session):
        """Redis keys are set with 24-hour TTL (86400 seconds). [11.1-SVC-011]"""
        mock_redis.get.return_value = None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        mock_db_session.add = MagicMock()
        mock_db_session.commit = AsyncMock()
        service = ConversationContextService(db=mock_db_session, redis_client=mock_redis)
        await service.update_context(
            conversation_id=123, merchant_id=1, message="test", mode="ecommerce"
        )
        ttl_arg = mock_redis.setex.call_args[0][1]
        assert ttl_arg == 86400

    @pytest.mark.asyncio
    async def test_sequential_updates_accumulate(self, mock_redis, mock_db_session):
        """Multiple sequential updates don't lose earlier context data. [11.1-SVC-012]"""
        stored_contexts = {}

        def fake_setex(key, ttl, value):
            stored_contexts[key] = value

        mock_redis.get.side_effect = lambda key: stored_contexts.get(key)
        mock_redis.setex = MagicMock(side_effect=fake_setex)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        mock_db_session.add = MagicMock()
        mock_db_session.commit = AsyncMock()
        service = ConversationContextService(db=mock_db_session, redis_client=mock_redis)
        for i, msg in enumerate(["Show me #100", "Also #200", "And #300"]):
            result = await service.update_context(
                conversation_id=123, merchant_id=1, message=msg, mode="ecommerce"
            )
            assert result["turn_count"] == i + 1
