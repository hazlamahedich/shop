"""Tests for Bot configuration schemas (Story 1.12).

Tests schema validation, field constraints, and serialization.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.bot_config import (
    BotNameUpdate,
    BotConfigResponse,
    BotConfigEnvelope,
)


class TestBotNameUpdate:
    """Tests for BotNameUpdate request schema."""

    def test_bot_name_valid(self) -> None:
        """Test valid bot name (Story 1.12 AC 2)."""
        update = BotNameUpdate(bot_name="GearBot")
        assert update.bot_name == "GearBot"

    def test_bot_name_optional(self) -> None:
        """Test that bot_name is optional (Story 1.12 AC 2)."""
        update = BotNameUpdate()
        assert update.bot_name is None

    def test_bot_name_none(self) -> None:
        """Test that bot_name can be explicitly None (Story 1.12 AC 2)."""
        update = BotNameUpdate(bot_name=None)
        assert update.bot_name is None

    def test_bot_name_whitespace_stripping(self) -> None:
        """Test that leading/trailing whitespace is stripped (Story 1.12 AC 2)."""
        update = BotNameUpdate(bot_name="  GearBot  ")
        assert update.bot_name == "GearBot"

    def test_bot_name_empty_string_after_strip(self) -> None:
        """Test that empty string after stripping becomes None (Story 1.12 AC 2)."""
        update = BotNameUpdate(bot_name="   ")
        assert update.bot_name is None

    def test_bot_name_max_length(self) -> None:
        """Test that bot_name respects 50 character limit (Story 1.12 AC 2)."""
        long_name = "A" * 50
        update = BotNameUpdate(bot_name=long_name)
        assert update.bot_name == long_name

    def test_bot_name_too_long_raises_error(self) -> None:
        """Test that bot_name over 50 characters raises validation error (Story 1.12 AC 2)."""
        with pytest.raises(ValidationError) as exc_info:
            BotNameUpdate(bot_name="A" * 51)
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("bot_name",)
        assert errors[0]["type"] == "string_too_long"

    def test_bot_name_various_valid_values(self) -> None:
        """Test various valid bot name formats (Story 1.12 AC 2)."""
        valid_names = [
            "GearBot",
            "ShopAssistant",
            "StoreBot123",
            "The-Helpful-Bot",
            "Alex's Bot",
            "A",  # Single character
            "A" * 50,  # Max length
        ]
        for name in valid_names:
            update = BotNameUpdate(bot_name=name)
            assert update.bot_name == name


class TestBotConfigResponse:
    """Tests for BotConfigResponse schema."""

    def test_bot_config_response_all_fields(self) -> None:
        """Test response with all fields populated."""
        response = BotConfigResponse(
            bot_name="GearBot",
            personality="friendly",
            custom_greeting="Welcome!",
        )
        assert response.bot_name == "GearBot"
        assert response.personality == "friendly"
        assert response.custom_greeting == "Welcome!"

    def test_bot_config_response_all_optional(self) -> None:
        """Test response with all fields None."""
        response = BotConfigResponse()
        assert response.bot_name is None
        assert response.personality is None
        assert response.custom_greeting is None

    def test_bot_config_response_partial_fields(self) -> None:
        """Test response with some fields populated."""
        response = BotConfigResponse(
            bot_name="GearBot",
            personality="enthusiastic",
        )
        assert response.bot_name == "GearBot"
        assert response.personality == "enthusiastic"
        assert response.custom_greeting is None


class TestBotConfigEnvelope:
    """Tests for BotConfigEnvelope schema."""

    def test_bot_config_envelope_structure(self) -> None:
        """Test envelope has correct structure with data and meta (Story 1.12 AC 5)."""
        envelope = BotConfigEnvelope(
            data=BotConfigResponse(bot_name="GearBot"),
            meta={"requestId": "test-123", "timestamp": "2026-02-11T12:00:00Z"},
        )
        assert envelope.data.bot_name == "GearBot"
        assert envelope.meta.request_id == "test-123"
        assert envelope.meta.timestamp == "2026-02-11T12:00:00Z"

    def test_bot_config_envelope_camel_case_serialization(self) -> None:
        """Test that bot_name serializes to botName (camelCase)."""
        envelope = BotConfigEnvelope(
            data=BotConfigResponse(bot_name="GearBot"),
            meta={"request_id": "test-123", "timestamp": "2026-02-11T12:00:00Z"},
        )
        json_data = envelope.model_dump(by_alias=True)
        assert "botName" in json_data["data"]
        assert json_data["data"]["botName"] == "GearBot"
