"""Tests for Retrieval Service.

Story 8-4: Backend - RAG Service (Document Processing)

Test Coverage:
- AC2: Retrieval with similarity scores (top 5 chunks)
- AC3: Threshold filtering (similarity < 0.7 returns empty)
- Multi-tenant isolation
- Timeout handling
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import APIError, ErrorCode
from app.services.rag.embedding_service import EmbeddingResult, EmbeddingService
from app.services.rag.retrieval_service import RetrievedChunk, RetrievalService


class TestRetrievalServiceInit:
    """Tests for RetrievalService initialization."""

    def test_init_default_values(self):
        """Test initialization with default values."""
        mock_db = MagicMock(spec=AsyncSession)
        mock_embedding = MagicMock(spec=EmbeddingService)

        service = RetrievalService(mock_db, mock_embedding)

        assert service.similarity_threshold == RetrievalService.SIMILARITY_THRESHOLD
        assert service.top_k == RetrievalService.TOP_K_DEFAULT
        assert service.db == mock_db
        assert service.embedding_service == mock_embedding

    def test_init_custom_values(self):
        """Test initialization with custom values."""
        mock_db = MagicMock(spec=AsyncSession)
        mock_embedding = MagicMock(spec=EmbeddingService)

        service = RetrievalService(
            mock_db,
            mock_embedding,
            similarity_threshold=0.8,
            top_k=10,
        )

        assert service.similarity_threshold == 0.8
        assert service.top_k == 10


class TestRetrieveRelevantChunks:
    """Tests for retrieve_relevant_chunks method."""

    @pytest.mark.asyncio
    async def test_retrieve_returns_top_k_chunks(self):
        """AC2: Test retrieval returns top 5 chunks with similarity scores."""
        mock_db = MagicMock(spec=AsyncSession)
        mock_embedding = MagicMock(spec=EmbeddingService)

        # Mock embedding generation
        mock_embedding.embed_query = AsyncMock(return_value=[0.1] * 1536)

        # Mock database query results
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            MagicMock(
                chunk_id=1,
                content="Chunk 1 content",
                chunk_index=0,
                document_name="doc1.pdf",
                document_id=1,
                similarity=0.95,
            ),
            MagicMock(
                chunk_id=2,
                content="Chunk 2 content",
                chunk_index=1,
                document_name="doc1.pdf",
                document_id=1,
                similarity=0.85,
            ),
            MagicMock(
                chunk_id=3,
                content="Chunk 3 content",
                chunk_index=0,
                document_name="doc2.pdf",
                document_id=2,
                similarity=0.75,
            ),
        ]
        mock_db.execute = AsyncMock(return_value=mock_result)

        service = RetrievalService(mock_db, mock_embedding)

        chunks = await service.retrieve_relevant_chunks(
            merchant_id=1,
            query="test query",
            top_k=5,
        )

        assert len(chunks) == 3
        assert all(isinstance(c, RetrievedChunk) for c in chunks)
        assert chunks[0].similarity == 0.95
        assert chunks[1].similarity == 0.85
        assert chunks[2].similarity == 0.75

    @pytest.mark.asyncio
    async def test_retrieve_filters_by_threshold(self):
        """AC3: Test retrieval filters chunks below threshold (0.7)."""
        mock_db = MagicMock(spec=AsyncSession)
        mock_embedding = MagicMock(spec=EmbeddingService)

        mock_embedding.embed_query = AsyncMock(return_value=[0.1] * 1536)

        # Mock database returns only chunks above threshold (SQL does filtering)
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []  # No chunks above threshold
        mock_db.execute = AsyncMock(return_value=mock_result)

        service = RetrievalService(mock_db, mock_embedding)

        chunks = await service.retrieve_relevant_chunks(
            merchant_id=1,
            query="irrelevant query",
        )

        assert chunks == []

    @pytest.mark.asyncio
    async def test_retrieve_custom_threshold(self):
        """Test retrieval with custom threshold parameter."""
        mock_db = MagicMock(spec=AsyncSession)
        mock_embedding = MagicMock(spec=EmbeddingService)

        mock_embedding.embed_query = AsyncMock(return_value=[0.1] * 1536)

        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            MagicMock(
                chunk_id=1,
                content="High similarity chunk",
                chunk_index=0,
                document_name="doc.pdf",
                document_id=1,
                similarity=0.9,
            ),
        ]
        mock_db.execute = AsyncMock(return_value=mock_result)

        service = RetrievalService(mock_db, mock_embedding)

        chunks = await service.retrieve_relevant_chunks(
            merchant_id=1,
            query="test query",
            threshold=0.85,  # Higher threshold
        )

        assert len(chunks) == 1
        assert chunks[0].similarity >= 0.85

    @pytest.mark.asyncio
    async def test_retrieve_multi_tenant_isolation(self):
        """Test retrieval filters by merchant_id for multi-tenant isolation."""
        mock_db = MagicMock(spec=AsyncSession)
        mock_embedding = MagicMock(spec=EmbeddingService)

        mock_embedding.embed_query = AsyncMock(return_value=[0.1] * 1536)

        executed_query = None
        executed_params = None

        async def capture_execute(query, params):
            nonlocal executed_query, executed_params
            executed_query = query
            executed_params = params
            mock_result = MagicMock()
            mock_result.fetchall.return_value = []
            return mock_result

        mock_db.execute = capture_execute

        service = RetrievalService(mock_db, mock_embedding)

        await service.retrieve_relevant_chunks(
            merchant_id=42,
            query="test query",
        )

        # Verify merchant_id was used in query
        assert executed_params["merchant_id"] == 42

    @pytest.mark.asyncio
    async def test_retrieve_embedding_timeout_returns_empty(self):
        """Test graceful degradation on embedding timeout."""
        mock_db = MagicMock(spec=AsyncSession)
        mock_embedding = MagicMock(spec=EmbeddingService)

        # Mock embedding timeout
        mock_embedding.embed_query = AsyncMock(
            side_effect=asyncio.TimeoutError("Embedding timeout")
        )

        service = RetrievalService(mock_db, mock_embedding)

        chunks = await service.retrieve_relevant_chunks(
            merchant_id=1,
            query="test query",
        )

        assert chunks == []

    @pytest.mark.asyncio
    async def test_retrieve_search_timeout_raises_error(self):
        """Test search timeout raises RETRIEVAL_TIMEOUT error."""
        mock_db = MagicMock(spec=AsyncSession)
        mock_embedding = MagicMock(spec=EmbeddingService)

        mock_embedding.embed_query = AsyncMock(return_value=[0.1] * 1536)

        # Mock database timeout
        async def timeout_execute(*args, **kwargs):
            await asyncio.sleep(1)  # Simulate slow query

        mock_db.execute = timeout_execute

        service = RetrievalService(mock_db, mock_embedding)

        # Should timeout and raise error
        with pytest.raises(APIError) as exc_info:
            await service.retrieve_relevant_chunks(
                merchant_id=1,
                query="test query",
            )

        assert exc_info.value.code == ErrorCode.RETRIEVAL_TIMEOUT


class TestFormatEmbedding:
    """Tests for _format_embedding method."""

    def test_format_embedding(self):
        """Test embedding formatting for pgvector."""
        mock_db = MagicMock(spec=AsyncSession)
        mock_embedding = MagicMock(spec=EmbeddingService)

        service = RetrievalService(mock_db, mock_embedding)

        embedding = [0.1, -0.2, 0.5, 0.0]
        result = service._format_embedding(embedding)

        assert result == "[0.1,-0.2,0.5,0.0]"

    def test_format_embedding_large(self):
        """Test formatting large embedding vector."""
        mock_db = MagicMock(spec=AsyncSession)
        mock_embedding = MagicMock(spec=EmbeddingService)

        service = RetrievalService(mock_db, mock_embedding)

        embedding = [0.1] * 1536
        result = service._format_embedding(embedding)

        assert result.startswith("[0.1")
        assert result.endswith("0.1]")
        assert result.count(",") == 1535  # 1536 values = 1535 commas


class TestCheckDocumentAccess:
    """Tests for check_document_access method."""

    @pytest.mark.asyncio
    async def test_check_access_true(self):
        """Test document access check returns True when merchant owns document."""
        mock_db = MagicMock(spec=AsyncSession)
        mock_embedding = MagicMock(spec=EmbeddingService)

        mock_result = MagicMock()
        mock_result.first.return_value = MagicMock()  # Document found
        mock_db.execute = AsyncMock(return_value=mock_result)

        service = RetrievalService(mock_db, mock_embedding)

        has_access = await service.check_document_access(
            merchant_id=1,
            document_id=42,
        )

        assert has_access is True

    @pytest.mark.asyncio
    async def test_check_access_false(self):
        """Test document access check returns False when merchant doesn't own document."""
        mock_db = MagicMock(spec=AsyncSession)
        mock_embedding = MagicMock(spec=EmbeddingService)

        mock_result = MagicMock()
        mock_result.first.return_value = None  # Document not found
        mock_db.execute = AsyncMock(return_value=mock_result)

        service = RetrievalService(mock_db, mock_embedding)

        has_access = await service.check_document_access(
            merchant_id=1,
            document_id=999,  # Non-existent or different merchant's doc
        )

        assert has_access is False


class TestRetrievedChunk:
    """Tests for RetrievedChunk dataclass."""

    def test_retrieved_chunk_creation(self):
        """Test RetrievedChunk dataclass instantiation."""
        chunk = RetrievedChunk(
            chunk_id=1,
            content="Test content",
            chunk_index=0,
            document_name="test.pdf",
            document_id=42,
            similarity=0.85,
        )

        assert chunk.chunk_id == 1
        assert chunk.content == "Test content"
        assert chunk.chunk_index == 0
        assert chunk.document_name == "test.pdf"
        assert chunk.document_id == 42
        assert chunk.similarity == 0.85
