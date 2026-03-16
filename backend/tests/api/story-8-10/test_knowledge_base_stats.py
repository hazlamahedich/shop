"""Tests for Story 8-10: Knowledge Base Stats API endpoint.

Tests the GET /api/knowledge-base/stats endpoint which returns:
- totalDocs: Total document count
- processingCount: Documents currently processing
- readyCount: Documents ready for use
- errorCount: Documents with errors
- lastUploadDate: ISO 8601 timestamp of most recent upload
"""

import pytest
import uuid
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.core.database import get_db
from app.models.knowledge_base import KnowledgeDocument, DocumentStatus
from app.models.merchant import Merchant


@pytest.fixture
async def test_merchant(async_session: AsyncSession) -> int:
    """Create a test merchant for integration tests."""
    merchant = Merchant(
        merchant_key=f"test-kb-stats-{uuid.uuid4().hex[:8]}",
        platform="messenger",
        email=f"kb-stats-test-{uuid.uuid4().hex[:8]}@example.com",
        status="active",
    )
    async_session.add(merchant)
    await async_session.flush()
    await async_session.commit()
    return merchant.id


@pytest.fixture
async def auth_headers(test_merchant: int) -> dict[str, str]:
    """Generate authentication headers with JWT token."""
    from app.core.auth import create_jwt

    session_id = str(uuid.uuid4())
    token = create_jwt(merchant_id=test_merchant, session_id=session_id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def async_client(async_session: AsyncSession, test_merchant: int):
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


@pytest.fixture
async def db_session(async_session: AsyncSession):
    """Alias for async_session fixture."""
    yield async_session


@pytest.mark.asyncio
class TestKnowledgeBaseStats:
    """Test suite for knowledge base stats endpoint."""

    async def test_stats_empty_knowledge_base(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test stats endpoint returns zeros when no documents exist."""
        response = await async_client.get(
            "/api/knowledge-base/stats",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["data"]["totalDocs"] == 0
        assert data["data"]["processingCount"] == 0
        assert data["data"]["readyCount"] == 0
        assert data["data"]["errorCount"] == 0
        assert data["data"]["lastUploadDate"] is None

    async def test_stats_with_documents(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_merchant: int,
    ):
        """Test stats endpoint with documents in various states."""
        # Create documents with different statuses
        doc1 = KnowledgeDocument(
            merchant_id=test_merchant,
            filename="ready_doc.pdf",
            file_type="pdf",
            file_size=1024,
            status=DocumentStatus.READY.value,
        )
        doc2 = KnowledgeDocument(
            merchant_id=test_merchant,
            filename="processing_doc.txt",
            file_type="txt",
            file_size=2048,
            status=DocumentStatus.PROCESSING.value,
        )
        doc3 = KnowledgeDocument(
            merchant_id=test_merchant,
            filename="error_doc.md",
            file_type="md",
            file_size=512,
            status=DocumentStatus.ERROR.value,
        )

        db_session.add_all([doc1, doc2, doc3])
        await db_session.commit()

        response = await async_client.get(
            "/api/knowledge-base/stats",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["data"]["totalDocs"] == 3
        assert data["data"]["readyCount"] == 1
        assert data["data"]["processingCount"] == 1
        assert data["data"]["errorCount"] == 1
        assert data["data"]["lastUploadDate"] is not None

        # Verify lastUploadDate is valid ISO 8601
        last_upload = datetime.fromisoformat(data["data"]["lastUploadDate"].replace("Z", "+00:00"))
        assert isinstance(last_upload, datetime)

    async def test_stats_multiple_ready_documents(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_merchant: int,
    ):
        """Test stats correctly counts multiple ready documents."""
        for i in range(5):
            doc = KnowledgeDocument(
                merchant_id=test_merchant,
                filename=f"doc_{i}.pdf",
                file_type="pdf",
                file_size=1024,
                status=DocumentStatus.READY.value,
            )
            db_session.add(doc)

        await db_session.commit()

        response = await async_client.get(
            "/api/knowledge-base/stats",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["data"]["totalDocs"] == 5
        assert data["data"]["readyCount"] == 5
        assert data["data"]["processingCount"] == 0
        assert data["data"]["errorCount"] == 0

    async def test_stats_last_upload_date_is_most_recent(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_merchant: int,
    ):
        """Test that lastUploadDate is the most recent upload."""
        from datetime import timedelta

        # Create documents with different timestamps
        base_time = datetime.utcnow() - timedelta(days=1)

        doc1 = KnowledgeDocument(
            merchant_id=test_merchant,
            filename="old_doc.pdf",
            file_type="pdf",
            file_size=1024,
            status=DocumentStatus.READY.value,
            created_at=base_time,
        )
        await db_session.commit()  # Commit first doc

        # Wait a moment and create second doc
        doc2 = KnowledgeDocument(
            merchant_id=test_merchant,
            filename="new_doc.pdf",
            file_type="pdf",
            file_size=1024,
            status=DocumentStatus.READY.value,
        )

        db_session.add_all([doc1, doc2])
        await db_session.commit()

        response = await async_client.get(
            "/api/knowledge-base/stats",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Should return a valid date
        assert data["data"]["lastUploadDate"] is not None
        last_upload = datetime.fromisoformat(data["data"]["lastUploadDate"].replace("Z", "+00:00"))
        assert isinstance(last_upload, datetime)
        # The second document should be the most recent
        assert last_upload > base_time

    async def test_stats_unauthenticated(self, async_client: AsyncClient):
        """Test stats endpoint requires authentication."""
        response = await async_client.get("/api/knowledge-base/stats")

        assert response.status_code == 401

    async def test_stats_merchant_isolation(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_merchant: int,
        async_session: AsyncSession,
    ):
        """Test that stats only include current merchant's documents."""
        # Create documents for current merchant
        doc1 = KnowledgeDocument(
            merchant_id=test_merchant,
            filename="my_doc.pdf",
            file_type="pdf",
            file_size=1024,
            status=DocumentStatus.READY.value,
        )
        db_session.add(doc1)

        # Create a different merchant
        other_merchant = Merchant(
            merchant_key=f"other-merchant-{uuid.uuid4().hex[:8]}",
            platform="messenger",
            email=f"other-{uuid.uuid4().hex[:8]}@example.com",
            status="active",
        )
        async_session.add(other_merchant)
        await async_session.flush()

        # Create documents for different merchant
        doc2 = KnowledgeDocument(
            merchant_id=other_merchant.id,
            filename="other_doc.pdf",
            file_type="pdf",
            file_size=1024,
            status=DocumentStatus.READY.value,
        )
        db_session.add(doc2)

        await db_session.commit()

        response = await async_client.get(
            "/api/knowledge-base/stats",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Should only count current merchant's documents
        assert data["data"]["totalDocs"] == 1
        assert data["data"]["readyCount"] == 1

    async def test_stats_response_format(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_merchant: int,
    ):
        """Test that response follows MinimalEnvelope format."""
        doc = KnowledgeDocument(
            merchant_id=test_merchant,
            filename="test.pdf",
            file_type="pdf",
            file_size=1024,
            status=DocumentStatus.READY.value,
        )
        db_session.add(doc)
        await db_session.commit()

        response = await async_client.get(
            "/api/knowledge-base/stats",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify envelope structure
        assert "data" in data
        assert "meta" in data
        assert "requestId" in data["meta"]
        assert "timestamp" in data["meta"]

        # Verify data structure
        assert "totalDocs" in data["data"]
        assert "processingCount" in data["data"]
        assert "readyCount" in data["data"]
        assert "errorCount" in data["data"]
        assert "lastUploadDate" in data["data"]
