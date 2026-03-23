"""Background task for document processing.

Async background task that processes uploaded documents through the RAG pipeline.
Triggered by the knowledge base upload API after document upload.

Story 8-4: Backend - RAG Service (Document Processing)
"""

from __future__ import annotations

from dataclasses import dataclass

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.core.errors import APIError, ErrorCode
from app.models.llm_configuration import LLMConfiguration
from app.models.merchant import Merchant
from app.services.knowledge.chunker import DocumentChunker
from app.services.rag.document_processor import DocumentProcessor, ProcessingResult
from app.services.rag.embedding_service import EmbeddingService

logger = structlog.get_logger(__name__)


@dataclass
class MerchantLLMConfig:
    """Merchant's LLM configuration with decrypted API key."""

    llm_provider: str
    llm_api_key: str | None
    llm_model: str | None = None
    ollama_url: str | None = None


async def get_merchant_llm_config(db: AsyncSession, merchant_id: int) -> MerchantLLMConfig:
    """Get merchant's LLM configuration with decrypted API key.

    CRITICAL: This function handles API key decryption.
    The api_key_encrypted field in the database is encrypted.

    Args:
        db: Database session
        merchant_id: Merchant ID

    Returns:
        MerchantLLMConfig with decrypted API key

    Raises:
        APIError: If merchant doesn't exist
    """
    from app.core.security import decrypt_access_token

    # Get merchant
    result = await db.execute(select(Merchant).where(Merchant.id == merchant_id))
    merchant = result.scalar_one_or_none()

    if not merchant:
        raise APIError(
            ErrorCode.MERCHANT_NOT_FOUND,
            f"Merchant {merchant_id} not found",
        )

    # Get LLM configuration
    llm_config_result = await db.execute(
        select(LLMConfiguration).where(LLMConfiguration.merchant_id == merchant_id)
    )
    llm_config = llm_config_result.scalar_one_or_none()

    if not llm_config:
        # No LLM config - return defaults (will use environment settings)
        return MerchantLLMConfig(
            llm_provider="ollama",
            llm_api_key=None,
            llm_model=None,
            ollama_url=None,
        )

    # Decrypt API key if present
    decrypted_key = None
    if llm_config.api_key_encrypted:
        decrypted_key = decrypt_access_token(llm_config.api_key_encrypted)

    return MerchantLLMConfig(
        llm_provider=llm_config.provider,
        llm_api_key=decrypted_key,
        llm_model=llm_config.cloud_model or llm_config.ollama_model,
        ollama_url=llm_config.ollama_url,
    )


async def process_document_background(document_id: int, merchant_id: int) -> ProcessingResult:
    """Background task to process uploaded document.

    This function is designed to be run as a FastAPI BackgroundTask.
    It creates its own database session and handles all errors internally.

    Args:
        document_id: ID of document to process
        merchant_id: Merchant ID (for LLM configuration lookup)

    Returns:
        ProcessingResult with status and metadata

    Usage in FastAPI:
        @router.post("/upload")
        async def upload_document(
            file: UploadFile,
            background_tasks: BackgroundTasks,
        ):
            # ... save file and create document record ...
            background_tasks.add_task(
                process_document_background,
                document_id=document.id,
                merchant_id=merchant_id,
            )
    """
    async with async_session() as db:
        try:
            # Get merchant and their LLM config
            result = await db.execute(select(Merchant).where(Merchant.id == merchant_id))
            merchant = result.scalar_one_or_none()
            if not merchant:
                raise APIError(ErrorCode.MERCHANT_NOT_FOUND, f"Merchant {merchant_id} not found")

            merchant_config = await get_merchant_llm_config(db, merchant_id)

            # Initialize embedding service using merchant's embedding settings (Story 8-11)
            provider = merchant.embedding_provider
            model = merchant.embedding_model
            
            # Use merchant's decrypted API key for cloud providers
            api_key = merchant_config.llm_api_key
            
            # Fallback for OpenAI if using Anthropic for chat but no specific embedding provider
            # (Though current schema handles this via Merchant fields)
            if provider == "anthropic":
                from app.core.config import settings
                provider = "openai"
                api_key = settings().get("OPENAI_API_KEY")
                model = "text-embedding-3-small"

            embedding_service = EmbeddingService(
                provider=provider,
                api_key=api_key,
                model=model,
                ollama_url=merchant_config.ollama_url,
            )

            # Initialize processor
            processor = DocumentProcessor(
                db=db,
                embedding_service=embedding_service,
                chunker=DocumentChunker(),
            )

            # Process document with performance tracking
            result = await processor.process_document(document_id)

            logger.info(
                "document_processing_complete",
                document_id=document_id,
                merchant_id=merchant_id,
                status=result.status,
                chunk_count=result.chunk_count,
                processing_time_ms=result.processing_time_ms,
                provider=provider,
            )

            return result

        except APIError as e:
            logger.error(
                "document_processing_api_error",
                document_id=document_id,
                merchant_id=merchant_id,
                error_code=e.code,
                error_message=e.message,
            )
            # Update document status to error
            await _update_document_error(db, document_id, str(e))
            raise

        except Exception as e:
            logger.error(
                "document_processing_failed",
                document_id=document_id,
                merchant_id=merchant_id,
                error=str(e),
                error_code="DOCUMENT_PROCESSING_FAILED",
            )
            # Update document status to error
            await _update_document_error(db, document_id, str(e))
            raise


async def _update_document_error(db: AsyncSession, document_id: int, error_message: str) -> None:
    """Update document status to error with message."""
    from sqlalchemy import update

    from app.models.knowledge_base import DocumentStatus, KnowledgeDocument

    try:
        await db.execute(
            update(KnowledgeDocument)
            .where(KnowledgeDocument.id == document_id)
            .values(
                status=DocumentStatus.ERROR.value,
                error_message=error_message[:500],  # Truncate to fit column
            )
        )
        await db.commit()
    except Exception as e:
        logger.error(
            "failed_to_update_document_error_status",
            document_id=document_id,
            error=str(e),
        )
