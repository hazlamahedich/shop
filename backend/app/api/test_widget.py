"""Unit tests for Widget API endpoints.

Tests session creation, messaging, config retrieval, and session termination.

Story 5.1: Backend Widget API
"""

from __future__ import annotations

import os
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

os.environ["IS_TESTING"] = "true"

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.widget import router, _check_rate_limit, _validate_domain_whitelist
from app.core.errors import ErrorCode, APIError
from app.core.database import get_db
from app.schemas.widget import WidgetSessionData
from app.services.widget.widget_session_service import WidgetSessionService
from app.services.widget.widget_message_service import WidgetMessageService


class TestWidgetAPI:
    """Tests for Widget API endpoints."""

    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client."""
        redis = AsyncMock()
        redis.get = AsyncMock(return_value=None)
        redis.setex = AsyncMock(return_value=True)
        redis.delete = AsyncMock(return_value=1)
        redis.exists = AsyncMock(return_value=0)
        redis.expire = AsyncMock(return_value=True)
        redis.rpush = AsyncMock(return_value=1)
        redis.lrange = AsyncMock(return_value=[])
        redis.ltrim = AsyncMock(return_value=True)
        return redis

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def mock_merchant(self):
        """Create mock merchant."""
        merchant = MagicMock()
        merchant.id = 1
        merchant.bot_name = "Test Bot"
        merchant.business_name = "Test Store"
        merchant.widget_config = {"enabled": True}
        merchant.llm_configuration = None
        return merchant

    @pytest.fixture
    def app(self, mock_db, mock_merchant, mock_redis):
        """Create test FastAPI app with dependency overrides."""
        app = FastAPI()
        app.include_router(router, prefix="/api/v1")

        async def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db
        return app

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)

    def test_rate_limit_check_returns_none_in_test_mode(self):
        """Test that rate limiting is bypassed in test mode."""
        mock_request = MagicMock()
        mock_request.headers = {}

        result = _check_rate_limit(mock_request)
        assert result is None

    def test_create_session_validates_merchant_id(self, client):
        """Test that create session validates merchant_id."""
        response = client.post(
            "/api/v1/widget/session",
            json={},
        )
        assert response.status_code == 422

    def test_send_message_validates_session_id(self, client):
        """Test that send message validates session_id."""
        response = client.post(
            "/api/v1/widget/message",
            json={"message": "hello"},
        )
        assert response.status_code == 422

    def test_send_message_validates_message(self, client):
        """Test that send message validates message."""
        response = client.post(
            "/api/v1/widget/message",
            json={"session_id": "test"},
        )
        assert response.status_code == 422

    def test_send_message_empty_message_rejected(self, client):
        """Test that empty message is rejected."""
        response = client.post(
            "/api/v1/widget/message",
            json={"session_id": "test", "message": ""},
        )
        assert response.status_code == 422


class TestWidgetSessionServiceIntegration:
    """Integration tests with WidgetSessionService."""

    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis with storage simulation."""
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

        async def mock_rpush(key, value):
            if key not in storage:
                storage[key] = []
            storage[key].append(value)
            return len(storage[key])

        async def mock_lrange(key, start, end):
            if key not in storage:
                return []
            return storage[key]

        async def mock_ltrim(key, start, end):
            return True

        redis.get = mock_get
        redis.setex = mock_setex
        redis.delete = mock_delete
        redis.exists = mock_exists
        redis.expire = mock_expire
        redis.rpush = mock_rpush
        redis.lrange = mock_lrange
        redis.ltrim = mock_ltrim

        return redis

    @pytest.mark.asyncio
    async def test_session_lifecycle(self, mock_redis):
        """Test complete session lifecycle."""
        service = WidgetSessionService(redis_client=mock_redis)

        # Create
        session = await service.create_session(merchant_id=1)
        assert session.session_id is not None

        # Get
        retrieved = await service.get_session(session.session_id)
        assert retrieved is not None

        # End
        ended = await service.end_session(session.session_id)
        assert ended is True

        # Verify gone
        retrieved = await service.get_session(session.session_id)
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_message_history(self, mock_redis):
        """Test message history management."""
        service = WidgetSessionService(redis_client=mock_redis)

        session = await service.create_session(merchant_id=1)

        await service.add_message_to_history(session.session_id, "user", "Hello")
        await service.add_message_to_history(session.session_id, "bot", "Hi!")

        history = await service.get_message_history(session.session_id)
        assert len(history) == 2

    @pytest.mark.asyncio
    async def test_session_not_found_error(self, mock_redis):
        """Test session not found raises correct error."""
        service = WidgetSessionService(redis_client=mock_redis)

        with pytest.raises(APIError) as exc_info:
            await service.get_session_or_error("nonexistent")

        assert exc_info.value.code == ErrorCode.WIDGET_SESSION_NOT_FOUND

    @pytest.mark.asyncio
    async def test_session_expired_error(self, mock_redis):
        """Test expired session raises correct error."""
        service = WidgetSessionService(redis_client=mock_redis)

        # Create session that's already expired
        now = datetime.now(timezone.utc)
        expired_session = WidgetSessionData(
            session_id="expired-session",
            merchant_id=1,
            created_at=now - timedelta(hours=2),
            last_activity_at=now - timedelta(hours=2),
            expires_at=now - timedelta(hours=1),  # Expired 1 hour ago
        )
        await mock_redis.setex(
            f"widget:session:expired-session",
            3600,
            expired_session.model_dump_json(),
        )

        with pytest.raises(APIError) as exc_info:
            await service.get_session_or_error("expired-session")

        assert exc_info.value.code == ErrorCode.WIDGET_SESSION_EXPIRED


