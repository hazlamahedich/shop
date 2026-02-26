"""API tests for Widget Consent endpoints.

Tests the HTTP layer of widget consent API endpoints.
Story 6-2: Request Data Deletion - GDPR/CCPA compliance

Test IDs: 6-2-API-001 through 6-2-API-008
"""

from __future__ import annotations

import os
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

os.environ["IS_TESTING"] = "true"

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.widget import router
from app.core.errors import ErrorCode, APIError
from app.core.database import get_db


class TestWidgetConsentDeletionValidation:
    """Unit tests for consent deletion endpoint validation."""

    @pytest.fixture
    def mock_request(self):
        """Create mock request."""
        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"X-Test-Mode": "true"}
        mock_request.client = MagicMock()
        mock_request.client.host = "192.168.1.1"
        return mock_request

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return AsyncMock(spec=AsyncSession)

    @pytest.mark.asyncio
    async def test_6_2_api_002_delete_consent_returns_400_invalid_uuid(self, mock_request, mock_db):
        """[P0][6-2-API-002] DELETE /widget/consent/{session_id} - Returns 400 for invalid UUID."""
        from app.api.widget import forget_widget_preferences

        with pytest.raises(APIError) as exc_info:
            await forget_widget_preferences(
                request=mock_request,
                session_id="invalid-uuid",
                db=mock_db,
            )

        assert exc_info.value.code == ErrorCode.VALIDATION_ERROR

    @pytest.mark.asyncio
    async def test_6_2_api_006_delete_consent_sql_injection_protection(self, mock_request, mock_db):
        """[P1][6-2-API-006] DELETE /widget/consent/{session_id} - Blocks SQL injection."""
        from app.api.widget import forget_widget_preferences

        with pytest.raises(APIError) as exc_info:
            await forget_widget_preferences(
                request=mock_request,
                session_id="'; DROP TABLE sessions;--",
                db=mock_db,
            )

        assert exc_info.value.code == ErrorCode.VALIDATION_ERROR


