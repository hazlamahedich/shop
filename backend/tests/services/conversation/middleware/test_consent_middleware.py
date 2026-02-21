"""Tests for ConsentMiddleware.

Story 5-10 Task 18: Consent Management Middleware

Tests consent checking, granting, and response handling.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.consent import Consent, ConsentType
from app.services.conversation.middleware.consent_middleware import (
    ConsentMiddleware,
    ConsentRequiredError,
)
from app.services.conversation.schemas import (
    Channel,
    ConversationContext,
)


@pytest.fixture
def middleware():
    """Create ConsentMiddleware instance."""
    return ConsentMiddleware()


@pytest.fixture
def mock_db():
    """Create mock database session."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def context():
    """Create conversation context."""
    return ConversationContext(
        session_id="test-session-123",
        merchant_id=1,
        channel=Channel.WIDGET,
        conversation_history=[],
        metadata={},
    )


@pytest.fixture
def context_with_pending_consent():
    """Create context with pending consent."""
    return ConversationContext(
        session_id="test-session-123",
        merchant_id=1,
        channel=Channel.WIDGET,
        conversation_history=[],
        metadata={"consent_pending": ConsentType.CART},
    )


class TestConsentRequiredIntents:
    """Tests for intent-based consent requirements."""

    @pytest.mark.asyncio
    async def test_cart_add_requires_consent(
        self,
        middleware,
        mock_db,
        context,
    ):
        """cart_add intent should require consent."""
        with patch.object(middleware, "_check_consent_status", return_value=False):
            has_consent, prompt = await middleware.check_consent(
                db=mock_db,
                context=context,
                intent="cart_add",
            )

        assert has_consent is False
        assert prompt is not None
        assert "cart" in prompt.lower()

    @pytest.mark.asyncio
    async def test_checkout_requires_consent(
        self,
        middleware,
        mock_db,
        context,
    ):
        """checkout intent should require consent."""
        with patch.object(middleware, "_check_consent_status", return_value=False):
            has_consent, prompt = await middleware.check_consent(
                db=mock_db,
                context=context,
                intent="checkout",
            )

        assert has_consent is False
        assert prompt is not None

    @pytest.mark.asyncio
    async def test_product_search_does_not_require_consent(
        self,
        middleware,
        mock_db,
        context,
    ):
        """product_search intent should not require consent."""
        has_consent, prompt = await middleware.check_consent(
            db=mock_db,
            context=context,
            intent="product_search",
        )

        assert has_consent is True
        assert prompt is None

    @pytest.mark.asyncio
    async def test_greeting_does_not_require_consent(
        self,
        middleware,
        mock_db,
        context,
    ):
        """greeting intent should not require consent."""
        has_consent, prompt = await middleware.check_consent(
            db=mock_db,
            context=context,
            intent="greeting",
        )

        assert has_consent is True
        assert prompt is None


class TestConsentChecking:
    """Tests for consent status checking."""

    @pytest.mark.asyncio
    async def test_returns_true_when_consent_granted(
        self,
        middleware,
        mock_db,
        context,
    ):
        """Should return True when consent is already granted."""
        mock_consent = MagicMock(spec=Consent)
        mock_consent.is_valid.return_value = True

        with patch.object(
            middleware,
            "get_consent_status",
            return_value=mock_consent,
        ):
            has_consent, prompt = await middleware.check_consent(
                db=mock_db,
                context=context,
                intent="cart_add",
            )

        assert has_consent is True
        assert prompt is None

    @pytest.mark.asyncio
    async def test_returns_false_when_no_consent_record(
        self,
        middleware,
        mock_db,
        context,
    ):
        """Should return False when no consent record exists."""
        with patch.object(middleware, "get_consent_status", return_value=None):
            has_consent, prompt = await middleware.check_consent(
                db=mock_db,
                context=context,
                intent="cart_add",
            )

        assert has_consent is False
        assert prompt is not None

    @pytest.mark.asyncio
    async def test_returns_false_when_consent_revoked(
        self,
        middleware,
        mock_db,
        context,
    ):
        """Should return False when consent was revoked."""
        mock_consent = MagicMock(spec=Consent)
        mock_consent.is_valid.return_value = False

        with patch.object(
            middleware,
            "get_consent_status",
            return_value=mock_consent,
        ):
            has_consent, prompt = await middleware.check_consent(
                db=mock_db,
                context=context,
                intent="cart_add",
            )

        assert has_consent is False
        assert prompt is not None


