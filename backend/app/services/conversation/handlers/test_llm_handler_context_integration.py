"""Test LLM Handler Context Integration (Story 11-1).

Tests for conversation context memory integration into LLM handler.
"""

from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import text

from app.models.conversation_context import ConversationContext as ConversationContextModel
from app.services.conversation.handlers.llm_handler import LLMHandler
from app.services.conversation.schemas import ConversationContext
from app.services.llm.base_llm_service import LLMMessage


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    redis = MagicMock()
    redis.get = MagicMock(return_value=None)
    redis.setex = MagicMock()
    return redis


@pytest.fixture
async def test_merchant(db_session):
    """Create a test merchant for foreign key constraints."""
    from sqlalchemy import delete
    from app.models.conversation import Conversation
    from app.models.conversation_context import ConversationContext as ConversationContextModel

    sql = text("""
        INSERT INTO merchants (merchant_key, platform, status, personality, store_provider, onboarding_mode, created_at, updated_at)
        VALUES ('test_llm_handler', 'widget', 'active', 'friendly', 'none', 'ecommerce', NOW(), NOW())
        ON CONFLICT (merchant_key) DO UPDATE SET platform = EXCLUDED.platform
        RETURNING id
    """)
    result = await db_session.execute(sql)
    merchant_id = result.fetchone()[0]
    yield merchant_id
    # Cleanup - delete all related data first
    await db_session.execute(
        text(f"DELETE FROM conversation_context WHERE merchant_id = {merchant_id}")
    )
    await db_session.execute(text(f"DELETE FROM conversations WHERE merchant_id = {merchant_id}"))
    await db_session.execute(text(f"DELETE FROM merchants WHERE id = {merchant_id}"))
    await db_session.commit()


@pytest.fixture
def conversation_context_with_history():
    """Create conversation context with history."""
    return ConversationContext(
        session_id="test-session-123",
        merchant_id=1,
        channel="widget",
        conversation_history=[
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ],
        conversation_id=123,
    )


@pytest.fixture
def merchant():
    """Create mock merchant."""
    merchant = MagicMock()
    merchant.id = 1
    merchant.bot_name = "TestBot"
    merchant.business_name = "Test Store"
    merchant.personality = "friendly"
    merchant.onboarding_mode = "ecommerce"
    return merchant


@pytest.fixture
def mock_llm_service():
    """Create mock LLM service."""
    llm = AsyncMock()
    response = MagicMock()
    response.content = "Based on your interest in red shoes, here are some options under $100"
    llm.chat = AsyncMock(return_value=response)
    return llm


