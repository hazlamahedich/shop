"""Tests for Document Processor.

Story 8-4: Backend - RAG Service (Document Processing)

Test Coverage:
- AC1: Processing pipeline (chunk → embed → store)
- AC4: Error handling (chunking failure, embedding failure)
- Performance tracking
- Document status updates
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import APIError, ErrorCode
from app.models.knowledge_base import DocumentStatus, KnowledgeDocument
from app.services.knowledge.chunker import ChunkingError, DocumentChunker
from app.services.rag.document_processor import DocumentProcessor, ProcessingResult
from app.services.rag.embedding_service import EmbeddingResult, EmbeddingService


class TestDocumentProcessorInit:
    """Tests for DocumentProcessor initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default chunker."""
        mock_db = MagicMock(spec=AsyncSession)
        mock_embedding = MagicMock(spec=EmbeddingService)

        processor = DocumentProcessor(mock_db, mock_embedding)

        assert processor.db == mock_db
        assert processor.embedding_service == mock_embedding
        assert processor.chunker is not None
        assert isinstance(processor.chunker, DocumentChunker)

    def test_init_with_custom_chunker(self):
        """Test initialization with custom chunker."""
        mock_db = MagicMock(spec=AsyncSession)
        mock_embedding = MagicMock(spec=EmbeddingService)
        mock_chunker = MagicMock(spec=DocumentChunker)

        processor = DocumentProcessor(mock_db, mock_embedding, chunker=mock_chunker)

        assert processor.chunker == mock_chunker


class TestProcessDocument:
    """Tests for process_document method."""

    @pytest.mark.asyncio
    async def test_process_document_success(self):
        """AC1: Test successful document processing pipeline."""
        mock_db = MagicMock(spec=AsyncSession)
        mock_embedding = MagicMock(spec=EmbeddingService)
        mock_chunker = MagicMock(spec=DocumentChunker)

        # Mock document load
        mock_document = KnowledgeDocument(
            id=1,
            merchant_id=1,
            filename="test.pdf",
            file_type="pdf",
            file_size=1000,
            status=DocumentStatus.PENDING.value,
        )

        async def mock_execute(query):
            result = MagicMock()
            result.scalar_one_or_none.return_value = mock_document
            return result

        mock_db.execute = mock_execute
        mock_db.commit = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.refresh = AsyncMock()

        # Mock chunker
        mock_chunker.chunk_document.return_value = [
            "Chunk 1 content",
            "Chunk 2 content",
            "Chunk 3 content",
        ]

        # Mock embedding service
        mock_embedding.embed_texts = AsyncMock(
            return_value=EmbeddingResult(
                embeddings=[[0.1] * 1536, [0.2] * 1536, [0.3] * 1536],
                model="text-embedding-3-small",
                provider="openai",
                dimension=1536,
                token_count=100,
            )
        )

        # Mock file path resolution
        with patch.object(
            DocumentProcessor,
            "_get_file_path",
            return_value="/path/to/test.pdf",
        ):
            processor = DocumentProcessor(mock_db, mock_embedding, mock_chunker)
            result = await processor.process_document(1)

        assert result.status == "ready"
        assert result.chunk_count == 3
        assert result.error_message is None
        assert result.processing_time_ms > 0

    @pytest.mark.asyncio
    async def test_process_document_chunking_failure(self):
        """AC4: Test chunking failure updates status to error."""
        mock_db = MagicMock(spec=AsyncSession)
        mock_embedding = MagicMock(spec=EmbeddingService)
        mock_chunker = MagicMock(spec=DocumentChunker)

        # Mock document load
        mock_document = KnowledgeDocument(
            id=1,
            merchant_id=1,
            filename="corrupted.pdf",
            file_type="pdf",
            file_size=1000,
            status=DocumentStatus.PENDING.value,
        )

        async def mock_execute(query):
            result = MagicMock()
            result.scalar_one_or_none.return_value = mock_document
            return result

        mock_db.execute = mock_execute
        mock_db.commit = AsyncMock()

        # Mock chunker to raise error
        mock_chunker.chunk_document.side_effect = ChunkingError("Failed to extract text from PDF")

        with patch.object(
            DocumentProcessor,
            "_get_file_path",
            return_value="/path/to/corrupted.pdf",
        ):
            processor = DocumentProcessor(mock_db, mock_embedding, mock_chunker)
            result = await processor.process_document(1)

        assert result.status == "error"
        assert "Chunking failed" in result.error_message
        assert result.chunk_count == 0

    @pytest.mark.asyncio
    async def test_process_document_embedding_failure(self):
        """AC4: Test embedding failure updates status to error."""
        mock_db = MagicMock(spec=AsyncSession)
        mock_embedding = MagicMock(spec=EmbeddingService)
        mock_chunker = MagicMock(spec=DocumentChunker)

        # Mock document load
        mock_document = KnowledgeDocument(
            id=1,
            merchant_id=1,
            filename="test.pdf",
            file_type="pdf",
            file_size=1000,
            status=DocumentStatus.PENDING.value,
        )

        async def mock_execute(query):
            result = MagicMock()
            result.scalar_one_or_none.return_value = mock_document
            return result

        mock_db.execute = mock_execute
        mock_db.commit = AsyncMock()

        # Mock chunker
        mock_chunker.chunk_document.return_value = ["Chunk 1", "Chunk 2"]

        # Mock embedding failure
        mock_embedding.embed_texts = AsyncMock(
            side_effect=APIError(
                ErrorCode.EMBEDDING_GENERATION_FAILED,
                "Embedding API error",
            )
        )

        with patch.object(
            DocumentProcessor,
            "_get_file_path",
            return_value="/path/to/test.pdf",
        ):
            processor = DocumentProcessor(mock_db, mock_embedding, mock_chunker)
            result = await processor.process_document(1)

        assert result.status == "error"
        assert "Embedding generation failed" in result.error_message
        assert result.chunk_count == 0

    @pytest.mark.asyncio
    async def test_process_document_not_found(self):
        """Test processing non-existent document returns error."""
        mock_db = MagicMock(spec=AsyncSession)
        mock_embedding = MagicMock(spec=EmbeddingService)

        async def mock_execute(query):
            result = MagicMock()
            result.scalar_one_or_none.return_value = None
            return result

        mock_db.execute = mock_execute

        processor = DocumentProcessor(mock_db, mock_embedding)
        result = await processor.process_document(999)

        assert result.status == "error"
        assert "not found" in result.error_message
        assert result.chunk_count == 0

    @pytest.mark.asyncio
    async def test_process_document_empty_chunks(self):
        """Test document with no extractable text."""
        mock_db = MagicMock(spec=AsyncSession)
        mock_embedding = MagicMock(spec=EmbeddingService)
        mock_chunker = MagicMock(spec=DocumentChunker)

        # Mock document load
        mock_document = KnowledgeDocument(
            id=1,
            merchant_id=1,
            filename="empty.pdf",
            file_type="pdf",
            file_size=100,
            status=DocumentStatus.PENDING.value,
        )

        async def mock_execute(query):
            result = MagicMock()
            result.scalar_one_or_none.return_value = mock_document
            return result

        mock_db.execute = mock_execute
        mock_db.commit = AsyncMock()

        # Mock chunker returns empty list
        mock_chunker.chunk_document.return_value = []

        with patch.object(
            DocumentProcessor,
            "_get_file_path",
            return_value="/path/to/empty.pdf",
        ):
            processor = DocumentProcessor(mock_db, mock_embedding, mock_chunker)
            result = await processor.process_document(1)

        assert result.status == "error"
        assert "No valid chunks" in result.error_message

    @pytest.mark.asyncio
    async def test_process_document_reprocessing(self):
        """Test reprocessing document deletes existing chunks."""
        mock_db = MagicMock(spec=AsyncSession)
        mock_embedding = MagicMock(spec=EmbeddingService)
        mock_chunker = MagicMock(spec=DocumentChunker)

        # Mock document load
        mock_document = KnowledgeDocument(
            id=1,
            merchant_id=1,
            filename="test.pdf",
            file_type="pdf",
            file_size=1000,
            status=DocumentStatus.ERROR.value,  # Previously failed
            error_message="Previous error",
        )

        execute_calls = []

        async def mock_execute(query):
            execute_calls.append(query)
            result = MagicMock()
            result.scalar_one_or_none.return_value = mock_document
            return result

        mock_db.execute = mock_execute
        mock_db.commit = AsyncMock()
        mock_db.add = MagicMock()

        # Mock chunker
        mock_chunker.chunk_document.return_value = ["New chunk"]

        # Mock embedding
        mock_embedding.embed_texts = AsyncMock(
            return_value=EmbeddingResult(
                embeddings=[[0.1] * 1536],
                model="text-embedding-3-small",
                provider="openai",
                dimension=1536,
                token_count=50,
            )
        )

        with patch.object(
            DocumentProcessor,
            "_get_file_path",
            return_value="/path/to/test.pdf",
        ):
            processor = DocumentProcessor(mock_db, mock_embedding, mock_chunker)
            result = await processor.process_document(1)

        assert result.status == "ready"
        assert result.chunk_count == 1
        # Verify chunks were deleted before adding new ones


class TestFormatEmbedding:
    """Tests for _format_embedding_for_storage method."""

    def test_format_embedding(self):
        """Test embedding formatting for pgvector storage."""
        mock_db = MagicMock(spec=AsyncSession)
        mock_embedding = MagicMock(spec=EmbeddingService)

        processor = DocumentProcessor(mock_db, mock_embedding)

        embedding = [0.1, -0.2, 0.5]
        result = processor._format_embedding_for_storage(embedding)

        assert result == "[0.1,-0.2,0.5]"

    def test_format_embedding_large(self):
        """Test formatting large embedding vector."""
        mock_db = MagicMock(spec=AsyncSession)
        mock_embedding = MagicMock(spec=EmbeddingService)

        processor = DocumentProcessor(mock_db, mock_embedding)

        embedding = [0.1] * 1536
        result = processor._format_embedding_for_storage(embedding)

        assert result.startswith("[0.1")
        assert result.endswith("0.1]")


class TestProcessingResult:
    """Tests for ProcessingResult dataclass."""

    def test_processing_result_success(self):
        """Test ProcessingResult for successful processing."""
        result = ProcessingResult(
            document_id=1,
            status="ready",
            chunk_count=10,
            processing_time_ms=500,
        )

        assert result.document_id == 1
        assert result.status == "ready"
        assert result.chunk_count == 10
        assert result.error_message is None
        assert result.processing_time_ms == 500

    def test_processing_result_error(self):
        """Test ProcessingResult for failed processing."""
        result = ProcessingResult(
            document_id=1,
            status="error",
            chunk_count=0,
            error_message="Chunking failed",
            processing_time_ms=100,
        )

        assert result.status == "error"
        assert result.chunk_count == 0
        assert result.error_message == "Chunking failed"
