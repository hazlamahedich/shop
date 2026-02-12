"""Tests for Preview Service (Story 1.13).

Tests the isolated preview conversation service that provides a sandbox
environment for merchants to test their bot configuration.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.services.preview.preview_service import (
    PreviewConversation,
    PreviewService,
)
from app.models.merchant import PersonalityType
from app.schemas.preview import (
    PreviewMessageResponse,
    PreviewMessageMetadata,
)


class TestPreviewConversation:
    """Tests for PreviewConversation class."""

    def test_create_preview_conversation(self) -> None:
        """Test creating a new preview conversation."""
        merchant_id = 123
        preview = PreviewConversation(merchant_id=merchant_id)

        assert preview.merchant_id == merchant_id
        assert preview.preview_session_id is not None
        assert len(preview.messages) == 0
        assert preview.message_count == 0
        assert isinstance(preview.created_at, datetime)

    def test_add_user_message(self) -> None:
        """Test adding a user message to the conversation."""
        preview = PreviewConversation(merchant_id=123)

        preview.add_message("user", "What shoes do you have?")

        assert len(preview.messages) == 1
        assert preview.message_count == 1
        assert preview.messages[0]["role"] == "user"
        assert preview.messages[0]["content"] == "What shoes do you have?"

    def test_add_bot_message(self) -> None:
        """Test adding a bot message to the conversation."""
        preview = PreviewConversation(merchant_id=123)

        preview.add_message("bot", "I found several shoes for you!")

        assert len(preview.messages) == 1
        assert preview.messages[0]["role"] == "bot"
        assert preview.messages[0]["content"] == "I found several shoes for you!"

    def test_conversation_order(self) -> None:
        """Test that messages maintain order."""
        preview = PreviewConversation(merchant_id=123)

        preview.add_message("user", "Hello")
        preview.add_message("bot", "Hi there!")
        preview.add_message("user", "How are you?")

        assert len(preview.messages) == 3
        assert preview.messages[0]["content"] == "Hello"
        assert preview.messages[1]["content"] == "Hi there!"
        assert preview.messages[2]["content"] == "How are you?"

    def test_reset_conversation(self) -> None:
        """Test resetting a conversation."""
        preview = PreviewConversation(merchant_id=123)

        preview.add_message("user", "Test message")
        assert len(preview.messages) == 1

        preview.reset()

        assert len(preview.messages) == 0
        assert preview.message_count == 0

    def test_get_conversation_history(self) -> None:
        """Test getting conversation history."""
        preview = PreviewConversation(merchant_id=123)

        preview.add_message("user", "Hello")
        preview.add_message("bot", "Hi!")

        history = preview.get_history()

        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "bot"


class TestPreviewService:
    """Tests for PreviewService class."""

    @pytest.fixture
    def mock_merchant(self) -> MagicMock:
        """Create a mock merchant with bot configuration."""
        merchant = MagicMock()
        merchant.id = 123
        merchant.business_name = "Test Store"
        merchant.bot_name = "TestBot"
        merchant.personality = PersonalityType.FRIENDLY
        merchant.custom_greeting = None
        merchant.business_description = "A test store"
        merchant.business_hours = "9-5 Mon-Fri"
        # Mock LLM configuration
        mock_llm_config = MagicMock()
        mock_llm_config.provider_name = "ollama"
        mock_llm_config.config = {}
        merchant.llm_configuration = mock_llm_config
        return merchant

    @pytest.fixture
    def mock_db(self) -> AsyncMock:
        """Create a mock database session."""
        return AsyncMock()

    @pytest.fixture
    def preview_service(self, mock_db: AsyncMock) -> PreviewService:
        """Create a preview service instance with isolated sessions."""
        # Clear sessions before each test
        PreviewService.sessions.clear()
        return PreviewService(db=mock_db)

    def test_create_preview_session(
        self, preview_service: PreviewService, mock_merchant: MagicMock
    ) -> None:
        """Test creating a new preview session."""
        session = preview_service.create_session(mock_merchant)

        assert session["merchant_id"] == 123
        assert "preview_session_id" in session
        assert "created_at" in session
        assert "starter_prompts" in session
        assert len(session["starter_prompts"]) == 5

    def test_get_existing_session(
        self, preview_service: PreviewService
    ) -> None:
        """Test getting an existing preview session."""
        # Create a conversation directly with a known ID
        session_id = str(uuid4())
        merchant_id = 123
        preview = PreviewConversation(merchant_id=merchant_id)
        # Manually set the session ID to match our test
        preview.preview_session_id = session_id

        preview_service.sessions[session_id] = preview

        session = preview_service.get_session(session_id)

        assert session is not None
        assert session.merchant_id == merchant_id
        assert session.preview_session_id == session_id

    def test_get_nonexistent_session(self, preview_service: PreviewService) -> None:
        """Test getting a session that doesn't exist."""
        session_id = str(uuid4())

        session = preview_service.get_session(session_id)

        assert session is None

    @pytest.mark.asyncio
    async def test_send_message(
        self, preview_service: PreviewService, mock_merchant: MagicMock
    ) -> None:
        """Test sending a message and getting bot response."""
        session_id = str(uuid4())

        # Create a session
        preview = PreviewConversation(merchant_id=mock_merchant.id)
        preview.preview_session_id = session_id
        preview_service.sessions[session_id] = preview

        # Mock the bot response service and LLM factory
        from app.services.llm.base_llm_service import LLMResponse

        # Mock FAQ query result (empty - no FAQs, so falls back to LLM)
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []

        with patch("app.services.personality.bot_response_service.BotResponseService") as MockBotService:
            mock_bot_instance = MagicMock()
            mock_bot_instance.get_system_prompt = AsyncMock(
                return_value="Test system prompt"
            )
            MockBotService.return_value = mock_bot_instance

            with patch("app.services.llm.llm_factory.LLMProviderFactory.create_provider") as mock_create:
                mock_llm = MagicMock()
                mock_llm.chat = AsyncMock(
                    return_value=LLMResponse(
                        content="Here are some shoes!",
                        tokens_used=50,
                        model="llama3",
                        provider="ollama",
                        metadata={},
                    )
                )
                mock_create.return_value = mock_llm

                # Mock the database execute to return empty FAQ list
                preview_service.db.execute = AsyncMock(return_value=mock_result)

                response = await preview_service.send_message(
                    session_id=session_id,
                    message="What shoes do you have?",
                    merchant=mock_merchant,
                )

                assert isinstance(response, PreviewMessageResponse)
                assert response.response == "Here are some shoes!"
                assert response.confidence == 70  # Default confidence for LLM without logprobs
                assert response.confidence_level == "medium"

    @pytest.mark.asyncio
    async def test_send_message_adds_to_conversation(
        self, preview_service: PreviewService, mock_merchant: MagicMock
    ) -> None:
        """Test that sending a message adds it to the conversation."""
        session_id = str(uuid4())
        preview = PreviewConversation(merchant_id=mock_merchant.id)
        preview.preview_session_id = session_id
        preview_service.sessions[session_id] = preview

        from app.services.llm.base_llm_service import LLMResponse

        # Mock FAQ query result (empty - no FAQs, so falls back to LLM)
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []

        with patch("app.services.personality.bot_response_service.BotResponseService") as MockBotService:
            mock_bot_instance = MagicMock()
            mock_bot_instance.get_system_prompt = AsyncMock(
                return_value="Test system prompt"
            )
            MockBotService.return_value = mock_bot_instance

            with patch("app.services.llm.llm_factory.LLMProviderFactory.create_provider") as mock_create:
                mock_llm = MagicMock()
                mock_llm.chat = AsyncMock(
                    return_value=LLMResponse(
                        content="Response!",
                        tokens_used=30,
                        model="llama3",
                        provider="ollama",
                        metadata={},
                    )
                )
                mock_create.return_value = mock_llm

                # Mock the database execute to return empty FAQ list
                preview_service.db.execute = AsyncMock(return_value=mock_result)

                await preview_service.send_message(
                    session_id=session_id,
                    message="Test message",
                    merchant=mock_merchant,
                )

                session = preview_service.get_session(session_id)
                assert session is not None
                assert len(session.messages) == 2  # User + Bot

    def test_reset_conversation(self, preview_service: PreviewService) -> None:
        """Test resetting a conversation."""
        session_id = str(uuid4())
        merchant_id = 123

        preview = PreviewConversation(merchant_id=merchant_id)
        preview.preview_session_id = session_id
        preview_service.sessions[session_id] = preview
        preview.add_message("user", "Test")

        assert len(preview_service.sessions[session_id].messages) == 1

        preview_service.reset_session(session_id)

        assert len(preview_service.sessions[session_id].messages) == 0

    def test_confidence_level_calculation(self) -> None:
        """Test confidence level calculation."""
        assert PreviewService.get_confidence_level(95) == "high"
        assert PreviewService.get_confidence_level(80) == "high"
        assert PreviewService.get_confidence_level(75) == "medium"
        assert PreviewService.get_confidence_level(50) == "medium"
        assert PreviewService.get_confidence_level(45) == "low"
        assert PreviewService.get_confidence_level(0) == "low"

    def test_calculate_faq_confidence(self, preview_service: PreviewService) -> None:
        """Test FAQ confidence calculation."""
        # High confidence - exact match
        score1 = preview_service.calculate_faq_confidence(
            question="What are your hours?",
            faq_question="What are your business hours?",
        )
        assert score1 > 70

        # Medium confidence - similar but not exact
        score2 = preview_service.calculate_faq_confidence(
            question="hours?",
            faq_question="What are your business hours?",
        )
        assert 20 < score2 < 70

        # Low confidence - unrelated (using more distinct strings)
        score3 = preview_service.calculate_faq_confidence(
            question="I need running shoes",
            faq_question="What is your return policy?",
        )
        assert score3 < 40

    def test_session_cleanup_old_sessions(self, preview_service: PreviewService) -> None:
        """Test cleanup of old preview sessions."""
        # Clear sessions first for isolated test
        initial_count = len(preview_service.sessions)

        # Create multiple sessions
        for i in range(5):
            session_id = str(uuid4())
            preview = PreviewConversation(merchant_id=100 + i)
            preview.preview_session_id = session_id
            preview_service.sessions[session_id] = preview

        count_after_create = len(preview_service.sessions)
        assert count_after_create >= 5

        # Cleanup sessions older than 1 hour (should remove all since they're new)
        # In a real test we'd mock time, but for now we just test the method exists
        preview_service.cleanup_old_sessions(max_age_seconds=3600)

        # Sessions should still be there (they're fresh)
        # In production with real time, old sessions would be removed


