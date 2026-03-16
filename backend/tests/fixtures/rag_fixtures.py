"""RAG test fixtures.

Story 8-9: Testing & Quality Assurance
Task 1.2: Create fixtures in backend/tests/fixtures/rag_fixtures.py
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from app.models.knowledge_base import DocumentChunk, DocumentStatus, KnowledgeDocument


def _utcnow_naive() -> datetime:
    """Return current UTC time as a naive datetime."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class RAGFixtures:
    """RAG test fixtures for integration tests."""

    @staticmethod
    def document_with_100_chunks(
        merchant_id: int,
        filename: str = "large_document.pdf",
    ) -> tuple[KnowledgeDocument, List[DocumentChunk]]:
        """Create a document with 100 chunks for performance testing.

        Args:
            merchant_id: Merchant ID
            filename: Document filename

        Returns:
            Tuple of (document, list of 100 chunks)
        """
        doc = KnowledgeDocument(
            merchant_id=merchant_id,
            filename=filename,
            file_type="pdf",
            file_size=1024 * 1024,  # 1MB
            status=DocumentStatus.READY.value,
            created_at=_utcnow_naive(),
        )

        chunks = []
        for i in range(100):
            chunk = DocumentChunk(
                document_id=0,  # Will be updated after doc is saved
                chunk_index=i,
                content=f"This is chunk {i} from {filename}. " * 20,  # ~500 chars
                embedding=[0.1] * 1536,  # Mock 1536-dim embedding
                created_at=_utcnow_naive(),
            )
            chunks.append(chunk)

        return doc, chunks

    @staticmethod
    def merchant_with_knowledge_base(
        merchant_id: int,
        doc_count: int = 5,
    ) -> List[KnowledgeDocument]:
        """Create multiple documents for a merchant.

        Args:
            merchant_id: Merchant ID
            doc_count: Number of documents to create

        Returns:
            List of KnowledgeDocument instances
        """
        docs = []
        for i in range(doc_count):
            doc = KnowledgeDocument(
                merchant_id=merchant_id,
                filename=f"doc_{i}.pdf",
                file_type="pdf",
                file_size=1024 * (i + 1),
                status=DocumentStatus.READY.value,
                created_at=_utcnow_naive(),
            )
            docs.append(doc)
        return docs

    @staticmethod
    def mock_embedding_service():
        """Create a mock embedding service for testing.

        Returns:
            Mock embedding service that returns deterministic embeddings
        """
        from unittest.mock import AsyncMock

        class MockEmbeddingService:
            """Mock embedding service for testing."""

            def __init__(self):
                self.call_count = 0
                self.dimension = 1536

            async def embed(self, text: str) -> List[float]:
                """Return deterministic embedding based on text hash."""
                self.call_count += 1
                # Simple hash-based embedding for consistent test results
                hash_val = hash(text) % 1000
                return [0.1 * (hash_val / 1000)] * self.dimension

            async def embed_batch(self, texts: List[str]) -> List[List[float]]:
                """Return embeddings for multiple texts."""
                return [await self.embed(t) for t in texts]

        return MockEmbeddingService()

    @staticmethod
    def create_sample_chunks(
        document_id: int,
        count: int = 5,
        content_prefix: str = "Sample content",
    ) -> List[DocumentChunk]:
        """Create sample chunks for a document.

        Args:
            document_id: Document ID
            count: Number of chunks
            content_prefix: Prefix for chunk content

        Returns:
            List of DocumentChunk instances
        """
        chunks = []
        for i in range(count):
            chunk = DocumentChunk(
                document_id=document_id,
                chunk_index=i,
                content=f"{content_prefix} - chunk {i} of {count}.",
                embedding=[0.1 * (i + 1)] * 1536,
                created_at=_utcnow_naive(),
            )
            chunks.append(chunk)
        return chunks

    @staticmethod
    def create_document_with_status(
        merchant_id: int,
        status: str = DocumentStatus.READY.value,
        filename: str = "test.pdf",
        error_message: Optional[str] = None,
    ) -> KnowledgeDocument:
        """Create a document with specific status.

        Args:
            merchant_id: Merchant ID
            status: Document status
            filename: Document filename
            error_message: Optional error message

        Returns:
            KnowledgeDocument instance
        """
        return KnowledgeDocument(
            merchant_id=merchant_id,
            filename=filename,
            file_type="pdf",
            file_size=1024,
            status=status,
            error_message=error_message,
            created_at=_utcnow_naive(),
        )
