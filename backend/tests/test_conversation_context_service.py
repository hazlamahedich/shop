"""Test Conversation Context Service (Task 2: Redis Context Storage).

Story 11-1: Conversation Context Memory
Tests for Redis-backed conversation context service with mode-aware extraction.
"""

import json
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from redis import Redis

from app.models.conversation_context import ConversationContext
from app.services.conversation_context import ConversationContextService


# Fixtures
@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    return MagicMock(spec=Redis)


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    return AsyncMock()


class TestConversationContextService:
    """Test ConversationContextService with Redis + PostgreSQL."""

    @pytest.mark.asyncio
    async def test_get_context_from_redis(self, mock_redis, mock_db_session):
        """Test retrieving context from Redis cache."""
        # Setup
        conversation_id = 123
        context_data = {
            "mode": "ecommerce",
            "turn_count": 5,
            "viewed_products": [123, 456],
            "constraints": {"budget_max": 100},
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
        }
        mock_redis.get.return_value = json.dumps(context_data)

        # Execute
        service = ConversationContextService(db=mock_db_session, redis_client=mock_redis)
        result = await service.get_context(conversation_id)

        # Verify
        assert result is not None
        assert result["mode"] == "ecommerce"
        assert result["turn_count"] == 5
        assert result["viewed_products"] == [123, 456]
        assert result["constraints"]["budget_max"] == 100
        mock_redis.get.assert_called_once_with(f"conversation_context:{conversation_id}")

    @pytest.mark.asyncio
    async def test_get_context_fallback_to_postgres(self, mock_redis, mock_db_session):
        """Test fallback to PostgreSQL when Redis cache miss."""
        # Setup: Redis returns None
        mock_redis.get.return_value = None

        # Setup: Mock database to return context
        conversation_id = 123
        mock_context_model = MagicMock(spec=ConversationContext)
        mock_context_model.mode = "ecommerce"
        mock_context_model.turn_count = 3
        mock_context_model.viewed_products = [789]
        mock_context_model.cart_items = None
        mock_context_model.constraints = None
        mock_context_model.search_history = None
        mock_context_model.topics_discussed = None
        mock_context_model.documents_referenced = None
        mock_context_model.support_issues = None
        mock_context_model.escalation_status = None
        mock_context_model.expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        # Mock SQLAlchemy result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_context_model

        async def mock_execute(stmt):
            return mock_result

        mock_db_session.execute = mock_execute

        # Execute
        service = ConversationContextService(db=mock_db_session, redis_client=mock_redis)
        result = await service.get_context(conversation_id)

        # Verify
        assert result is not None
        assert result["mode"] == "ecommerce"
        assert result["turn_count"] == 3
        assert result["viewed_products"] == [789]

    @pytest.mark.asyncio
    async def test_get_context_expired(self, mock_redis, mock_db_session):
        """Test that expired contexts return None."""
        # Setup: Redis miss, expired DB context
        mock_redis.get.return_value = None

        mock_context_model = MagicMock(spec=ConversationContext)
        mock_context_model.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)  # Expired

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_context_model

        async def mock_execute(stmt):
            return mock_result

        mock_db_session.execute = mock_execute

        # Execute
        service = ConversationContextService(db=mock_db_session, redis_client=mock_redis)
        result = await service.get_context(123)

        # Verify
        assert result is None

    @pytest.mark.asyncio
    async def test_update_context_ecommerce_mode(self, mock_redis, mock_db_session):
        """Test updating context in e-commerce mode."""
        # Setup: No existing context
        mock_redis.get.return_value = None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None  # No existing context

        async def mock_execute(stmt):
            return mock_result

        mock_db_session.execute = mock_execute
        mock_db_session.add = MagicMock()
        mock_db_session.commit = AsyncMock()

        # Execute
        service = ConversationContextService(db=mock_db_session, redis_client=mock_redis)
        result = await service.update_context(
            conversation_id=123,
            merchant_id=1,
            message="Show me red shoes under $100",
            mode="ecommerce",
        )

        # Verify context extracted
        assert result["mode"] == "ecommerce"
        assert result["turn_count"] == 1
        assert "constraints" in result
        assert "search_history" in result

        # Verify Redis set
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert "conversation_context:123" in str(call_args)

    @pytest.mark.asyncio
    async def test_update_context_general_mode(self, mock_redis, mock_db_session):
        """Test updating context in general mode."""
        # Setup: No existing context
        mock_redis.get.return_value = None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        async def mock_execute(stmt):
            return mock_result

        mock_db_session.execute = mock_execute
        mock_db_session.add = MagicMock()
        mock_db_session.commit = AsyncMock()

        # Execute
        service = ConversationContextService(db=mock_db_session, redis_client=mock_redis)
        result = await service.update_context(
            conversation_id=456,
            merchant_id=1,
            message="I'm having login issues",
            mode="general",
        )

        # Verify context extracted
        assert result["mode"] == "general"
        assert result["turn_count"] == 1
        assert "topics_discussed" in result

    @pytest.mark.asyncio
    async def test_update_context_merges_with_existing(self, mock_redis, mock_db_session):
        """Test that updates merge with existing context."""
        # Setup: Existing context
        existing_context = {
            "mode": "ecommerce",
            "turn_count": 2,
            "viewed_products": [123],
            "constraints": {"budget_max": 100},
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
        }
        mock_redis.get.return_value = json.dumps(existing_context)

        mock_result = MagicMock()
        mock_context_model = MagicMock(spec=ConversationContext)
        mock_context_model.context_data = existing_context
        mock_context_model.turn_count = 2
        mock_result.scalar_one_or_none.return_value = mock_context_model

        async def mock_execute(stmt):
            return mock_result

        mock_db_session.execute = mock_execute
        mock_db_session.commit = AsyncMock()

        # Execute
        service = ConversationContextService(db=mock_db_session, redis_client=mock_redis)
        result = await service.update_context(
            conversation_id=123,
            merchant_id=1,
            message="What about in blue?",
            mode="ecommerce",
        )

        # Verify merged
        assert result["turn_count"] == 3  # Incremented
        assert 123 in result["viewed_products"]  # Existing product preserved

    @pytest.mark.asyncio
    async def test_should_summarize_every_5_turns(self, mock_redis, mock_db_session):
        """Test summarization trigger every 5 turns."""
        service = ConversationContextService(db=mock_db_session, redis_client=mock_redis)

        # Test: 5 turns should trigger
        context_5_turns = {"turn_count": 5}
        assert await service.should_summarize(context_5_turns) is True

        # Test: 4 turns should not trigger
        context_4_turns = {"turn_count": 4}
        assert await service.should_summarize(context_4_turns) is False

    @pytest.mark.asyncio
    async def test_should_summarize_when_size_exceeds_1kb(self, mock_redis, mock_db_session):
        """Test summarization trigger when context size > 1KB."""
        service = ConversationContextService(db=mock_db_session, redis_client=mock_redis)

        # Create context > 1KB
        large_context = {
            "turn_count": 2,
            "data": "x" * 2000,  # 2KB of data
        }

        assert await service.should_summarize(large_context) is True

    @pytest.mark.asyncio
    async def test_summarize_context_with_llm(self, mock_redis, mock_db_session):
        """Test context summarization."""
        service = ConversationContextService(db=mock_db_session, redis_client=mock_redis)

        context = {
            "mode": "ecommerce",
            "turn_count": 10,
            "viewed_products": [123, 456, 789],
            "constraints": {"budget_max": 100, "color": "red"},
        }

        summary = await service.summarize_context(123, context)

        assert summary["original_turns"] == 10
        assert "summarized_at" in summary
        assert isinstance(summary["key_points"], list)
        assert summary["active_constraints"]["budget_max"] == 100

    @pytest.mark.asyncio
    async def test_delete_context(self, mock_redis, mock_db_session):
        """Test deleting context from Redis and PostgreSQL."""
        # Setup: Mock DB context
        mock_context_model = MagicMock(spec=ConversationContext)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_context_model

        async def mock_execute(stmt):
            return mock_result

        async def mock_delete(model):
            pass  # Async delete

        mock_db_session.execute = mock_execute
        mock_db_session.delete = mock_delete
        mock_db_session.commit = AsyncMock()

        # Execute
        service = ConversationContextService(db=mock_db_session, redis_client=mock_redis)
        await service.delete_context(123)

        # Verify
        mock_redis.delete.assert_called_once_with("conversation_context:123")
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_redis_24h_ttl(self, mock_redis, mock_db_session):
        """Test that Redis keys have 24-hour TTL."""
        # Setup
        mock_redis.get.return_value = None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        async def mock_execute(stmt):
            return mock_result

        mock_db_session.execute = mock_execute
        mock_db_session.add = MagicMock()
        mock_db_session.commit = AsyncMock()

        # Execute
        service = ConversationContextService(db=mock_db_session, redis_client=mock_redis)
        await service.update_context(
            conversation_id=123,
            merchant_id=1,
            message="test",
            mode="ecommerce",
        )

        # Verify TTL is 86400 seconds (24 hours)
        call_args = mock_redis.setex.call_args
        ttl_arg = call_args[0][1]  # Second argument is TTL
        assert ttl_arg == 86400


