"""Tests for Suggestion Generator service.

Story 10-3: Quick Reply Chips Widget

Tests cover:
- RAG-based suggestion generation
- Fallback suggestion generation
- Max suggestions limit
- Empty chunks handling
- Keyword detection for categories
"""

import pytest

from app.services.llm.base_llm_service import LLMResponse
from app.services.rag.retrieval_service import RetrievedChunk
from app.services.rag.suggestion_generator import (
    FALLBACK_SUGGESTIONS,
    KEYWORD_CATEGORIES,
    SuggestionConfig,
    SuggestionGenerator,
)


@pytest.fixture
def generator() -> SuggestionGenerator:
    """Create a SuggestionGenerator instance for testing."""
    return SuggestionGenerator()


@pytest.fixture
def sample_chunks() -> list[RetrievedChunk]:
    """Create sample RAG chunks for testing."""
    return [
        RetrievedChunk(
            chunk_id=1,
            content="Our pricing plans include Basic, Pro, and Enterprise tiers. Each plan offers different features and support levels.",
            chunk_index=0,
            document_name="Pricing Guide.pdf",
            document_id=1,
            similarity=0.92,
        ),
        RetrievedChunk(
            chunk_id=2,
            content="The Pro plan includes advanced analytics, priority support, and unlimited team members.",
            chunk_index=1,
            document_name="Pricing Guide.pdf",
            document_id=1,
            similarity=0.88,
        ),
    ]