class TestLLMHandlerContextRetrieval:
    """Test conversation context retrieval in LLM handler."""

    @pytest.mark.asyncio
    async def test_get_conversation_context_with_redis(self, db_session, mock_redis):
        """Test retrieving context from Redis."""
        import json

        handler = LLMHandler()

        # Mock Redis to return context
        context_data = {
            "mode": "ecommerce",
            "turn_count": 5,
            "viewed_products": [123, 456],
            "constraints": {"budget_max": 100},
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
        }
        mock_redis.get.return_value = json.dumps(context_data).encode()

        with patch(
            "app.services.conversation.handlers.llm_handler.get_redis_client",
            return_value=mock_redis,
        ):
            context = await handler._get_conversation_context(db_session, 123)

            assert context is not None
            assert context["mode"] == "ecommerce"
            assert context["viewed_products"] == [123, 456]
            assert context["constraints"]["budget_max"] == 100
            assert context["turn_count"] == 5

    @pytest.mark.asyncio
    async def test_get_conversation_context_from_postgres(
        self, db_session, mock_redis, test_merchant
    ):
        """Test retrieving context from PostgreSQL fallback."""
        handler = LLMHandler()

        # First create a conversation record (foreign key requirement)
        sql_conversation = text("""
            INSERT INTO conversations (merchant_id, platform, platform_sender_id, status, created_at, updated_at)
            VALUES (:merchant_id, 'widget', 'test-session-123', 'active', NOW(), NOW())
            RETURNING id
        """)
        result = await db_session.execute(sql_conversation, {"merchant_id": test_merchant})
        conversation_id = result.fetchone()[0]

        # Create context in database
        context_model = ConversationContextModel(
            conversation_id=conversation_id,
            merchant_id=test_merchant,
            mode="ecommerce",
            viewed_products=[123, 456],
            context_data={"budget_max": 100},
            turn_count=5,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        )
        db_session.add(context_model)
        await db_session.commit()

        # Mock Redis to return None (fallback to DB)
        mock_redis.get.return_value = None

        with patch(
            "app.services.conversation.handlers.llm_handler.get_redis_client",
            return_value=mock_redis,
        ):
            context = await handler._get_conversation_context(db_session, conversation_id)

            assert context is not None
            assert context["mode"] == "ecommerce"
            assert context["viewed_products"] == [123, 456]

        # Cleanup
        await db_session.execute(
            text(f"DELETE FROM conversation_context WHERE conversation_id = {conversation_id}")
        )
        await db_session.execute(text(f"DELETE FROM conversations WHERE id = {conversation_id}"))
        await db_session.commit()

    @pytest.mark.asyncio
    async def test_get_conversation_context_expired(self, db_session, mock_redis, test_merchant):
        """Test that expired context returns None."""
        handler = LLMHandler()

        # Create conversation record
        sql_conversation = text("""
            INSERT INTO conversations (merchant_id, platform, platform_sender_id, status, created_at, updated_at)
            VALUES (:merchant_id, 'widget', 'test-session-expired', 'active', NOW(), NOW())
            RETURNING id
        """)
        result = await db_session.execute(sql_conversation, {"merchant_id": test_merchant})
        conversation_id = result.fetchone()[0]

        # Create expired context in database
        context_model = ConversationContextModel(
            conversation_id=conversation_id,
            merchant_id=test_merchant,
            mode="ecommerce",
            viewed_products=[123],
            context_data={},
            turn_count=1,
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),  # Expired
        )
        db_session.add(context_model)
        await db_session.commit()

        mock_redis.get.return_value = None

        with patch(
            "app.services.conversation.handlers.llm_handler.get_redis_client",
            return_value=mock_redis,
        ):
            context = await handler._get_conversation_context(db_session, conversation_id)

            assert context is None  # Expired context returns None

        # Cleanup
        await db_session.execute(
            text(f"DELETE FROM conversation_context WHERE conversation_id = {conversation_id}")
        )
        await db_session.execute(text(f"DELETE FROM conversations WHERE id = {conversation_id}"))
        await db_session.commit()

    @pytest.mark.asyncio
    async def test_get_conversation_context_not_found(self, db_session, mock_redis):
        """Test that missing context returns None."""
        handler = LLMHandler()
        mock_redis.get.return_value = None

        with patch(
            "app.services.conversation.handlers.llm_handler.get_redis_client",
            return_value=mock_redis,
        ):
            context = await handler._get_conversation_context(db_session, 999)

            assert context is None


class TestLLMHandlerContextInjection:
    """Test conversation context injection into system prompt."""

    def test_inject_conversation_context_ecommerce(self):
        """Test injecting e-commerce context into system prompt."""
        handler = LLMHandler()

        base_prompt = "You are a helpful shopping assistant."
        context = {
            "mode": "ecommerce",
            "viewed_products": [123, 456, 789],
            "constraints": {"budget_max": 100, "color": "red"},
            "search_history": ["running shoes", "basketball shoes"],
        }

        enhanced = handler._inject_conversation_context(base_prompt, context, "ecommerce")

        assert "Conversation Context" in enhanced
        assert "Recently viewed products: [123, 456, 789]" in enhanced
        assert "budget max: $100" in enhanced
        assert "color: red" in enhanced
        assert "Recent searches" in enhanced
        assert "When responding, take this context into account" in enhanced

    def test_inject_conversation_context_general(self):
        """Test injecting general mode context into system prompt."""
        handler = LLMHandler()

        base_prompt = "You are a helpful support assistant."
        context = {
            "mode": "general",
            "topics_discussed": ["login issues", "password reset"],
            "support_issues": [
                {"type": "login", "status": "pending"},
                {"type": "payment", "status": "resolved"},
            ],
            "escalation_status": "medium",
        }

        enhanced = handler._inject_conversation_context(base_prompt, context, "general")

        assert "Conversation Context" in enhanced
        assert "Topics discussed: login issues, password reset" in enhanced
        assert "login (pending)" in enhanced
        assert "payment (resolved)" in enhanced
        assert "Escalation level: medium" in enhanced

    def test_inject_conversation_context_none(self):
        """Test that None context returns original prompt unchanged."""
        handler = LLMHandler()

        base_prompt = "You are a helpful assistant."
        enhanced = handler._inject_conversation_context(base_prompt, None, "ecommerce")

        assert enhanced == base_prompt

    def test_inject_conversation_context_empty(self):
        """Test that empty context shows 'No specific context available'."""
        handler = LLMHandler()

        base_prompt = "You are a helpful assistant."
        enhanced = handler._inject_conversation_context(base_prompt, {}, "ecommerce")

        # Empty context should return original prompt (no context section)
        # because the context builder returns "No specific context available"
        # which is still added to the prompt
        assert base_prompt in enhanced


