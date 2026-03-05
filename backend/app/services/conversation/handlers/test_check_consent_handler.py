"""Tests for CheckConsentHandler.

Story 6-1: Opt-In Consent Flow
Check consent status intent handler tests.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.models.merchant import Merchant, PersonalityType
from app.schemas.consent import ConsentStatus
from app.services.conversation.handlers.check_consent_handler import (
    CheckConsentHandler,
)
from app.services.conversation.schemas import (
    Channel,
    ConsentState,
    ConversationContext,
    ConversationResponse,
)


class TestCheckConsentHandler:
    """Tests for CheckConsentHandler."""

    @pytest.fixture
    def handler(self) -> CheckConsentHandler:
        """Create handler instance."""
        return CheckConsentHandler()

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
        merchant.personality = PersonalityType.FRIENDLY
        return merchant

    @pytest.fixture
    def context_with_opted_in_consent(self) -> ConversationContext:
        """Create context with opted-in consent."""
        return ConversationContext(
            session_id="test_session_123",
            merchant_id=1,
            channel=Channel.WIDGET,
            consent_state=ConsentState(
                prompt_shown=True,
                can_store_conversation=True,
                status="opted_in",
            ),
        )

    @pytest.fixture
    def context_with_opted_out_consent(self) -> ConversationContext:
        """Create context with opted-out consent."""
        return ConversationContext(
            session_id="test_session_456",
            merchant_id=1,
            channel=Channel.WIDGET,
            consent_state=ConsentState(
                prompt_shown=True,
                can_store_conversation=False,
                status="opted_out",
            ),
        )

    @pytest.fixture
    def context_with_pending_consent(self) -> ConversationContext:
        """Create context with pending consent."""
        return ConversationContext(
            session_id="test_session_789",
            merchant_id=1,
            channel=Channel.WIDGET,
            consent_state=ConsentState(
                prompt_shown=False,
                can_store_conversation=False,
                status="pending",
            ),
        )

    @pytest.mark.asyncio
    async def test_handle_returns_conversation_response(
        self,
        handler: CheckConsentHandler,
        mock_db: AsyncMock,
        mock_llm_service: AsyncMock,
        merchant: Merchant,
        context_with_opted_in_consent: ConversationContext,
    ) -> None:
        """Test that handler returns ConversationResponse."""
        mock_consent = MagicMock()
        mock_consent.granted = True
        mock_consent.revoked_at = None
        mock_consent.granted_at = datetime(2026, 3, 4, 12, 30, 0, tzinfo=timezone.utc)
        mock_consent_service = MagicMock()
        mock_consent_service.get_consent_for_consent = AsyncMock(return_value=mock_consent)
        with patch(
            "app.services.conversation.handlers.check_consent_handler.ConversationConsentService",
            return_value=mock_consent_service,
        ):
            response = await handler.handle(
                db=mock_db,
                merchant=merchant,
                llm_service=mock_llm_service,
                message="are my preferences saved?",
                context=context_with_opted_in_consent,
                entities=None,
            )
        assert isinstance(response, ConversationResponse)
        assert response.intent == "check_consent_status"
        assert response.confidence == 1.0

    @pytest.mark.asyncio
    async def test_handle_opted_in_returns_status_message(
        self,
        handler: CheckConsentHandler,
        mock_db: AsyncMock,
        mock_llm_service: AsyncMock,
        merchant: Merchant,
        context_with_opted_in_consent: ConversationContext,
    ) -> None:
        """Test that handler returns opted-in status message."""
        mock_consent = MagicMock()
        mock_consent.granted = True
        mock_consent.revoked_at = None
        mock_consent.granted_at = datetime(2026, 3, 4, 12, 30, 0, tzinfo=timezone.utc)
        mock_consent_service = MagicMock()
        mock_consent_service.get_consent_for_consent = AsyncMock(return_value=mock_consent)
        with patch(
            "app.services.conversation.handlers.check_consent_handler.ConversationConsentService",
            return_value=mock_consent_service,
        ):
            response = await handler.handle(
                db=mock_db,
                merchant=merchant,
                llm_service=mock_llm_service,
                message="are my preferences saved?",
                context=context_with_opted_in_consent,
                entities=None,
            )
        assert "saved" in response.message.lower()
        assert response.metadata.get("consent_status") == "opted_in"

    @pytest.mark.asyncio
    async def test_handle_opted_out_returns_status_message(
        self,
        handler: CheckConsentHandler,
        mock_db: AsyncMock,
        mock_llm_service: AsyncMock,
        merchant: Merchant,
        context_with_opted_out_consent: ConversationContext,
    ) -> None:
        """Test that handler returns opted-out status message."""
        mock_consent = MagicMock()
        mock_consent.granted = False
        mock_consent.revoked_at = datetime(2026, 3, 4, 12, 30, 0, tzinfo=timezone.utc)
        mock_consent.granted_at = None
        mock_consent_service = MagicMock()
        mock_consent_service.get_consent_for_consent = AsyncMock(return_value=mock_consent)
        with patch(
            "app.services.conversation.handlers.check_consent_handler.ConversationConsentService",
            return_value=mock_consent_service,
        ):
            response = await handler.handle(
                db=mock_db,
                merchant=merchant,
                llm_service=mock_llm_service,
                message="are my preferences saved?",
                context=context_with_opted_out_consent,
                entities=None,
            )
        assert "fresh start" in response.message.lower()
        assert response.metadata.get("consent_status") == "opted_out"

    @pytest.mark.asyncio
    async def test_handle_pending_returns_status_message(
        self,
        handler: CheckConsentHandler,
        mock_db: AsyncMock,
        mock_llm_service: AsyncMock,
        merchant: Merchant,
        context_with_pending_consent: ConversationContext,
    ) -> None:
        """Test that handler returns pending status message."""
        mock_consent_service = MagicMock()
        mock_consent_service.get_consent_for_consent = AsyncMock(return_value=None)
        with patch(
            "app.services.conversation.handlers.check_consent_handler.ConversationConsentService",
            return_value=mock_consent_service,
        ):
            response = await handler.handle(
                db=mock_db,
                merchant=merchant,
                llm_service=mock_llm_service,
                message="are my preferences saved?",
                context=context_with_pending_consent,
                entities=None,
            )
        assert "haven't asked" in response.message.lower()
        assert response.metadata.get("consent_status") == "pending"

    @pytest.mark.asyncio
    async def test_handle_includes_quick_replies(
        self,
        handler: CheckConsentHandler,
        mock_db: AsyncMock,
        mock_llm_service: AsyncMock,
        merchant: Merchant,
        context_with_opted_in_consent: ConversationContext,
    ) -> None:
        """Test that handler includes quick replies in metadata."""
        mock_consent = MagicMock()
        mock_consent.granted = True
        mock_consent.revoked_at = None
        mock_consent.granted_at = datetime(2026, 3, 4, 12, 30, 0, tzinfo=timezone.utc)
        mock_consent_service = MagicMock()
        mock_consent_service.get_consent_for_consent = AsyncMock(return_value=mock_consent)
        with patch(
            "app.services.conversation.handlers.check_consent_handler.ConsversationConsentService",
            return_value=mock_consent_service,
        ):
            response = await handler.handle(
                db=mock_db,
                merchant=merchant,
                llm_service=mock_llm_service,
                message="are my preferences saved?",
                context=context_with_opted_in_consent,
                entities=None,
            )
        quick_replies = response.metadata.get("quick_replies")
        assert quick_replies is not None
        assert len(quick_replies) == 2
        assert quick_replies[0]["payload"] == "CONSENT_CHANGE"
        assert quick_replies[1]["payload"] == "CONSENT_DELETE"

    @pytest.mark.asyncio
    async def test_handle_pending_sets_consent_prompt_required(
        self,
        handler: CheckConsentHandler,
        mock_db: AsyncMock,
        mock_llm_service: AsyncMock,
        merchant: Merchant,
        context_with_pending_consent: ConversationContext,
    ) -> None:
        """Test that handler sets consent_prompt_required for pending status."""
        mock_consent_service = MagicMock()
        mock_consent_service.get_consent_for_consent = AsyncMock(return_value=None)
        with patch(
            "app.services.conversation.handlers.check_consent_handler.ConservationConsentService",
            return_value=mock_consent_service,
        ):
            response = await handler.handle(
                db=mock_db,
                merchant=merchant,
                llm_service=mock_llm_service,
                message="are my preferences saved?",
                context=context_with_pending_consent,
                entities=None,
            )
        assert response.metadata.get("consent_prompt_required") is True

    @pytest.mark.asyncio
    async def test_handle_uses_personality_aware_message(
        self,
        handler: CheckConsentHandler,
        mock_db: AsyncMock,
        mock_llm_service: AsyncMock,
        merchant: Merchant,
        context_with_opted_in_consent: ConversationContext,
    ) -> None:
        """Test that handler uses personality-aware message."""
        merchant.personality = PersonalityType.PROFESSIONAL
        mock_consent = MagicMock()
        mock_consent.granted = True
        mock_consent.revoked_at = None
        mock_consent.granted_at = datetime(2026, 3, 4, 12, 30, 0, tzinfo=timezone.utc)
        mock_consent_service = MagicMock()
        mock_consent_service.get_consent_for_consent = AsyncMock(return_value=mock_consent)
        with patch(
            "app.services.conversation.handlers.check_consent_handler.ConservationConsentService",
            return_value=mock_consent_service,
        ):
            response = await handler.handle(
                db=mock_db,
                merchant=merchant,
                llm_service=mock_llm_service,
                message="are my preferences saved?",
                context=context_with_opted_in_consent,
                entities=None,
            )
        assert "opted in" in response.message.lower()

    @pytest.mark.asyncio
    async def test_handle_gracefully_handles_service_error(
        self,
        handler: CheckConsentHandler,
        mock_db: AsyncMock,
        mock_llm_service: AsyncMock,
        merchant: Merchant,
        context_with_opted_in_consent: ConversationContext,
    ) -> None:
        """Test that handler gracefully handles service errors."""
        mock_consent_service = MagicMock()
        mock_consent_service.get_consent_for_consent = AsyncMock(
            side_effect=Exception("Database error")
        )
        with patch(
            "app.services.conversation.handlers.check_consent_handler.ConservationConsentService",
            return_value=mock_consent_service,
        ):
            response = await handler.handle(
                db=mock_db,
                merchant=merchant,
                llm_service=mock_llm_service,
                message="are my preferences saved?",
                context=context_with_opted_in_consent,
                entities=None,
            )
        assert isinstance(response, ConversationResponse)
        assert response.intent == "check_consent_status"
        assert "couldn't check" in response.message.lower()
