"""Retrieval service for RAG document search.

Implements vector similarity search using pgvector's cosine distance operator.
Returns top-k most relevant chunks with similarity scores.

Story 8-4: Backend - RAG Service (Document Processing)
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import numpy as np
import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import APIError, ErrorCode
from app.models.rag_query_log import RAGQueryLog
from app.services.rag.embedding_service import EmbeddingService

logger = structlog.get_logger(__name__)

EMBEDDING_TIMEOUT = 5.0
SEARCH_TIMEOUT = 0.5

# Session factory type for creating fresh database sessions
SessionFactory = Callable[[], Any]  # Returns AsyncSession or context manager


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

    SIMILARITY_THRESHOLD = 0.3  # Minimum similarity score (lowered for better recall, fixes location queries)
    TOP_K_DEFAULT = 7  # Default number of chunks to retrieve (increased from 5 for better context)
    RETRIEVAL_TIMEOUT_MS = 500  # Timeout for retrieval

    def __init__(
        self,
        session_factory: SessionFactory,
        embedding_service: EmbeddingService,
        similarity_threshold: float = SIMILARITY_THRESHOLD,
        top_k: int = TOP_K_DEFAULT,
    ):
        """Initialize retrieval service.

        Args:
            session_factory: Factory function that creates fresh database sessions
            embedding_service: Service for generating query embeddings
            similarity_threshold: Minimum similarity score (0.0-1.0)
            top_k: Number of chunks to retrieve
        """
        self.session_factory = session_factory
        self.embedding_service = embedding_service
        self.similarity_threshold = similarity_threshold
        self.top_k = top_k

    async def retrieve_relevant_chunks(
        self,
        merchant_id: int,
        query: str,
        top_k: int | None = None,
        threshold: float | None = None,
        embedding_version: str | None = None,
    ) -> list[RetrievedChunk]:
        """Retrieve most relevant chunks for a query.

        Args:
            merchant_id: Merchant ID for multi-tenant isolation
            query: User's question or search query
            top_k: Override default number of chunks to retrieve
            threshold: Override default similarity threshold
            embedding_version: Filter by embedding version (e.g., "openai-text-embedding-3-small")
                              Prevents mixing embeddings from different dimensions (AC6)

        Returns:
            List of RetrievedChunk sorted by similarity (descending)
            Empty list if no relevant chunks found or timeout occurs

        Performance:
            - Target: <500ms end-to-end
            - Uses asyncio.wait_for() for timeout handling

        Story 8-11 AC6: Vector Consistency - only search embeddings from active model
        """
        top_k = top_k or self.top_k
        threshold = threshold or self.similarity_threshold

        try:
            # Generate query embedding with timeout
            # Note: Cloud providers like Gemini can take >1s for embedding
            try:
                query_embedding = await asyncio.wait_for(
                    self.embedding_service.embed_query(query),
                    timeout=5.0,  # 5s for embedding (cloud providers can be slow)
                )
            except TimeoutError:
                logger.warning(
                    "retrieval_embedding_timeout",
                    merchant_id=merchant_id,
                    query_length=len(query),
                )
                return []  # Graceful degradation

            # Format embedding for pgvector
            embedding_str = self._format_embedding(query_embedding)

            # Create fresh database session for this retrieval
            # This prevents greenlet errors from session reuse
            session_result = self.session_factory()

            # Handle both AsyncSession and context manager
            if hasattr(session_result, '__aenter__'):
                # It's a context manager
                async with session_result as db:
                    return await self._execute_search_and_log(
                        db=db,
                        merchant_id=merchant_id,
                        embedding_str=embedding_str,
                        threshold=threshold,
                        top_k=top_k,
                        embedding_version=embedding_version,
                        query=query,
                    )
            else:
                # It's a raw AsyncSession
                db = session_result
                return await self._execute_search_and_log(
                    db=db,
                    merchant_id=merchant_id,
                    embedding_str=embedding_str,
                    threshold=threshold,
                    top_k=top_k,
                    embedding_version=embedding_version,
                    query=query,
                )

        except APIError:
            raise
        except Exception as e:
            logger.error(
                "retrieval_failed",
                merchant_id=merchant_id,
                error=str(e),
            )
            return []  # Graceful degradation on errors

    async def _execute_search_and_log(
        self,
        db: AsyncSession,
        merchant_id: int,
        embedding_str: str,
        threshold: float,
        top_k: int,
        embedding_version: str | None,
        query: str,
    ) -> list[RetrievedChunk]:
        """Execute similarity search and log results."""
        # Perform vector similarity search with timeout
        try:
            results = await asyncio.wait_for(
                self._execute_similarity_search(
                    db=db,
                    merchant_id=merchant_id,
                    embedding_str=embedding_str,
                    threshold=threshold,
                    top_k=top_k,
                    embedding_version=embedding_version,
                ),
                timeout=2.0,  # 2s for search (Python-based similarity computation)
            )
        except TimeoutError:
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

        await self._log_query(
            db=db,
            merchant_id=merchant_id,
            query=query,
            results=results,
        )

        return results

    async def _execute_similarity_search(
        self,
        db: AsyncSession,
        merchant_id: int,
        embedding_str: str,
        threshold: float,
        top_k: int,
        embedding_version: str | None = None,
    ) -> list[RetrievedChunk]:
        """Execute pgvector similarity search query.

        Uses raw asyncpg connection with pgvector for proper vector operations.

        Handles double-encoded JSONB embeddings (stored as JSON strings).

        Filters by:
        - merchant_id (multi-tenant isolation)
        - document status = 'ready' (only processed documents)
        - embedding_version (prevents dimension mixing - Story 8-11 AC6)
        - similarity >= threshold
        """
        # Get candidate chunks using SQLAlchemy (no raw asyncpg needed)
        # Since embeddings are stored as JSON strings in JSONB, we can't cast directly in SQL
        # We'll fetch them as text and parse in Python

        base_query = """
            SELECT
                dc.id AS chunk_id,
                dc.content,
                dc.chunk_index,
                kd.filename AS document_name,
                kd.id AS document_id,
                dc.embedding::text AS embedding_json,
                dc.embedding_dimension
            FROM document_chunks dc
            JOIN knowledge_documents kd ON dc.document_id = kd.id
            WHERE kd.merchant_id = :merchant_id
              AND kd.status = 'ready'
              AND dc.embedding IS NOT NULL
              AND dc.embedding_dimension IS NOT NULL
        """

        params = {"merchant_id": merchant_id}

        if embedding_version:
            base_query += "\n              AND kd.embedding_version = :embedding_version"
            params["embedding_version"] = embedding_version

        # Execute query using SQLAlchemy
        logger.debug(
            "retrieval_executing_query", merchant_id=merchant_id, query=base_query, params=params
        )
        result = await db.execute(text(base_query), params)
        rows = result.fetchall()

        logger.debug("retrieval_query_executed", merchant_id=merchant_id, row_count=len(rows))

        logger.debug("retrieval_query_executed", merchant_id=merchant_id, row_count=len(rows))

        # Parse query embedding to numpy array
        query_embedding_np = np.array(json.loads(embedding_str), dtype=np.float32)

        # Compute similarities in Python
        chunks_with_similarity = []
        logger.debug("retrieval_rows_fetched", merchant_id=merchant_id, row_count=len(rows))

        for row_idx in range(len(rows)):
            row = rows[row_idx]
            try:
                # Parse double-encoded embedding: JSONB contains a JSON string
                embedding_json = row.embedding_json
                logger.debug(
                    "retrieval_parsing_embedding",
                    chunk_id=row.chunk_id,
                    embedding_json_length=len(embedding_json) if embedding_json else 0,
                )
                # First parse extracts the string from JSONB
                inner_string = json.loads(embedding_json)
                logger.debug(
                    "retrieval_inner_string_parsed",
                    chunk_id=row.chunk_id,
                    inner_string_length=len(inner_string),
                )
                # Second parse extracts the array from the string
                embedding_list = json.loads(inner_string)

                # Convert to numpy array
                stored_embedding = np.array(embedding_list, dtype=np.float32)

                # Compute cosine similarity using pgvector's distance
                # Cosine distance = 1 - cosine_similarity
                # We'll compute cosine similarity directly
                dot_product = np.dot(query_embedding_np, stored_embedding)
                norm_query = np.linalg.norm(query_embedding_np)
                norm_stored = np.linalg.norm(stored_embedding)

                if norm_query > 0 and norm_stored > 0:
                    cosine_similarity = dot_product / (norm_query * norm_stored)
                else:
                    cosine_similarity = 0.0

                logger.debug(
                    "retrieval_similarity_computed",
                    chunk_id=row.chunk_id,
                    similarity=cosine_similarity,
                    threshold=threshold,
                )

                if cosine_similarity >= threshold:
                    chunks_with_similarity.append(
                        {
                            "chunk_id": row.chunk_id,
                            "content": row.content,
                            "chunk_index": row.chunk_index,
                            "document_name": row.document_name,
                            "document_id": row.document_id,
                            "similarity": cosine_similarity,
                        }
                    )
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                logger.warning("embedding_parse_error", chunk_id=row.chunk_id, error=str(e))
                continue

        # Sort by similarity (descending) and take top_k
        chunks_with_similarity.sort(key=lambda x: x["similarity"], reverse=True)
        chunks_with_similarity = chunks_with_similarity[:top_k]

        # Convert to RetrievedChunk objects
        chunks = []
        for item in chunks_with_similarity:
            chunks.append(
                RetrievedChunk(
                    chunk_id=item["chunk_id"],
                    content=item["content"],
                    chunk_index=item["chunk_index"],
                    document_name=item["document_name"],
                    document_id=item["document_id"],
                    similarity=item["similarity"],
                )
            )

        return chunks

    def _format_embedding(self, embedding: list[float]) -> str:
        """Format embedding list for pgvector query.

        Converts Python list to PostgreSQL array literal format.
        Example: [0.1, -0.2, 0.5] -> "[0.1,-0.2,0.5]"
        """
        return f"[{','.join(map(str, embedding))}]"

    async def check_document_access(
        self,
        merchant_id: int,
        document_id: int,
        db: AsyncSession | None = None,
    ) -> bool:
        """Check if merchant has access to a document.

        Args:
            merchant_id: Merchant ID
            document_id: Document ID to check
            db: Optional database session (creates one if not provided)

        Returns:
            True if merchant owns the document
        """
        if db is None:
            session_result = self.session_factory()
            if hasattr(session_result, '__aenter__'):
                async with session_result as db:
                    return await self._check_document_access_impl(
                        db=db,
                        merchant_id=merchant_id,
                        document_id=document_id,
                    )
            else:
                db = session_result
                return await self._check_document_access_impl(
                    db=db,
                    merchant_id=merchant_id,
                    document_id=document_id,
                )
        else:
            return await self._check_document_access_impl(
                db=db,
                merchant_id=merchant_id,
                document_id=document_id,
            )

    async def _check_document_access_impl(
        self,
        db: AsyncSession,
        merchant_id: int,
        document_id: int,
    ) -> bool:
        """Implementation of document access check."""
        query = text(
            """
            SELECT 1 FROM knowledge_documents
            WHERE id = :document_id AND merchant_id = :merchant_id
            """
        )

        result = await db.execute(
            query,
            {"document_id": document_id, "merchant_id": merchant_id},
        )

        return result.first() is not None

    async def _log_query(
        self,
        db: AsyncSession,
        merchant_id: int,
        query: str,
        results: list[RetrievedChunk],
    ) -> None:
        """Log RAG query for analytics.

        Args:
            merchant_id: Merchant ID
            query: User's query text
            results: Retrieved chunks (empty if no match)
        """
        try:
            matched = len(results) > 0
            confidence = results[0].similarity if matched else None
            sources = (
                [
                    {
                        "document_id": r.document_id,
                        "document_name": r.document_name,
                        "chunk_id": r.chunk_id,
                        "similarity": r.similarity,
                    }
                    for r in results[:3]
                ]
                if matched
                else None
            )

            log_entry = RAGQueryLog(
                merchant_id=merchant_id,
                query=query[:1000],
                matched=matched,
                confidence=confidence,
                sources=sources,
            )
            db.add(log_entry)
            await db.commit()

            logger.debug(
                "rag_query_logged",
                merchant_id=merchant_id,
                matched=matched,
                confidence=confidence,
            )
        except Exception as e:
            logger.warning(
                "rag_query_log_failed",
                merchant_id=merchant_id,
                error=str(e),
            )
            await db.rollback()
