"""RAG context builder for formatting retrieved chunks into LLM context.

Formats retrieved document chunks into context string with source citations
for injection into LLM system prompts.

Story 8-5: Backend - RAG Integration in Conversation
Story 10-1: Query rewriting for follow-up questions
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

import structlog

from app.services.rag.query_rewriter import QueryRewriter
from app.services.rag.retrieval_service import RetrievalService, RetrievedChunk, SessionFactory

if TYPE_CHECKING:
    from app.services.llm.base_llm_service import BaseLLMService

logger = structlog.get_logger(__name__)


class RAGContextBuilder:
    """Build LLM context from retrieved document chunks.

    Formats retrieved chunks into context string with source citations
    for injection into LLM system prompts.

    Features:
    - 500ms timeout for retrieval (graceful degradation)
    - Token limit enforcement (~2000 tokens max)
    - Grouping by document name
    - Sentence-boundary truncation
    - Citation formatting
    """

    RETRIEVAL_TIMEOUT_MS = 10000  # 10s timeout for retrieval (cloud embeddings can be slow)
    MAX_CONTEXT_TOKENS = 2000  # Prevent prompt overflow
    REWRITE_TIMEOUT_MS = 2000  # 2s timeout for query rewriting
    TOP_K_DEFAULT = 7  # Default chunks to retrieve (increased from 5)
    SIMILARITY_THRESHOLD_DEFAULT = 0.2  # Lowered from 0.3 for better recall

    def __init__(
        self,
        session_factory: SessionFactory,
        embedding_service,
        llm_service: BaseLLMService | None = None,
    ):
        """Initialize RAG context builder.

        Args:
            session_factory: Factory function that creates fresh database sessions
            embedding_service: Service for generating query embeddings
            llm_service: Optional LLM service for query rewriting (Story 10-1)
        """
        self.retrieval_service = RetrievalService(
            session_factory=session_factory,
            embedding_service=embedding_service,
        )
        self.query_rewriter = QueryRewriter(llm_service) if llm_service else None

    async def build_rag_context(
        self,
        merchant_id: int,
        user_query: str,
        top_k: int = 7,  # Increased from 5 for better context coverage
        similarity_threshold: float = 0.2,  # Lowered for better recall
        embedding_version: str | None = None,
    ) -> str | None:
        """Retrieve relevant chunks and format as LLM context.

        Args:
            merchant_id: Merchant ID for multi-tenant isolation
            user_query: User's question or search query
            top_k: Number of chunks to retrieve (default 5)
            similarity_threshold: Minimum similarity score (default 0.7)
            embedding_version: Filter by embedding version (e.g., "openai-text-embedding-3-small")
                              Prevents dimension mixing when provider changes (Story 8-11 AC6)

        Returns:
            Formatted context string with citations, or None if:
            - Retrieval times out (>500ms)
            - No relevant chunks found
            - Error occurs during retrieval

        Performance:
            Target: <500ms end-to-end
            Uses asyncio.wait_for() for timeout handling
        """
        try:
            # Retrieve chunks with timeout
            chunks = await asyncio.wait_for(
                self.retrieval_service.retrieve_relevant_chunks(
                    merchant_id=merchant_id,
                    query=user_query,
                    top_k=top_k,
                    threshold=similarity_threshold,
                    embedding_version=embedding_version,
                ),
                timeout=self.RETRIEVAL_TIMEOUT_MS / 1000.0,
            )

            if not chunks:
                logger.info(
                    "rag_no_chunks_found",
                    merchant_id=merchant_id,
                    query_length=len(user_query),
                )
                return None

            # Format chunks as context
            context = self._format_chunks_as_context(chunks)

            # Enforce token limit
            if self._estimate_tokens(context) > self.MAX_CONTEXT_TOKENS:
                context = self._truncate_context(context, self.MAX_CONTEXT_TOKENS)
                logger.info(
                    "rag_context_truncated",
                    merchant_id=merchant_id,
                    max_tokens=self.MAX_CONTEXT_TOKENS,
                )

            # Log success metrics
            avg_similarity = sum(c.similarity for c in chunks) / len(chunks)
            logger.info(
                "rag_context_built",
                merchant_id=merchant_id,
                chunk_count=len(chunks),
                avg_similarity=round(avg_similarity, 3),
                context_tokens=self._estimate_tokens(context),
            )

            return context

        except TimeoutError:
            logger.warning(
                "rag_retrieval_timeout",
                merchant_id=merchant_id,
                timeout_ms=self.RETRIEVAL_TIMEOUT_MS,
            )
            return None
        except Exception as e:
            logger.error(
                "rag_retrieval_error",
                merchant_id=merchant_id,
                error=str(e),
            )
            return None

    async def build_rag_context_with_chunks(
        self,
        merchant_id: int,
        user_query: str,
        top_k: int = 7,  # Increased from 5 for better context coverage
        similarity_threshold: float = 0.2,  # Lowered for better recall
        embedding_version: str | None = None,
        conversation_history: list[dict] | None = None,
    ) -> tuple[str | None, list[RetrievedChunk]]:
        """Retrieve relevant chunks and return both context string and raw chunks.

        Story 10-1: Source Citations Widget
        Returns raw chunks for source citation extraction.

        Args:
            merchant_id: Merchant ID for multi-tenant isolation
            user_query: User's question or search query
            top_k: Number of chunks to retrieve (default 5)
            similarity_threshold: Minimum similarity score (default 0.7)
            embedding_version: Filter by embedding version
            conversation_history: Optional conversation history for query rewriting

        Returns:
            Tuple of (formatted context string or None, list of RetrievedChunk)
        """
        search_query = user_query

        if (
            self.query_rewriter
            and conversation_history
            and self.query_rewriter.is_follow_up(user_query)
        ):
            try:
                search_query = await asyncio.wait_for(
                    self.query_rewriter.rewrite_query(user_query, conversation_history),
                    timeout=self.REWRITE_TIMEOUT_MS / 1000.0,
                )
                logger.info(
                    "rag_query_rewritten",
                    merchant_id=merchant_id,
                    original=user_query[:50],
                    rewritten=search_query[:50],
                )
            except TimeoutError:
                logger.warning(
                    "rag_query_rewrite_timeout",
                    merchant_id=merchant_id,
                    fallback_to_original=True,
                )
            except Exception as e:
                logger.warning(
                    "rag_query_rewrite_failed",
                    merchant_id=merchant_id,
                    error=str(e),
                    fallback_to_original=True,
                )

        try:
            logger.info(
                "rag_retrieval_starting",
                merchant_id=merchant_id,
                query=search_query[:50],
                query_length=len(search_query),
                top_k=top_k,
                threshold=similarity_threshold,
                embedding_version=embedding_version,
            )
            chunks = await asyncio.wait_for(
                self.retrieval_service.retrieve_relevant_chunks(
                    merchant_id=merchant_id,
                    query=search_query,
                    top_k=top_k,
                    threshold=similarity_threshold,
                    embedding_version=embedding_version,
                ),
                timeout=self.RETRIEVAL_TIMEOUT_MS / 1000.0,
            )

            logger.info(
                "rag_retrieval_completed",
                merchant_id=merchant_id,
                chunks_found=len(chunks) if chunks else 0,
            )

            if not chunks:
                logger.info(
                    "rag_no_chunks_found_with_chunks",
                    merchant_id=merchant_id,
                    query_length=len(search_query),
                    original_query=user_query[:50] if search_query != user_query else None,
                )
                return None, []

            context = self._format_chunks_as_context(chunks)

            if self._estimate_tokens(context) > self.MAX_CONTEXT_TOKENS:
                context = self._truncate_context(context, self.MAX_CONTEXT_TOKENS)
                logger.info(
                    "rag_context_truncated_with_chunks",
                    merchant_id=merchant_id,
                    max_tokens=self.MAX_CONTEXT_TOKENS,
                )

            avg_similarity = sum(c.similarity for c in chunks) / len(chunks)
            logger.info(
                "rag_context_built_with_chunks",
                merchant_id=merchant_id,
                chunk_count=len(chunks),
                avg_similarity=round(avg_similarity, 3),
                context_tokens=self._estimate_tokens(context),
            )

            return context, chunks

        except TimeoutError:
            logger.warning(
                "rag_retrieval_timeout_with_chunks",
                merchant_id=merchant_id,
                timeout_ms=self.RETRIEVAL_TIMEOUT_MS,
            )
            return None, []
        except Exception as e:
            logger.error(
                "rag_retrieval_error_with_chunks",
                merchant_id=merchant_id,
                error=str(e),
            )
            return None, []

    def _format_chunks_as_context(self, chunks: list[RetrievedChunk]) -> str:
        """Format retrieved chunks as context string with citations.

        Groups chunks by document name and formats with bullet points.

        Args:
            chunks: List of retrieved chunks with similarity scores

        Returns:
            Formatted context string with document citations

        Example:
            From "Product Manual.pdf":
            - Product X has a battery life of 10 hours.
            - Warranty covers manufacturing defects for 1 year.

            From "FAQ.txt":
            - Returns accepted within 30 days of purchase.
        """
        # Group chunks by document name
        chunks_by_doc = {}
        for chunk in chunks:
            doc_name = chunk.document_name
            if doc_name not in chunks_by_doc:
                chunks_by_doc[doc_name] = []
            chunks_by_doc[doc_name].append(chunk)

        # Format as context string
        context_parts = []
        for doc_name, doc_chunks in chunks_by_doc.items():
            context_parts.append(f'From "{doc_name}":')
            for chunk in doc_chunks:
                context_parts.append(f"- {chunk.content}")
            context_parts.append("")  # Blank line between documents

        return "\n".join(context_parts).strip()

    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimate: ~4 chars per token.

        Args:
            text: Text to estimate tokens for

        Returns:
            Estimated token count
        """
        return len(text) // 4

    def _truncate_at_sentence(self, text: str, max_chars: int) -> str:
        """Truncate at last sentence boundary within limit.

        Args:
            text: Text to truncate
            max_chars: Maximum characters allowed

        Returns:
            Truncated text ending at sentence boundary
        """
        if len(text) <= max_chars:
            return text

        truncated = text[:max_chars]
        last_period = truncated.rfind(".")

        if last_period > 0:
            return truncated[: last_period + 1]
        else:
            return truncated

    def _truncate_context(self, context: str, max_tokens: int) -> str:
        """Truncate context to fit within token limit.

        Args:
            context: Full context string
            max_tokens: Maximum tokens allowed

        Returns:
            Truncated context preserving sentence boundaries
        """
        max_chars = max_tokens * 4
        return self._truncate_at_sentence(context, max_chars)