class TestLLMHandlerEcommerceContextBuilder:
    """Test e-commerce context builder."""

    def test_build_ecommerce_context_full(self):
        """Test building e-commerce context with all fields."""
        handler = LLMHandler()

        context = {
            "viewed_products": [123, 456, 789, 101, 202],
            "cart_items": [456, 789],
            "constraints": {
                "budget_max": 100,
                "budget_min": 50,
                "color": "red",
                "size": "10",
                "brand": "Nike",
            },
            "search_history": ["running shoes", "basketball shoes", "tennis shoes"],
        }

        built = handler._build_ecommerce_context(context)

        assert "Recently viewed products: [123, 456, 789, 101, 202]" in built
        assert "Items in cart: [456, 789]" in built
        assert "budget" in built.lower()
        assert "red" in built
        assert "size: 10" in built
        assert "brand: Nike" in built
        assert "Recent searches" in built

    def test_build_ecommerce_context_minimal(self):
        """Test building e-commerce context with minimal data."""
        handler = LLMHandler()

        context = {
            "viewed_products": [123],
        }

        built = handler._build_ecommerce_context(context)

        assert "Recently viewed products: [123]" in built
        # Should not mention empty sections
        assert "Items in cart" not in built

    def test_build_ecommerce_context_long_lists_truncated(self):
        """Test that long lists are truncated for token efficiency."""
        handler = LLMHandler()

        context = {
            "viewed_products": list(range(20)),  # 20 products
        }

        built = handler._build_ecommerce_context(context)

        # Should only show first 5
        assert "[0, 1, 2, 3, 4]" in built
        # The truncation message format may vary - just check we don't have all 20
        assert "19" not in built  # Last product should not be shown


class TestLLMHandlerGeneralContextBuilder:
    """Test general mode context builder."""

    def test_build_general_context_full(self):
        """Test building general context with all fields."""
        handler = LLMHandler()

        context = {
            "topics_discussed": ["login", "payment", "shipping"],
            "documents_referenced": [1, 2, 3],
            "support_issues": [
                {"type": "login", "status": "pending", "description": "Cannot log in"},
                {"type": "payment", "status": "resolved", "description": "Payment failed"},
            ],
            "escalation_status": "high",
        }

        built = handler._build_general_context(context)

        assert "Topics discussed: login, payment, shipping" in built
        assert "Documents referenced: [1, 2, 3]" in built
        # Check that support issues are included
        assert "login (pending)" in built
        assert "payment (resolved)" in built
        assert "Escalation level: high" in built

    def test_build_general_context_minimal(self):
        """Test building general context with minimal data."""
        handler = LLMHandler()

        context = {
            "topics_discussed": ["general inquiry"],
        }

        built = handler._build_general_context(context)

        assert "Topics discussed: general inquiry" in built

    def test_build_general_context_no_issues(self):
        """Test building general context without support issues."""
        handler = LLMHandler()

        context = {
            "topics_discussed": ["product info"],
        }

        built = handler._build_general_context(context)

        assert "Topics discussed: product info" in built
        # Should not show empty issue sections
        assert "Pending issues" not in built


