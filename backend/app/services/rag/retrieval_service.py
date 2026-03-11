"""Retrieval service for RAG document search.

Implements vector similarity search using pgvector's cosine distance operator.
Returns top-k most relevant chunks with similarity scores.

Story 8-4: Backend - RAG Service (Document Processing)
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import List, Optional

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import APIError, ErrorCode
from app.services.rag.embedding_service import EmbeddingService

logger = structlog.get_logger(__name__)


@dataclass
class RetrievedChunk:
    """A retrieved document chunk with similarity score."""

    chunk_id: int
    content: str
    chunk_index: int
    document_name: str
    document_id: int
    similarity: float


class RetrievalService:
    """Service for retrieving relevant document chunks using vector similarity.

    Features:
    - Vector similarity search using pgvector's cosine distance
    - Configurable similarity threshold (default 0.7)
    - Multi-tenant isolation (merchant_id filtering)
    - Timeout handling with graceful degradation
    - Only searches documents with status='ready'

    Performance Target: <500ms end-to-end (embed + search)
    """

    SIMILARITY_THRESHOLD = 0.7  # Minimum similarity score
    TOP_K_DEFAULT = 5  # Default number of chunks to retrieve
    RETRIEVAL_TIMEOUT_MS = 500  # Timeout for retrieval

    def __init__(
        self,
        db: AsyncSession,
        embedding_service: EmbeddingService,
        similarity_threshold: float = SIMILARITY_THRESHOLD,
        top_k: int = TOP_K_DEFAULT,
    ):
        """Initialize retrieval service.

        Args:
            db: Database session
            embedding_service: Service for generating query embeddings
            similarity_threshold: Minimum similarity score (0.0-1.0)
            top_k: Number of chunks to retrieve
        """
        self.db = db
        self.embedding_service = embedding_service
        self.similarity_threshold = similarity_threshold
        self.top_k = top_k

    async def retrieve_relevant_chunks(
        self,
        merchant_id: int,
        query: str,
        top_k: Optional[int] = None,
        threshold: Optional[float] = None,
    ) -> List[RetrievedChunk]:
        """Retrieve most relevant chunks for a query.

        Args:
            merchant_id: Merchant ID for multi-tenant isolation
            query: User's question or search query
            top_k: Override default number of chunks to retrieve
            threshold: Override default similarity threshold

        Returns:
            List of RetrievedChunk sorted by similarity (descending)
            Empty list if no relevant chunks found or timeout occurs

        Performance:
            - Target: <500ms end-to-end
            - Uses asyncio.wait_for() for timeout handling
        """
        top_k = top_k or self.top_k
        threshold = threshold or self.similarity_threshold

        try:
            # Generate query embedding with timeout
            try:
                query_embedding = await asyncio.wait_for(
                    self.embedding_service.embed_query(query),
                    timeout=0.3,  # 300ms for embedding
                )
            except asyncio.TimeoutError:
                logger.warning(
                    "retrieval_embedding_timeout",
                    merchant_id=merchant_id,
                    query_length=len(query),
                )
                return []  # Graceful degradation

            # Format embedding for pgvector
            embedding_str = self._format_embedding(query_embedding)

            # Perform vector similarity search with timeout
            try:
                results = await asyncio.wait_for(
                    self._execute_similarity_search(
                        merchant_id=merchant_id,
                        embedding_str=embedding_str,
                        threshold=threshold,
                        top_k=top_k,
                    ),
                    timeout=0.2,  # 200ms for search
                )
            except asyncio.TimeoutError:
                logger.warning(
                    "retrieval_search_timeout",
                    merchant_id=merchant_id,
                    threshold=threshold,
                    top_k=top_k,
                )
                raise APIError(
                    ErrorCode.RETRIEVAL_TIMEOUT,
                    "Retrieval search timed out",
                )

            logger.info(
                "retrieval_complete",
                merchant_id=merchant_id,
                results_count=len(results),
                threshold=threshold,
                top_k=top_k,
            )

            return results

        except APIError:
            raise
        except Exception as e:
            logger.error(
                "retrieval_failed",
                merchant_id=merchant_id,
                error=str(e),
            )
            return []  # Graceful degradation on errors

    async def _execute_similarity_search(
        self,
        merchant_id: int,
        embedding_str: str,
        threshold: float,
        top_k: int,
    ) -> List[RetrievedChunk]:
        """Execute pgvector similarity search query.

        Uses cosine distance operator (<=>) and converts to similarity score.
        Filters by:
        - merchant_id (multi-tenant isolation)
        - document status = 'ready' (only processed documents)
        - similarity >= threshold
        """
        query = text(
            """
            SELECT
                dc.id AS chunk_id,
                dc.content,
                dc.chunk_index,
                kd.filename AS document_name,
                kd.id AS document_id,
                1 - (dc.embedding <=> :embedding::vector) AS similarity
            FROM document_chunks dc
            JOIN knowledge_documents kd ON dc.document_id = kd.id
            WHERE kd.merchant_id = :merchant_id
              AND kd.status = 'ready'
              AND 1 - (dc.embedding <=> :embedding::vector) >= :threshold
            ORDER BY dc.embedding <=> :embedding::vector
            LIMIT :top_k
            """
        )

        result = await self.db.execute(
            query,
            {
                "embedding": embedding_str,
                "merchant_id": merchant_id,
                "threshold": threshold,
                "top_k": top_k,
            },
        )

        rows = result.fetchall()

        chunks = []
        for row in rows:
            chunks.append(
                RetrievedChunk(
                    chunk_id=row.chunk_id,
                    content=row.content,
                    chunk_index=row.chunk_index,
                    document_name=row.document_name,
                    document_id=row.document_id,
                    similarity=float(row.similarity),
                )
            )

        return chunks

    def _format_embedding(self, embedding: List[float]) -> str:
        """Format embedding list for pgvector query.

        Converts Python list to PostgreSQL array literal format.
        Example: [0.1, -0.2, 0.5] -> "[0.1,-0.2,0.5]"
        """
        return f"[{','.join(map(str, embedding))}]"

    async def check_document_access(
        self,
        merchant_id: int,
        document_id: int,
    ) -> bool:
        """Check if merchant has access to a document.

        Args:
            merchant_id: Merchant ID
            document_id: Document ID to check

        Returns:
            True if merchant owns the document
        """
        query = text(
            """
            SELECT 1 FROM knowledge_documents
            WHERE id = :document_id AND merchant_id = :merchant_id
            """
        )

        result = await self.db.execute(
            query,
            {"document_id": document_id, "merchant_id": merchant_id},
        )

        return result.first() is not None