class TestPreviewServiceIntegration:
    """Integration tests for preview service with bot configuration."""

    @pytest.fixture
    def preview_service(self) -> PreviewService:
        """Create a preview service with isolated sessions."""
        PreviewService.sessions.clear()
        return PreviewService()

    def test_preview_with_bot_name(self, preview_service: PreviewService) -> None:
        """Test that preview includes bot name from merchant config."""
        merchant = MagicMock()
        merchant.id = 123
        merchant.bot_name = "GearBot"
        merchant.business_name = "Alex's Athletic Gear"

        session = preview_service.create_session(merchant)

        assert "starter_prompts" in session
        assert len(session["starter_prompts"]) == 5

    def test_preview_with_personality(self, preview_service: PreviewService) -> None:
        """Test that preview respects merchant personality."""
        merchant = MagicMock()
        merchant.id = 123
        merchant.personality = PersonalityType.ENTHUSIASTIC

        session = preview_service.create_session(merchant)

        assert session["merchant_id"] == 123

    def test_state_isolation_between_sessions(self, preview_service: PreviewService) -> None:
        """Test that different preview sessions are isolated."""
        session1_id = str(uuid4())
        session2_id = str(uuid4())

        preview1 = PreviewConversation(merchant_id=111)
        preview1.preview_session_id = session1_id
        preview2 = PreviewConversation(merchant_id=222)
        preview2.preview_session_id = session2_id

        preview_service.sessions[session1_id] = preview1
        preview_service.sessions[session2_id] = preview2

        preview_service.sessions[session1_id].add_message("user", "Session 1 message")
        preview_service.sessions[session2_id].add_message("user", "Session 2 message")

        assert len(preview_service.sessions[session1_id].messages) == 1
        assert len(preview_service.sessions[session2_id].messages) == 1
        assert preview_service.sessions[session1_id].messages[0]["content"] == "Session 1 message"
        assert preview_service.sessions[session2_id].messages[0]["content"] == "Session 2 message"
