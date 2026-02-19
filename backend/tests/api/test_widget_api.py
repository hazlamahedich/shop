"""API contract tests for Widget endpoints.

Tests the HTTP layer of widget API endpoints using FastAPI TestClient.
Covers session creation, messaging, configuration, and session management.

Story 5-2: Widget Session Management
"""

from __future__ import annotations

import os
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

os.environ["IS_TESTING"] = "true"

from fastapi.testclient import TestClient


class TestWidgetSessionAPI:
    """API contract tests for /widget/session endpoint."""

    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client."""
        redis = AsyncMock()
        storage = {}

        async def mock_get(key):
            return storage.get(key)

        async def mock_setex(key, ttl, value):
            storage[key] = value
            return True

        async def mock_delete(*keys):
            count = 0
            for key in keys:
                if key in storage:
                    del storage[key]
                    count += 1
            return count

        async def mock_exists(key):
            return 1 if key in storage else 0

        async def mock_expire(key, ttl):
            return key in storage

        async def mock_ttl(key):
            return 3600 if key in storage else -1

        async def mock_scan(cursor=0, match=None, count=100):
            matching_keys = []
            if match and match.endswith("*"):
                prefix = match[:-1]
                for key in storage:
                    if key.startswith(prefix):
                        matching_keys.append(key)
            return 0, matching_keys

        redis.get = mock_get
        redis.setex = mock_setex
        redis.delete = mock_delete
        redis.exists = mock_exists
        redis.expire = mock_expire
        redis.ttl = mock_ttl
        redis.scan = mock_scan
        redis.storage = storage

        return redis

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        from sqlalchemy.ext.asyncio import AsyncSession

        db = MagicMock(spec=AsyncSession)
        db.execute = AsyncMock()
        return db

    @pytest.fixture
    def mock_merchant(self):
        """Create mock merchant with widget enabled."""
        merchant = MagicMock()
        merchant.id = 1
        merchant.bot_name = "Test Bot"
        merchant.business_name = "Test Store"
        merchant.business_description = "Test description"
        merchant.widget_config = {"enabled": True, "rate_limit": None}
        merchant.llm_configuration = None
        return merchant

    @pytest.fixture
    def mock_merchant_with_rate_limit(self):
        """Create mock merchant with custom rate limit."""
        merchant = MagicMock()
        merchant.id = 2
        merchant.bot_name = "Rate Limited Bot"
        merchant.business_name = "Rate Limited Store"
        merchant.business_description = None
        merchant.widget_config = {"enabled": True, "rate_limit": 5}
        merchant.llm_configuration = None
        return merchant

    @pytest.fixture
    def mock_merchant_disabled(self):
        """Create mock merchant with widget disabled."""
        merchant = MagicMock()
        merchant.id = 3
        merchant.bot_name = "Disabled Bot"
        merchant.business_name = "Disabled Store"
        merchant.business_description = None
        merchant.widget_config = {"enabled": False}
        merchant.llm_configuration = None
        return merchant

    @pytest.mark.asyncio
    async def test_p0_create_session_returns_200_with_valid_merchant(
        self, mock_redis, mock_db, mock_merchant
    ):
        """[P0] POST /widget/session - Creates session with valid merchant_id."""
        from app.core.errors import ErrorCode

        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_merchant
        mock_db.execute.return_value = mock_result

        with (
            patch("app.api.widget.WidgetSessionService") as mock_service_class,
            patch("app.api.widget.get_db", return_value=mock_db),
        ):
            mock_service = AsyncMock()
            mock_session = MagicMock()
            mock_session.session_id = "test-uuid-1234"
            mock_session.expires_at = datetime.now(timezone.utc)
            mock_service.create_session.return_value = mock_session
            mock_service_class.return_value = mock_service

            from app.api.widget import create_widget_session
            from fastapi import Request
            from app.schemas.widget import CreateSessionRequest

            mock_request = MagicMock(spec=Request)
            mock_request.headers = {"User-Agent": "Test Agent"}
            mock_request.client = MagicMock()
            mock_request.client.host = "192.168.1.1"

            session_request = CreateSessionRequest(merchant_id=1)

            result = await create_widget_session(
                request=mock_request,
                session_request=session_request,
                db=mock_db,
            )

            assert result.data.session_id == "test-uuid-1234"
            assert result.data.expires_at is not None

    @pytest.mark.asyncio
    async def test_p0_create_session_returns_404_for_invalid_merchant(self, mock_redis, mock_db):
        """[P0] POST /widget/session - Returns 404 for non-existent merchant."""
        from app.core.errors import APIError, ErrorCode

        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db.execute.return_value = mock_result

        from app.api.widget import create_widget_session
        from fastapi import Request
        from app.schemas.widget import CreateSessionRequest

        mock_request = MagicMock(spec=Request)
        mock_request.headers = {}
        mock_request.client = MagicMock()
        mock_request.client.host = "192.168.1.1"

        session_request = CreateSessionRequest(merchant_id=99999)

        with pytest.raises(APIError) as exc_info:
            await create_widget_session(
                request=mock_request,
                session_request=session_request,
                db=mock_db,
            )

        assert exc_info.value.code == ErrorCode.MERCHANT_NOT_FOUND

    @pytest.mark.asyncio
    async def test_p0_send_message_processes_with_valid_session(
        self, mock_redis, mock_db, mock_merchant
    ):
        """[P0] POST /widget/message - Processes message with valid session."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_merchant
        mock_db.execute.return_value = mock_result

        valid_uuid = "550e8400-e29b-41d4-a716-446655440000"
        mock_session = MagicMock()
        mock_session.session_id = valid_uuid
        mock_session.merchant_id = 1
        mock_session.expires_at = datetime.now(timezone.utc)

        with (
            patch("app.api.widget.WidgetSessionService") as mock_service_class,
            patch("app.api.widget.WidgetMessageService") as mock_msg_service_class,
        ):
            mock_service = AsyncMock()
            mock_service.get_session_or_error.return_value = mock_session
            mock_service_class.return_value = mock_service

            mock_msg_service = AsyncMock()
            mock_msg_service.process_message.return_value = {
                "message_id": "msg-123",
                "content": "Hello! How can I help?",
                "sender": "bot",
                "created_at": datetime.now(timezone.utc),
            }
            mock_msg_service_class.return_value = mock_msg_service

            from app.api.widget import send_widget_message
            from fastapi import Request
            from app.schemas.widget import SendMessageRequest

            mock_request = MagicMock(spec=Request)
            mock_request.headers = {}
            mock_request.client = MagicMock()
            mock_request.client.host = "192.168.1.1"

            message_request = SendMessageRequest(
                session_id=valid_uuid,
                message="Hello",
            )

            result = await send_widget_message(
                request=mock_request,
                message_request=message_request,
                db=mock_db,
            )

            assert result.data.content == "Hello! How can I help?"
            assert result.data.sender == "bot"

    @pytest.mark.asyncio
    async def test_p0_send_message_returns_401_for_invalid_session(self, mock_redis, mock_db):
        """[P0] POST /widget/message - Returns 404 for non-existent session."""
        from app.core.errors import APIError, ErrorCode

        valid_uuid = "550e8400-e29b-41d4-a716-446655440000"

        with patch("app.api.widget.WidgetSessionService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service.get_session_or_error.side_effect = APIError(
                ErrorCode.WIDGET_SESSION_NOT_FOUND,
                "Session not found",
            )
            mock_service_class.return_value = mock_service

            from app.api.widget import send_widget_message
            from fastapi import Request
            from app.schemas.widget import SendMessageRequest

            mock_request = MagicMock(spec=Request)
            mock_request.headers = {}
            mock_request.client = MagicMock()
            mock_request.client.host = "192.168.1.1"

            message_request = SendMessageRequest(
                session_id=valid_uuid,
                message="Hello",
            )

            with pytest.raises(APIError) as exc_info:
                await send_widget_message(
                    request=mock_request,
                    message_request=message_request,
                    db=mock_db,
                )

            assert exc_info.value.code == ErrorCode.WIDGET_SESSION_NOT_FOUND

    @pytest.mark.asyncio
    async def test_p1_get_config_returns_merchant_widget_config(self, mock_db, mock_merchant):
        """[P1] GET /widget/config/{merchant_id} - Returns widget configuration."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_merchant
        mock_db.execute.return_value = mock_result

        from app.api.widget import get_widget_config

        result = await get_widget_config(merchant_id=1, db=mock_db)

        assert result.data.bot_name == "Test Bot"
        assert result.data.enabled is True

    @pytest.mark.asyncio
    async def test_p1_get_config_returns_404_for_invalid_merchant(self, mock_db):
        """[P1] GET /widget/config/{merchant_id} - Returns 404 for invalid merchant."""
        from app.core.errors import APIError, ErrorCode

        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db.execute.return_value = mock_result

        from app.api.widget import get_widget_config

        with pytest.raises(APIError) as exc_info:
            await get_widget_config(merchant_id=99999, db=mock_db)

        assert exc_info.value.code == ErrorCode.MERCHANT_NOT_FOUND

    @pytest.mark.asyncio
    async def test_p1_delete_session_ends_session_successfully(self, mock_redis):
        """[P1] DELETE /widget/session/{session_id} - Ends session successfully."""
        valid_uuid = "550e8400-e29b-41d4-a716-446655440000"

        with patch("app.api.widget.WidgetSessionService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service.end_session.return_value = True
            mock_service_class.return_value = mock_service

            from app.api.widget import end_widget_session
            from fastapi import Request

            mock_request = MagicMock(spec=Request)
            mock_request.headers = {}
            mock_request.client = MagicMock()
            mock_request.client.host = "192.168.1.1"

            result = await end_widget_session(
                request=mock_request,
                session_id=valid_uuid,
            )

            assert result.data.success is True

    @pytest.mark.asyncio
    async def test_p1_delete_session_returns_404_for_invalid_session(self, mock_redis):
        """[P1] DELETE /widget/session/{session_id} - Returns 404 for non-existent session."""
        from app.core.errors import APIError, ErrorCode

        valid_uuid = "550e8400-e29b-41d4-a716-446655440000"

        with patch("app.api.widget.WidgetSessionService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service.end_session.return_value = False
            mock_service_class.return_value = mock_service

            from app.api.widget import end_widget_session
            from fastapi import Request

            mock_request = MagicMock(spec=Request)
            mock_request.headers = {}
            mock_request.client = MagicMock()
            mock_request.client.host = "192.168.1.1"

            with pytest.raises(APIError) as exc_info:
                await end_widget_session(
                    request=mock_request,
                    session_id=valid_uuid,
                )

            assert exc_info.value.code == ErrorCode.WIDGET_SESSION_NOT_FOUND

    @pytest.mark.asyncio
    async def test_p1_widget_disabled_returns_403(
        self, mock_redis, mock_db, mock_merchant_disabled
    ):
        """[P1] POST /widget/session - Returns 403 when widget is disabled."""
        from app.core.errors import APIError, ErrorCode

        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_merchant_disabled
        mock_db.execute.return_value = mock_result

        from app.api.widget import create_widget_session
        from fastapi import Request
        from app.schemas.widget import CreateSessionRequest

        mock_request = MagicMock(spec=Request)
        mock_request.headers = {}
        mock_request.client = MagicMock()
        mock_request.client.host = "192.168.1.1"

        session_request = CreateSessionRequest(merchant_id=3)

        with pytest.raises(APIError) as exc_info:
            await create_widget_session(
                request=mock_request,
                session_request=session_request,
                db=mock_db,
            )

        assert exc_info.value.code == ErrorCode.WIDGET_MERCHANT_DISABLED


class TestWidgetDomainWhitelist:
    """Unit tests for domain whitelist validation."""

    def test_p1_domain_whitelist_allows_exact_match(self):
        """[P1] Domain whitelist allows exact domain match."""
        from app.api.widget import _validate_domain_whitelist
        from fastapi import Request

        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"Origin": "https://example.com"}

        _validate_domain_whitelist(mock_request, ["example.com"])

    def test_p1_domain_whitelist_allows_subdomain(self):
        """[P1] Domain whitelist allows subdomains of allowed domains."""
        from app.api.widget import _validate_domain_whitelist
        from fastapi import Request

        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"Origin": "https://shop.example.com"}

        _validate_domain_whitelist(mock_request, ["example.com"])

    def test_p1_domain_whitelist_blocks_unauthorized_domain(self):
        """[P1] Domain whitelist blocks domains not in allowed list."""
        from app.api.widget import _validate_domain_whitelist
        from app.core.errors import APIError, ErrorCode
        from fastapi import Request

        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"Origin": "https://evil.com"}

        with pytest.raises(APIError) as exc_info:
            _validate_domain_whitelist(mock_request, ["example.com"])

        assert exc_info.value.code == ErrorCode.WIDGET_DOMAIN_NOT_ALLOWED

    def test_p1_domain_whitelist_allows_all_when_empty(self):
        """[P1] Domain whitelist allows all origins when list is empty."""
        from app.api.widget import _validate_domain_whitelist
        from fastapi import Request

        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"Origin": "https://any-domain.com"}

        _validate_domain_whitelist(mock_request, [])

    def test_p1_domain_whitelist_handles_missing_origin(self):
        """[P1] Domain whitelist handles requests without Origin header."""
        from app.api.widget import _validate_domain_whitelist
        from fastapi import Request

        mock_request = MagicMock(spec=Request)
        mock_request.headers = {}

        _validate_domain_whitelist(mock_request, ["example.com"])


class TestWidgetRateLimiting:
    """Unit tests for rate limiting helper functions."""

    def test_p2_check_rate_limit_returns_none_when_allowed(self):
        """[P2] Rate limit check returns None when client is not rate limited."""
        from app.api.widget import _check_rate_limit
        from app.core.rate_limiter import RateLimiter
        from fastapi import Request

        RateLimiter.reset_all()

        mock_request = MagicMock(spec=Request)
        mock_request.headers = {}
        mock_request.client = MagicMock()
        mock_request.client.host = "10.0.0.1"

        result = _check_rate_limit(mock_request)

        assert result is None

    def test_p2_check_merchant_rate_limit_returns_none_when_disabled(self):
        """[P2] Merchant rate limit returns None when no limit configured."""
        from app.api.widget import _check_merchant_rate_limit

        result = _check_merchant_rate_limit(merchant_id=1, rate_limit=None)

        assert result is None

    def test_p2_check_merchant_rate_limit_returns_none_when_zero(self):
        """[P2] Merchant rate limit returns None when limit is zero (disabled)."""
        from app.api.widget import _check_merchant_rate_limit

        result = _check_merchant_rate_limit(merchant_id=1, rate_limit=0)

        assert result is None


class TestWidgetSessionIdValidation:
    """Unit tests for session_id UUID validation (Story 5-7 AC3)."""

    @pytest.fixture
    def mock_request(self):
        """Create mock request."""
        from fastapi import Request

        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"X-Test-Mode": "true"}
        mock_request.client = MagicMock()
        mock_request.client.host = "192.168.1.1"
        return mock_request

    @pytest.mark.asyncio
    async def test_get_session_rejects_invalid_uuid_format(self, mock_request):
        """Invalid UUID format returns 400 VALIDATION_ERROR."""
        from app.api.widget import get_widget_session
        from app.core.errors import APIError, ErrorCode

        with pytest.raises(APIError) as exc_info:
            await get_widget_session(
                request=mock_request,
                session_id="not-a-valid-uuid",
            )

        assert exc_info.value.code == ErrorCode.VALIDATION_ERROR

    @pytest.mark.asyncio
    async def test_get_session_rejects_empty_string(self, mock_request):
        """Empty session_id returns 400 VALIDATION_ERROR."""
        from app.api.widget import get_widget_session
        from app.core.errors import APIError, ErrorCode

        with pytest.raises(APIError) as exc_info:
            await get_widget_session(
                request=mock_request,
                session_id="",
            )

        assert exc_info.value.code == ErrorCode.VALIDATION_ERROR

    @pytest.mark.asyncio
    async def test_get_session_rejects_sql_injection(self, mock_request):
        """SQL injection attempt returns 400 VALIDATION_ERROR."""
        from app.api.widget import get_widget_session
        from app.core.errors import APIError, ErrorCode

        with pytest.raises(APIError) as exc_info:
            await get_widget_session(
                request=mock_request,
                session_id="'; DROP TABLE sessions;--",
            )

        assert exc_info.value.code == ErrorCode.VALIDATION_ERROR

    @pytest.mark.asyncio
    async def test_end_session_rejects_invalid_uuid_format(self, mock_request):
        """Invalid UUID format in DELETE returns 400 VALIDATION_ERROR."""
        from app.api.widget import end_widget_session
        from app.core.errors import APIError, ErrorCode

        with pytest.raises(APIError) as exc_info:
            await end_widget_session(
                request=mock_request,
                session_id="invalid-uuid",
            )

        assert exc_info.value.code == ErrorCode.VALIDATION_ERROR


class TestWidgetMessageValidation:
    """Unit tests for message validation and sanitization (Story 5-7 AC5)."""

    @pytest.fixture
    def mock_request(self):
        """Create mock request."""
        from fastapi import Request

        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"X-Test-Mode": "true"}
        mock_request.client = MagicMock()
        mock_request.client.host = "192.168.1.1"
        return mock_request

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        from sqlalchemy.ext.asyncio import AsyncSession

        db = MagicMock(spec=AsyncSession)
        db.execute = AsyncMock()
        return db

    @pytest.mark.asyncio
    async def test_send_message_rejects_invalid_session_id(self, mock_request, mock_db):
        """Invalid session_id format returns 400 VALIDATION_ERROR."""
        from app.api.widget import send_widget_message
        from app.core.errors import APIError, ErrorCode
        from app.schemas.widget import SendMessageRequest

        message_request = SendMessageRequest(
            session_id="invalid-uuid",
            message="Hello",
        )

        with pytest.raises(APIError) as exc_info:
            await send_widget_message(
                request=mock_request,
                message_request=message_request,
                db=mock_db,
            )

        assert exc_info.value.code == ErrorCode.VALIDATION_ERROR

    @pytest.mark.asyncio
    async def test_send_message_rejects_empty_message(self, mock_request, mock_db):
        """Empty/whitespace-only message returns 400 VALIDATION_ERROR."""
        from app.api.widget import send_widget_message
        from app.core.errors import APIError, ErrorCode
        from app.schemas.widget import SendMessageRequest

        message_request = SendMessageRequest(
            session_id="550e8400-e29b-41d4-a716-446655440000",
            message="   ",
        )

        with pytest.raises(APIError) as exc_info:
            await send_widget_message(
                request=mock_request,
                message_request=message_request,
                db=mock_db,
            )

        assert exc_info.value.code == ErrorCode.VALIDATION_ERROR

    @pytest.mark.asyncio
    async def test_send_message_rejects_too_long_message(self, mock_request, mock_db):
        """Message exceeding 2000 chars returns 400 WIDGET_MESSAGE_TOO_LONG."""
        from app.api.widget import send_widget_message
        from app.core.errors import APIError, ErrorCode
        from app.schemas.widget import SendMessageRequest

        message_request = SendMessageRequest(
            session_id="550e8400-e29b-41d4-a716-446655440000",
            message="x" * 2001,
        )

        with pytest.raises(APIError) as exc_info:
            await send_widget_message(
                request=mock_request,
                message_request=message_request,
                db=mock_db,
            )

        assert exc_info.value.code == ErrorCode.WIDGET_MESSAGE_TOO_LONG
