"""Tests for Knowledge Base API endpoints.

Tests cover:
- AC1: Document upload with metadata
- AC2: Document chunking (verify chunk sizes)
- AC3: Document list endpoint
- AC4: Document deletion with chunks
- Edge cases: Invalid file type, file too large, unauthorized access, document not found
"""

from __future__ import annotations

import os
import tempfile

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.core.database import get_db
from app.models.knowledge_base import DocumentChunk, DocumentStatus, KnowledgeDocument
from app.models.merchant import Merchant
from app.services.knowledge.chunker import ChunkingError, DocumentChunker


@pytest.fixture
async def db_session(async_session: AsyncSession):
    """Alias for async_session fixture."""
    yield async_session


@pytest.fixture
async def test_merchant(async_session: AsyncSession) -> int:
    """Create a test merchant for integration tests."""
    merchant = Merchant(
        merchant_key="test-kb-merchant-key",
        platform="messenger",
        email="kb-test@example.com",
        status="active",
    )
    async_session.add(merchant)
    await async_session.commit()
    await async_session.refresh(merchant)
    return merchant.id


@pytest.fixture
async def auth_headers(test_merchant: int) -> dict[str, str]:
    """Generate authentication headers with JWT token."""
    from app.core.auth import create_jwt
    import uuid

    session_id = str(uuid.uuid4())
    token = create_jwt(merchant_id=test_merchant, session_id=session_id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def client(async_session: AsyncSession):
    """Create async HTTP client for testing."""

    async def override_get_db():
        yield async_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as http_client:
        yield http_client

    app.dependency_overrides.clear()


class TestKnowledgeBaseAPI:
    """Tests for knowledge base endpoints."""

    @pytest.mark.asyncio
    async def test_upload_document_pdf(
        self,
        db_session: AsyncSession,
        test_merchant: int,
        client: AsyncClient,
        auth_headers: dict,
    ) -> None:
        """AC1: Test document upload with PDF file (malformed PDF shows error handling)."""
        pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n%%EOF"

        response = await client.post(
            "/api/knowledge-base/upload",
            files={"file": ("test.pdf", pdf_content, "application/pdf")},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["filename"] == "test.pdf"
        assert data["fileType"] == "pdf"
        assert data["status"] == "error"

    @pytest.mark.asyncio
    async def test_upload_document_txt(
        self,
        db_session: AsyncSession,
        test_merchant: int,
        client: AsyncClient,
        auth_headers: dict,
    ) -> None:
        """AC1: Test document upload with TXT file."""
        txt_content = b"This is a test document for the knowledge base."

        response = await client.post(
            "/api/knowledge-base/upload",
            files={"file": ("test.txt", txt_content, "text/plain")},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["filename"] == "test.txt"
        assert data["fileType"] == "txt"

    @pytest.mark.asyncio
    async def test_upload_invalid_file_type(
        self,
        db_session: AsyncSession,
        test_merchant: int,
        client: AsyncClient,
        auth_headers: dict,
    ) -> None:
        """Test upload with invalid file type (400 error)."""
        response = await client.post(
            "/api/knowledge-base/upload",
            files={"file": ("test.exe", b"binary content", "application/octet-stream")},
            headers=auth_headers,
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_upload_file_too_large(
        self,
        db_session: AsyncSession,
        test_merchant: int,
        client: AsyncClient,
        auth_headers: dict,
    ) -> None:
        """Test upload with file too large (413 error)."""
        large_content = b"x" * (11 * 1024 * 1024)

        response = await client.post(
            "/api/knowledge-base/upload",
            files={"file": ("large.txt", large_content, "text/plain")},
            headers=auth_headers,
        )

        assert response.status_code == 413

    @pytest.mark.asyncio
    async def test_list_documents(
        self,
        db_session: AsyncSession,
        test_merchant: int,
        client: AsyncClient,
        auth_headers: dict,
    ) -> None:
        """AC3: Test document list endpoint."""
        doc = KnowledgeDocument(
            merchant_id=test_merchant,
            filename="list.txt",
            file_type="txt",
            file_size=100,
            status=DocumentStatus.READY.value,
        )
        db_session.add(doc)
        await db_session.commit()

        response = await client.get(
            "/api/knowledge-base",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data["documents"]) >= 1
        assert any(d["filename"] == "list.txt" for d in data["documents"])

    @pytest.mark.asyncio
    async def test_get_document(
        self,
        db_session: AsyncSession,
        test_merchant: int,
        client: AsyncClient,
        auth_headers: dict,
    ) -> None:
        """Test get document details endpoint."""
        doc = KnowledgeDocument(
            merchant_id=test_merchant,
            filename="detail.txt",
            file_type="txt",
            file_size=100,
            status=DocumentStatus.READY.value,
        )
        db_session.add(doc)
        await db_session.commit()
        await db_session.refresh(doc)

        response = await client.get(
            f"/api/knowledge-base/{doc.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["filename"] == "detail.txt"
        assert data["chunkCount"] == 0

    @pytest.mark.asyncio
    async def test_get_document_status(
        self,
        db_session: AsyncSession,
        test_merchant: int,
        client: AsyncClient,
        auth_headers: dict,
    ) -> None:
        """Test get document processing status endpoint."""
        doc = KnowledgeDocument(
            merchant_id=test_merchant,
            filename="status.txt",
            file_type="txt",
            file_size=100,
            status=DocumentStatus.PROCESSING.value,
        )
        db_session.add(doc)
        await db_session.commit()
        await db_session.refresh(doc)

        response = await client.get(
            f"/api/knowledge-base/{doc.id}/status",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["status"] == "processing"
        assert data["progress"] == 50

    @pytest.mark.asyncio
    async def test_delete_document(
        self,
        db_session: AsyncSession,
        test_merchant: int,
        client: AsyncClient,
        auth_headers: dict,
    ) -> None:
        """AC4: Test document deletion with chunks."""
        doc = KnowledgeDocument(
            merchant_id=test_merchant,
            filename="delete.txt",
            file_type="txt",
            file_size=100,
            status=DocumentStatus.READY.value,
        )
        db_session.add(doc)
        await db_session.commit()
        await db_session.refresh(doc)

        chunk = DocumentChunk(
            document_id=doc.id,
            chunk_index=0,
            content="Test chunk content",
        )
        db_session.add(chunk)
        await db_session.commit()

        response = await client.delete(
            f"/api/knowledge-base/{doc.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["deleted"] is True

        result = await db_session.execute(
            select(KnowledgeDocument).where(KnowledgeDocument.id == doc.id)
        )
        assert result.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_document(
        self,
        db_session: AsyncSession,
        test_merchant: int,
        client: AsyncClient,
        auth_headers: dict,
    ) -> None:
        """Test delete non-existent document (404 error)."""
        response = await client.delete(
            "/api/knowledge-base/99999",
            headers=auth_headers,
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_nonexistent_document(
        self,
        db_session: AsyncSession,
        test_merchant: int,
        client: AsyncClient,
        auth_headers: dict,
    ) -> None:
        """Test get non-existent document (404 error)."""
        response = await client.get(
            "/api/knowledge-base/99999",
            headers=auth_headers,
        )

        assert response.status_code == 404


class TestDocumentChunker:
    """Tests for document chunker service."""

    def test_chunk_text_file(self, tmp_path: str) -> None:
        """Test chunking of text file."""
        chunker = DocumentChunker()

        test_file = os.path.join(tmp_path, "test.txt")
        with open(test_file, "w") as f:
            f.write("This is a test document. " * 100)

        chunks = chunker.chunk_document(test_file, "txt")

        assert len(chunks) > 0
        for chunk in chunks:
            assert len(chunk) >= chunker.MIN_CHUNK_CHARS

    def test_chunk_markdown_file(self, tmp_path: str) -> None:
        """Test chunking of markdown file."""
        chunker = DocumentChunker()

        test_file = os.path.join(tmp_path, "test.md")
        with open(test_file, "w") as f:
            f.write("# Test Header\n\nThis is markdown content. " * 50)

        chunks = chunker.chunk_document(test_file, "md")

        assert len(chunks) > 0

    def test_chunk_empty_file(self, tmp_path: str) -> None:
        """Test chunking of empty file raises error."""
        chunker = DocumentChunker()

        test_file = os.path.join(tmp_path, "empty.txt")
        with open(test_file, "w") as f:
            f.write("")

        with pytest.raises(ChunkingError):
            chunker.chunk_document(test_file, "txt")

    def test_chunk_quality_validation(self, tmp_path: str) -> None:
        """Test that whitespace-only chunks are filtered."""
        chunker = DocumentChunker()

        test_file = os.path.join(tmp_path, "whitespace.txt")
        with open(test_file, "w") as f:
            f.write(
                "   \n\n   \t\t   \n\nValid content here with enough characters to pass validation."
            )

        chunks = chunker.chunk_document(test_file, "txt")

        for chunk in chunks:
            assert any(c.isalnum() for c in chunk)
