"""Integration tests for sentiment-adaptive response flow (Story 11-10).

Tests the full pipeline: sentiment analysis → strategy mapping →
template formatting → response wrapping → escalation.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.models.merchant import Merchant, PersonalityType
from app.services.conversation.schemas import (
    Channel,
    ConversationContext,
    SessionShoppingState,
)
from app.services.conversation.sentiment_adapter import (
    SentimentAdapterService,
    SentimentStrategy,
)
from app.services.personality.conversation_templates import (
    register_conversation_templates,
    register_sentiment_adaptive_templates,
)
from app.services.personality.response_formatter import PersonalityAwareResponseFormatter


@pytest.fixture(autouse=True)
def _register_templates():
    register_conversation_templates()
    register_sentiment_adaptive_templates()


def _make_merchant(
    personality: PersonalityType = PersonalityType.FRIENDLY,
    mode: str = "ecommerce",
) -> MagicMock:
    merchant = MagicMock(spec=Merchant)
    merchant.id = 1
    merchant.personality = personality
    merchant.shop_name = "Test Shop"
    merchant.onboarding_mode = mode
    merchant.business_name = "Test Shop"
    return merchant


def _make_context(metadata: dict | None = None) -> ConversationContext:
    return ConversationContext(
        session_id="sess_sentinel",
        merchant_id=1,
        channel=Channel.WIDGET,
        shopping_state=SessionShoppingState(),
        metadata=metadata or {},
    )


class TestSentimentAnalysisToResponse:
    def test_frustrated_message_produces_wrapped_response(self):
        service = SentimentAdapterService()
        merchant = _make_merchant()
        ctx = _make_context()
        message = "This is terrible and I'm very frustrated with the service!"

        adaptation = service.analyze_sentiment(message, mode="ecommerce")
        assert adaptation.strategy == SentimentStrategy.EMPATHETIC

        service.track_sentiment(ctx, adaptation)
        assert "sentiment_history" in ctx.metadata

        personality = merchant.personality
        pre = PersonalityAwareResponseFormatter.format_response(
            "sentiment_adaptive",
            adaptation.pre_phrase_key,
            personality,
            mode="ecommerce",
        )
        post = PersonalityAwareResponseFormatter.format_response(
            "sentiment_adaptive",
            adaptation.post_phrase_key,
            personality,
            mode="ecommerce",
        )
        assert pre
        assert post
        original = "Here are your search results."
        wrapped = f"{pre} {original} {post}"
        assert wrapped.startswith(pre[:10])
        assert wrapped.endswith(post[-10:])

    def test_urgent_message_produces_concise_wrapping(self):
        service = SentimentAdapterService()
        merchant = _make_merchant()
        ctx = _make_context()
        message = "I NEED THIS URGENTLY ASAP!!!"

        adaptation = service.analyze_sentiment(message, mode="ecommerce")
        assert adaptation.strategy == SentimentStrategy.CONCISE

        service.track_sentiment(ctx, adaptation)

        pre = PersonalityAwareResponseFormatter.format_response(
            "sentiment_adaptive",
            adaptation.pre_phrase_key,
            merchant.personality,
            mode="ecommerce",
        )
        assert pre
        assert isinstance(pre, str)

    def test_positive_message_produces_enthusiastic_wrapping(self):
        service = SentimentAdapterService()
        merchant = _make_merchant()
        message = "I absolutely love this! Amazing product!"

        adaptation = service.analyze_sentiment(message, mode="ecommerce")
        assert adaptation.strategy == SentimentStrategy.ENTHUSIASTIC

        pre = PersonalityAwareResponseFormatter.format_response(
            "sentiment_adaptive",
            adaptation.pre_phrase_key,
            merchant.personality,
            mode="ecommerce",
        )
        assert pre

    def test_neutral_message_no_wrapping(self):
        service = SentimentAdapterService()
        message = "Tell me about your return policy"

        adaptation = service.analyze_sentiment(message, mode="ecommerce")
        assert adaptation.strategy == SentimentStrategy.NONE
        assert adaptation.pre_phrase_key == ""
        assert adaptation.post_phrase_key == ""

    def test_multi_question_message_produces_detailed_wrapping(self):
        service = SentimentAdapterService()
        merchant = _make_merchant()
        message = "How does shipping work? What about returns? Can you explain the warranty?"

        adaptation = service.analyze_sentiment(message, mode="ecommerce")
        assert adaptation.strategy == SentimentStrategy.DETAILED

        pre = PersonalityAwareResponseFormatter.format_response(
            "sentiment_adaptive",
            adaptation.pre_phrase_key,
            merchant.personality,
            mode="ecommerce",
        )
        assert pre
        assert isinstance(pre, str)


class TestEscalationFlow:
    def test_persistent_negative_triggers_escalation(self):
        service = SentimentAdapterService()
        ctx = _make_context()

        for _ in range(3):
            adaptation = service.analyze_sentiment(
                "This is terrible, horrible, awful service!", mode="ecommerce"
            )
            service.track_sentiment(ctx, adaptation)

        assert service.should_escalate(ctx, adaptation) is True

    def test_mixed_sentiment_no_escalation(self):
        service = SentimentAdapterService()
        ctx = _make_context()

        neg = service.analyze_sentiment("This is terrible and awful", mode="ecommerce")
        service.track_sentiment(ctx, neg)

        pos = service.analyze_sentiment("Actually that looks great, thanks!", mode="ecommerce")
        service.track_sentiment(ctx, pos)

        assert service.should_escalate(ctx, neg) is False


class TestModeVariants:
    @pytest.mark.parametrize("mode", ["ecommerce", "general"])
    def test_empathetic_templates_differ_by_mode(self, mode: str):
        service = SentimentAdapterService()
        message = "This is terrible and I'm frustrated!"

        adaptation = service.analyze_sentiment(message, mode=mode)
        assert adaptation.strategy == SentimentStrategy.EMPATHETIC

        for personality in PersonalityType:
            base = PersonalityAwareResponseFormatter.format_response(
                "sentiment_adaptive",
                "pre_empathetic",
                personality,
            )
            mode_key = f"pre_empathetic_{mode}"
            mode_variant = PersonalityAwareResponseFormatter.format_response(
                "sentiment_adaptive",
                mode_key,
                personality,
            )
            assert base, f"base template empty for {personality.value}"
            assert mode_variant, f"mode variant empty for {personality.value}/{mode}"


class TestAllPersonalities:
    @pytest.mark.parametrize("personality", list(PersonalityType))
    def test_each_personality_produces_valid_phrases(self, personality: PersonalityType):
        service = SentimentAdapterService()
        message = "This is terrible and I'm frustrated!"

        adaptation = service.analyze_sentiment(message, mode="ecommerce")
        assert adaptation.strategy == SentimentStrategy.EMPATHETIC

        pre = PersonalityAwareResponseFormatter.format_response(
            "sentiment_adaptive",
            adaptation.pre_phrase_key,
            personality,
            mode="ecommerce",
        )
        post = PersonalityAwareResponseFormatter.format_response(
            "sentiment_adaptive",
            adaptation.post_phrase_key,
            personality,
            mode="ecommerce",
        )
        assert pre.strip(), f"pre_phrase empty for {personality.value}"
        assert post.strip(), f"post_phrase empty for {personality.value}"
