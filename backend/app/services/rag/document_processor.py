"""Document processor for RAG pipeline.

Orchestrates the document processing pipeline:
1. Load document from database
2. Update status to 'processing'
3. Extract text and chunk (use existing DocumentChunker)
4. Generate embeddings for chunks
5. Store chunks with embeddings in database
6. Update document status to 'ready'

Story 8-4: Backend - RAG Service (Document Processing)
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import List, Optional

import structlog
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import APIError, ErrorCode
from app.models.knowledge_base import DocumentChunk, DocumentStatus, KnowledgeDocument
from app.services.knowledge.chunker import ChunkingError, DocumentChunker
from app.services.rag.embedding_service import EmbeddingService

logger = structlog.get_logger(__name__)


@dataclass
class ProcessingResult:
    """Result of document processing."""

    document_id: int
    status: str  # 'ready' or 'error'
    chunk_count: int
    error_message: Optional[str] = None
    processing_time_ms: int = 0


class DocumentProcessor:
    """Service for processing documents through the RAG pipeline.

    Pipeline:
    1. Load document from database
    2. Update status to 'processing'
    3. Chunk document using DocumentChunker
    4. Generate embeddings for all chunks
    5. Store chunks with embeddings in database
    6. Update document status to 'ready'

    Error Handling:
    - Chunking failure → status='error', store error_message
    - Embedding failure → status='error', store error_message
    - Database failure → rollback transaction

    Performance Target: <30s for 1MB document
    """

    # Upload directory (must match knowledge_base API)
    UPLOAD_DIR = "uploads/knowledge-base"

    def __init__(
        self,
        db: AsyncSession,
        embedding_service: EmbeddingService,
        chunker: Optional[DocumentChunker] = None,
    ):
        """Initialize document processor.

        Args:
            db: Database session
            embedding_service: Service for generating embeddings
            chunker: Document chunker (optional, creates default if not provided)
        """
        self.db = db
        self.embedding_service = embedding_service
        self.chunker = chunker or DocumentChunker()

    async def process_document(self, document_id: int) -> ProcessingResult:
        """Process a document through the RAG pipeline.

        Args:
            document_id: ID of document to process

        Returns:
            ProcessingResult with status and metadata

        Performance:
            - Target: <30s for 1MB document
            - Logs processing time for monitoring
        """
        start_time = time.time()

        try:
            # Step 1: Load document from database
            document = await self._load_document(document_id)
            if not document:
                return ProcessingResult(
                    document_id=document_id,
                    status="error",
                    chunk_count=0,
                    error_message=f"Document {document_id} not found",
                    processing_time_ms=0,
                )

            # Step 2: Update status to 'processing'
            await self._update_status(document_id, DocumentStatus.PROCESSING.value)

            # Step 3: Chunk document
            try:
                file_path = self._get_file_path(document)
                chunks = self.chunker.chunk_document(file_path, document.file_type)
            except Exception as e:
                return await self._handle_error(
                    document_id=document_id,
                    error_message=f"Chunking failed: {str(e)}",
                    start_time=start_time,
                )

            if not chunks:
                return await self._handle_error(
                    document_id=document_id,
                    error_message="No valid chunks extracted from document",
                    start_time=start_time,
                )

            # Step 4: Generate embeddings for all chunks
            try:
                embedding_result = await self.embedding_service.embed_texts(chunks)
                embeddings = embedding_result.embeddings
            except APIError as e:
                return await self._handle_error(
                    document_id=document_id,
                    error_message=f"Embedding generation failed: {e.message}",
                    start_time=start_time,
                )
            except Exception as e:
                return await self._handle_error(
                    document_id=document_id,
                    error_message=f"Embedding generation failed: {str(e)}",
                    start_time=start_time,
                )

            # Step 5: Delete existing chunks (for reprocessing)
            await self._delete_existing_chunks(document_id)

            # Step 6: Store chunks with embeddings
            await self._store_chunks(document_id, chunks, embeddings)

            # Step 7: Update status to 'ready'
            await self._update_status(document_id, DocumentStatus.READY.value)

            # Calculate processing time
            duration_ms = int((time.time() - start_time) * 1000)

            logger.info(
                "document_processing_complete",
                document_id=document_id,
                chunk_count=len(chunks),
                processing_time_ms=duration_ms,
                embedding_dimension=embedding_result.dimension,
            )

            return ProcessingResult(
                document_id=document_id,
                status="ready",
                chunk_count=len(chunks),
                processing_time_ms=duration_ms,
            )

        except Exception as e:
            logger.error(
                "document_processing_failed",
                document_id=document_id,
                error=str(e),
            )
            return await self._handle_error(
                document_id=document_id,
                error_message=f"Unexpected error: {str(e)}",
                start_time=start_time,
            )

    async def _load_document(self, document_id: int) -> Optional[KnowledgeDocument]:
        """Load document from database."""
        result = await self.db.execute(
            select(KnowledgeDocument).where(KnowledgeDocument.id == document_id)
        )
        return result.scalar_one_or_none()

    async def _update_status(self, document_id: int, status: str) -> None:
        """Update document status."""
        await self.db.execute(
            update(KnowledgeDocument)
            .where(KnowledgeDocument.id == document_id)
            .values(status=status)
        )
        await self.db.commit()

    async def _delete_existing_chunks(self, document_id: int) -> None:
        """Delete existing chunks for a document (for reprocessing)."""
        await self.db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document_id))
        await self.db.commit()

    async def _store_chunks(
        self,
        document_id: int,
        chunks: List[str],
        embeddings: List[List[float]],
    ) -> None:
        """Store chunks with embeddings in database."""
        for index, (content, embedding) in enumerate(zip(chunks, embeddings)):
            # Format embedding for pgvector storage
            embedding_str = self._format_embedding_for_storage(embedding)

            chunk = DocumentChunk(
                document_id=document_id,
                chunk_index=index,
                content=content,
                embedding=embedding_str,
            )
            self.db.add(chunk)

        await self.db.commit()

    def _format_embedding_for_storage(self, embedding: List[float]) -> str:
        """Format embedding for pgvector storage.

        Converts Python list to PostgreSQL array literal format.
        Example: [0.1, -0.2, 0.5] -> "[0.1,-0.2,0.5]"
        """
        return f"[{','.join(map(str, embedding))}]"

    def _get_file_path(self, document: KnowledgeDocument) -> str:
        """Get file path for document.

        Files are stored in: uploads/knowledge-base/{merchant_id}/{uuid}_{filename}
        """
        import os

        merchant_dir = os.path.join(self.UPLOAD_DIR, str(document.merchant_id))

        # Find the actual file (has UUID prefix)
        for filename in os.listdir(merchant_dir):
            if filename.endswith(f"_{document.filename}"):
                return os.path.join(merchant_dir, filename)

        # Fallback: try without UUID prefix
        return os.path.join(merchant_dir, document.filename)

    async def _handle_error(
        self,
        document_id: int,
        error_message: str,
        start_time: float,
    ) -> ProcessingResult:
        """Handle processing error by updating status and logging."""
        duration_ms = int((time.time() - start_time) * 1000)

        # Update document status to error
        try:
            await self.db.execute(
                update(KnowledgeDocument)
                .where(KnowledgeDocument.id == document_id)
                .values(status=DocumentStatus.ERROR.value, error_message=error_message)
            )
            await self.db.commit()
        except Exception as e:
            logger.error(
                "failed_to_update_error_status",
                document_id=document_id,
                error=str(e),
            )

        logger.error(
            "document_processing_error",
            document_id=document_id,
            error_message=error_message,
            processing_time_ms=duration_ms,
        )

        return ProcessingResult(
            document_id=document_id,
            status="error",
            chunk_count=0,
            error_message=error_message,
            processing_time_ms=duration_ms,
        )
