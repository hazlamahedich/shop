"""Tests for FAQ preprocessor.

Story 5-10 Task 17: FAQ Pre-Processing

Tests FAQ matching before LLM processing.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.faq import Faq
from app.services.conversation.preprocessors.faq_preprocessor import (
    FAQPreprocessor,
    FAQPreprocessorMiddleware,
)
from app.services.conversation.schemas import (
    Channel,
    ConversationContext,
)


@pytest.fixture
def preprocessor():
    """Create FAQPreprocessor instance."""
    return FAQPreprocessor()


@pytest.fixture
def middleware():
    """Create FAQPreprocessorMiddleware instance."""
    return FAQPreprocessorMiddleware()


@pytest.fixture
def mock_db():
    """Create mock database session."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def mock_faqs():
    """Create mock FAQ list."""
    faq1 = MagicMock(spec=Faq)
    faq1.id = 1
    faq1.question = "What are your store hours?"
    faq1.answer = "We're open Monday-Friday 9am-6pm."
    faq1.keywords = "hours,open,time,schedule"
    faq1.order_index = 0

    faq2 = MagicMock(spec=Faq)
    faq2.id = 2
    faq2.question = "What is your return policy?"
    faq2.answer = "Returns accepted within 30 days with receipt."
    faq2.keywords = "return,refund,money back"
    faq2.order_index = 1

    faq3 = MagicMock(spec=Faq)
    faq3.id = 3
    faq3.question = "Do you offer shipping?"
    faq3.answer = "Yes, we offer free shipping on orders over $50."
    faq3.keywords = "shipping,delivery,ship"
    faq3.order_index = 2

    return [faq1, faq2, faq3]


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


class TestFAQPreprocessor:
    """Tests for FAQPreprocessor."""

    @pytest.mark.asyncio
    async def test_exact_question_match(
        self,
        preprocessor,
        mock_db,
        mock_faqs,
    ):
        """Exact question match should return FAQ answer."""
        with patch.object(
            preprocessor,
            "_get_merchant_faqs",
            return_value=mock_faqs,
        ):
            response = await preprocessor.check_faq(
                db=mock_db,
                merchant_id=1,
                message="What are your store hours?",
            )

        assert response is not None
        assert "9am-6pm" in response.message
        assert response.intent == "faq"
        assert response.confidence == 1.0

    @pytest.mark.asyncio
    async def test_keyword_match(
        self,
        preprocessor,
        mock_db,
        mock_faqs,
    ):
        """Keyword match should return FAQ answer."""
        with patch.object(
            preprocessor,
            "_get_merchant_faqs",
            return_value=mock_faqs,
        ):
            response = await preprocessor.check_faq(
                db=mock_db,
                merchant_id=1,
                message="When are you open?",
            )

        assert response is not None
        assert "9am-6pm" in response.message

    @pytest.mark.asyncio
    async def test_no_match_returns_none(
        self,
        preprocessor,
        mock_db,
        mock_faqs,
    ):
        """No FAQ match should return None."""
        with patch.object(
            preprocessor,
            "_get_merchant_faqs",
            return_value=mock_faqs,
        ):
            response = await preprocessor.check_faq(
                db=mock_db,
                merchant_id=1,
                message="I want to buy a shirt",
            )

        assert response is None

    @pytest.mark.asyncio
    async def test_empty_message_returns_none(
        self,
        preprocessor,
        mock_db,
    ):
        """Empty message should return None."""
        response = await preprocessor.check_faq(
            db=mock_db,
            merchant_id=1,
            message="",
        )

        assert response is None

    @pytest.mark.asyncio
    async def test_no_faqs_returns_none(
        self,
        preprocessor,
        mock_db,
    ):
        """No FAQs configured should return None."""
        with patch.object(
            preprocessor,
            "_get_merchant_faqs",
            return_value=[],
        ):
            response = await preprocessor.check_faq(
                db=mock_db,
                merchant_id=1,
                message="What are your hours?",
            )

        assert response is None

    @pytest.mark.asyncio
    async def test_response_includes_metadata(
        self,
        preprocessor,
        mock_db,
        mock_faqs,
    ):
        """Response should include FAQ metadata."""
        with patch.object(
            preprocessor,
            "_get_merchant_faqs",
            return_value=mock_faqs,
        ):
            response = await preprocessor.check_faq(
                db=mock_db,
                merchant_id=1,
                message="What are your store hours?",
            )

        assert response is not None
        assert response.metadata.get("faq_id") == 1
        assert response.metadata.get("faq_match_type") == "exact_question"
        assert "source" in response.metadata

    @pytest.mark.asyncio
    async def test_return_policy_match(
        self,
        preprocessor,
        mock_db,
        mock_faqs,
    ):
        """Return policy FAQ should match."""
        with patch.object(
            preprocessor,
            "_get_merchant_faqs",
            return_value=mock_faqs,
        ):
            response = await preprocessor.check_faq(
                db=mock_db,
                merchant_id=1,
                message="Can I get a refund?",
            )

        assert response is not None
        assert "30 days" in response.message

    @pytest.mark.asyncio
    async def test_shipping_match(
        self,
        preprocessor,
        mock_db,
        mock_faqs,
    ):
        """Shipping FAQ should match."""
        with patch.object(
            preprocessor,
            "_get_merchant_faqs",
            return_value=mock_faqs,
        ):
            response = await preprocessor.check_faq(
                db=mock_db,
                merchant_id=1,
                message="Do you ship to my area?",
            )

        assert response is not None
        assert "free shipping" in response.message.lower()


