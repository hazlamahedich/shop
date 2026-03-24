"""Knowledge base test factories.

Story 8-9: Testing & Quality Assurance
Task 9.1: Create backend/tests/fixtures/knowledge_base_factory.py
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.models.knowledge_base import DocumentChunk, DocumentStatus, KnowledgeDocument


def _utcnow_naive() -> datetime:
    """Return current UTC time as a naive datetime."""
    return datetime.now(UTC).replace(tzinfo=None)


class KnowledgeDocumentFactory:
    """Factory for creating test knowledge documents."""

    @staticmethod
    def create(
        merchant_id: int,
        filename: str = "test.pdf",
        file_type: str = "pdf",
        file_size: int = 1024,
        status: str = DocumentStatus.READY.value,
        error_message: str | None = None,
        created_at: datetime | None = None,
        **kwargs: Any,
    ) -> KnowledgeDocument:
        """Create a KnowledgeDocument instance."""
        return KnowledgeDocument(
            merchant_id=merchant_id,
            filename=filename,
            file_type=file_type,
            file_size=file_size,
            status=status,
            error_message=error_message,
            created_at=created_at or _utcnow_naive(),
            **kwargs,
        )


class DocumentChunkFactory:
    """Factory for creating test document chunks."""

    @staticmethod
    def create(
        document_id: int,
        chunk_index: int = 0,
        content: str = "Test chunk content.",
        embedding: list[float] | None = None,
        created_at: datetime | None = None,
        **kwargs: Any,
    ) -> DocumentChunk:
        """Create a DocumentChunk instance."""
        return DocumentChunk(
            document_id=document_id,
            chunk_index=chunk_index,
            content=content,
            embedding=embedding,
            created_at=created_at or _utcnow_naive(),
            **kwargs,
        )
