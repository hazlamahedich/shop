"""Sentiment-adaptive response service for conversation pipeline (Story 11-10).

Wraps SentimentAnalyzer to detect emotional tone in customer messages,
map detected sentiment to response strategies, track sentiment history,
and determine when auto-escalation to human handoff should occur.

Architecture: Post-processing layer — sentiment adaptation wraps handler
responses with pre/post phrases; it does NOT replace the handler pipeline.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any

import structlog

from app.core.errors import ErrorCode
from app.services.analytics.sentiment_analyzer import (
    Sentiment,
    SentimentScore,
    get_sentiment_score,
)
from app.services.conversation.schemas import ConversationContext

logger = structlog.get_logger(__name__)

URGENCY_KEYWORDS = frozenset({"urgent", "asap", "emergency", "right now", "immediately", "hurry"})

FRUSTRATION_KEYWORDS = frozenset(
    {
        "frustrated",
        "angry",
        "upset",
        "annoyed",
        "unacceptable",
        "ridiculous",
        "terrible",
        "horrible",
        "awful",
        "hate",
    }
)

MARKDOWN_BOLD_ITALIC_RE = re.compile(r"(?:\*\*|__|\*|_)(?=\s|$|[^*])", re.MULTILINE)


class SentimentStrategy(str, Enum):
    EMPATHETIC = "empathetic"
    CONCISE = "concise"
    DETAILED = "detailed"
    ENTHUSIASTIC = "enthusiastic"
    NONE = "none"


@dataclass
class SentimentAdaptation:
    strategy: SentimentStrategy
    original_score: SentimentScore
    pre_phrase_key: str
    post_phrase_key: str
    mode: str = "ecommerce"


class SentimentAdapterService:
    ESCALATION_THRESHOLD: float = 0.85
    _MAX_HISTORY: int = 10

    def analyze_sentiment(self, message: str, mode: str = "ecommerce") -> SentimentAdaptation:
        try:
            score = get_sentiment_score(message)
            strategy = self._map_strategy(message, score)
            pre_key = f"pre_{strategy.value}" if strategy != SentimentStrategy.NONE else ""
            post_key = f"post_{strategy.value}" if strategy != SentimentStrategy.NONE else ""
            return SentimentAdaptation(
                strategy=strategy,
                original_score=score,
                pre_phrase_key=pre_key,
                post_phrase_key=post_key,
                mode=mode,
            )
        except Exception:
            logger.exception(
                "sentiment_analysis_failed",
                error_code=ErrorCode.SENTIMENT_ANALYSIS_FAILED,
            )
            return SentimentAdaptation(
                strategy=SentimentStrategy.NONE,
                original_score=SentimentScore(
                    sentiment=Sentiment.NEUTRAL,
                    positive_score=0.0,
                    negative_score=0.0,
                    confidence=0.0,
                    matched_terms=[],
                ),
                pre_phrase_key="",
                post_phrase_key="",
                mode=mode,
            )

    def track_sentiment(
        self, context: ConversationContext, adaptation: SentimentAdaptation
    ) -> None:
        try:
            if context.metadata is None:
                context.metadata = {}
            history: list[dict[str, Any]] = context.metadata.get("sentiment_history", [])
            history.append(
                {
                    "turn": len(context.conversation_history),
                    "sentiment": adaptation.strategy.value,
                    "score": adaptation.original_score.confidence,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )
            if len(history) > self._MAX_HISTORY:
                history = history[-self._MAX_HISTORY :]
            context.metadata["sentiment_history"] = history
        except Exception:
            logger.exception(
                "sentiment_tracking_failed",
                error_code=ErrorCode.SENTIMENT_ANALYSIS_FAILED,
            )

    def should_escalate(
        self, context: ConversationContext, adaptation: SentimentAdaptation
    ) -> bool:
        try:
            if adaptation.strategy != SentimentStrategy.EMPATHETIC:
                return False
            pos = adaptation.original_score.positive_score
            neg = adaptation.original_score.negative_score
            total = max(pos + neg, 0.001)
            negative_ratio = neg / total
            if negative_ratio < self.ESCALATION_THRESHOLD:
                return False
            history: list[dict[str, Any]] = (context.metadata or {}).get("sentiment_history", [])
            if len(history) < 2:
                return False
            last_two = history[-2:]
            return all(
                entry.get("sentiment") == SentimentStrategy.EMPATHETIC.value for entry in last_two
            )
        except Exception:
            logger.exception(
                "sentiment_escalation_check_failed",
                error_code=ErrorCode.SENTIMENT_ADAPTATION_FAILED,
            )
            return False

    def _map_strategy(self, message: str, score: SentimentScore) -> SentimentStrategy:
        lower = message.lower()
        if self._is_empathetic(lower, score):
            return SentimentStrategy.EMPATHETIC
        if self._is_concise(lower, score):
            return SentimentStrategy.CONCISE
        if self._is_detailed(lower, score):
            return SentimentStrategy.DETAILED
        if self._is_enthusiastic(score):
            return SentimentStrategy.ENTHUSIASTIC
        return SentimentStrategy.NONE

    def _is_empathetic(self, lower: str, score: SentimentScore) -> bool:
        if score.sentiment != Sentiment.NEGATIVE:
            return False
        neg_ratio = score.negative_score / max(score.positive_score + score.negative_score, 0.001)
        has_frustration_kw = any(kw in lower for kw in FRUSTRATION_KEYWORDS)
        return neg_ratio > 0.6 or (neg_ratio > 0.4 and has_frustration_kw)

    def _is_concise(self, lower: str, score: SentimentScore) -> bool:
        if score.sentiment == Sentiment.POSITIVE:
            return False
        has_keyword = any(kw in lower for kw in URGENCY_KEYWORDS)
        if not has_keyword:
            return False
        cleaned = MARKDOWN_BOLD_ITALIC_RE.sub("", lower)
        words = cleaned.split()
        alpha_words = [w for w in words if any(c.isalpha() for c in w)]
        caps_ratio = (
            sum(1 for w in alpha_words if w.isupper()) / len(alpha_words) if alpha_words else 0
        )
        excl_count = lower.count("!")
        return caps_ratio >= 0.5 or excl_count >= 3

    def _is_detailed(self, lower: str, score: SentimentScore) -> bool:
        from app.services.analytics.sentiment_analyzer import QUESTION_INDICATORS

        q_count = sum(1 for qi in QUESTION_INDICATORS if qi in lower)
        question_marks = lower.count("?")
        if q_count >= 2:
            return score.sentiment in (Sentiment.NEUTRAL, Sentiment.NEGATIVE)
        if q_count >= 1 and question_marks >= 2:
            return score.sentiment in (Sentiment.NEUTRAL, Sentiment.NEGATIVE)
        return False

    def _is_enthusiastic(self, score: SentimentScore) -> bool:
        if score.sentiment != Sentiment.POSITIVE:
            return False
        return score.confidence >= 0.3
