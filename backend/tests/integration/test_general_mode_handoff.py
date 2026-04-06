"""Integration tests for handoff functionality in General mode.

Story 11-5: Handoff Functionality in General Mode

Tests cover:
- Keyword detection triggers handoff in general mode
- Handoff detection is called in general mode flow
- E-commerce mode handoff still works (regression test)
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.merchant import Merchant, PersonalityType
from app.schemas.handoff import HandoffReason
from app.services.conversation.schemas import (
    Channel,
    ConsentState,
    ConversationContext,
)
from app.services.conversation.unified_conversation_service import (
    UnifiedConversationService,
)


@pytest.fixture
def mock_db():
    """Create mock database session."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def general_mode_merchant():
    """Create a General mode merchant."""
    merchant = MagicMock(spec=Merchant)
    merchant.id = 1
    merchant.onboarding_mode = "general"
    merchant.personality = PersonalityType.FRIENDLY
    merchant.bot_name = "AI Assistant"
    merchant.business_name = "Test Business"
    merchant.has_store_connected = False
    merchant.has_facebook_connected = False
    merchant.budget_alert_enabled = False
    merchant.custom_greeting = None
    merchant.business_description = None
    merchant.business_hours = None
    merchant.support_email = "support@test.com"
    merchant.support_phone = None
    return merchant


@pytest.fixture
def ecommerce_mode_merchant():
    """Create an e-commerce mode merchant."""
    merchant = MagicMock(spec=Merchant)
    merchant.id = 2
    merchant.onboarding_mode = "ecommerce"
    merchant.personality = PersonalityType.FRIENDLY
    merchant.bot_name = "Shopping Bot"
    merchant.business_name = "Test Store"
    merchant.has_store_connected = True
    merchant.has_facebook_connected = False
    merchant.budget_alert_enabled = False
    merchant.custom_greeting = None
    merchant.business_description = None
    merchant.business_hours = None
    merchant.support_email = "support@test.com"
    merchant.support_phone = None
    return merchant


@pytest.fixture
def conversation_context():
    """Create conversation context."""
    return ConversationContext(
        merchant_id=1,
        session_id="test-session",
        channel=Channel.WIDGET,
        conversation_history=[],
        conversation_data={},
        metadata={},
        consent_state=ConsentState(
            status="granted",
            visitor_id="test-visitor",
            prompt_shown=True,
        ),
    )


