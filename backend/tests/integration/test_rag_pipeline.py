"""Integration tests for RAG pipeline.

Story 8-4: Backend - RAG Service (Document Processing)

Test Coverage:
- End-to-end RAG flow: upload → process → reprocess
- Multi-tenant isolation
- Background task integration
"""

from __future__ import annotations

import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.knowledge_base import DocumentChunk, DocumentStatus, KnowledgeDocument
from app.models.merchant import Merchant
from tests.conftest import auth_headers as make_auth_headers


@pytest.fixture
def sample_text_file():
    """Create a sample text file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w") as f:
        f.write(
            "This is a sample FAQ document.\n"
            "Q: What is your return policy?\n"
            "A: We accept returns within 30 days.\n"
            "Q: How long does shipping take?\n"
            "A: Shipping takes 3-5 business days.\n"
            "This document will be chunked and embedded.\n"
        )
        yield f.name

    os.unlink(f.name)


class TestRAGPipelineIntegration:
    """Integration tests for the complete RAG pipeline."""

    @pytest.mark.asyncio
    @pytest.mark.test_id("8-9-INT-009")
    @pytest.mark.priority("P0")
    async def test_upload_creates_pending_document(
        self,
        async_client: AsyncClient,
        async_session: AsyncSession,
        test_merchant: int,
        sample_text_file,
    ):
        """Test document upload creates document with pending status."""
        merchant_id = test_merchant
        headers = make_auth_headers(merchant_id)

        with patch("app.services.rag.processing_task.process_document_background"):
            with patch("app.api.knowledge_base._process_document_chunks"):
                with open(sample_text_file, "rb") as f:
                    response = await async_client.post(
                        "/api/knowledge-base/upload",
                        files={"file": ("test.txt", f, "text/plain")},
                        headers=headers,
                    )

        assert response.status_code == 200
        data = response.json()["data"]
        document_id = data["id"]

        assert data["status"] == "pending"

        result = await async_session.execute(
            select(KnowledgeDocument).where(KnowledgeDocument.id == document_id)
        )
        document = result.scalar_one_or_none()
        assert document is not None
        assert document.merchant_id == merchant_id

    @pytest.mark.asyncio
    @pytest.mark.test_id("8-9-INT-010")
    @pytest.mark.priority("P0")
    async def test_document_status_endpoint(
        self,
        async_client: AsyncClient,
        async_session: AsyncSession,
        test_merchant: int,
    ):
        """Test document status can be checked."""
        merchant_id = test_merchant
        headers = make_auth_headers(merchant_id)

        document = KnowledgeDocument(
            merchant_id=merchant_id,
            filename="faq.txt",
            file_type="txt",
            file_size=500,
            status=DocumentStatus.READY.value,
        )
        async_session.add(document)
        await async_session.commit()
        await async_session.refresh(document)

        response = await async_client.get(
            f"/api/knowledge-base/{document.id}/status",
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["status"] == "ready"

    @pytest.mark.asyncio
    @pytest.mark.test_id("8-9-INT-011")
    @pytest.mark.priority("P0")
    async def test_cross_merchant_document_isolation(
        self,
        async_client: AsyncClient,
        async_session: AsyncSession,
        test_merchant: int,
    ):
        """Test that merchants cannot access other merchants' documents."""
        merchant_id = test_merchant
        headers = make_auth_headers(merchant_id)

        other_merchant = Merchant(
            merchant_key="other-merchant",
            email="other@example.com",
            platform="messenger",
        )
        async_session.add(other_merchant)
        await async_session.commit()
        await async_session.refresh(other_merchant)

        other_document = KnowledgeDocument(
            merchant_id=other_merchant.id,
            filename="secret.txt",
            file_type="txt",
            file_size=100,
            status=DocumentStatus.READY.value,
        )
        async_session.add(other_document)
        await async_session.commit()
        await async_session.refresh(other_document)

        response = await async_client.get(
            f"/api/knowledge-base/{other_document.id}",
            headers=headers,
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    @pytest.mark.test_id("8-9-INT-012")
    @pytest.mark.priority("P1")
    async def test_reprocess_document_endpoint(
        self,
        async_client: AsyncClient,
        async_session: AsyncSession,
        test_merchant: int,
    ):
        """Test the reprocess document endpoint."""
        merchant_id = test_merchant
        headers = make_auth_headers(merchant_id)

        document = KnowledgeDocument(
            merchant_id=merchant_id,
            filename="faq.txt",
            file_type="txt",
            file_size=500,
            status=DocumentStatus.ERROR.value,
            error_message="Previous processing failed",
        )
        async_session.add(document)
        await async_session.commit()
        await async_session.refresh(document)

        with patch("app.services.rag.processing_task.process_document_background"):
            response = await async_client.post(
                f"/api/knowledge-base/{document.id}/reprocess",
                headers=headers,
            )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["message"] == "Document reprocessing triggered"
        assert data["document_id"] == document.id


class TestRAGServiceUnit:
    """Unit tests for RAG service components."""

    @pytest.mark.asyncio
    @pytest.mark.test_id("8-9-UNIT-001")
    @pytest.mark.priority("P2")
    async def test_embedding_service_initialization(self):
        """Test embedding service can be initialized."""
        from app.services.rag.embedding_service import EmbeddingService

        service = EmbeddingService(provider="openai", api_key="test-key")

        assert service.provider == "openai"
        assert service.model == "text-embedding-3-small"
        assert service.dimension == 1536

    @pytest.mark.asyncio
    @pytest.mark.test_id("8-9-UNIT-002")
    @pytest.mark.priority("P2")
    async def test_retrieval_service_initialization(
        self,
        async_session: AsyncSession,
    ):
        """Test retrieval service can be initialized."""
        from app.services.rag.embedding_service import EmbeddingService
        from app.services.rag.retrieval_service import RetrievalService

        embedding_service = EmbeddingService(provider="openai", api_key="test-key")
        retrieval_service = RetrievalService(
            db=async_session,
            embedding_service=embedding_service,
        )

        assert retrieval_service.db == async_session
        assert retrieval_service.embedding_service == embedding_service

    @pytest.mark.asyncio
    @pytest.mark.test_id("8-9-UNIT-003")
    @pytest.mark.priority("P2")
    async def test_document_processor_initialization(
        self,
        async_session: AsyncSession,
    ):
        """Test document processor can be initialized."""
        from app.services.knowledge.chunker import DocumentChunker
        from app.services.rag.document_processor import DocumentProcessor
        from app.services.rag.embedding_service import EmbeddingService

        embedding_service = EmbeddingService(provider="openai", api_key="test-key")
        processor = DocumentProcessor(
            db=async_session,
            embedding_service=embedding_service,
            chunker=DocumentChunker(),
        )

        assert processor.db == async_session
        assert processor.embedding_service == embedding_service
        assert processor.chunker is not None
