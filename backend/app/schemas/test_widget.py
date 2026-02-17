"""Unit tests for Widget schemas.

Tests validation and defaults for WidgetTheme and WidgetConfig.

Story 5.1: Backend Widget API
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.widget import (
    WidgetTheme,
    WidgetConfig,
    WidgetSessionData,
    CreateSessionRequest,
    SendMessageRequest,
    WidgetSessionResponse,
    WidgetMessageResponse,
    WidgetConfigResponse,
)
from datetime import datetime, timezone, timedelta


class TestWidgetTheme:
    """Tests for WidgetTheme schema."""

    def test_default_values(self):
        """Test that default values are applied."""
        theme = WidgetTheme()

        assert theme.primary_color == "#6366f1"
        assert theme.background_color == "#ffffff"
        assert theme.text_color == "#1f2937"
        assert theme.position == "bottom-right"
        assert theme.border_radius == 16

    def test_valid_custom_values(self):
        """Test that valid custom values are accepted."""
        theme = WidgetTheme(
            primary_color="#ff0000",
            background_color="#000000",
            text_color="#ffffff",
            position="bottom-left",
            border_radius=8,
        )

        assert theme.primary_color == "#ff0000"
        assert theme.background_color == "#000000"
        assert theme.text_color == "#ffffff"
        assert theme.position == "bottom-left"
        assert theme.border_radius == 8

    def test_invalid_hex_color(self):
        """Test that invalid hex color is rejected."""
        with pytest.raises(ValidationError):
            WidgetTheme(primary_color="red")

        with pytest.raises(ValidationError):
            WidgetTheme(primary_color="#fff")

        with pytest.raises(ValidationError):
            WidgetTheme(primary_color="ff0000")

    def test_invalid_position(self):
        """Test that invalid position is rejected."""
        with pytest.raises(ValidationError):
            WidgetTheme(position="top-right")

        with pytest.raises(ValidationError):
            WidgetTheme(position="center")

    def test_border_radius_bounds(self):
        """Test that border_radius is within bounds."""
        theme = WidgetTheme(border_radius=0)
        assert theme.border_radius == 0

        theme = WidgetTheme(border_radius=32)
        assert theme.border_radius == 32

        with pytest.raises(ValidationError):
            WidgetTheme(border_radius=-1)

        with pytest.raises(ValidationError):
            WidgetTheme(border_radius=33)


class TestWidgetConfig:
    """Tests for WidgetConfig schema."""

    def test_default_values(self):
        """Test that default values are applied."""
        config = WidgetConfig()

        assert config.enabled is True
        assert config.bot_name == "Shopping Assistant"
        assert config.welcome_message == "Hi! How can I help you today?"
        assert config.theme.primary_color == "#6366f1"
        assert config.allowed_domains == []

    def test_custom_values(self):
        """Test that custom values are accepted."""
        config = WidgetConfig(
            enabled=False,
            bot_name="Custom Bot",
            welcome_message="Hello there!",
            theme=WidgetTheme(primary_color="#ff0000"),
            allowed_domains=["example.com", "shop.example.com"],
        )

        assert config.enabled is False
        assert config.bot_name == "Custom Bot"
        assert config.welcome_message == "Hello there!"
        assert config.theme.primary_color == "#ff0000"
        assert len(config.allowed_domains) == 2

    def test_bot_name_max_length(self):
        """Test that bot_name max length is enforced."""
        config = WidgetConfig(bot_name="A" * 50)
        assert len(config.bot_name) == 50

        with pytest.raises(ValidationError):
            WidgetConfig(bot_name="A" * 51)

    def test_welcome_message_max_length(self):
        """Test that welcome_message max length is enforced."""
        config = WidgetConfig(welcome_message="A" * 500)
        assert len(config.welcome_message) == 500

        with pytest.raises(ValidationError):
            WidgetConfig(welcome_message="A" * 501)

    def test_partial_theme_override(self):
        """Test that partial theme can be provided."""
        config = WidgetConfig(theme={"primary_color": "#ff0000"})

        assert config.theme.primary_color == "#ff0000"
        assert config.theme.background_color == "#ffffff"


class TestWidgetSessionData:
    """Tests for WidgetSessionData schema."""

    def test_valid_session_data(self):
        """Test that valid session data is accepted."""
        now = datetime.now(timezone.utc)
        session = WidgetSessionData(
            session_id="test-session-id",
            merchant_id=1,
            created_at=now,
            last_activity_at=now,
            expires_at=now + timedelta(hours=1),
        )

        assert session.session_id == "test-session-id"
        assert session.merchant_id == 1
        assert session.visitor_ip is None
        assert session.user_agent is None

    def test_optional_fields(self):
        """Test that optional fields work correctly."""
        now = datetime.now(timezone.utc)
        session = WidgetSessionData(
            session_id="test-session-id",
            merchant_id=1,
            created_at=now,
            last_activity_at=now,
            expires_at=now + timedelta(hours=1),
            visitor_ip="192.168.1.1",
            user_agent="Mozilla/5.0",
        )

        assert session.visitor_ip == "192.168.1.1"
        assert session.user_agent == "Mozilla/5.0"


class TestCreateSessionRequest:
    """Tests for CreateSessionRequest schema."""

    def test_valid_request(self):
        """Test that valid request is accepted."""
        request = CreateSessionRequest(merchant_id=1)

        assert request.merchant_id == 1

    def test_merchant_id_required(self):
        """Test that merchant_id is required."""
        with pytest.raises(ValidationError):
            CreateSessionRequest()


class TestSendMessageRequest:
    """Tests for SendMessageRequest schema."""

    def test_valid_request(self):
        """Test that valid request is accepted."""
        request = SendMessageRequest(
            session_id="test-session",
            message="Hello",
        )

        assert request.session_id == "test-session"
        assert request.message == "Hello"

    def test_message_min_length(self):
        """Test that empty message is rejected."""
        with pytest.raises(ValidationError):
            SendMessageRequest(session_id="test", message="")

    def test_message_max_length(self):
        """Test that message max length is enforced."""
        request = SendMessageRequest(session_id="test", message="A" * 4000)
        assert len(request.message) == 4000

        with pytest.raises(ValidationError):
            SendMessageRequest(session_id="test", message="A" * 4001)

    def test_whitespace_only_message_not_validated_by_schema(self):
        """Test that whitespace-only message passes schema validation.

        Note: Pydantic's min_length counts whitespace as characters.
        Empty message validation is handled at the API layer (widget.py).
        """
        request = SendMessageRequest(session_id="test", message="   ")
        assert request.message == "   "


class TestWidgetSessionResponse:
    """Tests for WidgetSessionResponse schema."""

    def test_valid_response(self):
        """Test that valid response is accepted."""
        now = datetime.now(timezone.utc)
        response = WidgetSessionResponse(
            session_id="test-session",
            expires_at=now + timedelta(hours=1),
        )

        assert response.session_id == "test-session"
        assert response.expires_at > now


class TestWidgetMessageResponse:
    """Tests for WidgetMessageResponse schema."""

    def test_valid_response(self):
        """Test that valid response is accepted."""
        now = datetime.now(timezone.utc)
        response = WidgetMessageResponse(
            message_id="msg-123",
            content="Hello!",
            sender="bot",
            created_at=now,
        )

        assert response.message_id == "msg-123"
        assert response.content == "Hello!"
        assert response.sender == "bot"

    def test_default_sender(self):
        """Test that sender defaults to bot."""
        now = datetime.now(timezone.utc)
        response = WidgetMessageResponse(
            message_id="msg-123",
            content="Hello!",
            created_at=now,
        )

        assert response.sender == "bot"


class TestWidgetConfigResponse:
    """Tests for WidgetConfigResponse schema."""

    def test_valid_response(self):
        """Test that valid response is accepted."""
        response = WidgetConfigResponse(
            bot_name="Test Bot",
            welcome_message="Hello!",
            theme=WidgetTheme(),
            enabled=True,
        )

        assert response.bot_name == "Test Bot"
        assert response.welcome_message == "Hello!"
        assert response.enabled is True
