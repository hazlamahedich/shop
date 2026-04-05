"""Unit tests for SentimentAdapterService (Story 11-10).

Tests sentiment strategy mapping, tracking, and escalation logic.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from app.services.analytics.sentiment_analyzer import Sentiment, SentimentScore
from app.services.conversation.schemas import (
    Channel,
    ConversationContext,
    SessionShoppingState,
)
from app.services.conversation.sentiment_adapter import (
    SentimentAdapterService,
    SentimentAdaptation,
    SentimentStrategy,
)
from app.services.personality.conversation_templates import (
    register_sentiment_adaptive_templates,
)


@pytest.fixture(autouse=True)
def _register_templates():
    register_sentiment_adaptive_templates()


@pytest.fixture
def service():
    return SentimentAdapterService()


def _make_context(metadata: dict | None = None) -> ConversationContext:
    return ConversationContext(
        session_id="sess_test",
        merchant_id=1,
        channel=Channel.WIDGET,
        shopping_state=SessionShoppingState(),
        metadata=metadata or {},
    )


def _make_score(
    sentiment: Sentiment = Sentiment.NEUTRAL,
    positive: float = 0.0,
    negative: float = 0.0,
    confidence: float = 0.5,
) -> SentimentScore:
    return SentimentScore(
        sentiment=sentiment,
        positive_score=positive,
        negative_score=negative,
        confidence=confidence,
        matched_terms=[],
    )


class TestAnalyzeSentiment:
    def test_frustrated_message_maps_to_empathetic(self, service: SentimentAdapterService):
        adaptation = service.analyze_sentiment("This is terrible and I'm very frustrated")
        assert adaptation.strategy == SentimentStrategy.EMPATHETIC
        assert adaptation.pre_phrase_key == "pre_empathetic"
        assert adaptation.post_phrase_key == "post_empathetic"

    def test_urgent_caps_maps_to_concise(self, service: SentimentAdapterService):
        adaptation = service.analyze_sentiment("I NEED THIS URGENTLY ASAP!!!")
        assert adaptation.strategy == SentimentStrategy.CONCISE

    def test_positive_message_maps_to_enthusiastic(self, service: SentimentAdapterService):
        adaptation = service.analyze_sentiment("I love this product! It's amazing and wonderful!")
        assert adaptation.strategy == SentimentStrategy.ENTHUSIASTIC

    def test_neutral_message_maps_to_none(self, service: SentimentAdapterService):
        adaptation = service.analyze_sentiment("Tell me about your products")
        assert adaptation.strategy == SentimentStrategy.NONE
        assert adaptation.pre_phrase_key == ""
        assert adaptation.post_phrase_key == ""

    def test_exception_returns_none_strategy(self, service: SentimentAdapterService):
        with patch(
            "app.services.conversation.sentiment_adapter.get_sentiment_score",
            side_effect=RuntimeError("boom"),
        ):
            adaptation = service.analyze_sentiment("anything")
        assert adaptation.strategy == SentimentStrategy.NONE


class TestTrackSentiment:
    def test_appends_to_history(self, service: SentimentAdapterService):
        ctx = _make_context()
        adaptation = SentimentAdaptation(
            strategy=SentimentStrategy.EMPATHETIC,
            original_score=_make_score(confidence=0.7),
            pre_phrase_key="pre_empathetic",
            post_phrase_key="post_empathetic",
        )
        service.track_sentiment(ctx, adaptation)
        history = ctx.metadata["sentiment_history"]
        assert len(history) == 1
        assert history[0]["sentiment"] == "empathetic"

    def test_trims_history_to_max(self, service: SentimentAdapterService):
        ctx = _make_context()
        adaptation = SentimentAdaptation(
            strategy=SentimentStrategy.EMPATHETIC,
            original_score=_make_score(),
            pre_phrase_key="pre_empathetic",
            post_phrase_key="post_empathetic",
        )
        for i in range(15):
            service.track_sentiment(ctx, adaptation)
        history = ctx.metadata["sentiment_history"]
        assert len(history) == service._MAX_HISTORY

    def test_creates_metadata_if_none(self, service: SentimentAdapterService):
        ctx = _make_context(metadata=None)
        adaptation = SentimentAdaptation(
            strategy=SentimentStrategy.CONCISE,
            original_score=_make_score(),
            pre_phrase_key="pre_concise",
            post_phrase_key="post_concise",
        )
        service.track_sentiment(ctx, adaptation)
        assert "sentiment_history" in ctx.metadata


class TestShouldEscalate:
    def test_escalates_when_empathetic_and_high_negative_ratio(
        self, service: SentimentAdapterService
    ):
        ctx = _make_context()
        adaptation = SentimentAdaptation(
            strategy=SentimentStrategy.EMPATHETIC,
            original_score=_make_score(
                sentiment=Sentiment.NEGATIVE, positive=0.0, negative=10.0, confidence=0.9
            ),
            pre_phrase_key="pre_empathetic",
            post_phrase_key="post_empathetic",
        )
        service.track_sentiment(ctx, adaptation)
        service.track_sentiment(ctx, adaptation)
        assert service.should_escalate(ctx, adaptation) is True

    def test_no_escalate_when_not_empathetic(self, service: SentimentAdapterService):
        ctx = _make_context()
        adaptation = SentimentAdaptation(
            strategy=SentimentStrategy.CONCISE,
            original_score=_make_score(),
            pre_phrase_key="pre_concise",
            post_phrase_key="post_concise",
        )
        assert service.should_escalate(ctx, adaptation) is False

    def test_no_escalate_when_low_negative_ratio(self, service: SentimentAdapterService):
        ctx = _make_context()
        adaptation = SentimentAdaptation(
            strategy=SentimentStrategy.EMPATHETIC,
            original_score=_make_score(
                sentiment=Sentiment.NEGATIVE, positive=5.0, negative=2.0, confidence=0.5
            ),
            pre_phrase_key="pre_empathetic",
            post_phrase_key="post_empathetic",
        )
        service.track_sentiment(ctx, adaptation)
        service.track_sentiment(ctx, adaptation)
        assert service.should_escalate(ctx, adaptation) is False

    def test_no_escalate_when_insufficient_history(self, service: SentimentAdapterService):
        ctx = _make_context()
        adaptation = SentimentAdaptation(
            strategy=SentimentStrategy.EMPATHETIC,
            original_score=_make_score(
                sentiment=Sentiment.NEGATIVE, positive=0.0, negative=10.0, confidence=0.9
            ),
            pre_phrase_key="pre_empathetic",
            post_phrase_key="post_empathetic",
        )
        service.track_sentiment(ctx, adaptation)
        assert service.should_escalate(ctx, adaptation) is False

    def test_no_escalate_when_history_not_consecutive_empathetic(
        self, service: SentimentAdapterService
    ):
        ctx = _make_context()
        empathetic = SentimentAdaptation(
            strategy=SentimentStrategy.EMPATHETIC,
            original_score=_make_score(
                sentiment=Sentiment.NEGATIVE, positive=0.0, negative=10.0, confidence=0.9
            ),
            pre_phrase_key="pre_empathetic",
            post_phrase_key="post_empathetic",
        )
        concise = SentimentAdaptation(
            strategy=SentimentStrategy.CONCISE,
            original_score=_make_score(),
            pre_phrase_key="pre_concise",
            post_phrase_key="post_concise",
        )
        service.track_sentiment(ctx, empathetic)
        service.track_sentiment(ctx, concise)
        assert service.should_escalate(ctx, empathetic) is False


class TestStrategyMapping:
    def test_empathetic_with_frustration_keyword(self, service: SentimentAdapterService):
        score = _make_score(sentiment=Sentiment.NEGATIVE, positive=1.0, negative=2.0)
        assert service._is_empathetic("I'm angry about this", score) is True

    def test_concise_with_urgency_and_excl(self, service: SentimentAdapterService):
        score = _make_score()
        assert service._is_concise("i need this urgently asap!!!", score) is True

    def test_not_concise_without_caps_or_excl(self, service: SentimentAdapterService):
        score = _make_score()
        assert service._is_concise("i need this urgently please", score) is False

    def test_detailed_with_multiple_questions(self, service: SentimentAdapterService):
        score = _make_score(sentiment=Sentiment.NEUTRAL)
        assert service._is_detailed("how does this work? what about the warranty?", score) is True

    def test_enthusiastic_with_positive_high_confidence(self, service: SentimentAdapterService):
        score = _make_score(sentiment=Sentiment.POSITIVE, positive=3.0, confidence=0.6)
        assert service._is_enthusiastic(score) is True

    def test_not_enthusiastic_low_confidence(self, service: SentimentAdapterService):
        score = _make_score(sentiment=Sentiment.POSITIVE, positive=0.5, confidence=0.1)
        assert service._is_enthusiastic(score) is False
