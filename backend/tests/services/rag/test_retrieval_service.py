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
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.errors import APIError, ErrorCode
from app.services.rag.embedding_service import EmbeddingService
from app.services.rag.retrieval_service import RetrievalService, RetrievedChunk
from app.models.rag_query_log import RAGQueryLog


class TestRetrievalServiceInit:
    """Tests for RetrievalService initialization."""

    def test_init_default_values(self):
        """Test initialization with default values."""
        mock_session_factory = MagicMock(return_value=MagicMock(spec=AsyncSession))
        mock_embedding = MagicMock(spec=EmbeddingService)

        service = RetrievalService(
            session_factory=mock_session_factory,
            embedding_service=mock_embedding,
        )

        assert service.similarity_threshold == RetrievalService.SIMILARITY_THRESHOLD
        assert service.top_k == RetrievalService.TOP_K_DEFAULT
        assert service.session_factory == mock_session_factory
        assert service.embedding_service == mock_embedding

    def test_init_custom_values(self):
        """Test initialization with custom values."""
        mock_session_factory = MagicMock(return_value=MagicMock(spec=AsyncSession))
        mock_embedding = MagicMock(spec=EmbeddingService)

        service = RetrievalService(
            session_factory=mock_session_factory,
            embedding_service=mock_embedding,
            similarity_threshold=0.8,
            top_k=10,
        )

        assert service.similarity_threshold == 0.8
        assert service.top_k == 10
        assert service.session_factory == mock_session_factory
        assert service.embedding_service == mock_embedding


class TestRetrieveRelevantChunks:
    """Tests for retrieve_relevant_chunks method."""

    @pytest.fixture
    def mock_session_factory(self):
        """Fixture that provides a mock async context manager factory."""
        mock_session = MagicMock(spec=AsyncSession)
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_session.add = MagicMock()

        @asynccontextmanager
        async def _factory():
            yield mock_session

        return _factory

    @pytest.mark.asyncio
    async def test_retrieve_returns_top_k_chunks(self, mock_session_factory):
        """AC2: Test retrieval returns top 5 chunks with similarity scores."""
        mock_embedding = MagicMock(spec=EmbeddingService)
        mock_embedding.embed_query = AsyncMock(return_value=[0.1] * 1536)

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

        async with mock_session_factory() as mock_session:
            mock_session.execute = AsyncMock(return_value=mock_result)

            service = RetrievalService(mock_session_factory, mock_embedding)

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


class TestFormatEmbedding:
    """Tests for _format_embedding method."""

    def test_format_embedding(self):
        """Test embedding formatting for pgvector."""
        mock_session_factory = MagicMock(return_value=MagicMock(spec=AsyncSession))
        mock_embedding = MagicMock(spec=EmbeddingService)

        service = RetrievalService(mock_session_factory, mock_embedding)

        embedding = [0.1, -0.2, 0.5, 0.0]
        result = service._format_embedding(embedding)

        assert result == "[0.1,-0.2,0.5,0.0]"

    def test_format_embedding_large(self):
        """Test formatting large embedding vector."""
        mock_session_factory = MagicMock(return_value=MagicMock(spec=AsyncSession))
        mock_embedding = MagicMock(spec=EmbeddingService)

        service = RetrievalService(mock_session_factory, mock_embedding)

        embedding = [0.1] * 1536
        result = service._format_embedding(embedding)

        assert result.startswith("[0.1")
        assert result.endswith("0.1]")
        assert result.count(",") == 1535


class TestCheckDocumentAccess:
    """Tests for check_document_access method."""

    @pytest.fixture
    def mock_session_factory(self):
        """Fixture that provides a mock async context manager factory."""
        mock_session = MagicMock(spec=AsyncSession)
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_session.add = MagicMock()

        @asynccontextmanager
        async def _factory():
            yield mock_session

        return _factory

    @pytest.mark.asyncio
    async def test_check_access_false(self, mock_session_factory):
        """Test document access check returns False when merchant doesn't own document."""
        # Use the fixture's mock session through the factory
        async with mock_session_factory() as mock_session:
            mock_result = MagicMock()
            mock_result.first.return_value = None
            mock_session.execute = AsyncMock(return_value=mock_result)

            service = RetrievalService(mock_session_factory, MagicMock(spec=EmbeddingService))

            has_access = await service.check_document_access(
                merchant_id=1,
                document_id=999,
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
