"""Integration tests for Story 10-3: Quick Reply Chips Widget.

Tests suggestion generation from RAG context, fallback behavior,
and API response integration.

Story 10-3: Quick Reply Chips Widget
"""

from __future__ import annotations

import os
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

os.environ["IS_TESTING"] = "true"


class TestSuggestionGeneratorIntegration:
    """Integration tests for suggestion generator with RAG context."""

    @pytest.fixture
    def sample_chunks(self):
        """Create sample retrieved chunks for testing."""
        from app.services.rag.retrieval_service import RetrievedChunk

        return [
            RetrievedChunk(
                chunk_id=1,
                content="Our Pricing Plans include Basic, Pro, and Enterprise tiers. The Basic plan costs $10/month.",
                chunk_index=0,
                document_name="Pricing_Guide.pdf",
                document_id=1,
                similarity=0.95,
            ),
            RetrievedChunk(
                chunk_id=2,
                content="For support, contact our team via email or phone. Support hours are 9am-5pm EST.",
                chunk_index=0,
                document_name="Support_Contact.pdf",
                document_id=2,
                similarity=0.88,
            ),
            RetrievedChunk(
                chunk_id=3,
                content="Installation requires Node.js version 18 or higher. Follow the Quick Start guide.",
                chunk_index=1,
                document_name="Installation_Manual.pdf",
                document_id=3,
                similarity=0.82,
            ),
        ]

    @pytest.fixture
    def sample_empty_chunks(self):
        """Create empty chunks list for fallback testing."""
        return []

    @pytest.mark.asyncio
    async def test_suggestion_generation_with_rag_chunks(self, sample_chunks):
        """[P0] AC2: Suggestions should be generated from RAG chunk content."""
        from app.services.rag.suggestion_generator import SuggestionGenerator

        generator = SuggestionGenerator()
        suggestions = await generator.generate_suggestions(
            query="What are your pricing plans?",
            chunks=sample_chunks,
        )

        assert suggestions is not None
        assert len(suggestions) > 0
        assert len(suggestions) <= 4
        assert all(isinstance(s, str) for s in suggestions)

    @pytest.mark.asyncio
    async def test_suggestions_include_document_names(self, sample_chunks):
        """[P1] AC2: Suggestions should reference document names when available."""
        from app.services.rag.suggestion_generator import SuggestionGenerator

        generator = SuggestionGenerator()
        suggestions = await generator.generate_suggestions(
            query="Tell me about pricing",
            chunks=sample_chunks[:1],
        )

        assert suggestions is not None
        assert len(suggestions) > 0
        has_document_ref = any("pricing" in s.lower() or "guide" in s.lower() for s in suggestions)
        assert has_document_ref, f"Suggestions should reference document: {suggestions}"

    @pytest.mark.asyncio
    async def test_suggestion_fallback_when_no_chunks(self, sample_empty_chunks):
        """[P0] AC5: Fallback suggestions when RAG returns empty."""
        from app.services.rag.suggestion_generator import SuggestionGenerator

        generator = SuggestionGenerator()
        suggestions = await generator.generate_suggestions(
            query="What are your pricing plans?",
            chunks=sample_empty_chunks,
        )

        assert suggestions is not None
        assert len(suggestions) > 0
        assert len(suggestions) <= 4
        assert all(isinstance(s, str) for s in suggestions)

    @pytest.mark.asyncio
    async def test_suggestion_fallback_when_none_chunks(self):
        """[P1] AC5: Fallback suggestions when chunks is None."""
        from app.services.rag.suggestion_generator import SuggestionGenerator

        generator = SuggestionGenerator()
        suggestions = await generator.generate_suggestions(
            query="I need help with features",
            chunks=None,
        )

        assert suggestions is not None
        assert len(suggestions) > 0
        assert len(suggestions) <= 4

    @pytest.mark.asyncio
    async def test_max_suggestions_limit_enforced(self, sample_chunks):
        """[P0] AC2: Max 4 suggestions should be returned."""
        from app.services.rag.suggestion_generator import SuggestionGenerator

        generator = SuggestionGenerator()
        suggestions = await generator.generate_suggestions(
            query="test query",
            chunks=sample_chunks,
        )

        assert len(suggestions) <= 4

    @pytest.mark.asyncio
    async def test_suggestion_keyword_category_detection_pricing(self):
        """[P1] AC5: Keyword detection for pricing category."""
        from app.services.rag.suggestion_generator import SuggestionGenerator

        generator = SuggestionGenerator()
        suggestions = await generator.generate_suggestions(
            query="How much does it cost?",
            chunks=None,
        )

        assert suggestions is not None
        assert len(suggestions) > 0
        assert any("pricing" in s.lower() or "discount" in s.lower() for s in suggestions)

    @pytest.mark.asyncio
    async def test_suggestion_keyword_category_detection_contact(self):
        """[P1] AC5: Keyword detection for contact category."""
        from app.services.rag.suggestion_generator import SuggestionGenerator

        generator = SuggestionGenerator()
        suggestions = await generator.generate_suggestions(
            query="How can I reach support?",
            chunks=None,
        )

        assert suggestions is not None
        assert any(
            "contact" in s.lower() or "phone" in s.lower() or "support" in s.lower()
            for s in suggestions
        )

    @pytest.mark.asyncio
    async def test_suggestion_keyword_category_detection_hours(self):
        """[P1] AC5: Keyword detection for hours category."""
        from app.services.rag.suggestion_generator import SuggestionGenerator

        generator = SuggestionGenerator()
        suggestions = await generator.generate_suggestions(
            query="When are you open?",
            chunks=None,
        )

        assert suggestions is not None
        assert any("hour" in s.lower() or "open" in s.lower() for s in suggestions)

    @pytest.mark.asyncio
    async def test_suggestion_keyword_category_detection_features(self):
        """[P1] AC5: Keyword detection for features category."""
        from app.services.rag.suggestion_generator import SuggestionGenerator

        generator = SuggestionGenerator()
        suggestions = await generator.generate_suggestions(
            query="What features does this have?",
            chunks=None,
        )

        assert suggestions is not None
        assert any(
            "feature" in s.lower() or "work" in s.lower() or "demo" in s.lower()
            for s in suggestions
        )