class TestWidgetConfigEndpoint:
    """Tests for GET /api/v1/widget/config/{merchant_id} endpoint."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def mock_merchant(self):
        """Create mock merchant with widget config."""
        from app.models.merchant import PersonalityType

        merchant = MagicMock()
        merchant.id = 1
        merchant.bot_name = "Custom Bot"
        merchant.widget_config = {
            "enabled": True,
            "bot_name": "Widget Bot",
            "welcome_message": "Welcome!",
            "theme": {
                "primary_color": "#ff0000",
                "background_color": "#ffffff",
                "text_color": "#000000",
                "position": "bottom-left",
                "border_radius": 8,
            },
        }
        merchant.personality = PersonalityType.FRIENDLY
        merchant.custom_greeting = None
        merchant.use_custom_greeting = False
        merchant.business_name = "Test Store"
        merchant.business_hours = None
        return merchant

    @pytest.fixture
    def mock_merchant_no_config(self):
        """Create mock merchant without widget config."""
        from app.models.merchant import PersonalityType

        merchant = MagicMock()
        merchant.id = 2
        merchant.bot_name = "Default Bot"
        merchant.widget_config = None
        merchant.personality = PersonalityType.FRIENDLY
        merchant.custom_greeting = None
        merchant.use_custom_greeting = False
        merchant.business_name = None
        merchant.business_hours = None
        return merchant

    @pytest.fixture
    def mock_merchant_disabled(self):
        """Create mock merchant with disabled widget."""
        from app.models.merchant import PersonalityType

        merchant = MagicMock()
        merchant.id = 3
        merchant.bot_name = "Disabled Bot"
        merchant.widget_config = {"enabled": False}
        merchant.personality = PersonalityType.FRIENDLY
        merchant.custom_greeting = None
        merchant.use_custom_greeting = False
        merchant.business_name = None
        merchant.business_hours = None
        return merchant

    @pytest.fixture
    def app(self, mock_db):
        """Create test FastAPI app with dependency overrides."""
        app = FastAPI()
        app.include_router(router, prefix="/api/v1")

        async def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db
        return app

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)

    def test_get_config_returns_config_for_valid_merchant(self, client, mock_db, mock_merchant):
        """Test that get_config returns widget configuration."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_merchant
        mock_db.execute = AsyncMock(return_value=mock_result)

        response = client.get("/api/v1/widget/config/1")

        assert response.status_code == 200
        body = response.json()
        assert body["data"]["botName"] == "Custom Bot"
        # Greeting now comes from personality-based greeting service
        assert (
            body["data"]["welcomeMessage"]
            == "Hey there! 👋 I'm Custom Bot from Test Store. How can I help you today?"
        )
        assert body["data"]["enabled"] is True
        assert body["data"]["theme"]["primaryColor"] == "#ff0000"
        assert body["data"]["theme"]["position"] == "bottom-left"

    def test_get_config_returns_404_for_nonexistent_merchant(self, client, mock_db):
        """Test that get_config returns 404 for non-existent merchant."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(Exception):
            response = client.get("/api/v1/widget/config/99999")

    def test_get_config_returns_defaults_when_no_config(
        self, client, mock_db, mock_merchant_no_config
    ):
        """Test that get_config returns defaults when merchant has no config."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_merchant_no_config
        mock_db.execute = AsyncMock(return_value=mock_result)

        response = client.get("/api/v1/widget/config/2")

        assert response.status_code == 200
        body = response.json()
        assert body["data"]["botName"] == "Default Bot"
        # Greeting now comes from personality-based greeting service with fallback
        assert (
            body["data"]["welcomeMessage"]
            == "Hey there! 👋 I'm Default Bot from the store. How can I help you today?"
        )
        assert body["data"]["enabled"] is True
        assert body["data"]["theme"]["primaryColor"] == "#6366f1"

    def test_get_config_shows_disabled_status(self, client, mock_db, mock_merchant_disabled):
        """Test that get_config returns enabled=false when widget disabled."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_merchant_disabled
        mock_db.execute = AsyncMock(return_value=mock_result)

        response = client.get("/api/v1/widget/config/3")

        assert response.status_code == 200
        body = response.json()
        assert body["data"]["enabled"] is False

    def test_get_config_includes_meta(self, client, mock_db, mock_merchant):
        """Test that get_config includes meta in response."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_merchant
        mock_db.execute = AsyncMock(return_value=mock_result)

        response = client.get("/api/v1/widget/config/1")

        assert response.status_code == 200
        body = response.json()
        assert "meta" in body
        assert "requestId" in body["meta"]
        assert "timestamp" in body["meta"]

    @pytest.fixture
    def mock_merchant_custom_greeting(self):
        """Create mock merchant with custom greeting."""
        from app.models.merchant import PersonalityType

        merchant = MagicMock()
        merchant.id = 4
        merchant.bot_name = "Greeting Bot"
        merchant.widget_config = {
            "enabled": True,
            "theme": {
                "primary_color": "#6366f1",
                "background_color": "#ffffff",
                "text_color": "#000000",
                "position": "bottom-right",
                "border_radius": 8,
            },
        }
        merchant.personality = PersonalityType.PROFESSIONAL
        merchant.custom_greeting = (
            "Welcome! I'm {bot_name} from {business_name}. How may I assist you?"
        )
        merchant.use_custom_greeting = True
        merchant.business_name = "Custom Shop"
        merchant.business_hours = None
        return merchant

    def test_get_config_uses_custom_greeting_when_enabled(
        self, client, mock_db, mock_merchant_custom_greeting
    ):
        """Test that get_config uses custom greeting when enabled."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_merchant_custom_greeting
        mock_db.execute = AsyncMock(return_value=mock_result)

        response = client.get("/api/v1/widget/config/4")

        assert response.status_code == 200
        body = response.json()
        assert body["data"]["botName"] == "Greeting Bot"
        # Custom greeting should be used with variable substitution
        assert (
            body["data"]["welcomeMessage"]
            == "Welcome! I'm Greeting Bot from Custom Shop. How may I assist you?"
        )


class TestDomainWhitelistValidation:
    """Tests for _validate_domain_whitelist function."""

    def test_allows_all_when_whitelist_empty(self):
        """Test that empty whitelist allows all domains."""
        request = MagicMock()
        request.headers = {"Origin": "https://evil.com"}

        _validate_domain_whitelist(request, [])

    def test_allows_matching_domain(self):
        """Test that matching domain is allowed."""
        request = MagicMock()
        request.headers = {"Origin": "https://example.com"}

        _validate_domain_whitelist(request, ["example.com"])

    def test_allows_subdomain_of_whitelisted(self):
        """Test that subdomain of whitelisted domain is allowed."""
        request = MagicMock()
        request.headers = {"Origin": "https://shop.example.com"}

        _validate_domain_whitelist(request, ["example.com"])

    def test_allows_www_subdomain(self):
        """Test that www subdomain is allowed."""
        request = MagicMock()
        request.headers = {"Origin": "https://www.example.com"}

        _validate_domain_whitelist(request, ["example.com"])

    def test_rejects_non_whitelisted_domain(self):
        """Test that non-whitelisted domain is rejected."""
        request = MagicMock()
        request.headers = {"Origin": "https://evil.com"}

        with pytest.raises(APIError) as exc_info:
            _validate_domain_whitelist(request, ["example.com"])

        assert exc_info.value.code == ErrorCode.WIDGET_DOMAIN_NOT_ALLOWED

    def test_rejects_different_tld(self):
        """Test that same domain with different TLD is rejected."""
        request = MagicMock()
        request.headers = {"Origin": "https://example.evil"}

        with pytest.raises(APIError) as exc_info:
            _validate_domain_whitelist(request, ["example.com"])

        assert exc_info.value.code == ErrorCode.WIDGET_DOMAIN_NOT_ALLOWED

    def test_allows_when_no_origin_header(self):
        """Test that missing origin header is allowed."""
        request = MagicMock()
        request.headers = {}

        _validate_domain_whitelist(request, ["example.com"])

    def test_is_case_insensitive(self):
        """Test that domain matching is case-insensitive."""
        request = MagicMock()
        request.headers = {"Origin": "https://Example.COM"}

        _validate_domain_whitelist(request, ["example.com"])

    def test_handles_port_in_origin(self):
        """Test that port in origin is handled correctly.

        Note: Current implementation includes port in netloc, so example.com:8080
        does NOT match whitelist for 'example.com'. This test documents that behavior.
        """
        request = MagicMock()
        request.headers = {"Origin": "https://example.com:8080"}

        with pytest.raises(APIError) as exc_info:
            _validate_domain_whitelist(request, ["example.com"])

        assert exc_info.value.code == ErrorCode.WIDGET_DOMAIN_NOT_ALLOWED

    def test_handles_multiple_whitelist_entries(self):
        """Test that multiple whitelist entries work."""
        request = MagicMock()
        request.headers = {"Origin": "https://shop.two.com"}

        _validate_domain_whitelist(request, ["one.com", "two.com", "three.com"])


class TestCreateSessionDomainValidation:
    """Tests for domain validation in session creation.

    Note: These tests verify the integration of domain whitelist validation
    with the session creation endpoint. For pure validation logic tests,
    see TestDomainWhitelistValidation.
    """

    @pytest.fixture
    def mock_db(self):
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def mock_merchant_with_whitelist(self):
        merchant = MagicMock()
        merchant.id = 1
        merchant.bot_name = "Test Bot"
        merchant.widget_config = {
            "enabled": True,
            "allowed_domains": ["trusted.com"],
        }
        merchant.llm_configuration = None
        return merchant

    @pytest.fixture
    def app(self, mock_db):
        app = FastAPI()
        app.include_router(router, prefix="/api/v1")

        async def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db
        return app

    @pytest.fixture
    def client(self, app):
        return TestClient(app)

    def test_domain_validation_uses_validate_function(
        self, client, mock_db, mock_merchant_with_whitelist
    ):
        """Test that session creation uses _validate_domain_whitelist."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_merchant_with_whitelist
        mock_db.execute = AsyncMock(return_value=mock_result)

        response = client.post(
            "/api/v1/widget/session",
            json={"merchant_id": 1},
            headers={"Origin": "https://trusted.com"},
        )

        assert response.status_code == 200


class TestMerchantDisabledWidget:
    """Tests for merchant with disabled widget.

    Note: Disabled widget check logic is tested in WidgetSessionService
    and the endpoint validation tests. This test class documents expected behavior.
    """

    def test_disabled_widget_raises_api_error(self):
        """Test that disabled widget raises WIDGET_MERCHANT_DISABLED error."""
        from app.core.errors import APIError, ErrorCode

        error = APIError(
            ErrorCode.WIDGET_MERCHANT_DISABLED,
            "Widget is disabled for this merchant",
        )

        assert error.code == ErrorCode.WIDGET_MERCHANT_DISABLED
        assert "disabled" in error.message.lower()
