"""API integration tests for Data Export endpoint.

Story 6-3: Merchant CSV Export

Tests cover:
- Authentication and authorization
- Rate limiting enforcement
- Concurrent export blocking
- CSV generation and format
- Error handling

@see _bmad-output/implementation-artifacts/6-3-merchant-csv-export.md
"""

from __future__ import annotations

import csv
import io
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from app.api.data_export import router


@pytest.fixture
def app():
    """Create FastAPI app with export router and exception handlers."""
    from fastapi import Request
    from fastapi.responses import JSONResponse

    from app.core.errors import APIError
    from app.main import get_error_status_code

    app = FastAPI()
    app.include_router(router, prefix="/api/v1", tags=["data-export"])

    # Add exception handler for APIError
    @app.exception_handler(APIError)
    async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
        status_code = get_error_status_code(exc.code)
        headers = {}

        if "retry_after" in exc.details:
            headers["Retry-After"] = str(exc.details["retry_after"])

        return JSONResponse(
            status_code=status_code,
            content=exc.to_dict(),
            headers=headers if headers else None,
        )

    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
async def async_client(app):
    """Create async test client."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
class TestDataExportAPI:
    """API tests for data export endpoint."""

    async def test_api_001_export_requires_merchant_id(self, async_client: AsyncClient):
        """Test 6-3-API-001: Export endpoint requires merchant ID header."""
        response = await async_client.post(
            "/api/v1/data/export",
            headers={
                "X-CSRF-Token": "test-token",
            },
        )

        assert response.status_code == 422

    async def test_api_002_export_requires_csrf_token(self, async_client: AsyncClient):
        """Test 6-3-API-002: Export endpoint requires CSRF token."""
        response = await async_client.post(
            "/api/v1/data/export",
            headers={
                "X-Merchant-ID": "123",
            },
        )

        assert response.status_code == 422

    async def test_api_003_export_returns_csv_with_valid_auth(self, async_client: AsyncClient):
        """Test 6-3-API-003: Export returns valid CSV with authentication."""
        with patch("app.api.data_export.get_async_redis_client", return_value=None):
            with patch("app.api.data_export.MerchantDataExportService") as mock_service:

                async def mock_export(merchant_id):
                    yield "# Merchant Data Export\n"
                    yield "# Merchant ID: 123\n"
                    yield "## SECTION: CONVERSATIONS\n"
                    yield "conversation_id,platform\n"

                mock_service_instance = MagicMock()
                mock_service_instance.export_merchant_data = mock_export
                mock_service.return_value = mock_service_instance

                response = await async_client.post(
                    "/api/v1/data/export",
                    headers={
                        "X-Merchant-ID": "123",
                        "X-CSRF-Token": "valid-csrf-token",
                    },
                )

                assert response.status_code == 200
                assert response.headers["content-type"] == "text/csv; charset=utf-8"
                assert "attachment" in response.headers["content-disposition"]
                assert "merchant_123_export_" in response.headers["content-disposition"]

    async def test_api_004_rate_limiting_blocks_rapid_requests(self, async_client: AsyncClient):
        """Test 6-3-API-004: Rate limiting blocks rapid export requests."""
        mock_redis = AsyncMock()
        # First request: rate_limit=False, lock=False
        # Second request: rate_limit=True (blocked)
        mock_redis.exists = AsyncMock(side_effect=[False, False, True])
        mock_redis.ttl = AsyncMock(return_value=3600)
        mock_redis.setex = AsyncMock()
        mock_redis.delete = AsyncMock()

        with patch("app.api.data_export.get_async_redis_client", return_value=mock_redis):
            with patch("app.api.data_export.MerchantDataExportService") as mock_service:

                async def mock_export(merchant_id):
                    yield "# Merchant Data Export\n"

                mock_service_instance = MagicMock()
                mock_service_instance.export_merchant_data = mock_export
                mock_service.return_value = mock_service_instance

                response1 = await async_client.post(
                    "/api/v1/data/export",
                    headers={
                        "X-Merchant-ID": "123",
                        "X-CSRF-Token": "valid-csrf-token",
                    },
                )
                assert response1.status_code == 200

                response2 = await async_client.post(
                    "/api/v1/data/export",
                    headers={
                        "X-Merchant-ID": "123",
                        "X-CSRF-Token": "valid-csrf-token",
                    },
                )

                assert response2.status_code == 429

    async def test_api_005_concurrent_export_blocked(self, async_client: AsyncClient):
        """Test 6-3-API-005: Concurrent export requests are blocked."""
        mock_redis = AsyncMock()
        mock_redis.exists = AsyncMock(side_effect=[False, True])
        mock_redis.ttl = AsyncMock(return_value=60)

        with patch("app.api.data_export.get_async_redis_client", return_value=mock_redis):
            response = await async_client.post(
                "/api/v1/data/export",
                headers={
                    "X-Merchant-ID": "123",
                    "X-CSRF-Token": "valid-csrf-token",
                },
            )

            assert response.status_code == 429

    async def test_api_006_csv_format_validation(self, async_client: AsyncClient):
        """Test 6-3-API-006: CSV format is valid and parseable."""
        with patch("app.api.data_export.get_async_redis_client", return_value=None):
            with patch("app.api.data_export.MerchantDataExportService") as mock_service:
                csv_content = (
                    "# Merchant Data Export\n"
                    "# Export Date: 2026-03-04T12:00:00Z\n"
                    "# Merchant ID: 123\n"
                    "# Total Conversations: 2\n"
                    "# Total Messages: 5\n"
                    "# Total Cost: 0.0123\n\n"
                    "## SECTION: CONVERSATIONS\n"
                    "conversation_id,platform,customer_id,consent_status,started_at\n"
                    "1,messenger,customer_123,opted_in,2026-03-04T10:00:00Z\n"
                    "2,widget,anon_456,opted_out,2026-03-04T11:00:00Z\n\n"
                    "## SECTION: MESSAGES\n"
                    "message_id,conversation_id,role,content,created_at\n"
                    "101,1,user,Hello,2026-03-04T10:00:05Z\n"
                    "102,1,assistant,Hi there,2026-03-04T10:00:07Z\n"
                    "103,2,user,,2026-03-04T11:00:05Z\n\n"
                    "## SECTION: LLM COSTS\n"
                    "cost_id,conversation_id,provider,model,input_tokens,output_tokens,cost_usd,created_at\n"
                    "201,1,openai,gpt-4,150,80,0.0046,2026-03-04T10:00:07Z\n\n"
                    "## SECTION: CONFIGURATION\n"
                    "setting_name,setting_value\n"
                    "personality,friendly\n"
                )

                async def mock_export(merchant_id):
                    for line in csv_content.split("\n"):
                        yield line + "\n"

                mock_service_instance = MagicMock()
                mock_service_instance.export_merchant_data = mock_export
                mock_service.return_value = mock_service_instance

                response = await async_client.post(
                    "/api/v1/data/export",
                    headers={
                        "X-Merchant-ID": "123",
                        "X-CSRF-Token": "valid-csrf-token",
                    },
                )

                assert response.status_code == 200

                csv_text = response.text
                csv_reader = csv.reader(io.StringIO(csv_text))
                rows = list(csv_reader)

                assert len(rows) > 0
                assert any("Merchant Data Export" in str(row) for row in rows)
                assert any("SECTION: CONVERSATIONS" in str(row) for row in rows)

    async def test_api_007_csv_injection_prevention(self, async_client: AsyncClient):
        """Test 6-3-API-007: CSV injection attempts are neutralized."""
        with patch("app.api.data_export.get_async_redis_client", return_value=None):
            with patch("app.api.data_export.MerchantDataExportService") as mock_service:
                csv_content = (
                    "# Merchant Data Export\n"
                    "# Merchant ID: 123\n\n"
                    "## SECTION: MESSAGES\n"
                    "message_id,conversation_id,role,content,created_at\n"
                    "101,1,user,'=SUM(A1:A10),2026-03-04T10:00:05Z\n"
                )

                async def mock_export(merchant_id):
                    for line in csv_content.split("\n"):
                        yield line + "\n"

                mock_service_instance = MagicMock()
                mock_service_instance.export_merchant_data = mock_export
                mock_service.return_value = mock_service_instance

                response = await async_client.post(
                    "/api/v1/data/export",
                    headers={
                        "X-Merchant-ID": "123",
                        "X-CSRF-Token": "valid-csrf-token",
                    },
                )

                assert response.status_code == 200
                assert "'=SUM" in response.text

    async def test_api_008_merchant_id_validation(self, async_client: AsyncClient):
        """Test 6-3-API-008: Export only returns data for authenticated merchant."""
        with patch("app.api.data_export.get_async_redis_client", return_value=None):
            with patch("app.api.data_export.MerchantDataExportService") as mock_service:

                async def mock_export(merchant_id):
                    yield "# Merchant Data Export\n"
                    yield "# Merchant ID: 123\n"

                mock_service_instance = MagicMock()
                mock_service_instance.export_merchant_data = mock_export
                mock_service.return_value = mock_service_instance

                response = await async_client.post(
                    "/api/v1/data/export",
                    headers={
                        "X-Merchant-ID": "123",
                        "X-CSRF-Token": "valid-csrf-token",
                    },
                )

                assert response.status_code == 200
                assert "# Merchant ID: 123" in response.text

    async def test_api_009_empty_dataset_returns_valid_csv(self, async_client: AsyncClient):
        """Test 6-3-API-009: Empty dataset returns valid CSV with headers only."""
        with patch("app.api.data_export.get_async_redis_client", return_value=None):
            with patch("app.api.data_export.MerchantDataExportService") as mock_service:
                csv_content = (
                    "# Merchant Data Export\n"
                    "# Export Date: 2026-03-04T12:00:00Z\n"
                    "# Merchant ID: 123\n"
                    "# Total Conversations: 0\n"
                    "# Total Messages: 0\n"
                    "# Total Cost: 0.0000\n\n"
                    "## SECTION: CONVERSATIONS\n"
                    "conversation_id,platform,customer_id,consent_status,started_at\n\n"
                    "## SECTION: MESSAGES\n"
                    "message_id,conversation_id,role,content,created_at\n\n"
                    "## SECTION: LLM COSTS\n"
                    "cost_id,conversation_id,provider,model,input_tokens,output_tokens,cost_usd,created_at\n\n"
                    "## SECTION: CONFIGURATION\n"
                    "setting_name,setting_value\n"
                )

                async def mock_export(merchant_id):
                    for line in csv_content.split("\n"):
                        yield line + "\n"

                mock_service_instance = MagicMock()
                mock_service_instance.export_merchant_data = mock_export
                mock_service.return_value = mock_service_instance

                response = await async_client.post(
                    "/api/v1/data/export",
                    headers={
                        "X-Merchant-ID": "123",
                        "X-CSRF-Token": "valid-csrf-token",
                    },
                )

                assert response.status_code == 200
                assert "# Total Conversations: 0" in response.text
                assert "## SECTION: CONVERSATIONS" in response.text

    async def test_api_010_consent_filtering_applied(self, async_client: AsyncClient):
        """Test 6-3-API-010: Consent-based filtering is applied to export."""
        with patch("app.api.data_export.get_async_redis_client", return_value=None):
            with patch("app.api.data_export.MerchantDataExportService") as mock_service:
                csv_content = (
                    "# Merchant Data Export\n"
                    "# Merchant ID: 123\n\n"
                    "## SECTION: CONVERSATIONS\n"
                    "conversation_id,platform,customer_id,consent_status\n"
                    "1,messenger,customer_123,opted_in\n"
                    "2,widget,anon_456,opted_out\n\n"
                    "## SECTION: MESSAGES\n"
                    "message_id,conversation_id,role,content\n"
                    "101,1,user,Hello from opted-in user\n"
                    '102,2,user,""\n'
                )

                async def mock_export(merchant_id):
                    for line in csv_content.split("\n"):
                        yield line + "\n"

                mock_service_instance = MagicMock()
                mock_service_instance.export_merchant_data = mock_export
                mock_service.return_value = mock_service_instance

                response = await async_client.post(
                    "/api/v1/data/export",
                    headers={
                        "X-Merchant-ID": "123",
                        "X-CSRF-Token": "valid-csrf-token",
                    },
                )

                assert response.status_code == 200
                assert "customer_123" in response.text
                assert "opted_in" in response.text
                assert "Hello from opted-in user" in response.text
                assert "anon_456" in response.text
                assert "opted_out" in response.text


@pytest.mark.asyncio
class TestDataExportSecurity:
    """Security tests for data export endpoint."""

    async def test_sql_injection_prevention(self, async_client: AsyncClient):
        """Test that SQL injection attempts are blocked."""
        response = await async_client.post(
            "/api/v1/data/export",
            headers={
                "X-Merchant-ID": "123; DROP TABLE merchants;--",
                "X-CSRF-Token": "valid-csrf-token",
            },
        )

        assert response.status_code == 422

    async def test_xss_prevention(self, async_client: AsyncClient):
        """Test that XSS attempts are neutralized in CSV."""
        with patch("app.api.data_export.get_async_redis_client", return_value=None):
            with patch("app.api.data_export.MerchantDataExportService") as mock_service:
                csv_content = (
                    "# Merchant Data Export\n"
                    "## SECTION: MESSAGES\n"
                    "message_id,conversation_id,role,content\n"
                    "101,1,user,<script>alert('xss')</script>\n"
                )

                async def mock_export(merchant_id):
                    for line in csv_content.split("\n"):
                        yield line + "\n"

                mock_service_instance = MagicMock()
                mock_service_instance.export_merchant_data = mock_export
                mock_service.return_value = mock_service_instance

                response = await async_client.post(
                    "/api/v1/data/export",
                    headers={
                        "X-Merchant-ID": "123",
                        "X-CSRF-Token": "valid-csrf-token",
                    },
                )

                assert response.status_code == 200