class TestEcommerceContextExtractor:
    """Test E-commerce mode context extractor."""

    @pytest.mark.asyncio
    async def test_extract_price_constraints(self):
        """Test extracting price constraints from messages."""
        from app.services.context import EcommerceContextExtractor

        extractor = EcommerceContextExtractor()

        # Test: "under $100"
        context = {}
        updates = await extractor.extract("Show me shoes under $100", context)
        assert "constraints" in updates
        assert updates["constraints"]["budget_max"] == 100.0

        # Test: "max $50"
        updates = await extractor.extract("What about max $50?", context)
        assert updates["constraints"]["budget_max"] == 50.0

    @pytest.mark.asyncio
    async def test_extract_viewed_products(self):
        """Test extracting product IDs from messages."""
        from app.services.context import EcommerceContextExtractor

        extractor = EcommerceContextExtractor()

        # Test: "#123 format"
        updates = await extractor.extract("Tell me about #123", {})
        assert "viewed_products" in updates
        assert 123 in updates["viewed_products"]

        # Test: "product-456 format"
        updates = await extractor.extract("Add product-456 to cart", {})
        assert 456 in updates["viewed_products"]

    @pytest.mark.asyncio
    async def test_extract_size_color_preferences(self):
        """Test extracting size and color preferences."""
        from app.services.context import EcommerceContextExtractor

        extractor = EcommerceContextExtractor()

        # Test: size + color
        updates = await extractor.extract("I need size 10 in red", {})
        assert "constraints" in updates
        assert updates["constraints"]["size"] == "10"
        assert updates["constraints"]["color"] == "red"

    @pytest.mark.asyncio
    async def test_merge_with_existing_context(self):
        """Test merging extracted context with existing."""
        from app.services.context import EcommerceContextExtractor

        extractor = EcommerceContextExtractor()

        existing = {
            "viewed_products": [123, 456],
            "constraints": {"budget_max": 100},
        }

        updates = await extractor.extract("Add #789 to cart", existing)

        # Verify merge
        assert 123 in updates["viewed_products"]  # Existing preserved
        assert 789 in updates["viewed_products"]  # New added
        assert updates["constraints"]["budget_max"] == 100  # Existing preserved