class TestSuggestionSchemaIntegration:
    """Integration tests for suggestion field in API response schemas."""

    @pytest.fixture
    def sample_suggestions(self):
        """Create sample suggestions."""
        return [
            "Tell me more about Pricing Guide",
            "What about Basic?",
            "Can you tell me more?",
            "What else should I know?",
        ]

    @pytest.mark.asyncio
    async def test_conversation_response_includes_suggestions(self, sample_suggestions):
        """[P0] ConversationResponse should include suggested_replies field."""
        from app.services.conversation.schemas import ConversationResponse

        response = ConversationResponse(
            message="Based on our documentation...",
            suggested_replies=sample_suggestions,
        )

        assert response.suggested_replies is not None
        assert len(response.suggested_replies) == 4
        assert response.suggested_replies[0] == "Tell me more about Pricing Guide"

    @pytest.mark.asyncio
    async def test_conversation_response_without_suggestions(self):
        """[P1] ConversationResponse should work without suggestions."""
        from app.services.conversation.schemas import ConversationResponse

        response = ConversationResponse(
            message="Hello! How can I help?",
        )

        assert response.suggested_replies is None

    @pytest.mark.asyncio
    async def test_widget_message_response_includes_suggestions(self, sample_suggestions):
        """[P0] WidgetMessageResponse should include suggestedReplies with alias."""
        from app.schemas.widget import WidgetMessageResponse

        response = WidgetMessageResponse(
            messageId="msg-123",
            content="Based on our documentation...",
            sender="bot",
            createdAt=datetime.now(timezone.utc),
            suggested_replies=sample_suggestions,
        )

        assert response.suggested_replies is not None
        assert len(response.suggested_replies) == 4

    @pytest.mark.asyncio
    async def test_widget_message_response_camel_case_alias(self, sample_suggestions):
        """[P0] WidgetMessageResponse should use camelCase alias for JSON."""
        from app.schemas.widget import WidgetMessageResponse

        response = WidgetMessageResponse(
            messageId="msg-456",
            content="Response content",
            sender="bot",
            createdAt=datetime.now(timezone.utc),
            suggested_replies=sample_suggestions,
        )

        json_data = response.model_dump(by_alias=True)

        assert "suggestedReplies" in json_data
        assert "suggested_replies" not in json_data

    @pytest.mark.asyncio
    async def test_widget_message_envelope_contains_suggestions(self, sample_suggestions):
        """[P0] Widget message envelope should include suggestions in response."""
        from app.schemas.widget import (
            WidgetMessageResponse,
            WidgetMessageEnvelope,
            create_meta,
        )

        response = WidgetMessageResponse(
            messageId="msg-789",
            content="Here is the information...",
            sender="bot",
            createdAt=datetime.now(timezone.utc),
            suggested_replies=sample_suggestions,
        )

        envelope = WidgetMessageEnvelope(
            data=response,
            meta=create_meta(),
        )

        assert envelope.data.suggested_replies is not None
        assert len(envelope.data.suggested_replies) == 4
        assert envelope.meta.request_id is not None

    @pytest.mark.asyncio
    async def test_max_suggestions_in_schema(self):
        """[P1] Schema should accept exactly 4 suggestions."""
        from app.schemas.widget import WidgetMessageResponse

        four_suggestions = [f"Suggestion {i}" for i in range(4)]

        response = WidgetMessageResponse(
            messageId="msg-test",
            content="Content",
            sender="bot",
            createdAt=datetime.now(timezone.utc),
            suggested_replies=four_suggestions,
        )

        assert len(response.suggested_replies) == 4


