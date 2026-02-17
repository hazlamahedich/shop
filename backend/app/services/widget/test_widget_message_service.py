"""Unit tests for WidgetMessageService.

Tests message processing with LLM integration, conversation history,
and error handling.

Story 5.1: Backend Widget API
"""

from __future__ import annotations

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.errors import APIError, ErrorCode
from app.schemas.widget import WidgetSessionData
from app.services.widget.widget_message_service import (
    WidgetMessageService,
    MAX_MESSAGE_LENGTH,
)


class TestWidgetMessageService:
    """Tests for WidgetMessageService."""

    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client."""
        redis = AsyncMock()
        redis.get = AsyncMock(return_value=None)
        redis.setex = AsyncMock(return_value=True)
        redis.delete = AsyncMock(return_value=1)
        redis.rpush = AsyncMock(return_value=1)
        redis.lrange = AsyncMock(return_value=[])
        redis.ltrim = AsyncMock(return_value=True)
        redis.expire = AsyncMock(return_value=True)
        return redis

    @pytest.fixture
    def mock_session_service(self, mock_redis):
        """Create mock WidgetSessionService."""
        from app.services.widget.widget_session_service import WidgetSessionService

        service = WidgetSessionService(redis_client=mock_redis)
        return service

    @pytest.fixture
    def message_service(self, mock_session_service):
        """Create WidgetMessageService with mocks."""
        return WidgetMessageService(
            db=None,
            session_service=mock_session_service,
        )

    @pytest.fixture
    def test_session(self):
        """Create test session data."""
        now = datetime.now(timezone.utc)
        return WidgetSessionData(
            session_id="test-session-id",
            merchant_id=1,
            created_at=now,
            last_activity_at=now,
            expires_at=now + timedelta(hours=1),
        )

    @pytest.fixture
    def mock_merchant(self):
        """Create mock merchant."""
        merchant = MagicMock()
        merchant.id = 1
        merchant.bot_name = "Test Bot"
        merchant.business_name = "Test Store"
        merchant.business_description = "A test store"
        merchant.llm_configuration = None
        return merchant

    @pytest.mark.asyncio
    async def test_process_message_raises_error_on_too_long(
        self, message_service, test_session, mock_merchant
    ):
        """Test that process_message raises WIDGET_MESSAGE_TOO_LONG."""
        long_message = "x" * (MAX_MESSAGE_LENGTH + 1)

        with pytest.raises(APIError) as exc_info:
            await message_service.process_message(
                session=test_session,
                message=long_message,
                merchant=mock_merchant,
            )

        assert exc_info.value.code == ErrorCode.WIDGET_MESSAGE_TOO_LONG

    @pytest.mark.asyncio
    async def test_process_message_returns_response(
        self, message_service, test_session, mock_merchant, mock_redis
    ):
        """Test that process_message returns valid response."""
        # Mock history and LLM
        mock_redis.lrange.return_value = []

        with (
            patch.object(message_service, "_build_llm_messages") as mock_build,
            patch.object(message_service, "_get_system_prompt") as mock_prompt,
        ):
            mock_build.return_value = []
            mock_prompt.return_value = "System prompt"

            # Mock LLM factory
            with patch(
                "app.services.widget.widget_message_service.LLMProviderFactory"
            ) as mock_factory:
                mock_llm = AsyncMock()
                mock_llm.chat.return_value = MagicMock(content="Hello! How can I help?")
                mock_factory.create_provider.return_value = mock_llm

                result = await message_service.process_message(
                    session=test_session,
                    message="Hello",
                    merchant=mock_merchant,
                )

        assert result["message_id"] is not None
        assert result["content"] == "Hello! How can I help?"
        assert result["sender"] == "bot"
        assert isinstance(result["created_at"], datetime)

    @pytest.mark.asyncio
    async def test_process_message_adds_to_history(
        self, message_service, test_session, mock_merchant, mock_redis
    ):
        """Test that process_message adds messages to history."""
        mock_redis.lrange.return_value = []

        with (
            patch.object(message_service, "_build_llm_messages") as mock_build,
            patch.object(message_service, "_get_system_prompt") as mock_prompt,
        ):
            mock_build.return_value = []
            mock_prompt.return_value = "System prompt"

            with patch(
                "app.services.widget.widget_message_service.LLMProviderFactory"
            ) as mock_factory:
                mock_llm = AsyncMock()
                mock_llm.chat.return_value = MagicMock(content="Response")
                mock_factory.create_provider.return_value = mock_llm

                await message_service.process_message(
                    session=test_session,
                    message="Hello",
                    merchant=mock_merchant,
                )

        # Verify rpush was called twice (user + bot message)
        assert mock_redis.rpush.call_count == 2

    @pytest.mark.asyncio
    async def test_process_message_refreshes_session(
        self, message_service, test_session, mock_merchant, mock_redis
    ):
        """Test that process_message refreshes session expiry."""
        mock_redis.lrange.return_value = []

        with (
            patch.object(message_service, "_build_llm_messages") as mock_build,
            patch.object(message_service, "_get_system_prompt") as mock_prompt,
        ):
            mock_build.return_value = []
            mock_prompt.return_value = "System prompt"

            with patch(
                "app.services.widget.widget_message_service.LLMProviderFactory"
            ) as mock_factory:
                mock_llm = AsyncMock()
                mock_llm.chat.return_value = MagicMock(content="Response")
                mock_factory.create_provider.return_value = mock_llm

                await message_service.process_message(
                    session=test_session,
                    message="Hello",
                    merchant=mock_merchant,
                )

        # Verify expire was called for session refresh
        mock_redis.expire.assert_called()

    @pytest.mark.asyncio
    async def test_build_llm_messages_includes_system_prompt(self, message_service, mock_merchant):
        """Test that _build_llm_messages includes system prompt."""
        messages = await message_service._build_llm_messages(
            merchant=mock_merchant,
            history=[],
            current_message="Hello",
        )

        assert len(messages) >= 1
        assert messages[0].role == "system"

    @pytest.mark.asyncio
    async def test_build_llm_messages_includes_history(self, message_service, mock_merchant):
        """Test that _build_llm_messages includes conversation history."""
        history = [
            {"role": "user", "content": "Hi"},
            {"role": "bot", "content": "Hello"},
        ]

        messages = await message_service._build_llm_messages(
            merchant=mock_merchant,
            history=history,
            current_message="How are you?",
        )

        # System + 2 history + 1 current = 4 messages
        assert len(messages) == 4
        assert messages[1].content == "Hi"
        assert messages[2].content == "Hello"
        assert messages[3].content == "How are you?"

    @pytest.mark.asyncio
    async def test_get_system_prompt_includes_bot_name(self, message_service, mock_merchant):
        """Test that _get_system_prompt includes bot name."""
        prompt = await message_service._get_system_prompt(mock_merchant)

        assert "Test Bot" in prompt
        assert "Test Store" in prompt

    @pytest.mark.asyncio
    async def test_get_system_prompt_includes_business_description(
        self, message_service, mock_merchant
    ):
        """Test that _get_system_prompt includes business description."""
        prompt = await message_service._get_system_prompt(mock_merchant)

        assert "A test store" in prompt

    @pytest.mark.asyncio
    async def test_process_message_uses_merchant_llm_config(
        self, message_service, test_session, mock_redis
    ):
        """Test that process_message uses merchant's LLM configuration."""
        mock_merchant = MagicMock()
        mock_merchant.id = 1
        mock_merchant.bot_name = "Bot"
        mock_merchant.business_name = "Store"
        mock_merchant.business_description = None
        mock_llm_config = MagicMock()
        mock_llm_config.provider_name = "openai"
        mock_llm_config.config = {"api_key": "test"}
        mock_merchant.llm_configuration = mock_llm_config

        mock_redis.lrange.return_value = []

        with patch("app.services.widget.widget_message_service.LLMProviderFactory") as mock_factory:
            mock_llm = AsyncMock()
            mock_llm.chat.return_value = MagicMock(content="Response")
            mock_factory.create_provider.return_value = mock_llm

            await message_service.process_message(
                session=test_session,
                message="Hello",
                merchant=mock_merchant,
            )

            # Verify factory was called with correct provider
            mock_factory.create_provider.assert_called_once_with(
                provider_name="openai",
                config={"api_key": "test"},
            )

    @pytest.mark.asyncio
    async def test_process_message_handles_llm_error(
        self, message_service, test_session, mock_merchant, mock_redis
    ):
        """Test that process_message handles LLM errors gracefully."""
        mock_redis.lrange.return_value = []

        with patch("app.services.widget.widget_message_service.LLMProviderFactory") as mock_factory:
            mock_factory.create_provider.side_effect = Exception("LLM error")

            with pytest.raises(APIError) as exc_info:
                await message_service.process_message(
                    session=test_session,
                    message="Hello",
                    merchant=mock_merchant,
                )

            assert exc_info.value.code == ErrorCode.LLM_PROVIDER_ERROR
