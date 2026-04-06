"""Knowledge Base API endpoints.

API endpoints for managing knowledge base documents:
- POST /api/knowledge-base/upload - Upload a document
- GET /api/knowledge-base - List all documents
- GET /api/knowledge-base/{document_id} - Get document details
- GET /api/knowledge-base/{document_id}/status - Get processing status
- DELETE /api/knowledge-base/{document_id} - Delete a document

SECURITY: All endpoints extract merchant_id from authenticated session (JWT)
instead of accepting it as a query parameter to prevent IDOR.
"""

from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime

import structlog
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import get_request_merchant_id
from app.models.knowledge_base import DocumentChunk, DocumentStatus, KnowledgeDocument
from app.schemas.knowledge_base import (
    DocumentDeleteResponse,
    DocumentDetail,
    DocumentStatusResponse,
    DocumentUploadResponse,
    KnowledgeBaseStatsResponse,
)
from app.services.knowledge.chunker import ChunkingError, DocumentChunker

logger = structlog.get_logger()

router = APIRouter(prefix="/knowledge-base", tags=["knowledge-base"])

# Allowed file types and max size
ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md", ".docx"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Upload directory
UPLOAD_DIR = "uploads/knowledge-base"


def _ensure_upload_dir(merchant_id: int) -> str:
    """Ensure upload directory exists for merchant."""
    merchant_dir = os.path.join(UPLOAD_DIR, str(merchant_id))
    os.makedirs(merchant_dir, exist_ok=True)
    return merchant_dir