class TestSuggestionGeneratorEdgeCases:
    """Edge case tests for suggestion generator."""

    @pytest.mark.asyncio
    async def test_chunks_with_no_extractable_topics(self):
        """[P2] Chunks with no extractable topics should use fallback."""
        from app.services.rag.suggestion_generator import SuggestionGenerator
        from app.services.rag.retrieval_service import RetrievedChunk

        chunks = [
            RetrievedChunk(
                chunk_id=1,
                content="the the the the the",
                chunk_index=0,
                document_name="doc.pdf",
                document_id=1,
                similarity=0.9,
            ),
        ]

        generator = SuggestionGenerator()
        suggestions = await generator.generate_suggestions(
            query="test",
            chunks=chunks,
        )

        assert suggestions is not None
        assert len(suggestions) > 0

    @pytest.mark.asyncio
    async def test_chunks_with_generic_document_names(self):
        """[P2] Generic document names should be filtered out."""
        from app.services.rag.suggestion_generator import SuggestionGenerator
        from app.services.rag.retrieval_service import RetrievedChunk

        chunks = [
            RetrievedChunk(
                chunk_id=1,
                content="Some content here",
                chunk_index=0,
                document_name="document.pdf",
                document_id=1,
                similarity=0.9,
            ),
        ]

        generator = SuggestionGenerator()
        suggestions = await generator.generate_suggestions(
            query="test",
            chunks=chunks,
        )

        assert suggestions is not None
        assert len(suggestions) > 0
        assert not any("document" in s.lower() and "tell me more" in s.lower() for s in suggestions)

    @pytest.mark.asyncio
    async def test_query_with_no_matching_keywords(self):
        """[P2] Query with no matching keywords should use default category."""
        from app.services.rag.suggestion_generator import SuggestionGenerator

        generator = SuggestionGenerator()
        suggestions = await generator.generate_suggestions(
            query="xyzabc random words",
            chunks=None,
        )

        assert suggestions is not None
        assert len(suggestions) > 0
        assert any(
            "tell me more" in s.lower()
            or "else" in s.lower()
            or "documentation" in s.lower()
            or "started" in s.lower()
            for s in suggestions
        )

    @pytest.mark.asyncio
    async def test_document_name_cleaning_removes_extensions(self):
        """[P2] Document name cleaning should remove file extensions."""
        from app.services.rag.suggestion_generator import SuggestionGenerator
        from app.services.rag.retrieval_service import RetrievedChunk

        chunks = [
            RetrievedChunk(
                chunk_id=1,
                content="Some content",
                chunk_index=0,
                document_name="User_Manual.docx",
                document_id=1,
                similarity=0.9,
            ),
        ]

        generator = SuggestionGenerator()
        suggestions = await generator.generate_suggestions(
            query="test",
            chunks=chunks,
        )

        assert suggestions is not None
        assert not any(".docx" in s for s in suggestions)

    @pytest.mark.asyncio
    async def test_deduplication_of_suggestions(self):
        """[P2] Duplicate suggestions should be removed."""
        from app.services.rag.suggestion_generator import SuggestionGenerator
        from app.services.rag.retrieval_service import RetrievedChunk

        chunks = [
            RetrievedChunk(
                chunk_id=1,
                content="Content",
                chunk_index=0,
                document_name="Guide.pdf",
                document_id=1,
                similarity=0.9,
            ),
            RetrievedChunk(
                chunk_id=2,
                content="More content",
                chunk_index=0,
                document_name="Guide.pdf",
                document_id=1,
                similarity=0.85,
            ),
        ]

        generator = SuggestionGenerator()
        suggestions = await generator.generate_suggestions(
            query="test",
            chunks=chunks,
        )

        assert suggestions is not None
        assert len(suggestions) == len(set(s.lower() for s in suggestions))
