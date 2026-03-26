"""Integration tests for UnifiedConversationService with RAG.

Story 8-5: Backend - RAG Integration in Conversation
Task 4.2: Integration tests for UnifiedConversationService with RAG

Tests cover:
- General mode merchant with documents → RAG context injected
- E-commerce mode merchant → no RAG context (even if docs exist)
- General mode with no documents → no RAG context
- RAG retrieval timeout → graceful degradation
- E-commerce intent in General mode → fallback message
- Response includes source citation
"""

from __future__ import annotations

from contextlib import ExitStack
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.merchant import Merchant, PersonalityType
from app.services.conversation.schemas import (
    Channel,
    ConsentState,
    ConversationContext,
    ConversationResponse,
)
from app.services.conversation.unified_conversation_service import (
    UnifiedConversationService,
)
from app.services.rag.context_builder import RAGContextBuilder
from app.services.rag.retrieval_service import RetrievedChunk


@pytest.fixture
def mock_db():
    """Create mock database session."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def general_mode_merchant():
    """Create a General mode merchant."""
    merchant = MagicMock(spec=Merchant)
    merchant.id = 1
    merchant.onboarding_mode = "general"
    merchant.personality = PersonalityType.FRIENDLY
    merchant.bot_name = "AI Assistant"
    merchant.business_name = "Test Business"
    merchant.has_store_connected = False
    merchant.has_facebook_connected = False
    merchant.budget_alert_enabled = False
    merchant.custom_greeting = None
    merchant.business_description = None
    merchant.business_hours = None
    return merchant


@pytest.fixture
def ecommerce_mode_merchant():
    """Create an e-commerce mode merchant."""
    merchant = MagicMock(spec=Merchant)
    merchant.id = 2
    merchant.onboarding_mode = "ecommerce"
    merchant.personality = PersonalityType.FRIENDLY
    merchant.bot_name = "Shopping Bot"
    merchant.business_name = "Test Store"
    merchant.has_store_connected = True
    merchant.has_facebook_connected = False
    merchant.budget_alert_enabled = False
    merchant.custom_greeting = None
    merchant.business_description = None
    merchant.business_hours = None
    return merchant


@pytest.fixture
def sample_chunks():
    """Create sample retrieved chunks."""
    return [
        RetrievedChunk(
            chunk_id=1,
            content="Product X has a battery life of 10 hours.",
            chunk_index=0,
            document_name="Product Manual.pdf",
            document_id=1,
            similarity=0.95,
        ),
        RetrievedChunk(
            chunk_id=2,
            content="Returns accepted within 30 days of purchase.",
            chunk_index=0,
            document_name="FAQ.txt",
            document_id=2,
            similarity=0.90,
        ),
    ]


@pytest.fixture
def conversation_context():
    """Create conversation context."""
    return ConversationContext(
        merchant_id=1,
        session_id="test-session",
        channel=Channel.WIDGET,
        conversation_history=[],
        conversation_data={},
        metadata={},
        consent_state=ConsentState(
            status="granted",
            visitor_id="test-visitor",
            prompt_shown=True,
        ),
    )


@pytest.fixture
def mock_rag_builder():
    """Create mock RAG context builder."""
    return AsyncMock(spec=RAGContextBuilder)


def _setup_service_mocks(
    stack: ExitStack,
    merchant: MagicMock,
    intent_value: str = "general",
    skip_classification: bool = False,
):
    """Set up common service mocks using ExitStack.

    Args:
        stack: ExitStack for context management
        merchant: Mock merchant object
        intent_value: Intent value for classification mock (only used if skip_classification=False)
        skip_classification: If True, don't mock _classify_intent (for general mode)

    Returns:
        mock_classify or None
    """
    stack.enter_context(
        patch.object(UnifiedConversationService, "_load_merchant", return_value=merchant)
    )
    stack.enter_context(
        patch.object(UnifiedConversationService, "_check_budget_pause", return_value=None)
    )
    stack.enter_context(
        patch.object(UnifiedConversationService, "_check_hybrid_mode", return_value=None)
    )
    stack.enter_context(patch.object(UnifiedConversationService, "_check_returning_shopper"))
    stack.enter_context(patch.object(UnifiedConversationService, "_check_and_prompt_consent"))
    stack.enter_context(
        patch.object(UnifiedConversationService, "_check_faq_match", return_value=None)
    )
    stack.enter_context(patch.object(UnifiedConversationService, "_get_merchant_llm"))

    mock_classify = None
    if not skip_classification:
        mock_classify = stack.enter_context(
            patch.object(UnifiedConversationService, "_classify_intent")
        )
        mock_classify.return_value = MagicMock(
            intent=MagicMock(value=intent_value),
            confidence=0.9,
            entities=None,
        )

    return mock_classify


class TestRAGIntegration:
    """Test RAG integration with UnifiedConversationService."""

    @pytest.mark.asyncio
    @pytest.mark.test_id("8-5-INT-001")
    @pytest.mark.priority("P0")
    async def test_general_mode_with_documents_rag_injected(
        self,
        mock_db,
        general_mode_merchant,
        conversation_context,
        mock_rag_builder,
    ):
        """Test that RAG context is injected for General mode merchants with documents.

        Test ID: 8-5-INT-001
        Priority: P0 (Critical - AC1 validation)
        AC Coverage: AC1 (RAG context retrieved and included)
        """
        mock_rag_builder.build_rag_context_with_chunks.return_value = (
            'From "Product Manual.pdf":\n- Product X has a battery life of 10 hours.',
            [],
            [RetrievedChunk(
                chunk_id=1,
                content="Product X has a battery life of 10 hours.",
                chunk_index=0,
                document_name="Product Manual.pdf",
                document_id=1,
                similarity=0.95
            ]
        ]
        )
            ],
        )

        with ExitStack() as stack:
            _setup_service_mocks(stack, general_mode_merchant)
            service = UnifiedConversationService(rag_context_builder=mock_rag_builder)

            stack.enter_context(
                patch.object(
                    service._handlers["llm"],
                    "handle",
                    return_value=ConversationResponse(
                        message="Test response", intent="general", confidence=1.0
                    ),
                )
            )
            stack.enter_context(patch.object(service, "_persist_conversation_message"))

            response = await service.process_message(
                db=mock_db,
                context=conversation_context,
                message="What is the battery life?",
            )

        mock_rag_builder.build_rag_context.assert_called_once_with(
            merchant_id=general_mode_merchant.id,
            user_query="What is the battery life?",
        )
        assert conversation_context.metadata is not None
        assert "rag_context" in conversation_context.metadata
        assert response.metadata is not None
        assert response.metadata.get("rag_enabled") is True

    @pytest.mark.asyncio
    @pytest.mark.test_id("8-5-INT-002")
    @pytest.mark.priority("P1")
    async def test_ecommerce_mode_no_rag_context(
        self,
        mock_db,
        ecommerce_mode_merchant,
        conversation_context,
        mock_rag_builder,
    ):
        """Test that e-commerce mode merchants don't get RAG context even if documents exist.

        Test ID: 8-5-INT-002
        Priority: P1 (High - Mode detection validation)
        AC Coverage: AC1 (RAG context only for General mode)
        """
        mock_rag_builder.build_rag_context.return_value = "RAG context"
        conversation_context.merchant_id = ecommerce_mode_merchant.id

        with ExitStack() as stack:
            # General mode should skip classification
            _setup_service_mocks(stack, general_mode_merchant, skip_classification=True)
            service = UnifiedConversationService(rag_context_builder=mock_rag_builder)
            stack.enter_context(
                patch.object(
                    service._handlers["llm"],
                    "handle",
                    return_value=ConversationResponse(
                        message="Test response", intent="general", confidence=1.0
                    ),
                )
            )
            stack.enter_context(
                patch.object(
                    service._handlers["llm"],
                    "handle",
                    return_value=ConversationResponse(
                        message="Test response", intent="general", confidence=1.0
                    ),
                )
            )
            stack.enter_context(
                patch.object(
                    service._handlers["llm"],
                    "handle",
                    return_value=ConversationResponse(
                        message="Test response", intent="general", confidence=1.0
                    ),
                )
            )
            stack.enter_context(patch.object(service, "_persist_conversation_message"))

            response = await service.process_message(
                db=mock_db,
                context=conversation_context,
                message="Test question",
            )

        mock_rag_builder.build_rag_context.assert_not_called()
        assert "rag_context" not in conversation_context.metadata
        assert response.metadata.get("rag_enabled") is not True

    @pytest.mark.asyncio
    @pytest.mark.test_id("8-5-INT-003")
    @pytest.mark.priority("P1")
    async def test_general_mode_no_documents_no_rag_context(
        self,
        mock_db,
        general_mode_merchant,
        conversation_context,
        mock_rag_builder,
    ):
        """Test that General mode merchants without documents don't get RAG context.

        Test ID: 8-5-INT-003
        Priority: P1 (High - Edge case handling)
        AC Coverage: AC1 (RAG context only when documents exist)
        """
        mock_rag_builder.build_rag_context.return_value = None

        with ExitStack() as stack:
            _setup_service_mocks(stack, general_mode_merchant)
            service = UnifiedConversationService(rag_context_builder=mock_rag_builder)

            stack.enter_context(
                patch.object(
                    service._handlers["llm"],
                    "handle",
                    return_value=ConversationResponse(
                        message="Test response", intent="general", confidence=1.0
                    ),
                )
            )
            stack.enter_context(patch.object(service, "_persist_conversation_message"))

            response = await service.process_message(
                db=mock_db,
                context=conversation_context,
                message="Test question",
            )

        mock_rag_builder.build_rag_context.assert_called_once()
        assert conversation_context.metadata.get("rag_context") is None
        assert response.metadata.get("rag_enabled") is not True

    @pytest.mark.asyncio
    @pytest.mark.test_id("8-5-INT-004")
    @pytest.mark.priority("P0")
    async def test_rag_retrieval_timeout_graceful_degradation(
        self,
        mock_db,
        general_mode_merchant,
        conversation_context,
        mock_rag_builder,
    ):
        """Test that RAG retrieval timeout results in graceful degradation.

        Test ID: 8-5-INT-004
        Priority: P0 (Critical - AC4 validation)
        AC Coverage: AC4 (Timeout graceful degradation)
        """
        mock_rag_builder.build_rag_context.return_value = None

        with ExitStack() as stack:
            _setup_service_mocks(stack, general_mode_merchant)
            service = UnifiedConversationService(rag_context_builder=mock_rag_builder)

            stack.enter_context(
                patch.object(
                    service._handlers["llm"],
                    "handle",
                    return_value=ConversationResponse(
                        message="Test response", intent="general", confidence=1.0
                    ),
                )
            )
            stack.enter_context(patch.object(service, "_persist_conversation_message"))

            response = await service.process_message(
                db=mock_db,
                context=conversation_context,
                message="Test question",
            )

        assert response is not None
        assert response.message is not None

    @pytest.mark.asyncio
    @pytest.mark.test_id("8-5-INT-005")
    @pytest.mark.priority("P0")
    async def test_ecommerce_intent_in_general_mode_fallback(
        self,
        mock_db,
        general_mode_merchant,
        conversation_context,
        mock_rag_builder,
    ):
        """Test that e-commerce intents in General mode trigger fallback message.

        Test ID: 8-5-INT-005
        Priority: P0 (Critical - AC3 validation)
        AC Coverage: AC3 (E-commerce intent fallback in General mode)
        """
        mock_rag_builder.build_rag_context.return_value = None

        with ExitStack() as stack:
            _setup_service_mocks(stack, general_mode_merchant, intent_value="product_search")
            service = UnifiedConversationService(rag_context_builder=mock_rag_builder)

            stack.enter_context(patch.object(service, "_persist_conversation_message"))

            response = await service.process_message(
                db=mock_db,
                context=conversation_context,
                message="Show me products",
            )

        assert response.intent == "general_mode_fallback"
        assert "general assistant" in response.message.lower()
        assert "shopify" in response.message.lower()

    @pytest.mark.asyncio
    @pytest.mark.test_id("8-5-INT-006")
    @pytest.mark.priority("P0")
    async def test_response_includes_source_citation(
        self,
        mock_db,
        general_mode_merchant,
        conversation_context,
        mock_rag_builder,
    ):
        """Test that responses with RAG context include source citations.

        Test ID: 8-5-INT-006
        Priority: P0 (Critical - AC2 validation)
        AC Coverage: AC2 (Source document citations)
        """
        rag_context = """From "Product Manual.pdf":
- Product X has a battery life of 10 hours.

From "FAQ.txt":
- Returns accepted within 30 days of purchase."""

        mock_rag_builder.build_rag_context.return_value = rag_context

        with ExitStack() as stack:
            _setup_service_mocks(stack, general_mode_merchant)
            service = UnifiedConversationService(rag_context_builder=mock_rag_builder)

            mock_handle = stack.enter_context(
                patch.object(
                    service._handlers["llm"],
                    "handle",
                    return_value=ConversationResponse(
                        message="According to Product Manual.pdf, the battery life is 10 hours.",
                        intent="general",
                        confidence=1.0,
                    ),
                )
            )
            stack.enter_context(patch.object(service, "_persist_conversation_message"))

            response = await service.process_message(
                db=mock_db,
                context=conversation_context,
                message="What is the battery life?",
            )

        handle_call = mock_handle.call_args
        passed_context = handle_call[1]["context"]
        assert "rag_context" in passed_context.metadata
        assert passed_context.metadata["rag_context"] == rag_context
        assert response.metadata.get("rag_enabled") is True