class TestSuggestionGenerator:
    """Test suite for SuggestionGenerator."""

    @pytest.mark.asyncio
    async def test_generate_suggestions_with_chunks_returns_suggestions(
        self, generator: SuggestionGenerator, sample_chunks: list[RetrievedChunk]
    ) -> None:
        """Test that suggestions are generated when chunks are provided."""
        suggestions = await generator.generate_suggestions(
            query="What are your pricing plans?",
            chunks=sample_chunks,
        )

        assert len(suggestions) > 0
        assert len(suggestions) <= 4

    @pytest.mark.asyncio
    async def test_generate_suggestions_no_chunks_returns_fallback(
        self, generator: SuggestionGenerator
    ) -> None:
        """Test that fallback suggestions are returned when no chunks."""
        suggestions = await generator.generate_suggestions(
            query="What are your pricing plans?",
            chunks=None,
        )

        assert len(suggestions) > 0
        assert len(suggestions) <= 4
        assert all(isinstance(s, str) for s in suggestions)

    @pytest.mark.asyncio
    async def test_max_suggestions_limit_enforced(
        self, generator: SuggestionGenerator, sample_chunks: list[RetrievedChunk]
    ) -> None:
        """Test that max suggestions limit is respected."""
        config = SuggestionConfig(max_suggestions=2)
        gen = SuggestionGenerator(config=config)

        suggestions = await gen.generate_suggestions(
            query="Tell me about pricing",
            chunks=sample_chunks,
        )

        assert len(suggestions) <= 2

    @pytest.mark.asyncio
    async def test_empty_chunks_uses_fallback(self, generator: SuggestionGenerator) -> None:
        """Test that empty chunks list triggers fallback."""
        suggestions = await generator.generate_suggestions(
            query="What are your hours?",
            chunks=[],
        )

        assert len(suggestions) > 0
        assert len(suggestions) <= 4

    def test_keyword_detection_pricing_category(self, generator: SuggestionGenerator) -> None:
        """Test keyword detection for pricing category."""
        category = generator._detect_category("How much does it cost?")
        assert category == "pricing"

        category = generator._detect_category("What are your prices?")
        assert category == "pricing"

        category = generator._detect_category("Do you offer discounts?")
        assert category == "pricing"

    def test_keyword_detection_hours_category(self, generator: SuggestionGenerator) -> None:
        """Test keyword detection for hours category."""
        category = generator._detect_category("What are your business hours?")
        assert category == "hours"

        category = generator._detect_category("When are you open?")
        assert category == "hours"

        category = generator._detect_category("What's your schedule?")
        assert category == "hours"

    def test_keyword_detection_contact_category(self, generator: SuggestionGenerator) -> None:
        """Test keyword detection for contact category."""
        category = generator._detect_category("How can I contact you?")
        assert category == "contact"

        category = generator._detect_category("What's your phone number?")
        assert category == "contact"

    def test_keyword_detection_features_category(self, generator: SuggestionGenerator) -> None:
        """Test keyword detection for features category."""
        category = generator._detect_category("What features do you offer?")
        assert category == "features"

        category = generator._detect_category("How does this work?")
        assert category == "features"

    def test_keyword_detection_default_category(self, generator: SuggestionGenerator) -> None:
        """Test default category when no keywords match."""
        category = generator._detect_category("Tell me about your company")
        assert category == "default"

        category = generator._detect_category("Hello there!")
        assert category == "default"

    def test_fallback_suggestions_structure(self) -> None:
        """Test that fallback suggestions have correct structure."""
        for category, suggestions in FALLBACK_SUGGESTIONS.items():
            assert isinstance(suggestions, list)
            assert len(suggestions) > 0
            assert all(isinstance(s, str) for s in suggestions)

    def test_keyword_categories_structure(self) -> None:
        """Test that keyword categories have correct structure."""
        for category, keywords in KEYWORD_CATEGORIES.items():
            assert isinstance(keywords, list)
            assert len(keywords) > 0
            assert all(isinstance(k, str) for k in keywords)

    @pytest.mark.asyncio
    async def test_document_name_extraction(self, generator: SuggestionGenerator) -> None:
        """Test that document names are used for suggestions."""
        chunks = [
            RetrievedChunk(
                chunk_id=1,
                content="Some content here",
                chunk_index=0,
                document_name="Getting Started Guide.pdf",
                document_id=1,
                similarity=0.9,
            ),
        ]

        suggestions = await generator.generate_suggestions(
            query="How do I get started?",
            chunks=chunks,
        )

        assert any("Getting Started Guide" in s for s in suggestions)

    def test_clean_document_name_removes_extensions(self, generator: SuggestionGenerator) -> None:
        """Test that file extensions are removed from document names."""
        assert generator._clean_document_name("Guide.pdf") == "Guide"
        assert generator._clean_document_name("Manual.txt") == "Manual"
        assert generator._clean_document_name("README.md") is None
        assert generator._clean_document_name("document") is None

    def test_clean_document_name_handles_underscores(self, generator: SuggestionGenerator) -> None:
        """Test that underscores are converted to spaces."""
        assert generator._clean_document_name("User_Manual.pdf") == "User Manual"
        assert (
            generator._clean_document_name("Getting_Started_Guide.txt") == "Getting Started Guide"
        )

    @pytest.mark.asyncio
    async def test_suggestions_deduplicated(self, generator: SuggestionGenerator) -> None:
        """Test that duplicate suggestions are removed."""
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

        suggestions = await generator.generate_suggestions(
            query="Help",
            chunks=chunks,
        )

        assert len(suggestions) == len(set(s.lower() for s in suggestions))

    @pytest.mark.asyncio
    async def test_config_custom_max_suggestions(self) -> None:
        """Test custom max_suggestions in config."""
        config = SuggestionConfig(max_suggestions=3)
        generator = SuggestionGenerator(config=config)

        suggestions = await generator.generate_suggestions(
            query="test query",
            chunks=None,
        )

        assert len(suggestions) <= 3


