"""Tests for Export API endpoint.

Tests POST /api/conversations/export endpoint with authentication,
filter support, and CSV response validation.
"""

from __future__ import annotations

from datetime import datetime
import pytest
from httpx import AsyncClient

from app.core.errors import ErrorCode
from app.models.merchant import Merchant
from app.models.conversation import Conversation


class TestExportAPI:
    """Test suite for Export API endpoint."""

    @pytest.mark.asyncio
    async def test_export_empty_conversations(
        self, async_client: AsyncClient, async_session
    ) -> None:
        """Test export with no conversations returns CSV with headers only."""
        # Create merchant
        merchant = Merchant(
            merchant_key="test-export-empty",
            platform="facebook",
            status="active",
        )
        async_session.add(merchant)
        await async_session.commit()
        await async_session.refresh(merchant)

        response = await async_client.post(
            "/api/conversations/export",
            headers={"X-Merchant-ID": str(merchant.id)},
            json={},
        )

        # Debug: print error details if not 200
        if response.status_code != 200:
            print(f"Error response: {response.text}")

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "attachment" in response.headers["content-disposition"]

        # Verify CSV content
        csv_content = response.text
        assert csv_content.startswith("\ufeff")  # UTF-8 BOM
        assert "Conversation ID" in csv_content
        assert "X-Export-Count" in response.headers

    @pytest.mark.asyncio
    async def test_export_with_conversations(
        self, async_client: AsyncClient, async_session
    ) -> None:
        """Test export with conversations includes data in CSV."""
        merchant = Merchant(
            merchant_key="test-export-data",
            platform="facebook",
            status="active",
        )
        async_session.add(merchant)
        await async_session.commit()
        await async_session.refresh(merchant)

        # Create conversation
        conv = Conversation(
            merchant_id=merchant.id,
            platform="facebook",
            platform_sender_id="test_user_123",
        )
        async_session.add(conv)
        await async_session.commit()

        response = await async_client.post(
            "/api/conversations/export",
            headers={"X-Merchant-ID": str(merchant.id)},
            json={},
        )

        # Debug: print error details if not 200
        if response.status_code != 200:
            print(f"Error response: {response.text}")

        assert response.status_code == 200
        assert response.headers["X-Export-Count"] == "1"

        csv_content = response.text
        assert "****_123" in csv_content  # Masked customer ID (with underscore)

    @pytest.mark.asyncio
    async def test_export_with_date_filter(
        self, async_client: AsyncClient, async_session
    ) -> None:
        """Test export with date range filter."""
        merchant = Merchant(
            merchant_key="test-export-date",
            platform="facebook",
            status="active",
        )
        async_session.add(merchant)
        await async_session.commit()
        await async_session.refresh(merchant)

        # Create conversations at different dates
        conv1 = Conversation(
            merchant_id=merchant.id,
            platform="facebook",
            platform_sender_id="user1",
            created_at=datetime(2026, 1, 15, 10, 0, 0),
        )
        async_session.add(conv1)

        conv2 = Conversation(
            merchant_id=merchant.id,
            platform="facebook",
            platform_sender_id="user2",
            created_at=datetime(2026, 2, 15, 10, 0, 0),
        )
        async_session.add(conv2)
        await async_session.commit()

        response = await async_client.post(
            "/api/conversations/export",
            headers={"X-Merchant-ID": str(merchant.id)},
            json={
                "dateFrom": "2026-02-01",
                "dateTo": "2026-02-28",
            },
        )

        assert response.status_code == 200
        assert response.headers["X-Export-Count"] == "1"

    @pytest.mark.asyncio
    async def test_export_with_status_filter(
        self, async_client: AsyncClient, async_session
    ) -> None:
        """Test export with status filter."""
        merchant = Merchant(
            merchant_key="test-export-status",
            platform="facebook",
            status="active",
        )
        async_session.add(merchant)
        await async_session.commit()
        await async_session.refresh(merchant)

        conv1 = Conversation(
            merchant_id=merchant.id,
            platform="facebook",
            platform_sender_id="user1",
            status="active",
        )
        async_session.add(conv1)

        conv2 = Conversation(
            merchant_id=merchant.id,
            platform="facebook",
            platform_sender_id="user2",
            status="closed",
        )
        async_session.add(conv2)
        await async_session.commit()

        response = await async_client.post(
            "/api/conversations/export",
            headers={"X-Merchant-ID": str(merchant.id)},
            json={"status": ["active"]},
        )

        assert response.status_code == 200
        assert response.headers["X-Export-Count"] == "1"

    @pytest.mark.asyncio
    async def test_export_invalid_merchant_id(
        self, async_client: AsyncClient
    ) -> None:
        """Test export with invalid merchant ID returns 422."""
        # FastAPI validates header type before custom logic
        response = await async_client.post(
            "/api/conversations/export",
            headers={"X-Merchant-ID": "invalid"},
            json={},
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_export_missing_merchant_header(
        self, async_client: AsyncClient
    ) -> None:
        """Test export without merchant header returns error."""
        response = await async_client.post(
            "/api/conversations/export",
            json={},
        )

        # FastAPI returns 422 for missing required header
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_export_merchant_isolation(
        self, async_client: AsyncClient, async_session
    ) -> None:
        """Test that merchant can only export their own conversations."""
        # Create two merchants
        merchant1 = Merchant(
            merchant_key="test-export-iso-1",
            platform="facebook",
            status="active",
        )
        async_session.add(merchant1)

        merchant2 = Merchant(
            merchant_key="test-export-iso-2",
            platform="facebook",
            status="active",
        )
        async_session.add(merchant2)
        await async_session.commit()
        await async_session.refresh(merchant1)
        await async_session.refresh(merchant2)

        # Create conversation for merchant1
        conv1 = Conversation(
            merchant_id=merchant1.id,
            platform="facebook",
            platform_sender_id="user1",
        )
        async_session.add(conv1)
        await async_session.commit()

        # Merchant2's export should be empty
        response = await async_client.post(
            "/api/conversations/export",
            headers={"X-Merchant-ID": str(merchant2.id)},
            json={},
        )

        assert response.status_code == 200
        assert response.headers["X-Export-Count"] == "0"

    @pytest.mark.asyncio
    async def test_export_response_headers(
        self, async_client: AsyncClient, async_session
    ) -> None:
        """Test that export response includes proper headers."""
        merchant = Merchant(
            merchant_key="test-export-headers",
            platform="facebook",
            status="active",
        )
        async_session.add(merchant)
        await async_session.commit()
        await async_session.refresh(merchant)

        response = await async_client.post(
            "/api/conversations/export",
            headers={"X-Merchant-ID": str(merchant.id)},
            json={},
        )

        # Debug: print error details if not 200
        if response.status_code != 200:
            print(f"Error response: {response.text}")

        assert response.status_code == 200
        assert "content-disposition" in response.headers

        # Verify filename format
        content_disposition = response.headers["content-disposition"]
        assert "filename=" in content_disposition
        assert "conversations-" in content_disposition
        assert ".csv" in content_disposition

        # Verify export metadata headers
        assert "X-Export-Count" in response.headers
        assert "X-Export-Date" in response.headers

    @pytest.mark.asyncio
    async def test_export_content_type(
        self, async_client: AsyncClient, async_session
    ) -> None:
        """Test that export returns correct content type."""
        merchant = Merchant(
            merchant_key="test-export-content-type",
            platform="facebook",
            status="active",
        )
        async_session.add(merchant)
        await async_session.commit()
        await async_session.refresh(merchant)

        response = await async_client.post(
            "/api/conversations/export",
            headers={"X-Merchant-ID": str(merchant.id)},
            json={},
        )

        assert response.headers["content-type"] == "text/csv; charset=utf-8"

    @pytest.mark.asyncio
    async def test_export_csv_format(
        self, async_client: AsyncClient, async_session
    ) -> None:
        """Test that export returns properly formatted CSV."""
        import csv
        from io import StringIO

        merchant = Merchant(
            merchant_key="test-export-csv-format",
            platform="facebook",
            status="active",
        )
        async_session.add(merchant)
        await async_session.commit()
        await async_session.refresh(merchant)

        conv = Conversation(
            merchant_id=merchant.id,
            platform="facebook",
            platform_sender_id="test_user_12345",
        )
        async_session.add(conv)
        await async_session.commit()

        response = await async_client.post(
            "/api/conversations/export",
            headers={"X-Merchant-ID": str(merchant.id)},
            json={},
        )

        csv_content = response.text

        # Parse CSV to verify format
        # Strip BOM first
        if csv_content.startswith("\ufeff"):
            csv_content = csv_content[1:]

        reader = csv.DictReader(StringIO(csv_content))
        rows = list(reader)

        # Should have header row + 1 data row
        assert len(rows) == 1

        # Verify expected columns
        expected_columns = [
            "Conversation ID",
            "Customer ID",
            "Created Date",
            "Updated Date",
            "Status",
            "Sentiment",
            "Message Count",
            "Has Order",
            "LLM Provider",
            "Total Tokens",
            "Estimated Cost (USD)",
            "Last Message Preview",
        ]

        for col in expected_columns:
            assert col in rows[0]

    @pytest.mark.asyncio
    async def test_export_invalid_date_format(
        self, async_client: AsyncClient, async_session
    ) -> None:
        """Test that invalid date format returns validation error."""
        merchant = Merchant(
            merchant_key="test-export-invalid-date",
            platform="facebook",
            status="active",
        )
        async_session.add(merchant)
        await async_session.commit()
        await async_session.refresh(merchant)

        response = await async_client.post(
            "/api/conversations/export",
            headers={"X-Merchant-ID": str(merchant.id)},
            json={"dateFrom": "invalid-date"},
        )

        assert response.status_code == 422

        error_detail = response.json()
        assert "detail" in error_detail
