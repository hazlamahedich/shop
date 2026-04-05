from __future__ import annotations

from typing import Any

import pytest

from app.services.conversation.schemas import (
    Channel,
    ClarificationState,
    ConversationContext,
    SessionShoppingState,
)
from app.services.conversation.sentiment_adapter import (
    SentimentAdaptation,
    SentimentStrategy,
)
from app.services.analytics.sentiment_analyzer import Sentiment, SentimentScore


@pytest.fixture
def make_context():
    def _factory(
        history: list[dict[str, Any]] | None = None,
        clarification_state: ClarificationState | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ConversationContext:
        return ConversationContext(
            session_id="sess-test",
            merchant_id=1,
            channel=Channel.WIDGET,
            shopping_state=SessionShoppingState(),
            conversation_history=history or [],
            clarification_state=clarification_state or ClarificationState(),
            metadata=metadata or {},
        )

    return _factory


@pytest.fixture
def make_sentiment_adaptation():
    def _factory(
        strategy: SentimentStrategy = SentimentStrategy.EMPATHETIC,
        confidence: float = 0.8,
    ) -> SentimentAdaptation:
        return SentimentAdaptation(
            strategy=strategy,
            original_score=SentimentScore(
                sentiment=Sentiment.NEGATIVE,
                positive_score=0.1,
                negative_score=0.8,
                confidence=confidence,
                matched_terms=["frustrated"],
            ),
            pre_phrase_key=f"pre_{strategy.value}",
            post_phrase_key=f"post_{strategy.value}",
            mode="ecommerce",
        )

    return _factory


@pytest.fixture(autouse=True)
def _reset_turn_write_metrics():
    from app.services.conversation.unified_conversation_service import (
        UnifiedConversationService,
    )

    saved = dict(UnifiedConversationService._turn_write_metrics)
    yield
    UnifiedConversationService._turn_write_metrics.update(saved)