class TestGeneralContextExtractor:
    """Test General mode context extractor."""

    @pytest.mark.asyncio
    async def test_extract_topics_discussed(self):
        """Test extracting topics from messages."""
        from app.services.context import GeneralContextExtractor

        extractor = GeneralContextExtractor()

        # Test: login issues
        updates = await extractor.extract("I'm having login problems", {})
        assert "topics_discussed" in updates
        assert "login" in updates["topics_discussed"]

    @pytest.mark.asyncio
    async def test_extract_support_issues(self):
        """Test detecting and classifying support issues."""
        from app.services.context import GeneralContextExtractor

        extractor = GeneralContextExtractor()

        # Test: billing issue
        updates = await extractor.extract("I was charged incorrectly", {})
        assert "support_issues" in updates
        assert any(issue["type"] == "billing" for issue in updates["support_issues"])

    @pytest.mark.asyncio
    async def test_detect_escalation_keywords(self):
        """Test escalation keyword detection."""
        from app.services.context import GeneralContextExtractor

        extractor = GeneralContextExtractor()

        # Test: high priority
        updates = await extractor.extract("I need to speak to a human", {})
        assert updates.get("escalation_status") == "high"

        # Test: medium priority
        updates = await extractor.extract("I'm frustrated with this", {})
        assert updates.get("escalation_status") == "medium"

    @pytest.mark.asyncio
    async def test_merge_with_existing_context(self):
        """Test merging general context."""
        from app.services.context import GeneralContextExtractor

        extractor = GeneralContextExtractor()

        existing = {
            "topics_discussed": ["login"],
            "support_issues": [{"type": "login", "status": "pending"}],
        }

        updates = await extractor.extract("Now I have billing issues", existing)

        # Verify merge
        assert "login" in updates["topics_discussed"]  # Existing preserved
        assert "billing" in updates["topics_discussed"]  # New added


class TestContextExpiry:
    """Test 24-hour expiration behavior."""

    @pytest.mark.asyncio
    async def test_context_expires_after_24h(self, mock_redis, mock_db_session):
        """Test that contexts expire after 24 hours."""
        # Setup: Expired context
        mock_context_model = MagicMock(spec=ConversationContext)
        mock_context_model.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_context_model

        async def mock_execute(stmt):
            return mock_result

        mock_db_session.execute = mock_execute

        # Execute
        service = ConversationContextService(db=mock_db_session, redis_client=mock_redis)
        result = await service.get_context(123)

        # Verify
        assert result is None  # Expired context returns None

    @pytest.mark.asyncio
    async def test_cross_session_context_restoration(self, mock_redis, mock_db_session):
        """Test that context persists across sessions within 24h."""
        # Setup: Context from 1 hour ago
        hour_ago_context = {
            "mode": "ecommerce",
            "turn_count": 5,
            "viewed_products": [123, 456],
            "constraints": {"budget_max": 100},
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=23)).isoformat(),
        }
        mock_redis.get.return_value = json.dumps(hour_ago_context)

        # Execute: User returns after 1 hour
        service = ConversationContextService(db=mock_db_session, redis_client=mock_redis)
        result = await service.get_context(123)

        # Verify: Context restored
        assert result is not None
        assert result["turn_count"] == 5
        assert result["viewed_products"] == [123, 456]