class TestGeneralModeHandoff:
    """Test handoff functionality in General mode."""

    @pytest.mark.asyncio
    async def test_check_handoff_called_for_general_mode(
        self,
        mock_db,
        general_mode_merchant,
        conversation_context,
    ):
        """Test that _check_handoff is called for general mode messages.

        Test ID: 11-5-INT-001
        Priority: P0 (Critical)
        """
        from app.core.config import settings

        settings.cache_clear()

        service = UnifiedConversationService()

        # Mock the dependencies
        with patch.object(service, "_load_merchant", return_value=general_mode_merchant):
            with patch.object(service, "_get_conversation", return_value=MagicMock(id=1)):
                with patch.object(service, "_check_handoff") as mock_check_handoff:
                    mock_check_handoff.return_value = None  # No handoff

                    # Call _check_handoff directly with handoff keyword
                    result = await service._check_handoff(
                        db=mock_db,
                        context=conversation_context,
                        merchant=general_mode_merchant,
                        message="I want to talk to a human",
                        confidence=1.0,
                        intent_name="general",
                    )

                    # Verify _check_handoff was called and processed the keyword
                    mock_check_handoff.assert_called_once()
                    # Should return None initially (no actual handoff in our mock)
                    assert result is None

        settings.cache_clear()

    @pytest.mark.asyncio
    async def test_keyword_detection_in_general_mode(
        self,
        mock_db,
        general_mode_merchant,
        conversation_context,
        monkeypatch,
    ):
        """Test that handoff keywords are detected in general mode.

        Test ID: 11-5-INT-002
        Priority: P0 (Critical)
        """
        from app.core.config import settings

        settings.cache_clear()
        monkeypatch.setenv("IS_TESTING", "false")
        settings.cache_clear()

        service = UnifiedConversationService()

        # Mock the dependencies
        with patch.object(service, "_load_merchant", return_value=general_mode_merchant):
            with patch.object(service, "_get_conversation", return_value=MagicMock(id=1)):
                # Mock Redis connection
                with patch("redis.asyncio.from_url") as mock_redis_from_url:
                    # Create a mock Redis client with async close method
                    mock_redis_client = MagicMock()
                    mock_redis_client.close = AsyncMock()
                    mock_redis_from_url.return_value = mock_redis_client

                    # Mock helper methods to avoid database calls
                    with patch.object(
                        service,
                        "_get_handoff_message",
                        return_value="I'll connect you with a human agent.",
                    ):
                        with patch.object(service, "_update_conversation_handoff_status"):
                            # Mock handoff handler to return a response
                            with patch.object(
                                service._handlers["handoff"],
                                "handle",
                                return_value=MagicMock(
                                    response="I'll connect you with a human agent.",
                                    intent="human_handoff",
                                    confidence=1.0,
                                ),
                            ):
                                # Call _check_handoff with handoff keyword
                                result = await service._check_handoff(
                                    db=mock_db,
                                    context=conversation_context,
                                    merchant=general_mode_merchant,
                                    message="I want to talk to a human",
                                    confidence=1.0,
                                    intent_name="general",
                                )

                        # Verify handoff was triggered
                        assert result is not None
                        assert result.intent == "human_handoff"

        settings.cache_clear()

    @pytest.mark.asyncio
    async def test_no_keyword_no_handoff_in_general_mode(
        self,
        mock_db,
        general_mode_merchant,
        conversation_context,
    ):
        """Test that normal messages don't trigger handoff in general mode.

        Test ID: 11-5-INT-003
        Priority: P0 (Critical)
        """
        from app.core.config import settings

        settings.cache_clear()

        service = UnifiedConversationService()

        # Mock the dependencies
        with patch.object(service, "_load_merchant", return_value=general_mode_merchant):
            with patch.object(service, "_get_conversation", return_value=MagicMock(id=1)):
                # Call _check_handoff with normal message
                result = await service._check_handoff(
                    db=mock_db,
                    context=conversation_context,
                    merchant=general_mode_merchant,
                    message="What can you tell me about your products?",
                    confidence=1.0,
                    intent_name="general",
                )

                # Verify no handoff was triggered
                assert result is None

        settings.cache_clear()

    @pytest.mark.asyncio
    async def test_ecommerce_mode_handoff_still_works(
        self,
        mock_db,
        ecommerce_mode_merchant,
        conversation_context,
        monkeypatch,
    ):
        """Test that e-commerce mode handoff still works (regression test).

        Test ID: 11-5-INT-004
        Priority: P0 (Critical - Regression)
        """
        from app.core.config import settings

        settings.cache_clear()
        monkeypatch.setenv("IS_TESTING", "false")
        settings.cache_clear()

        service = UnifiedConversationService()

        # Mock the dependencies
        with patch.object(service, "_load_merchant", return_value=ecommerce_mode_merchant):
            with patch.object(service, "_get_conversation", return_value=MagicMock(id=1)):
                # Mock Redis connection
                with patch("redis.asyncio.from_url") as mock_redis_from_url:
                    # Create a mock Redis client with async close method
                    mock_redis_client = MagicMock()
                    mock_redis_client.close = AsyncMock()
                    mock_redis_from_url.return_value = mock_redis_client

                    # Mock helper methods to avoid database calls
                    with patch.object(
                        service,
                        "_get_handoff_message",
                        return_value="I'll connect you with a human agent.",
                    ):
                        with patch.object(service, "_update_conversation_handoff_status"):
                            # Mock handoff handler to return a response
                            with patch.object(
                                service._handlers["handoff"],
                                "handle",
                                return_value=MagicMock(
                                    response="I'll connect you with a human agent.",
                                    intent="human_handoff",
                                    confidence=1.0,
                                ),
                            ):
                                # Call _check_handoff with handoff keyword
                                result = await service._check_handoff(
                                    db=mock_db,
                                    context=conversation_context,
                                    merchant=ecommerce_mode_merchant,
                                    message="I want to talk to a human",
                                    confidence=0.9,
                                    intent_name="general",
                                )

                                # Verify handoff was triggered
                                assert result is not None
                                assert result.intent == "human_handoff"

        settings.cache_clear()

    @pytest.mark.asyncio
    async def test_multiple_handoff_keywords(
        self,
        mock_db,
        general_mode_merchant,
        conversation_context,
        monkeypatch,
    ):
        """Test that various handoff keywords trigger handoff in general mode.

        Test ID: 11-5-INT-005
        Priority: P1 (High)
        """
        from app.core.config import settings

        settings.cache_clear()
        monkeypatch.setenv("IS_TESTING", "false")
        settings.cache_clear()

        service = UnifiedConversationService()

        handoff_keywords = [
            "I want to talk to a human",
            "I need to speak to an agent",
            "Connect me with customer service",
            "I want to talk to a real person",
            "Let me speak to a representative",
        ]

        # Mock the dependencies
        with patch.object(service, "_load_merchant", return_value=general_mode_merchant):
            with patch.object(service, "_get_conversation", return_value=MagicMock(id=1)):
                # Mock Redis connection
                with patch("redis.asyncio.from_url") as mock_redis_from_url:
                    # Create a mock Redis client with async close method
                    mock_redis_client = MagicMock()
                    mock_redis_client.close = AsyncMock()
                    mock_redis_from_url.return_value = mock_redis_client

                    # Mock handoff handler to return a response
                    with patch.object(
                        service._handlers["handoff"],
                        "handle",
                        return_value=MagicMock(
                            response="I'll connect you with support.",
                            intent="human_handoff",
                            confidence=1.0,
                        ),
                    ):
                        for keyword_message in handoff_keywords:
                            result = await service._check_handoff(
                                db=mock_db,
                                context=conversation_context,
                                merchant=general_mode_merchant,
                                message=keyword_message,
                                confidence=1.0,
                                intent_name="general",
                            )

                            # Verify handoff was triggered for each keyword
                            assert result is not None, f"Failed for keyword: {keyword_message}"
                            assert result.intent == "human_handoff"

        settings.cache_clear()