class TestFAQPreprocessorMiddleware:
    """Tests for FAQPreprocessorMiddleware."""

    @pytest.mark.asyncio
    async def test_process_returns_faq_response(
        self,
        middleware,
        mock_db,
        mock_faqs,
        context,
    ):
        """Middleware should return FAQ response when matched."""
        with patch.object(
            middleware.preprocessor,
            "_get_merchant_faqs",
            return_value=mock_faqs,
        ):
            response = await middleware.process(
                db=mock_db,
                context=context,
                message="What are your store hours?",
            )

        assert response is not None
        assert response.intent == "faq"

    @pytest.mark.asyncio
    async def test_process_returns_none_when_no_match(
        self,
        middleware,
        mock_db,
        mock_faqs,
        context,
    ):
        """Middleware should return None when no FAQ match."""
        with patch.object(
            middleware.preprocessor,
            "_get_merchant_faqs",
            return_value=mock_faqs,
        ):
            response = await middleware.process(
                db=mock_db,
                context=context,
                message="I want to buy something",
            )

        assert response is None

    @pytest.mark.asyncio
    async def test_should_skip_when_consent_pending(
        self,
        middleware,
    ):
        """Should skip FAQ processing when consent is pending."""
        context = ConversationContext(
            session_id="test-session",
            merchant_id=1,
            channel=Channel.WIDGET,
            conversation_history=[],
            metadata={"consent_pending": "cart"},
        )

        assert middleware.should_skip(context) is True

    @pytest.mark.asyncio
    async def test_should_skip_when_clarification_active(
        self,
        middleware,
    ):
        """Should skip FAQ processing during clarification flow."""
        context = ConversationContext(
            session_id="test-session",
            merchant_id=1,
            channel=Channel.WIDGET,
            conversation_history=[],
            metadata={"clarification": {"active": True}},
        )

        assert middleware.should_skip(context) is True

    @pytest.mark.asyncio
    async def test_should_not_skip_normal_flow(
        self,
        middleware,
        context,
    ):
        """Should not skip FAQ processing in normal flow."""
        assert middleware.should_skip(context) is False


class TestFAQPreprocessorCache:
    """Tests for FAQ preprocessor cache."""

    def test_clear_cache_specific_merchant(
        self,
        preprocessor,
    ):
        """Clear cache should remove specific merchant's FAQs."""
        preprocessor._faq_cache[1] = ([], 0.0)
        preprocessor._faq_cache[2] = ([], 0.0)

        preprocessor.clear_cache(merchant_id=1)

        assert 1 not in preprocessor._faq_cache
        assert 2 in preprocessor._faq_cache

    def test_clear_cache_all(
        self,
        preprocessor,
    ):
        """Clear cache with no merchant_id should clear all."""
        preprocessor._faq_cache[1] = ([], 0.0)
        preprocessor._faq_cache[2] = ([], 0.0)

        preprocessor.clear_cache()

        assert len(preprocessor._faq_cache) == 0


class TestFAQPreprocessorEdgeCases:
    """Tests for edge cases."""

    @pytest.mark.asyncio
    async def test_whitespace_message_returns_none(
        self,
        preprocessor,
        mock_db,
    ):
        """Whitespace-only message should return None."""
        response = await preprocessor.check_faq(
            db=mock_db,
            merchant_id=1,
            message="   ",
        )

        assert response is None

    @pytest.mark.asyncio
    async def test_case_insensitive_match(
        self,
        preprocessor,
        mock_db,
        mock_faqs,
    ):
        """FAQ match should be case insensitive."""
        with patch.object(
            preprocessor,
            "_get_merchant_faqs",
            return_value=mock_faqs,
        ):
            response = await preprocessor.check_faq(
                db=mock_db,
                merchant_id=1,
                message="WHAT ARE YOUR STORE HOURS?",
            )

        assert response is not None
        assert response.confidence == 1.0

    @pytest.mark.asyncio
    async def test_partial_question_match(
        self,
        preprocessor,
        mock_db,
        mock_faqs,
    ):
        """Partial question match should still return FAQ."""
        with patch.object(
            preprocessor,
            "_get_merchant_faqs",
            return_value=mock_faqs,
        ):
            response = await preprocessor.check_faq(
                db=mock_db,
                merchant_id=1,
                message="store hours",
            )

        assert response is not None
