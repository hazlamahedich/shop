"""Unit tests for RAGContextBuilder.

Story 8-5: Backend - RAG Integration in Conversation
Task 4.1: Unit tests for RAGContextBuilder

Tests cover:
- Formatting chunks with citations
- Grouping chunks by document name
- Handling empty chunk lists
- Retrieval timeout handling
- Error handling
- Token limit enforcement
- Sentence boundary truncation
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock

import pytest

from app.services.rag.context_builder import RAGContextBuilder
from app.services.rag.retrieval_service import RetrievedChunk


@pytest.fixture
def mock_retrieval_service():
    """Create mock retrieval service."""
    return AsyncMock()


@pytest.fixture
def context_builder(mock_retrieval_service):
    """Create RAGContextBuilder with mocked dependencies."""
    return RAGContextBuilder(retrieval_service=mock_retrieval_service)


@pytest.fixture
def sample_chunks():
    """Create sample retrieved chunks for testing."""
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
            content="Warranty covers manufacturing defects for 1 year.",
            chunk_index=1,
            document_name="Product Manual.pdf",
            document_id=1,
            similarity=0.90,
        ),
        RetrievedChunk(
            chunk_id=3,
            content="Returns accepted within 30 days of purchase.",
            chunk_index=0,
            document_name="FAQ.txt",
            document_id=2,
            similarity=0.85,
        ),
    ]


class TestFormatChunksAsContext:
    """Test _format_chunks_as_context method."""

    @pytest.mark.test_id("8-5-UNIT-001")
    @pytest.mark.priority("P0")
    def test_format_chunks_with_citations(self, context_builder, sample_chunks):
        """Test that chunks are formatted with document citations.

        Test ID: 8-5-UNIT-001
        Priority: P0 (Critical - Core RAG functionality)
        AC Coverage: AC2 (Source document citations)
        """
        result = context_builder._format_chunks_as_context(sample_chunks)

        # Check document names are included
        assert 'From "Product Manual.pdf":' in result
        assert 'From "FAQ.txt":' in result

        # Check chunk content is included
        assert "Product X has a battery life of 10 hours." in result
        assert "Warranty covers manufacturing defects for 1 year." in result
        assert "Returns accepted within 30 days of purchase." in result

    @pytest.mark.test_id("8-5-UNIT-002")
    @pytest.mark.priority("P1")
    def test_group_chunks_by_document(self, context_builder, sample_chunks):
        """Test that chunks are grouped by document name.

        Test ID: 8-5-UNIT-002
        Priority: P1 (High - Context organization)
        AC Coverage: AC2 (Source document citations)
        """
        result = context_builder._format_chunks_as_context(sample_chunks)

        # Check that Product Manual chunks appear together
        lines = result.split("\n")
        product_manual_indices = [i for i, line in enumerate(lines) if "Product Manual.pdf" in line]

        # Should have exactly one document header
        assert len(product_manual_indices) == 1

    @pytest.mark.test_id("8-5-UNIT-003")
    @pytest.mark.priority("P1")
    def test_format_empty_chunk_list(self, context_builder):
        """Test handling of empty chunk list.

        Test ID: 8-5-UNIT-003
        Priority: P1 (High - Edge case handling)
        AC Coverage: AC1 (RAG context retrieved)
        """
        result = context_builder._format_chunks_as_context([])
        assert result == ""

    @pytest.mark.test_id("8-5-UNIT-004")
    @pytest.mark.priority("P2")
    def test_format_single_chunk(self, context_builder):
        """Test formatting with single chunk.

        Test ID: 8-5-UNIT-004
        Priority: P2 (Medium - Edge case)
        AC Coverage: AC2 (Source document citations)
        """
        chunk = RetrievedChunk(
            chunk_id=1,
            content="Single chunk content",
            chunk_index=0,
            document_name="doc.txt",
            document_id=1,
            similarity=0.9,
        )

        result = context_builder._format_chunks_as_context([chunk])
        assert 'From "doc.txt":' in result
        assert "Single chunk content" in result


class TestBuildRagContext:
    """Test build_rag_context method."""

    @pytest.mark.asyncio
    @pytest.mark.test_id("8-5-UNIT-005")
    @pytest.mark.priority("P0")
    async def test_successful_retrieval(
        self, context_builder, mock_retrieval_service, sample_chunks
    ):
        """Test successful RAG context building.

        Test ID: 8-5-UNIT-005
        Priority: P0 (Critical - Core RAG functionality)
        AC Coverage: AC1 (RAG context retrieved and included)
        """
        mock_retrieval_service.retrieve_relevant_chunks.return_value = sample_chunks

        result = await context_builder.build_rag_context(
            merchant_id=1,
            user_query="What is the battery life?",
        )

        assert result is not None
        assert "Product Manual.pdf" in result
        assert "FAQ.txt" in result
        mock_retrieval_service.retrieve_relevant_chunks.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.test_id("8-5-UNIT-006")
    @pytest.mark.priority("P1")
    async def test_no_chunks_found(self, context_builder, mock_retrieval_service):
        """Test handling when no chunks are found.

        Test ID: 8-5-UNIT-006
        Priority: P1 (High - Edge case handling)
        AC Coverage: AC1 (RAG context retrieved)
        """
        mock_retrieval_service.retrieve_relevant_chunks.return_value = []

        result = await context_builder.build_rag_context(
            merchant_id=1,
            user_query="irrelevant query",
        )

        assert result is None

    @pytest.mark.asyncio
    @pytest.mark.test_id("8-5-UNIT-007")
    @pytest.mark.priority("P0")
    async def test_retrieval_timeout(self, context_builder, mock_retrieval_service):
        """Test handling of retrieval timeout.

        Test ID: 8-5-UNIT-007
        Priority: P0 (Critical - AC4 requirement)
        AC Coverage: AC4 (Timeout graceful degradation)
        """

        async def slow_retrieve(*args, **kwargs):
            await asyncio.sleep(1)  # Longer than 500ms timeout
            return []

        mock_retrieval_service.retrieve_relevant_chunks = slow_retrieve

        result = await context_builder.build_rag_context(
            merchant_id=1,
            user_query="test query",
        )

        # Should return None gracefully
        assert result is None

    @pytest.mark.asyncio
    @pytest.mark.test_id("8-5-UNIT-008")
    @pytest.mark.priority("P1")
    async def test_retrieval_error(self, context_builder, mock_retrieval_service):
        """Test handling of retrieval errors.

        Test ID: 8-5-UNIT-008
        Priority: P1 (High - Error handling)
        AC Coverage: AC4 (Graceful degradation)
        """
        mock_retrieval_service.retrieve_relevant_chunks.side_effect = Exception("Database error")

        result = await context_builder.build_rag_context(
            merchant_id=1,
            user_query="test query",
        )

        # Should return None gracefully
        assert result is None

    @pytest.mark.asyncio
    @pytest.mark.test_id("8-5-UNIT-009")
    @pytest.mark.priority("P2")
    async def test_custom_parameters(self, context_builder, mock_retrieval_service, sample_chunks):
        """Test that custom top_k and threshold are passed through.

        Test ID: 8-5-UNIT-009
        Priority: P2 (Medium - Parameter validation)
        AC Coverage: AC1 (RAG context retrieved)
        """
        mock_retrieval_service.retrieve_relevant_chunks.return_value = sample_chunks

        await context_builder.build_rag_context(
            merchant_id=1,
            user_query="test query",
            top_k=10,
            similarity_threshold=0.8,
        )

        mock_retrieval_service.retrieve_relevant_chunks.assert_called_once_with(
            merchant_id=1,
            query="test query",
            top_k=10,
            threshold=0.8,
        )


class TestTokenLimit:
    """Test token limit enforcement."""

    @pytest.mark.test_id("8-5-UNIT-010")
    @pytest.mark.priority("P2")
    def test_estimate_tokens(self, context_builder):
        """Test token estimation.

        Test ID: 8-5-UNIT-010
        Priority: P2 (Medium - Helper function)
        AC Coverage: N/A (Implementation detail)
        """
        # ~4 chars per token
        text = "This is a test"  # 14 chars
        tokens = context_builder._estimate_tokens(text)
        assert tokens == 3  # 14 // 4

    @pytest.mark.test_id("8-5-UNIT-011")
    @pytest.mark.priority("P2")
    def test_truncate_at_sentence(self, context_builder):
        """Test truncation at sentence boundary.

        Test ID: 8-5-UNIT-011
        Priority: P2 (Medium - Helper function)
        AC Coverage: N/A (Implementation detail)
        """
        text = "First sentence. Second sentence. Third sentence."

        # Truncate to fit first sentence (period at position 15)
        result = context_builder._truncate_at_sentence(text, 30)

        assert result == "First sentence."
        assert "Third" not in result

    @pytest.mark.test_id("8-5-UNIT-012")
    @pytest.mark.priority("P2")
    def test_truncate_no_period(self, context_builder):
        """Test truncation when no period exists.

        Test ID: 8-5-UNIT-012
        Priority: P2 (Medium - Edge case)
        AC Coverage: N/A (Implementation detail)
        """
        text = "No sentence boundary here"
        result = context_builder._truncate_at_sentence(text, 15)
        # _truncate_at_sentence returns text[:15] which is 15 chars, but then
        # we check for period which doesn't exist, so we return truncated[:15]
        # which is actually "No sentence bou" (14 chars due to 0-indexing)
        assert len(result) <= 15
        assert result.startswith("No sentence")

    @pytest.mark.test_id("8-5-UNIT-013")
    @pytest.mark.priority("P1")
    def test_truncate_context(self, context_builder, sample_chunks):
        """Test context truncation to fit token limit.

        Test ID: 8-5-UNIT-013
        Priority: P1 (High - Token limit enforcement)
        AC Coverage: N/A (Implementation detail)
        """
        # Create very long context
        long_chunks = [
            RetrievedChunk(
                chunk_id=i,
                content="This is a very long chunk. " * 100,
                chunk_index=0,
                document_name=f"doc{i}.txt",
                document_id=i,
                similarity=0.9,
            )
            for i in range(10)
        ]

        context = context_builder._format_chunks_as_context(long_chunks)
        truncated = context_builder._truncate_context(context, max_tokens=100)

        # Should be truncated
        assert len(truncated) < len(context)
        # Should end at sentence boundary
        assert truncated.endswith(".")

    @pytest.mark.asyncio
    @pytest.mark.test_id("8-5-UNIT-014")
    @pytest.mark.priority("P1")
    async def test_context_truncation_enforced(self, context_builder, mock_retrieval_service):
        """Test that context is truncated when exceeding token limit.

        Test ID: 8-5-UNIT-014
        Priority: P1 (High - Token limit enforcement)
        AC Coverage: AC1 (RAG context retrieved)
        """
        # Create chunks that would exceed 2000 tokens
        long_chunks = [
            RetrievedChunk(
                chunk_id=i,
                content="This is a test chunk. " * 500,  # ~2500 chars each
                chunk_index=0,
                document_name=f"doc{i}.txt",
                document_id=i,
                similarity=0.9,
            )
            for i in range(5)
        ]

        mock_retrieval_service.retrieve_relevant_chunks.return_value = long_chunks

        result = await context_builder.build_rag_context(
            merchant_id=1,
            user_query="test",
        )

        # Result should exist but be truncated
        assert result is not None
        # Should be within reasonable size (rough check)
        estimated_tokens = context_builder._estimate_tokens(result)
        assert estimated_tokens <= context_builder.MAX_CONTEXT_TOKENS * 1.1  # 10% margin


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    @pytest.mark.test_id("8-5-UNIT-015")
    @pytest.mark.priority("P3")
    def test_format_chunks_with_special_characters(self, context_builder):
        """Test formatting chunks with special characters in document names.

        Test ID: 8-5-UNIT-015
        Priority: P3 (Low - Edge case)
        AC Coverage: AC2 (Source document citations)
        """
        chunks = [
            RetrievedChunk(
                chunk_id=1,
                content="Content",
                chunk_index=0,
                document_name="Product's Manual (v2).pdf",
                document_id=1,
                similarity=0.9,
            )
        ]

        result = context_builder._format_chunks_as_context(chunks)
        assert "Product's Manual (v2).pdf" in result

    @pytest.mark.test_id("8-5-UNIT-016")
    @pytest.mark.priority("P3")
    def test_format_chunks_with_empty_content(self, context_builder):
        """Test formatting chunks with empty content.

        Test ID: 8-5-UNIT-016
        Priority: P3 (Low - Edge case)
        AC Coverage: AC2 (Source document citations)
        """
        chunks = [
            RetrievedChunk(
                chunk_id=1,
                content="",
                chunk_index=0,
                document_name="doc.txt",
                document_id=1,
                similarity=0.9,
            )
        ]

        result = context_builder._format_chunks_as_context(chunks)
        assert 'From "doc.txt":' in result

    @pytest.mark.asyncio
    @pytest.mark.test_id("8-5-UNIT-017")
    @pytest.mark.priority("P2")
    async def test_multiple_documents_context(self, context_builder, mock_retrieval_service):
        """Test context building with multiple documents.

        Test ID: 8-5-UNIT-017
        Priority: P2 (Medium - Multi-document handling)
        AC Coverage: AC2 (Source document citations)
        """
        chunks = [
            RetrievedChunk(
                chunk_id=i,
                content=f"Content from document {i}",
                chunk_index=0,
                document_name=f"doc{i}.txt",
                document_id=i,
                similarity=0.9,
            )
            for i in range(5)
        ]

        mock_retrieval_service.retrieve_relevant_chunks.return_value = chunks

        result = await context_builder.build_rag_context(
            merchant_id=1,
            user_query="test",
        )

        # Should include all documents
        for i in range(5):
            assert f"doc{i}.txt" in result
