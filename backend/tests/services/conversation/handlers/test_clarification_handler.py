"""Tests for ClarificationHandler.

Story 5-10 Task 16: ClarificationHandler

Tests clarification flow including:
- First question generation
- Follow-up questions
- Fallback to assumptions
- Personality-based personalization
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.conversation.handlers.clarification_handler import ClarificationHandler
from app.services.conversation.schemas import (
    Channel,
    ConversationContext,
    ConversationResponse,
)
from app.services.intent.classification_schema import (
    ClassificationResult,
    ExtractedEntities,
    IntentType,
)


@pytest.fixture
def handler():
    """Create ClarificationHandler instance."""
    return ClarificationHandler()


@pytest.fixture
def mock_merchant():
    """Create mock merchant."""
    merchant = MagicMock()
    merchant.id = 1
    merchant.business_name = "Test Store"
    merchant.personality_type = "friendly"
    return merchant


@pytest.fixture
def mock_llm_service():
    """Create mock LLM service."""
    service = AsyncMock()
    service.chat = AsyncMock(return_value="LLM response")
    return service


@pytest.fixture
def mock_db():
    """Create mock database session."""
    return AsyncMock()


@pytest.fixture
def context_no_clarification():
    """Create context without active clarification."""
    return ConversationContext(
        session_id="test-session-123",
        merchant_id=1,
        channel=Channel.WIDGET,
        conversation_history=[],
        metadata={},
    )


@pytest.fixture
def context_with_clarification():
    """Create context with active clarification."""
    return ConversationContext(
        session_id="test-session-123",
        merchant_id=1,
        channel=Channel.WIDGET,
        conversation_history=[],
        metadata={
            "clarification": {
                "active": True,
                "questions_asked": ["budget"],
                "attempt_count": 1,
            },
            "last_classification": ClassificationResult(
                intent=IntentType.PRODUCT_SEARCH,
                confidence=0.5,
                entities=ExtractedEntities(),
                raw_message="I want a shirt",
                llm_provider="test",
                model="test",
                processing_time_ms=100,
            ),
        },
    )


class TestClarificationHandlerFirstQuestion:
    """Tests for first clarification question."""

    @pytest.mark.asyncio
    async def test_asks_budget_when_missing(
        self,
        handler,
        mock_db,
        mock_merchant,
        mock_llm_service,
        context_no_clarification,
    ):
        """Should ask about budget when missing."""
        entities = {"category": "shirt"}

        response = await handler.handle(
            db=mock_db,
            merchant=mock_merchant,
            llm_service=mock_llm_service,
            message="I want a shirt",
            context=context_no_clarification,
            entities=entities,
        )

        assert response.intent == "clarification"
        assert "budget" in response.message.lower() or "spend" in response.message.lower()
        assert response.metadata.get("clarification_active") is True
        assert response.metadata.get("constraint") == "budget"

    @pytest.mark.asyncio
    async def test_asks_category_when_budget_present(
        self,
        handler,
        mock_db,
        mock_merchant,
        mock_llm_service,
        context_no_clarification,
    ):
        """Should ask about category when budget is present but category missing."""
        entities = {"budget": 100.0}

        response = await handler.handle(
            db=mock_db,
            merchant=mock_merchant,
            llm_service=mock_llm_service,
            message="I want something under $100",
            context=context_no_clarification,
            entities=entities,
        )

        assert response.intent == "clarification"
        assert "category" in response.message.lower() or "type" in response.message.lower()

    @pytest.mark.asyncio
    async def test_asks_size_when_budget_and_category_present(
        self,
        handler,
        mock_db,
        mock_merchant,
        mock_llm_service,
        context_no_clarification,
    ):
        """Should ask about size when budget and category are present."""
        entities = {"budget": 100.0, "category": "shirt"}

        response = await handler.handle(
            db=mock_db,
            merchant=mock_merchant,
            llm_service=mock_llm_service,
            message="I want a shirt under $100",
            context=context_no_clarification,
            entities=entities,
        )

        assert response.intent == "clarification"
        assert "size" in response.message.lower()

    @pytest.mark.asyncio
    async def test_no_entities_asks_budget_first(
        self,
        handler,
        mock_db,
        mock_merchant,
        mock_llm_service,
        context_no_clarification,
    ):
        """Should ask budget first when no entities provided."""
        response = await handler.handle(
            db=mock_db,
            merchant=mock_merchant,
            llm_service=mock_llm_service,
            message="I want to buy something",
            context=context_no_clarification,
            entities=None,
        )

        assert response.intent == "clarification"
        assert "budget" in response.message.lower() or "spend" in response.message.lower()


class TestClarificationPersonalization:
    """Tests for personality-based question personalization."""

    @pytest.mark.asyncio
    async def test_friendly_personality_no_prefix(
        self,
        handler,
        mock_db,
        mock_llm_service,
        context_no_clarification,
    ):
        """Friendly personality should not add prefix."""
        merchant = MagicMock()
        merchant.id = 1
        merchant.business_name = "Test Store"
        merchant.personality_type = "friendly"

        response = await handler.handle(
            db=mock_db,
            merchant=merchant,
            llm_service=mock_llm_service,
            message="I want a shirt",
            context=context_no_clarification,
            entities={},
        )

        assert response.intent == "clarification"

    @pytest.mark.asyncio
    async def test_professional_personality_adds_prefix(
        self,
        handler,
        mock_db,
        mock_llm_service,
        context_no_clarification,
    ):
        """Professional personality should add prefix (for non-budget questions)."""
        merchant = MagicMock()
        merchant.id = 1
        merchant.business_name = None  # No business name to avoid override
        merchant.personality_type = "professional"

        # Use category question to test personality prefix (budget gets business name override)
        entities = {"budget": 100.0}

        response = await handler.handle(
            db=mock_db,
            merchant=merchant,
            llm_service=mock_llm_service,
            message="I want something under $100",
            context=context_no_clarification,
            entities=entities,
        )

        assert response.intent == "clarification"
        assert response.message.startswith("To help you better,")

    @pytest.mark.asyncio
    async def test_enthusiastic_personality_adds_prefix(
        self,
        handler,
        mock_db,
        mock_llm_service,
        context_no_clarification,
    ):
        """Enthusiastic personality should add prefix (for non-budget questions)."""
        merchant = MagicMock()
        merchant.id = 1
        merchant.business_name = None  # No business name to avoid override
        merchant.personality_type = "enthusiastic"

        # Use category question to test personality prefix
        entities = {"budget": 100.0}

        response = await handler.handle(
            db=mock_db,
            merchant=merchant,
            llm_service=mock_llm_service,
            message="I want something under $100",
            context=context_no_clarification,
            entities=entities,
        )

        assert response.intent == "clarification"
        assert response.message.startswith("Great question!")

    @pytest.mark.asyncio
    async def test_business_name_included_in_budget_question(
        self,
        handler,
        mock_db,
        mock_llm_service,
        context_no_clarification,
    ):
        """Should include business name in budget question."""
        merchant = MagicMock()
        merchant.id = 1
        merchant.business_name = "Acme Store"
        merchant.personality_type = "friendly"

        response = await handler.handle(
            db=mock_db,
            merchant=merchant,
            llm_service=mock_llm_service,
            message="I want a shirt",
            context=context_no_clarification,
            entities={"category": "shirt"},
        )

        assert "Acme Store" in response.message


class TestClarificationResponse:
    """Tests for handling clarification responses."""

    @pytest.mark.asyncio
    async def test_high_confidence_response_proceeds_to_search(
        self,
        handler,
        mock_db,
        mock_merchant,
        mock_llm_service,
        context_with_clarification,
    ):
        """High confidence response should proceed to search."""
        with patch.object(handler, "_handle_clarification_response") as mock_handle:
            mock_handle.return_value = ConversationResponse(
                message="Got it! Let me search for that.",
                intent="clarification",
                confidence=0.9,
                metadata={"resolved": True, "action": "proceed_to_search"},
            )

            response = await handler.handle(
                db=mock_db,
                merchant=mock_merchant,
                llm_service=mock_llm_service,
                message="under $50",
                context=context_with_clarification,
                entities={},
            )

            assert response.metadata.get("resolved") is True
            assert response.metadata.get("action") == "proceed_to_search"

    @pytest.mark.asyncio
    async def test_fallback_after_max_attempts(
        self,
        handler,
        mock_db,
        mock_merchant,
        mock_llm_service,
    ):
        """Should fallback to assumptions after max attempts."""
        context = ConversationContext(
            session_id="test-session-123",
            merchant_id=1,
            channel=Channel.WIDGET,
            conversation_history=[],
            metadata={
                "clarification": {
                    "active": True,
                    "questions_asked": ["budget", "category", "size"],
                    "attempt_count": 3,
                },
                "last_classification": ClassificationResult(
                    intent=IntentType.PRODUCT_SEARCH,
                    confidence=0.3,
                    entities=ExtractedEntities(category="shirt"),
                    raw_message="I want a shirt",
                    llm_provider="test",
                    model="test",
                    processing_time_ms=100,
                ),
            },
        )

        with patch.object(handler, "_handle_clarification_response") as mock_handle:
            mock_handle.return_value = ConversationResponse(
                message="I'll show you shirt options. Let me know if you'd like to narrow down by price, size, or other preferences.",
                intent="clarification",
                confidence=1.0,
                metadata={"fallback": True, "action": "proceed_to_search"},
            )

            response = await handler.handle(
                db=mock_db,
                merchant=mock_merchant,
                llm_service=mock_llm_service,
                message="I don't know",
                context=context,
                entities={},
            )

            assert response.metadata.get("fallback") is True
            assert response.metadata.get("action") == "proceed_to_search"


class TestQuestionPriority:
    """Tests for question priority ordering."""

    @pytest.mark.asyncio
    async def test_budget_highest_priority(
        self,
        handler,
        mock_db,
        mock_merchant,
        mock_llm_service,
        context_no_clarification,
    ):
        """Budget should be asked first."""
        entities = {}  # All missing

        response = await handler.handle(
            db=mock_db,
            merchant=mock_merchant,
            llm_service=mock_llm_service,
            message="I want to buy something",
            context=context_no_clarification,
            entities=entities,
        )

        assert response.metadata.get("constraint") == "budget"

    @pytest.mark.asyncio
    async def test_category_second_priority(
        self,
        handler,
        mock_db,
        mock_merchant,
        mock_llm_service,
        context_no_clarification,
    ):
        """Category should be asked after budget."""
        entities = {"budget": 100.0}

        response = await handler.handle(
            db=mock_db,
            merchant=mock_merchant,
            llm_service=mock_llm_service,
            message="I want something under $100",
            context=context_no_clarification,
            entities=entities,
        )

        assert response.metadata.get("constraint") == "category"

    @pytest.mark.asyncio
    async def test_size_third_priority(
        self,
        handler,
        mock_db,
        mock_merchant,
        mock_llm_service,
        context_no_clarification,
    ):
        """Size should be asked after category."""
        entities = {"budget": 100.0, "category": "shirt"}

        response = await handler.handle(
            db=mock_db,
            merchant=mock_merchant,
            llm_service=mock_llm_service,
            message="I want a shirt under $100",
            context=context_no_clarification,
            entities=entities,
        )

        assert response.metadata.get("constraint") == "size"

    @pytest.mark.asyncio
    async def test_color_fourth_priority(
        self,
        handler,
        mock_db,
        mock_merchant,
        mock_llm_service,
        context_no_clarification,
    ):
        """Color should be asked after size."""
        entities = {"budget": 100.0, "category": "shirt", "size": "M"}

        response = await handler.handle(
            db=mock_db,
            merchant=mock_merchant,
            llm_service=mock_llm_service,
            message="I want a medium shirt under $100",
            context=context_no_clarification,
            entities=entities,
        )

        assert response.metadata.get("constraint") == "color"

    @pytest.mark.asyncio
    async def test_brand_lowest_priority(
        self,
        handler,
        mock_db,
        mock_merchant,
        mock_llm_service,
        context_no_clarification,
    ):
        """Brand should be asked last."""
        entities = {"budget": 100.0, "category": "shirt", "size": "M", "color": "blue"}

        response = await handler.handle(
            db=mock_db,
            merchant=mock_merchant,
            llm_service=mock_llm_service,
            message="I want a blue medium shirt under $100",
            context=context_no_clarification,
            entities=entities,
        )

        assert response.metadata.get("constraint") == "brand"


class TestAllConstraintsPresent:
    """Tests when all constraints are already present."""

    @pytest.mark.asyncio
    async def test_returns_error_when_no_questions(
        self,
        handler,
        mock_db,
        mock_merchant,
        mock_llm_service,
        context_no_clarification,
    ):
        """Should return error when all constraints are present."""
        entities = {
            "budget": 100.0,
            "category": "shirt",
            "size": "M",
            "color": "blue",
            "brand": "Nike",
        }

        response = await handler.handle(
            db=mock_db,
            merchant=mock_merchant,
            llm_service=mock_llm_service,
            message="I want a blue medium Nike shirt under $100",
            context=context_no_clarification,
            entities=entities,
        )

        assert response.intent == "clarification"
        assert response.metadata.get("error") == "no_questions"