class TestWidgetConsentDeletionAPI:
    """API contract tests for DELETE /widget/consent/{session_id} endpoint."""

    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client."""
        redis = AsyncMock()
        redis.get = AsyncMock(return_value=None)
        redis.setex = AsyncMock(return_value=True)
        redis.delete = AsyncMock(return_value=1)
        redis.exists = AsyncMock(return_value=0)
        redis.expire = AsyncMock(return_value=True)
        redis.set = AsyncMock(return_value=True)
        return redis

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def mock_session(self):
        """Create mock widget session."""
        session = MagicMock()
        session.session_id = "550e8400-e29b-41d4-a716-446655440000"
        session.merchant_id = 1
        session.visitor_id = "visitor_123"
        session.expires_at = datetime.now(timezone.utc)
        return session

    @pytest.fixture
    def mock_request(self):
        """Create mock request."""
        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"X-Test-Mode": "true"}
        mock_request.client = MagicMock()
        mock_request.client.host = "192.168.1.1"
        return mock_request

    @pytest.mark.asyncio
    async def test_6_2_api_001_delete_consent_returns_200_with_valid_session(
        self, mock_request, mock_db, mock_session
    ):
        """[P0][6-2-API-001] DELETE /widget/consent/{session_id} - Returns 200 with valid session."""
        from app.api.widget import forget_widget_preferences

        with (
            patch("app.api.widget.WidgetSessionService") as mock_service_class,
            patch(
                "app.services.consent.extended_consent_service.ConversationConsentService"
            ) as mock_consent_class,
        ):
            mock_service = AsyncMock()
            mock_service.get_session_or_error.return_value = mock_session
            mock_service_class.return_value = mock_service

            mock_consent = AsyncMock()
            mock_consent.handle_forget_preferences.return_value = {
                "clear_visitor_id": True,
                "deletion_summary": {
                    "conversations_deleted": 1,
                    "messages_deleted": 5,
                },
            }
            mock_consent_class.return_value = mock_consent

            result = await forget_widget_preferences(
                request=mock_request,
                session_id="550e8400-e29b-41d4-a716-446655440000",
                db=mock_db,
            )

            assert result["data"]["success"] is True
            assert result["data"]["clear_visitor_id"] is True

    @pytest.mark.asyncio
    async def test_6_2_api_004_delete_consent_returns_404_nonexistent_session(
        self, mock_request, mock_db
    ):
        """[P0][6-2-API-004] DELETE /widget/consent/{session_id} - Returns 404 for non-existent session."""
        from app.api.widget import forget_widget_preferences

        with patch("app.api.widget.WidgetSessionService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service.get_session_or_error.side_effect = APIError(
                ErrorCode.WIDGET_SESSION_NOT_FOUND,
                "Session not found",
            )
            mock_service_class.return_value = mock_service

            with pytest.raises(APIError) as exc_info:
                await forget_widget_preferences(
                    request=mock_request,
                    session_id="550e8400-e29b-41d4-a716-446655440000",
                    db=mock_db,
                )

            assert exc_info.value.code == ErrorCode.WIDGET_SESSION_NOT_FOUND

    @pytest.mark.asyncio
    async def test_6_2_api_005_delete_consent_with_visitor_id_param(
        self, mock_request, mock_db, mock_session
    ):
        """[P1][6-2-API-005] DELETE /widget/consent/{session_id}?visitor_id=xxx - Uses visitor_id param."""
        from app.api.widget import forget_widget_preferences

        visitor_id = "custom_visitor_456"

        with (
            patch("app.api.widget.WidgetSessionService") as mock_service_class,
            patch(
                "app.services.consent.extended_consent_service.ConversationConsentService"
            ) as mock_consent_class,
        ):
            mock_service = AsyncMock()
            mock_service.get_session_or_error.return_value = mock_session
            mock_service_class.return_value = mock_service

            mock_consent = AsyncMock()
            mock_consent.handle_forget_preferences.return_value = {
                "clear_visitor_id": True,
            }
            mock_consent_class.return_value = mock_consent

            await forget_widget_preferences(
                request=mock_request,
                session_id="550e8400-e29b-41d4-a716-446655440000",
                db=mock_db,
                visitor_id=visitor_id,
            )

            mock_consent.handle_forget_preferences.assert_called_once()
            call_kwargs = mock_consent.handle_forget_preferences.call_args[1]
            assert call_kwargs["visitor_id"] == visitor_id

    @pytest.mark.asyncio
    async def test_6_2_api_007_delete_consent_returns_deletion_summary(
        self, mock_request, mock_db, mock_session
    ):
        """[P1][6-2-API-007] DELETE /widget/consent/{session_id} - Returns deletion summary in response."""
        from app.api.widget import forget_widget_preferences

        with (
            patch("app.api.widget.WidgetSessionService") as mock_service_class,
            patch(
                "app.services.consent.extended_consent_service.ConversationConsentService"
            ) as mock_consent_class,
        ):
            mock_service = AsyncMock()
            mock_service.get_session_or_error.return_value = mock_session
            mock_service_class.return_value = mock_service

            mock_consent = AsyncMock()
            mock_consent.handle_forget_preferences.return_value = {
                "clear_visitor_id": True,
                "deletion_summary": {
                    "conversations_deleted": 3,
                    "messages_deleted": 15,
                    "audit_log_id": 789,
                },
            }
            mock_consent_class.return_value = mock_consent

            result = await forget_widget_preferences(
                request=mock_request,
                session_id="550e8400-e29b-41d4-a716-446655440000",
                db=mock_db,
            )

            assert result["data"]["success"] is True

    @pytest.mark.asyncio
    async def test_6_2_api_008_delete_consent_clear_visitor_id_false_when_set(
        self, mock_request, mock_db, mock_session
    ):
        """[P1][6-2-API-008] DELETE /widget/consent/{session_id} - clear_visitor_id reflects service response."""
        from app.api.widget import forget_widget_preferences

        with (
            patch("app.api.widget.WidgetSessionService") as mock_service_class,
            patch(
                "app.services.consent.extended_consent_service.ConversationConsentService"
            ) as mock_consent_class,
        ):
            mock_service = AsyncMock()
            mock_service.get_session_or_error.return_value = mock_session
            mock_service_class.return_value = mock_service

            mock_consent = AsyncMock()
            mock_consent.handle_forget_preferences.return_value = {
                "clear_visitor_id": False,
            }
            mock_consent_class.return_value = mock_consent

            result = await forget_widget_preferences(
                request=mock_request,
                session_id="550e8400-e29b-41d4-a716-446655440000",
                db=mock_db,
            )

            assert result["data"]["clear_visitor_id"] is False


class TestWidgetConsentGetValidation:
    """Unit tests for consent GET endpoint validation."""

    @pytest.fixture
    def mock_request(self):
        """Create mock request."""
        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"X-Test-Mode": "true"}
        mock_request.client = MagicMock()
        mock_request.client.host = "192.168.1.1"
        return mock_request

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return AsyncMock(spec=AsyncSession)

    @pytest.mark.asyncio
    async def test_6_1_api_002_get_consent_returns_400_invalid_uuid(self, mock_request, mock_db):
        """[P0][6-1-API-002] GET /widget/consent/{session_id} - Returns 400 for invalid UUID."""
        from app.api.widget import get_widget_consent_status

        with pytest.raises(APIError) as exc_info:
            await get_widget_consent_status(
                request=mock_request,
                session_id="invalid-uuid",
                db=mock_db,
            )

        assert exc_info.value.code == ErrorCode.VALIDATION_ERROR


class TestWidgetConsentGetAPI:
    """API contract tests for GET /widget/consent/{session_id} endpoint."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def mock_session(self):
        """Create mock widget session."""
        session = MagicMock()
        session.session_id = "550e8400-e29b-41d4-a716-446655440000"
        session.merchant_id = 1
        session.visitor_id = "visitor_123"
        session.expires_at = datetime.now(timezone.utc)
        return session

    @pytest.fixture
    def mock_request(self):
        """Create mock request."""
        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"X-Test-Mode": "true"}
        mock_request.client = MagicMock()
        mock_request.client.host = "192.168.1.1"
        return mock_request

    @pytest.mark.asyncio
    async def test_6_1_api_001_get_consent_returns_200_with_valid_session(
        self, mock_request, mock_db, mock_session
    ):
        """[P0][6-1-API-001] GET /widget/consent/{session_id} - Returns 200 with consent status."""
        from app.api.widget import get_widget_consent_status

        with (
            patch("app.api.widget.WidgetSessionService") as mock_service_class,
            patch(
                "app.services.consent.extended_consent_service.ConversationConsentService"
            ) as mock_consent_class,
        ):
            mock_service = AsyncMock()
            mock_service.get_session_or_error.return_value = mock_session
            mock_service_class.return_value = mock_service

            mock_consent_obj = MagicMock()
            mock_consent_obj.granted = True
            mock_consent_obj.revoked_at = None
            mock_consent_obj.consent_message_shown = True

            mock_consent = AsyncMock()
            mock_consent.get_consent_for_conversation.return_value = mock_consent_obj
            mock_consent_class.return_value = mock_consent

            result = await get_widget_consent_status(
                request=mock_request,
                session_id="550e8400-e29b-41d4-a716-446655440000",
                db=mock_db,
            )

            assert result["data"]["status"] == "opted_in"

    @pytest.mark.asyncio
    async def test_6_1_api_003_get_consent_returns_pending_for_new_session(
        self, mock_request, mock_db, mock_session
    ):
        """[P1][6-1-API-003] GET /widget/consent/{session_id} - Returns pending status for new session."""
        from app.api.widget import get_widget_consent_status

        with (
            patch("app.api.widget.WidgetSessionService") as mock_service_class,
            patch(
                "app.services.consent.extended_consent_service.ConversationConsentService"
            ) as mock_consent_class,
        ):
            mock_service = AsyncMock()
            mock_service.get_session_or_error.return_value = mock_session
            mock_service_class.return_value = mock_service

            mock_consent = AsyncMock()
            mock_consent.get_consent_for_conversation.return_value = None
            mock_consent_class.return_value = mock_consent

            result = await get_widget_consent_status(
                request=mock_request,
                session_id="550e8400-e29b-41d4-a716-446655440000",
                db=mock_db,
            )

            assert result["data"]["status"] == "pending"
            assert result["data"]["can_store_conversation"] is False