# MIME type mapping for security validation
MIME_TYPE_MAP = {
    ".pdf": {"application/pdf"},
    ".txt": {"text/plain"},
    ".md": {"text/plain", "text/markdown"},
    ".docx": {"application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
}


def _validate_file(file: UploadFile) -> tuple[bool, str]:
    """Validate file type (extension + MIME type) and size.

    Security: Checks BOTH extension and MIME type to prevent malicious file uploads.
    """
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"

    # Validate MIME type for security
    if file.content_type and ext in MIME_TYPE_MAP:
        allowed_mime_types = MIME_TYPE_MAP[ext]
        if file.content_type not in allowed_mime_types:
            return False, f"Invalid file content type for {ext} file"

    return True, ""


@router.post("/upload")
async def upload_document(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Upload a document to the knowledge base.

    The document is chunked immediately, and embedding generation
    is triggered as a background task.
    """
    merchant_id = get_request_merchant_id(request)

    # Validate file type
    is_valid, error_msg = _validate_file(file)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

    # Get file info
    filename = file.filename or "unknown"
    file_type = os.path.splitext(filename)[1].lower().lstrip(".")

    # Read file content
    content = await file.read()
    file_size = len(content)

    # Validate file size
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large. Maximum size: 10MB",
        )

    try:
        # Ensure upload directory exists
        merchant_dir = _ensure_upload_dir(merchant_id)

        # Generate unique filename with UUID prefix
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(merchant_dir, unique_filename)

        # Save file
        with open(file_path, "wb") as f:
            f.write(content)

        # Create database record
        document = KnowledgeDocument(
            merchant_id=merchant_id,
            filename=filename,
            file_type=file_type,
            file_size=file_size,
            status=DocumentStatus.PENDING.value,
        )
        db.add(document)
        await db.commit()
        await db.refresh(document)

        # Chunk document (without embeddings yet - status stays pending)
        await _process_document_chunks(db, document, file_path, file_type)

        # Trigger background embedding processing
        from app.services.rag.processing_task import process_document_background

        background_tasks.add_task(
            process_document_background,
            document_id=document.id,
            merchant_id=merchant_id,
        )

        logger.info(
            "document_uploaded",
            merchant_id=merchant_id,
            document_id=document.id,
            filename=filename,
            file_size=file_size,
            background_processing_triggered=True,
        )

        return {
            "data": DocumentUploadResponse(
                id=document.id,
                filename=document.filename,
                file_type=document.file_type,
                file_size=document.file_size,
                status=document.status,  # Will be 'pending' until embeddings complete
                created_at=document.created_at,
            ).model_dump(by_alias=True),
            "meta": {
                "requestId": "upload",
                "timestamp": datetime.now(UTC).isoformat(),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("document_upload_failed", merchant_id=merchant_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload document: {str(e)}",
        )


async def _process_document_chunks(
    db: AsyncSession,
    document: KnowledgeDocument,
    file_path: str,
    file_type: str,
) -> None:
    """Process document and create chunks (without embeddings).

    Story 8-4: Chunking only - embeddings generated by background task.
    Status remains 'pending' until embeddings are complete.
    """
    try:
        # Update status to processing (for chunking)
        document.status = DocumentStatus.PROCESSING.value
        await db.commit()

        # Chunk document
        chunker = DocumentChunker()
        chunks = chunker.chunk_document(file_path, file_type)

        # Create chunk records (without embeddings)
        for index, content in enumerate(chunks):
            chunk = DocumentChunk(
                document_id=document.id,
                chunk_index=index,
                content=content,
                embedding=None,  # Embeddings generated by background task
            )
            db.add(chunk)

        # Reset status to pending - waiting for embedding processing
        # Background task will update to 'ready' when embeddings complete
        document.status = DocumentStatus.PENDING.value
        document.error_message = None
        await db.commit()

    except ChunkingError as e:
        document.status = DocumentStatus.ERROR.value
        document.error_message = str(e)
        await db.commit()
        logger.error(
            "document_chunking_failed",
            document_id=document.id,
            error=str(e),
        )
    except Exception as e:
        document.status = DocumentStatus.ERROR.value
        document.error_message = f"Unexpected error: {str(e)}"
        await db.commit()
        logger.error(
            "document_processing_failed",
            document_id=document.id,
            error=str(e),
        )


@router.get("")
async def list_documents(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List all documents for the merchant."""
    merchant_id = get_request_merchant_id(request)

    try:
        # Query documents with chunk counts
        result = await db.execute(
            select(
                KnowledgeDocument,
                func.count(DocumentChunk.id).label("chunk_count"),
            )
            .outerjoin(DocumentChunk, KnowledgeDocument.id == DocumentChunk.document_id)
            .where(KnowledgeDocument.merchant_id == merchant_id)
            .group_by(KnowledgeDocument.id)
            .order_by(KnowledgeDocument.created_at.desc())
        )
        rows = result.all()

        documents = []
        for row in rows:
            doc = row[0]
            chunk_count = row[1]
            documents.append(
                DocumentDetail(
                    id=doc.id,
                    filename=doc.filename,
                    file_type=doc.file_type,
                    file_size=doc.file_size,
                    status=doc.status,
                    error_message=doc.error_message,
                    chunk_count=chunk_count,
                    created_at=doc.created_at,
                    updated_at=doc.updated_at,
                ).model_dump(by_alias=True)
            )

        return {
            "data": {"documents": documents},
            "meta": {
                "requestId": "list",
                "timestamp": datetime.now(UTC).isoformat(),
            },
        }

    except Exception as e:
        logger.error("document_list_failed", merchant_id=merchant_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list documents: {str(e)}",
        )


@router.get("/stats")
async def get_knowledge_base_stats(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get knowledge base statistics for dashboard widget.

    Returns total document count, status breakdown, and last upload date.
    """
    merchant_id = get_request_merchant_id(request)

    try:
        # Count documents by status
        status_result = await db.execute(
            select(KnowledgeDocument.status, func.count(KnowledgeDocument.id).label("count"))
            .where(KnowledgeDocument.merchant_id == merchant_id)
            .group_by(KnowledgeDocument.status)
        )

        status_counts = {row.status: row.count for row in status_result}
        total_docs = sum(status_counts.values())

        # Get last upload date
        last_upload_result = await db.execute(
            select(KnowledgeDocument.created_at)
            .where(KnowledgeDocument.merchant_id == merchant_id)
            .order_by(KnowledgeDocument.created_at.desc())
            .limit(1)
        )
        last_upload_date = last_upload_result.scalar_one_or_none()

        logger.info(
            "kb_stats_fetched",
            merchant_id=merchant_id,
            total_docs=total_docs,
            status_breakdown=status_counts,
        )

        return {
            "data": KnowledgeBaseStatsResponse(
                total_docs=total_docs,
                processing_count=status_counts.get("processing", 0),
                ready_count=status_counts.get("ready", 0),
                error_count=status_counts.get("error", 0),
                last_upload_date=last_upload_date,
            ).model_dump(by_alias=True),
            "meta": {
                "requestId": "stats",
                "timestamp": datetime.now(UTC).isoformat(),
            },
        }

    except Exception as e:
        logger.error("kb_stats_failed", merchant_id=merchant_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get knowledge base stats: {str(e)}",
        )


@router.get("/{document_id}")
async def get_document(
    document_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get document details."""
    merchant_id = get_request_merchant_id(request)

    try:
        # Query document with chunk count
        result = await db.execute(
            select(
                KnowledgeDocument,
                func.count(DocumentChunk.id).label("chunk_count"),
            )
            .outerjoin(DocumentChunk, KnowledgeDocument.id == DocumentChunk.document_id)
            .where(
                KnowledgeDocument.id == document_id,
                KnowledgeDocument.merchant_id == merchant_id,
            )
            .group_by(KnowledgeDocument.id)
        )
        row = result.first()

        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )

        doc = row[0]
        chunk_count = row[1]

        return {
            "data": DocumentDetail(
                id=doc.id,
                filename=doc.filename,
                file_type=doc.file_type,
                file_size=doc.file_size,
                status=doc.status,
                error_message=doc.error_message,
                chunk_count=chunk_count,
                created_at=doc.created_at,
                updated_at=doc.updated_at,
            ).model_dump(by_alias=True),
            "meta": {
                "requestId": "get",
                "timestamp": datetime.now(UTC).isoformat(),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "document_get_failed",
            merchant_id=merchant_id,
            document_id=document_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get document: {str(e)}",
        )


@router.get("/{document_id}/status")
async def get_document_status(
    document_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get document processing status."""
    merchant_id = get_request_merchant_id(request)

    try:
        # Query document
        result = await db.execute(
            select(KnowledgeDocument).where(
                KnowledgeDocument.id == document_id,
                KnowledgeDocument.merchant_id == merchant_id,
            )
        )
        doc = result.scalar_one_or_none()

        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )

        # Get chunk count
        chunk_result = await db.execute(
            select(func.count(DocumentChunk.id)).where(DocumentChunk.document_id == document_id)
        )
        chunk_count = chunk_result.scalar() or 0

        # Calculate progress
        progress = 0
        if doc.status == DocumentStatus.READY.value:
            progress = 100
        elif doc.status == DocumentStatus.PROCESSING.value:
            progress = 50
        elif doc.status == DocumentStatus.ERROR.value:
            progress = 0

        return {
            "data": DocumentStatusResponse(
                status=doc.status,
                progress=progress,
                chunk_count=chunk_count,
                error_message=doc.error_message,
            ).model_dump(by_alias=True),
            "meta": {
                "requestId": "status",
                "timestamp": datetime.now(UTC).isoformat(),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "document_status_failed",
            merchant_id=merchant_id,
            document_id=document_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get document status: {str(e)}",
        )


@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Delete a document and all its chunks."""
    merchant_id = get_request_merchant_id(request)

    try:
        # Query document
        result = await db.execute(
            select(KnowledgeDocument).where(
                KnowledgeDocument.id == document_id,
                KnowledgeDocument.merchant_id == merchant_id,
            )
        )
        doc = result.scalar_one_or_none()

        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )

        # Delete file from storage
        merchant_dir = _ensure_upload_dir(merchant_id)
        for filename in os.listdir(merchant_dir):
            if filename.endswith(f"_{doc.filename}"):
                file_path = os.path.join(merchant_dir, filename)
                try:
                    os.remove(file_path)
                except OSError:
                    pass  # File may not exist
                break

        # Delete database record (CASCADE deletes chunks)
        await db.delete(doc)
        await db.commit()

        logger.info(
            "document_deleted",
            merchant_id=merchant_id,
            document_id=document_id,
            filename=doc.filename,
        )

        return {
            "data": DocumentDeleteResponse(
                deleted=True,
                message="Document deleted successfully",
            ).model_dump(by_alias=True),
            "meta": {
                "requestId": "delete",
                "timestamp": datetime.now(UTC).isoformat(),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "document_delete_failed",
            merchant_id=merchant_id,
            document_id=document_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}",
        )


@router.post("/re-embed")
async def trigger_reembedding(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Manually trigger re-embedding of all knowledge base documents.

    This endpoint allows merchants to force re-embedding when:
    - Testing embedding provider changes
    - Recovering from embedding errors
    - Preparing for a provider switch
    """
    merchant_id = get_request_merchant_id(request)

    from app.services.rag.dimension_handler import DimensionHandler
    from app.services.rag.reembedding_worker import trigger_reembedding_for_merchant

    # Mark all documents for re-embedding
    doc_count = await DimensionHandler.mark_documents_for_reembedding(
        db=db,
        merchant_id=merchant_id,
    )

    if doc_count > 0:
        # Trigger background task
        background_tasks.add_task(
            trigger_reembedding_for_merchant,
            merchant_id=merchant_id,
        )

    logger.info(
        "reembedding_triggered",
        merchant_id=merchant_id,
        document_count=doc_count,
    )

    return {
        "data": {
            "message": f"Re-embedding triggered for {doc_count} documents",
            "documentCount": doc_count,
        },
        "meta": {
            "requestId": "reembed",
            "timestamp": datetime.now(UTC).isoformat(),
        },
    }


@router.get("/re-embed/status")
async def get_reembedding_status(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get re-embedding progress for merchant.

    Returns status counts and progress information for all documents.
    """
    merchant_id = get_request_merchant_id(request)

    from app.services.rag.dimension_handler import DimensionHandler

    status = await DimensionHandler.get_reembedding_status(
        db=db,
        merchant_id=merchant_id,
    )

    return {
        "data": status,
        "meta": {
            "requestId": "reembed-status",
            "timestamp": datetime.now(UTC).isoformat(),
        },
    }


@router.post("/test-rag")
async def test_rag_query(
    request: Request,
    query: str,
    top_k: int = 7,
    similarity_threshold: float = 0.2,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Test RAG query and return results for debugging.

    Enhanced RAG Testing Endpoint:
    - Tests RAG retrieval with specified parameters
    - Returns chunks with similarity scores
    - Shows which documents were matched
    - Useful for debugging RAG performance and quality

    Args:
        query: Search query to test
        top_k: Number of chunks to retrieve (default: 7)
        similarity_threshold: Minimum similarity score (default: 0.2)

    Returns:
        Retrieved chunks with similarity scores and document info
    """
    merchant_id = get_request_merchant_id(request)

    from app.core.security import decrypt_access_token
    from app.services.rag.context_builder import RAGContextBuilder
    from app.services.rag.embedding_service import EmbeddingService
    from sqlalchemy.ext.asyncio import async_sessionmaker

    # Get merchant LLM configuration for API key
    from app.models.llm_configuration import LLMConfiguration
    from app.models.merchant import Merchant

    merchant_result = await db.execute(select(Merchant).where(Merchant.id == merchant_id))
    merchant = merchant_result.scalar_one_or_none()

    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Merchant {merchant_id} not found",
        )

    # Get LLM configuration
    llm_config_result = await db.execute(
        select(LLMConfiguration).where(LLMConfiguration.merchant_id == merchant_id)
    )
    llm_config = llm_config_result.scalar_one_or_none()

    # Determine embedding provider
    provider = merchant.embedding_provider or "openai"
    model = merchant.embedding_model or "text-embedding-3-small"
    api_key = None
    ollama_url = None

    if llm_config and llm_config.api_key_encrypted:
        api_key = decrypt_access_token(llm_config.api_key_encrypted)
    if llm_config and llm_config.ollama_url:
        ollama_url = llm_config.ollama_url

    # Special case: Anthropic doesn't support embeddings, use OpenAI
    if provider == "anthropic":
        from app.core.config import settings

        provider = "openai"
        model = "text-embedding-3-small"
        if not api_key:
            api_key = settings().get("OPENAI_API_KEY")

    # Create embedding service
    embedding_service = EmbeddingService(
        provider=provider,
        api_key=api_key,
        model=model,
        ollama_url=ollama_url,
    )

    # Create RAG context builder
    async_session = async_sessionmaker(db.__class__, db.bind, expire_on_commit=False)

    def session_factory():
        return async_session()

    rag_context_builder = RAGContextBuilder(
        session_factory=session_factory,
        embedding_service=embedding_service,
    )

    # Build embedding version for consistency
    embedding_version = None
    if merchant.embedding_provider and merchant.embedding_model:
        embedding_version = f"{merchant.embedding_provider}-{merchant.embedding_model}"

    # Retrieve chunks
    context, chunks = await rag_context_builder.build_rag_context_with_chunks(
        merchant_id=merchant_id,
        user_query=query,
        top_k=top_k,
        similarity_threshold=similarity_threshold,
        embedding_version=embedding_version,
    )

    # Format results
    return {
        "data": {
            "query": query,
            "parameters": {
                "top_k": top_k,
                "similarity_threshold": similarity_threshold,
                "embedding_version": embedding_version,
            },
            "results": {
                "context": context,
                "chunks": [
                    {
                        "content": chunk.content[:200] + "..."
                        if len(chunk.content) > 200
                        else chunk.content,
                        "similarity": round(chunk.similarity, 3),
                        "document": {
                            "id": chunk.document_id,
                            "name": chunk.document_name,
                            "chunk_index": chunk.chunk_index,
                        },
                    }
                    for chunk in chunks
                ],
                "total_chunks": len(chunks),
                "has_context": context is not None,
            },
        },
        "meta": {
            "requestId": "test-rag",
            "timestamp": datetime.now(UTC).isoformat(),
        },
    }
