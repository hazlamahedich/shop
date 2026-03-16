"""Dimension change handler for embedding provider switches.

Handles detection of embedding dimension changes and triggers re-embedding
when switching between providers with different vector dimensions.

Story 8-11: LLM Embedding Provider Integration & Re-embedding
"""

from __future__ import annotations

import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge_base import KnowledgeDocument
from app.models.merchant import Merchant
from app.services.rag.embedding_service import EMBEDDING_DIMENSIONS

logger = structlog.get_logger(__name__)


class DimensionHandler:
    """Handle embedding dimension changes.

    When a merchant changes their embedding provider, this handler:
    1. Detects if the dimension changed (e.g., 1536 -> 768)
    2. Marks all documents for re-embedding
    3. Provides status tracking for re-embedding progress

    Dimension Reference:
    - OpenAI text-embedding-3-small: 1536
    - Gemini text-embedding-004: 768
    - Ollama nomic-embed-text: 768
    """

    @staticmethod
    async def check_dimension_change(
        db: AsyncSession,
        merchant_id: int,
        new_provider: str,
    ) -> bool:
        """Check if provider change requires re-embedding.

        Args:
            db: Database session
            merchant_id: Merchant ID
            new_provider: New embedding provider name

        Returns:
            True if dimension changed (re-embedding required)
        """
        result = await db.execute(
            select(Merchant.embedding_dimension).where(Merchant.id == merchant_id)
        )
        old_dimension = result.scalar_one_or_none() or 1536
        new_dimension = EMBEDDING_DIMENSIONS.get(new_provider, 1536)

        if old_dimension != new_dimension:
            logger.info(
                "dimension_change_detected",
                merchant_id=merchant_id,
                old_dimension=old_dimension,
                new_dimension=new_dimension,
                new_provider=new_provider,
            )
            return True

        return False

    @staticmethod
    async def mark_documents_for_reembedding(
        db: AsyncSession,
        merchant_id: int,
    ) -> int:
        """Mark all documents for re-embedding.

        Sets status to 'pending' and re_embedding_status to 'queued'.
        The background worker will process these documents.

        Args:
            db: Database session
            merchant_id: Merchant ID

        Returns:
            Number of documents marked for re-embedding
        """
        result = await db.execute(
            update(KnowledgeDocument)
            .where(KnowledgeDocument.merchant_id == merchant_id)
            .values(
                status="pending",
                re_embedding_status="queued",
                re_embedding_progress=0,
            )
        )
        await db.commit()

        doc_count = result.rowcount

        logger.info(
            "documents_marked_for_reembedding",
            merchant_id=merchant_id,
            document_count=doc_count,
        )

        return doc_count

    @staticmethod
    async def get_reembedding_status(
        db: AsyncSession,
        merchant_id: int,
    ) -> dict:
        """Get re-embedding status for a merchant.

        Args:
            db: Database session
            merchant_id: Merchant ID

        Returns:
            Dict with status counts and progress information
        """
        result = await db.execute(
            select(
                KnowledgeDocument.re_embedding_status,
            ).where(KnowledgeDocument.merchant_id == merchant_id)
        )

        status_counts: dict[str, int] = {
            "none": 0,
            "queued": 0,
            "in_progress": 0,
            "completed": 0,
            "failed": 0,
        }

        for row in result:
            status = row[0] or "none"
            if status in status_counts:
                status_counts[status] += 1

        total_docs = sum(status_counts.values())
        completed = status_counts.get("completed", 0)
        progress = (completed / total_docs * 100) if total_docs > 0 else 0

        return {
            "status_counts": status_counts,
            "total_documents": total_docs,
            "completed_documents": completed,
            "progress_percent": round(progress, 1),
        }

    @staticmethod
    def get_provider_dimension(provider: str) -> int:
        """Get embedding dimension for a provider.

        Args:
            provider: Provider name (openai, ollama, gemini)

        Returns:
            Dimension (1536 for OpenAI, 768 for others)
        """
        return EMBEDDING_DIMENSIONS.get(provider, 1536)
