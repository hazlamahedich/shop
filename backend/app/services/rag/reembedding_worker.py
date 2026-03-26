"""Re-embedding background worker.

Handles background re-embedding of documents when embedding provider changes.
Processes documents marked with re_embedding_status='queued'.

Story 8-11: LLM Embedding Provider Integration & Re-embedding
"""

from __future__ import annotations

import asyncio

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.models.knowledge_base import DocumentChunk, KnowledgeDocument
from app.models.merchant import Merchant
from app.core.config import settings
from app.services.rag.dimension_handler import DimensionHandler
from app.services.rag.embedding_service import EMBEDDING_MODELS, EmbeddingService
from app.services.rag.gemini_embedding_provider import GeminiEmbeddingProvider

logger = structlog.get_logger(__name__)

RETRY_CONFIG = {
    "max_attempts": 3,
    "backoff_factor": 2.0,
    "retryable_errors": [429, 503, 504],
}

# Rate limiting configuration per provider (requests per second)
RATE_LIMITS = {
    "openai": {"rpm": 3000, "delay_ms": 33},  # ~33ms between requests
    "gemini": {"rpm": 1500, "delay_ms": 67},  # ~67ms between requests
    "ollama": {"rpm": 100, "delay_ms": 10},  # Local, fast
}


async def reembed_all_documents(merchant_id: int) -> None:
    """Background task to re-embed all documents for a merchant.

    This function is triggered when:
    1. Merchant changes embedding provider (dimension change detected)
    2. Manual re-embed is triggered via API

    Args:
        merchant_id: Merchant ID whose documents to re-embed
    """
    async with async_session() as db:
        try:
            merchant = await _get_merchant_with_config(db, merchant_id)
            if not merchant:
                logger.error(
                    "reembedding_merchant_not_found",
                    merchant_id=merchant_id,
                )
                return

            # Determine embedding provider from LLM config (Story 8-11)
            # Default to LLM provider if embedding provider not explicitly configured
            llm_config = merchant.llm_configuration
            llm_provider = llm_config.provider if llm_config else "openai"

            # Decrypt API key if present
            api_key = None
            if llm_config and llm_config.api_key_encrypted:
                from app.core.security import decrypt_access_token

                api_key = decrypt_access_token(llm_config.api_key_encrypted)

            # Map LLM provider to embedding provider (same logic as processing_task.py)
            if llm_provider == "gemini":
                provider = "gemini"
                model = EMBEDDING_MODELS["gemini"]
            elif llm_provider == "openai":
                provider = "openai"
                model = EMBEDDING_MODELS["openai"]
            elif llm_provider == "ollama":
                provider = "ollama"
                model = EMBEDDING_MODELS["ollama"]
                api_key = None  # Ollama doesn't need API key
            elif llm_provider == "anthropic":
                # Anthropic doesn't support embeddings - fallback to OpenAI with env key
                provider = "openai"
                model = EMBEDDING_MODELS["openai"]
                api_key = settings().get("OPENAI_API_KEY")
                logger.info(
                    "reembedding_anthropic_fallback",
                    merchant_id=merchant_id,
                    fallback_provider="openai",
                )
            else:
                # Unknown provider - use database values as-is
                provider = merchant.embedding_provider or "openai"
                model = merchant.embedding_model or EMBEDDING_MODELS["openai"]

            documents = await _get_queued_documents(db, merchant_id)
            if not documents:
                logger.info(
                    "reembedding_no_documents",
                    merchant_id=merchant_id,
                )
                return

            logger.info(
                "reembedding_started",
                merchant_id=merchant_id,
                document_count=len(documents),
                provider=provider,
                model=model,
            )

            embedding_service = _create_embedding_service(
                provider=provider,
                model=model,
                api_key=api_key,
            )

            for i, doc in enumerate(documents):
                try:
                    progress = int(((i + 1) / len(documents)) * 100)
                    doc.re_embedding_status = "in_progress"
                    doc.re_embedding_progress = progress
                    await db.commit()

                    # Retry logic with exponential backoff (MEDIUM-4)
                    last_error = None
                    for attempt in range(RETRY_CONFIG["max_attempts"]):
                        try:
                            await _reembed_document(db, doc, embedding_service, provider, model)
                            break  # Success, exit retry loop
                        except Exception as e:
                            last_error = e
                            if attempt < RETRY_CONFIG["max_attempts"] - 1:
                                wait_time = RETRY_CONFIG["backoff_factor"] ** attempt
                                logger.warning(
                                    "reembedding_document_retry",
                                    document_id=doc.id,
                                    attempt=attempt + 1,
                                    wait_seconds=wait_time,
                                    error=str(e),
                                )
                                await asyncio.sleep(wait_time)
                            else:
                                raise  # Re-raise after all attempts exhausted

                    doc.re_embedding_status = "completed"
                    doc.re_embedding_progress = 100
                    doc.embedding_version = f"{provider}-{model}"
                    doc.status = "ready"
                    await db.commit()

                    logger.info(
                        "reembedding_document_complete",
                        document_id=doc.id,
                        progress=progress,
                    )

                    # Rate limiting delay between documents (MEDIUM-5)
                    delay_ms = RATE_LIMITS.get(provider, RATE_LIMITS["openai"])["delay_ms"]
                    if i < len(documents) - 1:  # Don't delay after last document
                        await asyncio.sleep(delay_ms / 1000.0)

                except Exception as e:
                    doc.re_embedding_status = "failed"
                    doc.error_message = str(e)
                    await db.commit()

                    logger.error(
                        "reembedding_document_failed",
                        document_id=doc.id,
                        error=str(e),
                    )

            logger.info(
                "reembedding_complete",
                merchant_id=merchant_id,
                total_documents=len(documents),
            )

        except Exception as e:
            logger.error(
                "reembedding_failed",
                merchant_id=merchant_id,
                error=str(e),
            )


