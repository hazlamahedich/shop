"""Integration tests for Story 10-3: Suggestion Generation Service.

Tests suggestion generation from RAG context, fallback behavior, and API response integration.

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
                chunk_id=2,
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
            query="Tell me about pricing", chunks=sample_chunks[:1]
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
            query="I need help with features", chunks=None
        )

        assert suggestions is not None
        assert len(suggestions) > 0
        assert len(suggestions) <= 4

    @pytest.mark.asyncio
    async def test_max_suggestions_limit_enforced(self, sample_chunks):
        """[P0] AC2: Max 4 suggestions should be returned."""
        from app.services.rag.suggestion_generator import SuggestionGenerator

        generator = SuggestionGenerator()
        suggestions = await generator.generate_suggestions(query="test query", chunks=sample_chunks)

        assert len(suggestions) <= 4

    @pytest.mark.asyncio
    async def test_suggestion_keyword_category_detection_pricing(self):
        """[P1] AC5: Keyword detection for pricing category."""
        from app.services.rag.suggestion_generator import SuggestionGenerator

        generator = SuggestionGenerator()
        suggestions = await generator.generate_suggestions(
            query="How much does it cost?", chunks=None
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
            query="How can I reach support?", chunks=None
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
        suggestions = await generator.generate_suggestions(query="When are you open?", chunks=None)

        assert suggestions is not None
        assert any("hour" in s.lower() or "open" in s.lower() for s in suggestions)