class TestSuggestionGeneratorPerformance:
    """Performance and edge case tests for SuggestionGenerator."""

    @pytest.fixture
    def generator(self) -> SuggestionGenerator:
        """Create a SuggestionGenerator instance for testing."""
        return SuggestionGenerator()

    @pytest.mark.asyncio
    async def test_generation_performance_under_50ms(self, generator: SuggestionGenerator) -> None:
        """[P2] AC2: Suggestion generation should complete in < 50ms."""
        import time

        chunks = [
            RetrievedChunk(
                chunk_id=i,
                content=f"Pricing tier {i} includes features and benefits.",
                chunk_index=0,
                document_name=f"Pricing_Guide_{i}.pdf",
                document_id=i,
                similarity=0.9 - (i * 0.05),
            )
            for i in range(4)
        ]

        start_time = time.perf_counter()
        suggestions = await generator.generate_suggestions(
            query="What are your pricing plans?",
            chunks=chunks,
        )
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        assert elapsed_ms < 50, f"Generation took {elapsed_ms}ms, expected < 50ms"
        assert len(suggestions) > 0

    @pytest.mark.asyncio
    async def test_large_chunk_content_handling(self, generator: SuggestionGenerator) -> None:
        """[P2] Large chunk content (1000+ chars) should be handled efficiently."""
        large_content = "A" * 1500

        chunks = [
            RetrievedChunk(
                chunk_id=1,
                content=large_content,
                chunk_index=0,
                document_name="Large_Document.pdf",
                document_id=1,
                similarity=0.9,
            )
        ]

        suggestions = await generator.generate_suggestions(
            query="test query",
            chunks=chunks,
        )

        assert suggestions is not None
        assert len(suggestions) > 0
        assert len(suggestions) <= 4

    @pytest.mark.asyncio
    async def test_many_chunks_more_than_max_suggestions(
        self, generator: SuggestionGenerator
    ) -> None:
        """[P2] With 10+ chunks, should still return max 4 suggestions."""
        many_chunks = [
            RetrievedChunk(
                chunk_id=i,
                content=f"Content for chunk {i} with various topics.",
                chunk_index=0,
                document_name=f"Document_{i}.pdf",
                document_id=i,
                similarity=0.9 - (i * 0.02),
            )
            for i in range(12)
        ]

        suggestions = await generator.generate_suggestions(
            query="test query",
            chunks=many_chunks,
        )

        assert len(suggestions) <= 4
        assert len(set(s.lower() for s in suggestions)) == len(suggestions)

    @pytest.mark.asyncio
    async def test_special_characters_in_content(self, generator: SuggestionGenerator) -> None:
        """[P2] Special characters in chunk content should not break generation."""
        chunks = [
            RetrievedChunk(
                chunk_id=1,
                content="Price: $99.99 (50% off!) - Limited time offer <click here>",
                chunk_index=0,
                document_name="Special_Offers.pdf",
                document_id=1,
                similarity=0.9,
            )
        ]

        suggestions = await generator.generate_suggestions(
            query="What's on sale?",
            chunks=chunks,
        )

        assert suggestions is not None
        assert len(suggestions) > 0
        for suggestion in suggestions:
            assert isinstance(suggestion, str)
            assert len(suggestion) > 0

    @pytest.mark.asyncio
    async def test_unicode_content_handling(self, generator: SuggestionGenerator) -> None:
        """[P2] Unicode characters in content should be handled correctly."""
        chunks = [
            RetrievedChunk(
                chunk_id=1,
                content="Prices start at €99 or ¥10,000. 中文支持 日本語サポート",
                chunk_index=0,
                document_name="International_Pricing.pdf",
                document_id=1,
                similarity=0.9,
            )
        ]

        suggestions = await generator.generate_suggestions(
            query="pricing",
            chunks=chunks,
        )

        assert suggestions is not None
        assert len(suggestions) > 0


