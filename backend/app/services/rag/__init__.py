"""RAG (Retrieval-Augmented Generation) Service Module.

Implements the core RAG pipeline for document-based Q&A:
- Embedding generation (OpenAI, Ollama)
- Vector similarity search using pgvector
- Document processing pipeline
- Background async processing

Story 8-4: Backend - RAG Service (Document Processing)
"""

from app.services.rag.document_processor import DocumentProcessor, ProcessingResult
from app.services.rag.embedding_service import (
    EMBEDDING_DIMENSIONS,
    EMBEDDING_MODELS,
    EmbeddingResult,
    EmbeddingService,
)
from app.services.rag.processing_task import (
    MerchantLLMConfig,
    get_merchant_llm_config,
    process_document_background,
)
from app.services.rag.retrieval_service import RetrievalService, RetrievedChunk

__all__ = [
    "EmbeddingService",
    "EmbeddingResult",
    "EMBEDDING_DIMENSIONS",
    "EMBEDDING_MODELS",
    "RetrievalService",
    "RetrievedChunk",
    "DocumentProcessor",
    "ProcessingResult",
    "process_document_background",
    "get_merchant_llm_config",
    "MerchantLLMConfig",
]