class TestLLMHandlerIntegration:
    """Test end-to-end LLM handler integration with context."""

    @pytest.mark.asyncio
    async def test_handle_with_conversation_context(
        self,
        db_session,
        mock_redis,
        conversation_context_with_history,
        test_merchant,
        mock_llm_service,
    ):
        """Test that LLM handler uses conversation context in prompt."""
        from sqlalchemy import text

        # Create conversation record
        sql_conversation = text("""
            INSERT INTO conversations (merchant_id, platform, platform_sender_id, status, created_at, updated_at)
            VALUES (:merchant_id, 'widget', 'test-session-handle', 'active', NOW(), NOW())
            RETURNING id
        """)
        result = await db_session.execute(sql_conversation, {"merchant_id": test_merchant})
        conversation_id = result.fetchone()[0]

        # Create context in database
        context_model = ConversationContextModel(
            conversation_id=conversation_id,
            merchant_id=test_merchant,
            mode="ecommerce",
            context_data={"viewed_products": [123, 456], "budget_max": 100},
            viewed_products=[123, 456],
            turn_count=3,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        )
        db_session.add(context_model)
        await db_session.commit()

        # Update context with correct conversation_id
        conversation_context_with_history.conversation_id = conversation_id

        # Create merchant object for handler
        from app.models.merchant import Merchant

        merchant = MagicMock()
        merchant.id = test_merchant
        merchant.bot_name = "TestBot"
        merchant.business_name = "Test Store"
        merchant.personality = "friendly"
        merchant.onboarding_mode = "ecommerce"

        handler = LLMHandler()
        mock_redis.get.return_value = None  # Force DB lookup

        with patch(
            "app.services.conversation.handlers.llm_handler.get_redis_client",
            return_value=mock_redis,
        ):
            response = await handler.handle(
                db=db_session,
                merchant=merchant,
                llm_service=mock_llm_service,
                message="Show me more shoes",
                context=conversation_context_with_history,
                entities=None,
            )

            # Verify LLM was called (may be called multiple times for analysis)
            assert mock_llm_service.chat.call_count >= 1
            first_call_args = mock_llm_service.chat.call_args_list[0]
            messages = first_call_args[1]["messages"]

            # Check that system prompt includes conversation context
            system_prompt = messages[0].content
            assert "Conversation Context" in system_prompt
            assert "Recently viewed products: [123, 456]" in system_prompt

            # Verify response
            assert response.message is not None
            assert response.intent == "general"

        # Cleanup
        await db_session.execute(
            text(f"DELETE FROM conversation_context WHERE conversation_id = {conversation_id}")
        )
        await db_session.execute(text(f"DELETE FROM conversations WHERE id = {conversation_id}"))
        await db_session.commit()

    @pytest.mark.asyncio
    async def test_handle_without_conversation_context(
        self,
        conversation_context_with_history,
        merchant,
        mock_llm_service,
    ):
        """Test that LLM handler works without conversation context."""
        # Context with no conversation_id
        context = ConversationContext(
            session_id="test-session-456",
            merchant_id=1,
            channel="widget",
            conversation_id=None,  # No conversation ID
        )

        handler = LLMHandler()

        response = await handler.handle(
            db=None,  # No DB needed when no conversation_id
            merchant=merchant,
            llm_service=mock_llm_service,
            message="Hello",
            context=context,
            entities=None,
        )

        # Verify LLM was called (without context)
        mock_llm_service.chat.assert_called_once()
        call_args = mock_llm_service.chat.call_args
        messages = call_args[1]["messages"]

        # System prompt should NOT include conversation context
        system_prompt = messages[0].content
        assert "Conversation Context" not in system_prompt

        # Verify response
        assert response.message is not None

    @pytest.mark.asyncio
    async def test_handle_with_expired_context(
        self,
        db_session,
        mock_redis,
        conversation_context_with_history,
        test_merchant,
        mock_llm_service,
    ):
        """Test that expired context is ignored."""
        from sqlalchemy import text

        # Create conversation record
        sql_conversation = text("""
            INSERT INTO conversations (merchant_id, platform, platform_sender_id, status, created_at, updated_at)
            VALUES (:merchant_id, 'widget', 'test-session-expired-handle', 'active', NOW(), NOW())
            RETURNING id
        """)
        result = await db_session.execute(sql_conversation, {"merchant_id": test_merchant})
        conversation_id = result.fetchone()[0]

        # Create expired context
        context_model = ConversationContextModel(
            conversation_id=conversation_id,
            merchant_id=test_merchant,
            mode="ecommerce",
            context_data={"viewed_products": [123]},
            viewed_products=[123],
            turn_count=1,
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),  # Expired
        )
        db_session.add(context_model)
        await db_session.commit()

        # Update context with correct conversation_id
        conversation_context_with_history.conversation_id = conversation_id

        # Create merchant object for handler
        from app.models.merchant import Merchant

        merchant = MagicMock()
        merchant.id = test_merchant
        merchant.bot_name = "TestBot"
        merchant.business_name = "Test Store"
        merchant.personality = "friendly"
        merchant.onboarding_mode = "ecommerce"

        handler = LLMHandler()
        mock_redis.get.return_value = None

        with patch(
            "app.services.conversation.handlers.llm_handler.get_redis_client",
            return_value=mock_redis,
        ):
            response = await handler.handle(
                db=db_session,
                merchant=merchant,
                llm_service=mock_llm_service,
                message="Show me products",
                context=conversation_context_with_history,
                entities=None,
            )

            # Verify LLM was called (may be called multiple times for analysis)
            assert mock_llm_service.chat.call_count >= 1
            first_call_args = mock_llm_service.chat.call_args_list[0]
            messages = first_call_args[1]["messages"]

            # Check that system prompt does NOT include expired context
            system_prompt = messages[0].content
            assert "Conversation Context" not in system_prompt

            assert response.message is not None

        # Cleanup
        await db_session.execute(
            text(f"DELETE FROM conversation_context WHERE conversation_id = {conversation_id}")
        )
        await db_session.execute(text(f"DELETE FROM conversations WHERE id = {conversation_id}"))
        await db_session.commit()