class TestSuggestionGeneratorLLM:
    """Test LLM-powered suggestion generation."""

    @pytest.fixture
    def mock_llm_service(self):
        """Create a mock LLM service."""
        from unittest.mock import AsyncMock

        mock_service = AsyncMock()
        mock_service.chat = AsyncMock()
        return mock_service

    @pytest.mark.asyncio
    async def test_llm_generation_when_service_provided(self, mock_llm_service) -> None:
        """Test that LLM is used when service is provided with chunks."""
        mock_llm_service.chat.return_value = LLMResponse(
            content='["What are your hours?", "How can I contact support?", "Do you offer refunds?", "Where is your store located?"]',
            tokens_used=50,
            model="test-model",
            provider="test",
        )

        generator = SuggestionGenerator(llm_service=mock_llm_service)
        chunks = [
            RetrievedChunk(
                chunk_id=1,
                content="Our store is open 9-5. Contact us at support@example.com",
                chunk_index=0,
                document_name="Store Info.pdf",
                document_id=1,
                similarity=0.9,
            )
        ]

        suggestions = await generator.generate_suggestions(
            query="Tell me about your store",
            chunks=chunks,
        )

        assert len(suggestions) == 4
        assert "What are your hours?" in suggestions
        mock_llm_service.chat.assert_called_once()

    @pytest.mark.asyncio
    async def test_llm_generation_handles_json_in_code_block(self, mock_llm_service) -> None:
        """Test that LLM responses with markdown code blocks are handled."""
        mock_llm_service.chat.return_value = LLMResponse(
            content='```json\n["Question 1?", "Question 2?", "Question 3?", "Question 4?"]\n```',
            tokens_used=50,
            model="test-model",
            provider="test",
        )

        generator = SuggestionGenerator(llm_service=mock_llm_service)
        chunks = [
            RetrievedChunk(
                chunk_id=1,
                content="Test content",
                chunk_index=0,
                document_name="Test.pdf",
                document_id=1,
                similarity=0.9,
            )
        ]

        suggestions = await generator.generate_suggestions(
            query="test",
            chunks=chunks,
        )

        assert len(suggestions) == 4
        assert "Question 1?" in suggestions

    @pytest.mark.asyncio
    async def test_llm_fallback_on_parse_error(self, mock_llm_service) -> None:
        """Test fallback to chunk extraction when LLM returns invalid JSON."""
        mock_llm_service.chat.return_value = LLMResponse(
            content="This is not valid JSON at all",
            tokens_used=50,
            model="test-model",
            provider="test",
        )

        generator = SuggestionGenerator(llm_service=mock_llm_service)
        chunks = [
            RetrievedChunk(
                chunk_id=1,
                content="Our Pricing Guide includes Basic and Pro tiers.",
                chunk_index=0,
                document_name="Pricing Guide.pdf",
                document_id=1,
                similarity=0.9,
            )
        ]

        suggestions = await generator.generate_suggestions(
            query="Tell me about pricing",
            chunks=chunks,
        )

        assert len(suggestions) > 0
        assert any("Pricing Guide" in s for s in suggestions)

    @pytest.mark.asyncio
    async def test_llm_filters_short_suggestions(self, mock_llm_service) -> None:
        """Test that LLM suggestions under 5 chars are filtered out."""
        mock_llm_service.chat.return_value = LLMResponse(
            content='["OK", "Yes", "A valid question here?", "Another good question?"]',
            tokens_used=50,
            model="test-model",
            provider="test",
        )

        generator = SuggestionGenerator(llm_service=mock_llm_service)
        chunks = [
            RetrievedChunk(
                chunk_id=1,
                content="Test content",
                chunk_index=0,
                document_name="Test.pdf",
                document_id=1,
                similarity=0.9,
            )
        ]

        suggestions = await generator.generate_suggestions(
            query="test",
            chunks=chunks,
        )

        assert "OK" not in suggestions
        assert "Yes" not in suggestions
        assert "A valid question here?" in suggestions

    @pytest.mark.asyncio
    async def test_no_llm_uses_chunk_extraction(self) -> None:
        """Test that without LLM service, chunk extraction is used."""
        generator = SuggestionGenerator(llm_service=None)
        chunks = [
            RetrievedChunk(
                chunk_id=1,
                content="Our Pricing Guide includes various tiers.",
                chunk_index=0,
                document_name="Pricing Guide.pdf",
                document_id=1,
                similarity=0.9,
            )
        ]

        suggestions = await generator.generate_suggestions(
            query="Tell me about pricing",
            chunks=chunks,
        )

        assert len(suggestions) > 0
        assert any("Pricing Guide" in s for s in suggestions)