async def _get_merchant_with_config(db: AsyncSession, merchant_id: int) -> Merchant | None:
    """Get merchant with LLM configuration."""
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(Merchant)
        .options(selectinload(Merchant.llm_configuration))
        .where(Merchant.id == merchant_id)
    )
    return result.scalars().first()


async def _get_queued_documents(db: AsyncSession, merchant_id: int) -> list[KnowledgeDocument]:
    """Get all documents queued for re-embedding."""
    result = await db.execute(
        select(KnowledgeDocument)
        .where(
            KnowledgeDocument.merchant_id == merchant_id,
            KnowledgeDocument.re_embedding_status == "queued",
        )
        .order_by(KnowledgeDocument.created_at)
    )
    return list(result.scalars().all())


async def _reembed_document(
    db: AsyncSession,
    document: KnowledgeDocument,
    embedding_service: EmbeddingService,
    provider: str,
    model: str,
) -> None:
    """Re-embed a single document's chunks.

    Args:
        db: Database session
        document: Document to re-embed
        embedding_service: Embedding service instance
        provider: Provider name
        model: Model name
    """
    result = await db.execute(
        select(DocumentChunk)
        .where(DocumentChunk.document_id == document.id)
        .order_by(DocumentChunk.chunk_index)
    )
    chunks = list(result.scalars().all())

    if not chunks:
        logger.warning(
            "reembedding_no_chunks",
            document_id=document.id,
        )
        return

    texts = [chunk.content for chunk in chunks]
    embedding_result = await embedding_service.embed_texts(texts)

    # Get embedding dimension from the first embedding
    embedding_dimension = len(embedding_result.embeddings[0]) if embedding_result.embeddings else 0

    for chunk, embedding in zip(chunks, embedding_result.embeddings):
        # Store as JSONB for flexible dimension support (Story 8-11)
        chunk.embedding = embedding
        chunk.embedding_dimension = embedding_dimension

    await db.commit()

    logger.info(
        "reembedding_chunks_complete",
        document_id=document.id,
        chunks_embedded=len(chunks),
        embedding_dimension=embedding_dimension,
    )


def _create_embedding_service(
    provider: str,
    model: str,
    api_key: str | None,
) -> EmbeddingService:
    """Create embedding service for the provider.

    Args:
        provider: Embedding provider
        model: Embedding model
        api_key: API key

    Returns:
        EmbeddingService instance
    """
    if provider == "gemini":
        gemini_provider = GeminiEmbeddingProvider(
            api_key=api_key or "",
            model=model,
        )

        class GeminiServiceAdapter:
            """Adapter to make GeminiProvider work like EmbeddingService."""

            def __init__(self, provider: GeminiEmbeddingProvider):
                self._provider = provider
                self.dimension = provider.DIMENSION

            async def embed_texts(self, texts: list[str]):
                return await self._provider.embed_texts(texts)

            async def embed_query(self, query: str) -> list[float]:
                return await self._provider.embed_query(query)

            def get_dimension(self) -> int:
                return self._provider.get_dimension()

            async def close(self):
                pass

        return GeminiServiceAdapter(gemini_provider)

    return EmbeddingService(
        provider=provider,
        api_key=api_key,
        model=model,
    )


async def trigger_reembedding_for_merchant(
    db: AsyncSession,
    merchant_id: int,
) -> int:
    """Trigger re-embedding for all documents of a merchant.

    Marks all documents as queued and starts background processing.

    Args:
        db: Database session
        merchant_id: Merchant ID

    Returns:
        Number of documents queued
    """
    doc_count = await DimensionHandler.mark_documents_for_reembedding(
        db=db,
        merchant_id=merchant_id,
    )

    if doc_count > 0:
        asyncio.create_task(reembed_all_documents(merchant_id))

    return doc_count