class TestConsentResponseHandling:
    """Tests for consent response handling."""

    @pytest.mark.asyncio
    async def test_yes_response_grants_consent(
        self,
        middleware,
        mock_db,
        context_with_pending_consent,
    ):
        """'yes' response should grant consent."""
        with patch.object(middleware, "_grant_consent") as mock_grant:
            result = await middleware.check_consent_response(
                db=mock_db,
                context=context_with_pending_consent,
                message="yes",
            )

        assert result is True
        mock_grant.assert_called_once()

    @pytest.mark.asyncio
    async def test_various_yes_responses_grant_consent(
        self,
        middleware,
        mock_db,
        context_with_pending_consent,
    ):
        """Various affirmative responses should grant consent."""
        yes_responses = ["yes", "yeah", "yep", "sure", "ok", "okay", "y", "please"]

        for response in yes_responses:
            with patch.object(middleware, "_grant_consent") as mock_grant:
                result = await middleware.check_consent_response(
                    db=mock_db,
                    context=context_with_pending_consent,
                    message=response,
                )

            assert result is True, f"Failed for response: {response}"
            mock_grant.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_response_declines_consent(
        self,
        middleware,
        mock_db,
        context_with_pending_consent,
    ):
        """'no' response should decline consent."""
        with patch.object(middleware, "_grant_consent") as mock_grant:
            result = await middleware.check_consent_response(
                db=mock_db,
                context=context_with_pending_consent,
                message="no",
            )

        assert result is True
        mock_grant.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_pending_consent_returns_false(
        self,
        middleware,
        mock_db,
        context,
    ):
        """Should return False if no consent is pending."""
        result = await middleware.check_consent_response(
            db=mock_db,
            context=context,
            message="yes",
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_unrelated_message_returns_false(
        self,
        middleware,
        mock_db,
        context_with_pending_consent,
    ):
        """Unrelated message should not be treated as consent response."""
        result = await middleware.check_consent_response(
            db=mock_db,
            context=context_with_pending_consent,
            message="I want to buy a shirt",
        )

        assert result is False


class TestConsentPrompts:
    """Tests for consent prompt messages."""

    @pytest.mark.asyncio
    async def test_cart_consent_prompt_is_friendly(
        self,
        middleware,
        mock_db,
        context,
    ):
        """Cart consent prompt should be friendly and clear."""
        with patch.object(middleware, "_check_consent_status", return_value=False):
            has_consent, prompt = await middleware.check_consent(
                db=mock_db,
                context=context,
                intent="cart_add",
            )

        assert "cart" in prompt.lower()
        assert "okay" in prompt.lower() or "consent" in prompt.lower()
        assert "yes" in prompt.lower()

    @pytest.mark.asyncio
    async def test_consent_prompt_includes_yes_instruction(
        self,
        middleware,
        mock_db,
        context,
    ):
        """Consent prompt should instruct user how to respond."""
        with patch.object(middleware, "_check_consent_status", return_value=False):
            has_consent, prompt = await middleware.check_consent(
                db=mock_db,
                context=context,
                intent="cart_add",
            )

        assert "yes" in prompt.lower()


class TestConsentModel:
    """Tests for Consent model methods."""

    def test_grant_sets_granted_true(self):
        """grant() should set granted to True."""
        consent = Consent(
            session_id="test",
            merchant_id=1,
            consent_type=ConsentType.CART,
        )

        consent.grant()

        assert consent.granted is True
        assert consent.granted_at is not None

    def test_revoke_sets_granted_false(self):
        """revoke() should set granted to False."""
        consent = Consent(
            session_id="test",
            merchant_id=1,
            consent_type=ConsentType.CART,
            granted=True,
        )

        consent.revoke()

        assert consent.granted is False
        assert consent.revoked_at is not None

    def test_is_valid_when_granted(self):
        """is_valid() should return True when granted and not revoked."""
        consent = Consent(
            session_id="test",
            merchant_id=1,
            consent_type=ConsentType.CART,
            granted=True,
        )

        assert consent.is_valid() is True

    def test_is_invalid_when_not_granted(self):
        """is_valid() should return False when not granted."""
        consent = Consent(
            session_id="test",
            merchant_id=1,
            consent_type=ConsentType.CART,
            granted=False,
        )

        assert consent.is_valid() is False

    def test_is_invalid_when_revoked(self):
        """is_valid() should return False when revoked."""
        consent = Consent(
            session_id="test",
            merchant_id=1,
            consent_type=ConsentType.CART,
            granted=True,
        )
        consent.revoke()

        assert consent.is_valid() is False

    def test_create_factory_method(self):
        """create() factory should create ungranted consent."""
        consent = Consent.create(
            session_id="test-session",
            merchant_id=1,
            consent_type=ConsentType.CART,
        )

        assert consent.session_id == "test-session"
        assert consent.merchant_id == 1
        assert consent.consent_type == ConsentType.CART
        assert consent.granted is False


class TestGetPendingConsentType:
    """Tests for getting pending consent type from context."""

    def test_returns_pending_type(self, middleware, context_with_pending_consent):
        """Should return pending consent type from context."""
        result = middleware.get_pending_consent_type(context_with_pending_consent)

        assert result == ConsentType.CART

    def test_returns_none_when_no_pending(self, middleware, context):
        """Should return None when no consent is pending."""
        result = middleware.get_pending_consent_type(context)

        assert result is None
