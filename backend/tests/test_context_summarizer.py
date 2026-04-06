"""Test Context Summarization Service (Task 4: LLM-based Summarization).

Story 11-1: Conversation Context Memory
Tests for LLM-based conversation context summarization.
"""

import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.context_summarizer import ContextSummarizerService
from app.services.llm.base_llm_service import BaseLLMService, LLMMessage, LLMResponse


# Mock LLM Service
class MockLLMService(BaseLLMService):
    """Mock LLM service for testing."""

    def __init__(self, config: dict, is_testing: bool = False):
        super().__init__(config, is_testing)
        self.mock_response = None

    @property
    def provider_name(self) -> str:
        return "mock"

    async def test_connection(self) -> bool:
        return True

    async def chat(
        self,
        messages: list[LLMMessage],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> LLMResponse:
        """Return mock response."""
        if self.mock_response:
            return self.mock_response

        # Default mock response
        return LLMResponse(
            content=json.dumps(
                {
                    "key_points": ["Customer looking for red shoes under $100"],
                    "active_constraints": {"budget_max": 100, "color": "red"},
                }
            ),
            tokens_used=50,
            model="mock-model",
            provider="mock",
        )

    def count_tokens(self, text: str) -> int:
        return len(text.split())


# Fixtures
@pytest.fixture
def mock_llm_service():
    """Mock LLM service."""
    return MockLLMService(config={})


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    return AsyncMock(spec=AsyncSession)


class TestContextSummarizerService:
    """Test context summarization service."""

    @pytest.mark.asyncio
    async def test_summarize_ecommerce_context(self, mock_llm_service, mock_db_session):
        """Test summarizing e-commerce context."""
        # Setup: Mock LLM response
        mock_response = LLMResponse(
            content=json.dumps(
                {
                    "key_points": [
                        "Customer looking for red running shoes under $100",
                        "Prefers Nike brand, size 10",
                    ],
                    "active_constraints": {
                        "budget_max": 100,
                        "brand": "Nike",
                        "size": "10",
                        "color": "red",
                    },
                }
            ),
            tokens_used=50,
            model="mock-model",
            provider="mock",
        )
        mock_llm_service.mock_response = mock_response

        # Setup: E-commerce context
        context = {
            "mode": "ecommerce",
            "turn_count": 5,
            "viewed_products": [123, 456, 789],
            "constraints": {"budget_max": 100, "size": "10", "color": "red", "brand": "Nike"},
            "search_history": ["running shoes", "nike", "under $100"],
        }

        # Execute
        summarizer = ContextSummarizerService(db=mock_db_session, llm_service=mock_llm_service)
        summary = await summarizer.summarize_context(context, conversation_id=123)

        # Verify
        assert summary["original_turns"] == 5
        assert "summarized_at" in summary
        assert len(summary["key_points"]) == 2
        assert "red running shoes" in summary["key_points"][0]
        assert summary["active_constraints"]["budget_max"] == 100
        assert summary["active_constraints"]["brand"] == "Nike"

    @pytest.mark.asyncio
    async def test_summarize_general_context(self, mock_llm_service, mock_db_session):
        """Test summarizing general mode context."""
        # Setup: Mock LLM response
        mock_response = LLMResponse(
            content=json.dumps(
                {
                    "key_points": [
                        "Customer has login issues",
                        "Referenced KB article 123",
                        "Low frustration detected",
                    ],
                    "active_constraints": {"escalation_status": "low", "active_issues": ["login"]},
                }
            ),
            tokens_used=50,
            model="mock-model",
            provider="mock",
        )
        mock_llm_service.mock_response = mock_response

        # Setup: General mode context
        context = {
            "mode": "general",
            "turn_count": 3,
            "topics_discussed": ["login", "password", "authentication"],
            "documents_referenced": [123, 456],
            "support_issues": [{"type": "login", "status": "pending"}],
            "escalation_status": "low",
        }

        # Execute
        summarizer = ContextSummarizerService(db=mock_db_session, llm_service=mock_llm_service)
        summary = await summarizer.summarize_context(context, conversation_id=456)

        # Verify
        assert summary["original_turns"] == 3
        assert len(summary["key_points"]) == 3
        assert "login issues" in summary["key_points"][0]
        assert summary["active_constraints"]["escalation_status"] == "low"

    @pytest.mark.asyncio
    async def test_summarize_with_markdown_response(self, mock_llm_service, mock_db_session):
        """Test parsing LLM response with markdown code blocks."""
        # Setup: Mock response with markdown
        mock_response = LLMResponse(
            content="""```json
{
    "key_points": ["Customer wants size 10 shoes"],
    "active_constraints": {"size": "10"}
}
```""",
            tokens_used=30,
            model="mock-model",
            provider="mock",
        )
        mock_llm_service.mock_response = mock_response

        context = {
            "mode": "ecommerce",
            "turn_count": 2,
            "constraints": {"size": "10"},
        }

        # Execute
        summarizer = ContextSummarizerService(db=mock_db_session, llm_service=mock_llm_service)
        summary = await summarizer.summarize_context(context)

        # Verify: Parsed correctly from markdown
        assert len(summary["key_points"]) == 1
        assert summary["active_constraints"]["size"] == "10"

    @pytest.mark.asyncio
    async def test_fallback_on_invalid_json(self, mock_llm_service, mock_db_session):
        """Test fallback summarization when LLM returns invalid JSON."""
        # Setup: Invalid JSON response
        mock_response = LLMResponse(
            content="This is not valid JSON at all",
            tokens_used=20,
            model="mock-model",
            provider="mock",
        )
        mock_llm_service.mock_response = mock_response

        context = {
            "mode": "ecommerce",
            "turn_count": 3,
            "viewed_products": [123, 456],
            "constraints": {"budget_max": 100},
        }

        # Execute
        summarizer = ContextSummarizerService(db=mock_db_session, llm_service=mock_llm_service)
        summary = await summarizer.summarize_context(context)

        # Verify: Fallback summary generated
        assert summary["original_turns"] == 3
        assert len(summary["key_points"]) > 0
        assert summary["active_constraints"]["budget_max"] == 100

    @pytest.mark.asyncio
    async def test_fallback_ecommerce_mode(self, mock_db_session):
        """Test fallback summarization for e-commerce mode."""
        summarizer = ContextSummarizerService(db=mock_db_session)

        context = {
            "mode": "ecommerce",
            "turn_count": 5,
            "viewed_products": [123, 456, 789],
            "constraints": {"budget_max": 100, "brand": "Nike", "size": "10", "color": "red"},
        }

        # Execute without LLM service (will use fallback)
        summary = await summarizer.summarize_context(context)

        # Verify fallback extracted key information
        assert summary["original_turns"] == 5
        assert len(summary["key_points"]) > 0
        assert summary["active_constraints"]["budget_max"] == 100
        assert summary["active_constraints"]["brand"] == "Nike"

    @pytest.mark.asyncio
    async def test_fallback_general_mode(self, mock_db_session):
        """Test fallback summarization for general mode."""
        summarizer = ContextSummarizerService(db=mock_db_session)

        context = {
            "mode": "general",
            "turn_count": 4,
            "topics_discussed": ["login", "billing", "technical"],
            "documents_referenced": [123, 456],
            "support_issues": [
                {"type": "login", "status": "pending"},
                {"type": "billing", "status": "resolved"},
            ],
            "escalation_status": "medium",
        }

        # Execute without LLM service (will use fallback)
        summary = await summarizer.summarize_context(context)

        # Verify fallback extracted key information
        assert summary["original_turns"] == 4
        assert len(summary["key_points"]) > 0
        assert "login" in summary["key_points"][0] or "Topics" in summary["key_points"][0]

    @pytest.mark.asyncio
    async def test_llm_error_handling(self, mock_llm_service, mock_db_session):
        """Test graceful handling of LLM errors."""

        # Setup: Mock LLM that raises exception
        async def failing_chat(*args, **kwargs):
            raise Exception("LLM service unavailable")

        mock_llm_service.chat = failing_chat

        context = {
            "mode": "ecommerce",
            "turn_count": 2,
            "viewed_products": [123],
        }

        # Execute: Should fall back gracefully
        summarizer = ContextSummarizerService(db=mock_db_session, llm_service=mock_llm_service)
        summary = await summarizer.summarize_context(context)

        # Verify: Fallback summary returned despite error
        assert summary["original_turns"] == 2
        assert len(summary["key_points"]) > 0

    def test_get_system_prompt_ecommerce(self, mock_db_session):
        """Test system prompt generation for e-commerce mode."""
        summarizer = ContextSummarizerService(db=mock_db_session)
        prompt = summarizer._get_system_prompt("ecommerce")

        assert "e-commerce" in prompt.lower()
        assert "products viewed" in prompt.lower()
        assert "budget" in prompt.lower()
        assert "size" in prompt.lower()
        assert "key_points" in prompt
        assert "active_constraints" in prompt

    def test_get_system_prompt_general(self, mock_db_session):
        """Test system prompt generation for general mode."""
        summarizer = ContextSummarizerService(db=mock_db_session)
        prompt = summarizer._get_system_prompt("general")

        assert "customer support" in prompt.lower()
        assert "topics" in prompt.lower()
        assert "documents" in prompt.lower()
        assert "support issues" in prompt.lower()
        assert "escalation" in prompt.lower()

    def test_build_user_prompt_ecommerce(self, mock_db_session):
        """Test user prompt building for e-commerce mode."""
        summarizer = ContextSummarizerService(db=mock_db_session)

        context = {
            "mode": "ecommerce",
            "viewed_products": [123, 456],
            "constraints": {"budget_max": 100},
        }

        prompt = summarizer._build_user_prompt(context, "ecommerce")

        assert "ecommerce" in prompt.lower()
        assert "123" in prompt
        assert "100" in prompt

    def test_parse_summary_response_with_code_blocks(self, mock_db_session):
        """Test parsing JSON from markdown code blocks."""
        summarizer = ContextSummarizerService(db=mock_db_session)

        llm_response = """```json
{
    "key_points": ["Test point"],
    "active_constraints": {"test": "value"}
}
```"""

        context = {"mode": "ecommerce", "turn_count": 1}

        summary = summarizer._parse_summary_response(llm_response, context, "ecommerce")

        assert len(summary["key_points"]) == 1
        assert summary["key_points"][0] == "Test point"
        assert summary["active_constraints"]["test"] == "value"

    def test_fallback_summary_ecommerce(self, mock_db_session):
        """Test fallback summary generation for e-commerce."""
        summarizer = ContextSummarizerService(db=mock_db_session)

        context = {
            "mode": "ecommerce",
            "turn_count": 3,
            "viewed_products": [111, 222, 333],
            "constraints": {"budget_max": 50, "brand": "Adidas", "size": "9"},
        }

        summary = summarizer._fallback_summary(context)

        assert summary["original_turns"] == 3
        assert len(summary["key_points"]) > 0
        assert summary["active_constraints"]["budget_max"] == 50
        assert summary["active_constraints"]["brand"] == "Adidas"

    def test_fallback_summary_general(self, mock_db_session):
        """Test fallback summary generation for general mode."""
        summarizer = ContextSummarizerService(db=mock_db_session)

        context = {
            "mode": "general",
            "turn_count": 2,
            "topics_discussed": ["login", "password"],
            "documents_referenced": [123],
            "support_issues": [{"type": "login", "status": "pending"}],
            "escalation_status": "high",
        }

        summary = summarizer._fallback_summary(context)

        assert summary["original_turns"] == 2
        assert len(summary["key_points"]) > 0
        # Should have escalation info
        assert any("escalation" in point.lower() for point in summary["key_points"])


class TestSummarizationIntegration:
    """Test summarization integration with context service."""

    @pytest.mark.asyncio
    async def test_summarization_trigger_every_5_turns(self, mock_llm_service, mock_db_session):
        """Test that summarization is triggered every 5 turns."""
        from app.services.conversation_context import ConversationContextService

        # Mock Redis and LLM
        mock_redis = MagicMock()
        mock_redis.get.return_value = None

        # Setup: Mock response
        mock_response = LLMResponse(
            content=json.dumps({"key_points": ["Summary test"], "active_constraints": {}}),
            tokens_used=20,
            model="mock",
            provider="mock",
        )
        mock_llm_service.mock_response = mock_response

        # Create service
        service = ConversationContextService(db=mock_db_session, redis_client=mock_redis)

        # Test: 5 turns should trigger
        context_5_turns = {"turn_count": 5, "mode": "ecommerce"}
        should_summarize = await service.should_summarize(context_5_turns)
        assert should_summarize is True

        # Test: 4 turns should not trigger
        context_4_turns = {"turn_count": 4, "mode": "ecommerce"}
        should_summarize = await service.should_summarize(context_4_turns)
        assert should_summarize is False

    @pytest.mark.asyncio
    async def test_summarization_trigger_size_limit(self, mock_llm_service, mock_db_session):
        """Test that large contexts trigger summarization."""
        from app.services.conversation_context import ConversationContextService

        mock_redis = MagicMock()

        service = ConversationContextService(db=mock_db_session, redis_client=mock_redis)

        # Create context > 1KB
        large_context = {
            "turn_count": 2,  # Not 5 turns
            "data": "x" * 2000,  # But > 1KB
            "mode": "ecommerce",
        }

        should_summarize = await service.should_summarize(large_context)
        assert should_summarize is True
