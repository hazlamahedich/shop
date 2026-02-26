"""Tests for ForgetPreferencesHandler.

Story 6-1: Opt-In Consent Flow
Task 3.3: Implement "forget my preferences" handler
"""

from datetime import datetime, timezone
from typing import Any, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.merchant import Merchant
from app.schemas.consent import ConsentStatus
from app.services.conversation.handlers.forget_preferences_handler import (
    ForgetPreferencesHandler,
)
from app.services.conversation.schemas import (
    Channel,
    ConsentState,
    ConversationContext,
    ConversationResponse,
)


class TestForgetPreferencesHandler:
    """Tests for ForgetPreferencesHandler."""

    @pytest.fixture
    def handler(self) -> ForgetPreferencesHandler:
        """Create handler instance."""
        return ForgetPreferencesHandler()

    @pytest.fixture
    def mock_db(self) -> AsyncMock:
        """Create mock database session."""
        return AsyncMock()

    @pytest.fixture
    def mock_llm_service(self) -> AsyncMock:
        """Create mock LLM service."""
        return AsyncMock()

    @pytest.fixture
    def merchant(self) -> Merchant:
        """Create test merchant."""
        merchant = Merchant()
        merchant.id = 1
        merchant.business_name = "Test Store"
        merchant.personality = "friendly"
        return merchant

    @pytest.fixture
    def context_with_consent(self) -> ConversationContext:
        """Create context with opted-in consent."""
        return ConversationContext(
            session_id="test_session_123",
            merchant_id=1,
            channel=Channel.WIDGET,
            consent_state=ConsentState(
                prompt_shown=True,
                can_store_conversation=True,
                status=ConsentStatus.OPTED_IN,
            ),
        )

    @pytest.fixture
    def context_without_consent(self) -> ConversationContext:
        """Create context without consent."""
        return ConversationContext(
            session_id="test_session_456",
            merchant_id=1,
            channel=Channel.WIDGET,
            consent_state=ConsentState(
                prompt_shown=False,
                can_store_conversation=False,
                status=ConsentStatus.PENDING,
            ),
        )

    @pytest.mark.asyncio
    async def test_handle_resets_consent_state(
        self,
        handler: ForgetPreferencesHandler,
        mock_db: AsyncMock,
        mock_llm_service: AsyncMock,
        merchant: Merchant,
        context_with_consent: ConversationContext,
    ) -> None:
        """Test that handler resets consent state to pending."""
        with patch(
            "app.services.conversation.handlers.forget_preferences_handler.ConversationConsentService"
        ) as mock_service_class:
            mock_service = AsyncMock()
            mock_service.handle_forget_preferences = AsyncMock(
                return_value={
                    "session_id": "test_session_123",
                    "merchant_id": 1,
                    "status": ConsentStatus.PENDING,
                    "message": "Preferences deleted",
                }
            )
            mock_service_class.return_value = mock_service

            response = await handler.handle(
                db=mock_db,
                merchant=merchant,
                llm_service=mock_llm_service,
                message="forget my preferences",
                context=context_with_consent,
                entities=None,
            )

            assert context_with_consent.consent_state.status == "pending"
            assert context_with_consent.consent_state.can_store_conversation is False
            assert context_with_consent.consent_state.prompt_shown is False

    @pytest.mark.asyncio
    async def test_handle_returns_confirmation_message(
        self,
        handler: ForgetPreferencesHandler,
        mock_db: AsyncMock,
        mock_llm_service: AsyncMock,
        merchant: Merchant,
        context_with_consent: ConversationContext,
    ) -> None:
        """Test that handler returns confirmation message."""
        with patch(
            "app.services.conversation.handlers.forget_preferences_handler.ConversationConsentService"
        ) as mock_service_class:
            mock_service = AsyncMock()
            mock_service.handle_forget_preferences = AsyncMock(
                return_value={
                    "session_id": "test_session_123",
                    "merchant_id": 1,
                    "status": ConsentStatus.PENDING,
                }
            )
            mock_service_class.return_value = mock_service

            response = await handler.handle(
                db=mock_db,
                merchant=merchant,
                llm_service=mock_llm_service,
                message="forget my preferences",
                context=context_with_consent,
                entities=None,
            )

            assert isinstance(response, ConversationResponse)
            assert response.intent == "forget_preferences"
            assert response.confidence == 1.0
            assert response.metadata.get("preferences_forgotten") is True
            assert response.metadata.get("consent_reset") is True

    @pytest.mark.asyncio
    async def test_handle_calls_consent_service(
        self,
        handler: ForgetPreferencesHandler,
        mock_db: AsyncMock,
        mock_llm_service: AsyncMock,
        merchant: Merchant,
        context_with_consent: ConversationContext,
    ) -> None:
        """Test that handler calls ConversationConsentService."""
        with patch(
            "app.services.conversation.handlers.forget_preferences_handler.ConversationConsentService"
        ) as mock_service_class:
            mock_service = AsyncMock()
            mock_service.handle_forget_preferences = AsyncMock(
                return_value={
                    "session_id": "test_session_123",
                    "merchant_id": 1,
                    "status": ConsentStatus.PENDING,
                }
            )
            mock_service_class.return_value = mock_service

            await handler.handle(
                db=mock_db,
                merchant=merchant,
                llm_service=mock_llm_service,
                message="forget my preferences",
                context=context_with_consent,
                entities=None,
            )

            mock_service.handle_forget_preferences.assert_called_once_with(
                session_id="test_session_123",
                merchant_id=1,
            )

    @pytest.mark.asyncio
    async def test_handle_uses_personality_aware_message(
        self,
        handler: ForgetPreferencesHandler,
        mock_db: AsyncMock,
        mock_llm_service: AsyncMock,
        merchant: Merchant,
        context_with_consent: ConversationContext,
    ) -> None:
        """Test that handler uses personality-aware confirmation message."""
        merchant.personality = "professional"

        with patch(
            "app.services.conversation.handlers.forget_preferences_handler.ConversationConsentService"
        ) as mock_service_class:
            mock_service = AsyncMock()
            mock_service.handle_forget_preferences = AsyncMock(return_value={})
            mock_service_class.return_value = mock_service

            response = await handler.handle(
                db=mock_db,
                merchant=merchant,
                llm_service=mock_llm_service,
                message="forget my preferences",
                context=context_with_consent,
                entities=None,
            )

            assert "Order references are retained" in response.message

    @pytest.mark.asyncio
    async def test_handle_friendly_personality_message(
        self,
        handler: ForgetPreferencesHandler,
        mock_db: AsyncMock,
        mock_llm_service: AsyncMock,
        merchant: Merchant,
        context_with_consent: ConversationContext,
    ) -> None:
        """Test friendly personality message contains emoji."""
        merchant.personality = "friendly"

        with patch(
            "app.services.conversation.handlers.forget_preferences_handler.ConversationConsentService"
        ) as mock_service_class:
            mock_service = AsyncMock()
            mock_service.handle_forget_preferences = AsyncMock(return_value={})
            mock_service_class.return_value = mock_service

            response = await handler.handle(
                db=mock_db,
                merchant=merchant,
                llm_service=mock_llm_service,
                message="forget my preferences",
                context=context_with_consent,
                entities=None,
            )

            assert any(char in response.message for char in ["🗑", "✨"])

    @pytest.mark.asyncio
    async def test_handle_enthusiastic_personality_message(
        self,
        handler: ForgetPreferencesHandler,
        mock_db: AsyncMock,
        mock_llm_service: AsyncMock,
        merchant: Merchant,
        context_with_consent: ConversationContext,
    ) -> None:
        """Test enthusiastic personality message."""
        merchant.personality = "enthusiastic"

        with patch(
            "app.services.conversation.handlers.forget_preferences_handler.ConversationConsentService"
        ) as mock_service_class:
            mock_service = AsyncMock()
            mock_service.handle_forget_preferences = AsyncMock(return_value={})
            mock_service_class.return_value = mock_service

            response = await handler.handle(
                db=mock_db,
                merchant=merchant,
                llm_service=mock_llm_service,
                message="forget my preferences",
                context=context_with_consent,
                entities=None,
            )

            assert "POOF" in response.message.upper() or "gone" in response.message.lower()

    @pytest.mark.asyncio
    async def test_handle_gracefully_handles_service_error(
        self,
        handler: ForgetPreferencesHandler,
        mock_db: AsyncMock,
        mock_llm_service: AsyncMock,
        merchant: Merchant,
        context_with_consent: ConversationContext,
    ) -> None:
        """Test that handler gracefully handles service errors."""
        with patch(
            "app.services.conversation.handlers.forget_preferences_handler.ConversationConsentService"
        ) as mock_service_class:
            mock_service = AsyncMock()
            mock_service.handle_forget_preferences = AsyncMock(
                side_effect=Exception("Database error")
            )
            mock_service_class.return_value = mock_service

            response = await handler.handle(
                db=mock_db,
                merchant=merchant,
                llm_service=mock_llm_service,
                message="forget my preferences",
                context=context_with_consent,
                entities=None,
            )

            assert isinstance(response, ConversationResponse)
            assert response.intent == "forget_preferences"

    @pytest.mark.asyncio
    async def test_handle_updates_legacy_consent_status(
        self,
        handler: ForgetPreferencesHandler,
        mock_db: AsyncMock,
        mock_llm_service: AsyncMock,
        merchant: Merchant,
        context_with_consent: ConversationContext,
    ) -> None:
        """Test that handler updates legacy consent_status field."""
        context_with_consent.consent_status = "granted"

        with patch(
            "app.services.conversation.handlers.forget_preferences_handler.ConversationConsentService"
        ) as mock_service_class:
            mock_service = AsyncMock()
            mock_service.handle_forget_preferences = AsyncMock(return_value={})
            mock_service_class.return_value = mock_service

            await handler.handle(
                db=mock_db,
                merchant=merchant,
                llm_service=mock_llm_service,
                message="forget my preferences",
                context=context_with_consent,
                entities=None,
            )

            assert context_with_consent.consent_status == "pending"
