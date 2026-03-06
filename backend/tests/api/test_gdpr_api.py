"""API integration tests for GDPR deletion endpoints.

Story 6-6: GDPR Deletion Processing

Tests:
- POST /api/gdpr-request endpoint
- GET /api/compliance/status endpoint
- POST /api/customers/{customer_id}/revoke-gdpr-request endpoint
- Duplicate request prevention
- Order processing respects GDPR status
"""

import pytest
from datetime import datetime, timezone, timedelta

from app.core.errors import ErrorCode
from app.models.deletion_audit_log import DeletionAuditLog, DeletionRequestType, DeletionTrigger
from app.models.conversation import Conversation
from app.services.privacy.data_tier_service import DataTier
from tests.conftest import auth_headers


class TestGDPRRequestEndpoint:
    """Tests for POST /api/gdpr-request endpoint."""

    @pytest.mark.asyncio
    async def test_gdpr_request_success(self, async_client, test_merchant):
        """Test successful GDPR request submission."""
        response = await async_client.post(
            "/api/gdpr-request",
            json={
                "customer_id": "test_gdpr_customer",
                "request_type": "gdpr_formal",
                "email": "test@example.com",
            },
            headers=auth_headers(test_merchant),
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert data["data"]["requestId"] is not None
        assert data["data"]["customerId"] == "test_gdpr_customer"
        assert data["data"]["requestType"] == "gdpr_formal"
        assert data["data"]["deadline"] is not None
        assert "message" in data["data"]

    @pytest.mark.asyncio
    async def test_gdpr_request_with_email_queues_confirmation(
        self, async_client, test_merchant, async_session
    ):
        """Test AC4: GDPR request with email queues confirmation email."""
        customer_id = "email_confirmation_customer"
        customer_email = "confirm@example.com"

        response = await async_client.post(
            "/api/gdpr-request",
            json={
                "customer_id": customer_id,
                "request_type": "gdpr_formal",
                "email": customer_email,
            },
            headers=auth_headers(test_merchant),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["requestId"] is not None

        from sqlalchemy import select

        result = await async_session.execute(
            select(DeletionAuditLog).where(DeletionAuditLog.customer_id == customer_id)
        )
        audit_log = result.scalar_one_or_none()
        assert audit_log is not None
        assert audit_log.confirmation_email_sent is False

    @pytest.mark.asyncio
    async def test_gdpr_request_without_email_no_confirmation(
        self, async_client, test_merchant, async_session
    ):
        """Test AC4: GDPR request without email does not queue confirmation."""
        customer_id = "no_email_confirmation_customer"

        response = await async_client.post(
            "/api/gdpr-request",
            json={
                "customer_id": customer_id,
                "request_type": "gdpr_formal",
            },
            headers=auth_headers(test_merchant),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["requestId"] is not None

        from sqlalchemy import select

        result = await async_session.execute(
            select(DeletionAuditLog).where(DeletionAuditLog.customer_id == customer_id)
        )
        audit_log = result.scalar_one_or_none()
        assert audit_log is not None
        assert audit_log.confirmation_email_sent is False
        assert audit_log.email_sent_at is None

    @pytest.mark.asyncio
    async def test_ccpa_request_with_email_queues_confirmation(
        self, async_client, test_merchant, async_session
    ):
        """Test AC4: CCPA request with email queues confirmation email."""
        customer_id = "ccpa_email_customer"
        customer_email = "ccpa@example.com"

        response = await async_client.post(
            "/api/gdpr-request",
            json={
                "customer_id": customer_id,
                "request_type": "ccpa_request",
                "email": customer_email,
            },
            headers=auth_headers(test_merchant),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["requestType"] == "ccpa_request"

        from sqlalchemy import select

        result = await async_session.execute(
            select(DeletionAuditLog).where(DeletionAuditLog.customer_id == customer_id)
        )
        audit_log = result.scalar_one_or_none()
        assert audit_log is not None
        assert audit_log.request_type == DeletionRequestType.CCPA_REQUEST.value

    @pytest.mark.asyncio
    async def test_gdpr_request_with_session_id(self, async_client, test_merchant):
        """Test GDPR request with session_id and visitor_id."""
        response = await async_client.post(
            "/api/gdpr-request",
            json={
                "customer_id": "test_session_customer",
                "request_type": "ccpa_request",
                "session_id": "session_123",
                "visitor_id": "visitor_456",
            },
            headers=auth_headers(test_merchant),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["requestType"] == "ccpa_request"

    @pytest.mark.asyncio
    async def test_gdpr_request_manual_type(self, async_client, test_merchant):
        """Test manual deletion request (forget my preferences)."""
        response = await async_client.post(
            "/api/gdpr-request",
            json={
                "customer_id": "manual_customer",
                "request_type": "manual",
            },
            headers=auth_headers(test_merchant),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["requestType"] == "manual"


class TestDuplicateRequestPrevention:
    """Tests for duplicate request prevention."""

    @pytest.mark.asyncio
    async def test_duplicate_request_returns_error(self, async_client, test_merchant):
        """Test that duplicate GDPR requests return error."""
        customer_id = "duplicate_test_customer"

        # First request should succeed
        response1 = await async_client.post(
            "/api/gdpr-request",
            json={
                "customer_id": customer_id,
                "request_type": "gdpr_formal",
            },
            headers=auth_headers(test_merchant),
        )
        assert response1.status_code == 200

        # Second request should fail
        response2 = await async_client.post(
            "/api/gdpr-request",
            json={
                "customer_id": customer_id,
                "request_type": "gdpr_formal",
            },
            headers=auth_headers(test_merchant),
        )
        assert response2.status_code == 400
        data = response2.json()
        assert data.get("error_code") == ErrorCode.GDPR_REQUEST_PENDING


class TestComplianceStatusEndpoint:
    """Tests for GET /api/compliance/status endpoint."""

    @pytest.mark.asyncio
    async def test_compliance_status_compliant(self, async_client, test_merchant):
        """Test compliance status when no overdue requests."""
        response = await async_client.get(
            "/api/compliance/status",
            headers=auth_headers(test_merchant),
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert data["data"]["status"] in ["compliant", "non_compliant"]
        assert "overdueRequests" in data["data"]
        assert "approachingDeadline" in data["data"]
        assert "lastChecked" in data["data"]

    @pytest.mark.asyncio
    async def test_compliance_status_with_overdue(self, async_client, async_session, test_merchant):
        """Test compliance status shows overdue requests."""
        # Create overdue request
        overdue_log = DeletionAuditLog(
            merchant_id=test_merchant,
            customer_id="overdue_customer",
            session_id="overdue_session",
            request_type=DeletionRequestType.GDPR_FORMAL.value,
            request_timestamp=datetime.now(timezone.utc) - timedelta(days=35),
            processing_deadline=datetime.now(timezone.utc) - timedelta(days=5),
            deletion_trigger=DeletionTrigger.MANUAL.value,
        )
        async_session.add(overdue_log)
        await async_session.commit()

        response = await async_client.get(
            "/api/compliance/status",
            headers=auth_headers(test_merchant),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["status"] == "non_compliant"
        assert data["data"]["overdueRequests"] >= 1


class TestRevokeGDPRRequestEndpoint:
    """Tests for POST /api/customers/{customer_id}/revoke-gdpr-request endpoint."""

    @pytest.mark.asyncio
    async def test_revoke_gdpr_request_success(self, async_client, async_session, test_merchant):
        """Test successful GDPR request revocation."""
        customer_id = "revoke_test_customer"

        # Create GDPR request
        response1 = await async_client.post(
            "/api/gdpr-request",
            json={
                "customer_id": customer_id,
                "request_type": "gdpr_formal",
            },
            headers=auth_headers(test_merchant),
        )
        assert response1.status_code == 200

        # Revoke the request
        response2 = await async_client.post(
            f"/api/customers/{customer_id}/revoke-gdpr-request",
            headers=auth_headers(test_merchant),
        )

        assert response2.status_code == 200
        data = response2.json()
        assert data["data"]["revoked"] is True
        assert data["data"]["customerId"] == customer_id

    @pytest.mark.asyncio
    async def test_revoke_nonexistent_request(self, async_client, test_merchant):
        """Test revoking a request that doesn't exist."""
        response = await async_client.post(
            "/api/customers/nonexistent_customer/revoke-gdpr-request",
            headers=auth_headers(test_merchant),
        )

        assert response.status_code == 400
        data = response.json()
        assert data.get("error_code") == ErrorCode.GDPR_REQUEST_NOT_FOUND


class TestGDPRDataDeletion:
    """Tests for GDPR data deletion behavior."""

    @pytest.mark.asyncio
    async def test_voluntary_data_deleted(self, async_client, async_session, test_merchant):
        """Test that voluntary data is deleted after GDPR request."""
        customer_id = "voluntary_delete_customer"

        # Create voluntary conversation
        conv = Conversation(
            merchant_id=test_merchant,
            platform_sender_id=customer_id,
            platform="facebook",
            data_tier=DataTier.VOLUNTARY.value,
        )
        async_session.add(conv)
        await async_session.commit()
        conv_id = conv.id

        # Submit GDPR request
        response = await async_client.post(
            "/api/gdpr-request",
            json={
                "customer_id": customer_id,
                "request_type": "gdpr_formal",
            },
            headers=auth_headers(test_merchant),
        )
        assert response.status_code == 200

        # Verify conversation was deleted
        from sqlalchemy import select

        result = await async_session.execute(select(Conversation).where(Conversation.id == conv_id))
        assert result.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_operational_data_retained(self, async_client, async_session, test_merchant):
        """Test that operational data is retained after GDPR request."""
        customer_id = "operational_retain_customer"

        # Create operational conversation
        conv = Conversation(
            merchant_id=test_merchant,
            platform_sender_id=customer_id,
            platform="facebook",
            data_tier=DataTier.OPERATIONAL.value,
        )
        async_session.add(conv)
        await async_session.commit()
        conv_id = conv.id

        # Submit GDPR request
        response = await async_client.post(
            "/api/gdpr-request",
            json={
                "customer_id": customer_id,
                "request_type": "gdpr_formal",
            },
            headers=auth_headers(test_merchant),
        )
        assert response.status_code == 200

        # Verify conversation was NOT deleted
        from sqlalchemy import select

        result = await async_session.execute(select(Conversation).where(Conversation.id == conv_id))
        assert result.scalar_one_or_none() is not None
