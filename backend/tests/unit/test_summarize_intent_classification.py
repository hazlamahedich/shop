"""Unit tests for SUMMARIZE intent pattern detection (Story 11-9).

Tests the _check_summarize_pattern method on UnifiedConversationService.
Validates tight ^...$ anchoring prevents false matches.
"""

from __future__ import annotations

import pytest

from app.services.intent.classification_schema import IntentType as ClassifierIntentType


def _get_service():
    """Create a real UnifiedConversationService for pattern testing."""
    from app.services.conversation.unified_conversation_service import UnifiedConversationService

    return UnifiedConversationService.__new__(UnifiedConversationService)


class TestSummarizePatternPositive:
    """Messages that SHOULD match SUMMARIZE intent."""

    @pytest.mark.parametrize(
        "message",
        [
            "recap",
            "Recap",
            "RECAP",
            "summarize",
            "Summarize",
            "SUMMARIZE",
            "summary",
            "quick recap",
            "Quick Recap",
            "recap!",
            "summarize?",
            "summary.",
            "quick recap!!!",
            "what did we discuss?",
            "what have we discussed?",
            "what did we talk about",
            "what have we talked about?",
            "what did we cover?",
            "What did we discuss?",
            "refresh my memory",
            "Refresh My Memory",
            "refresh my memory!",
            "catch me up",
            "Catch Me Up",
            "catch me up!",
            "summarize our conversation",
            "summarize this chat",
            "summarize the discussion",
            "give me a recap",
            "give me a summary",
            "give me an overview",
            "give me the recap",
            "give me the summary",
            "give me recap",
        ],
    )
    def test_positive_matches(self, message):
        svc = _get_service()
        result = svc._check_summarize_pattern(message)
        assert result == ClassifierIntentType.SUMMARIZE, f"Expected SUMMARIZE for: {message!r}"


class TestSummarizePatternNegative:
    """Messages that should NOT match SUMMARIZE intent (tight anchoring)."""

    @pytest.mark.parametrize(
        "message",
        [
            "summarize the return policy",
            "can you summarize what this product does",
            "recap the meeting notes",
            "I want a summary of the order",
            "please give me a summary of shipping costs",
            "what did we discuss about shoes",
            "can you catch me up on the order",
            "I need to recap the issues",
            "summarize our conversation about returns",
            "give me a recap of the cart",
            "I'd like a quick recap of products",
            "could you summarize the warranty",
            "what did the customer discuss",
            "refresh my memory about the product",
            "catch me up on what happened yesterday",
        ],
    )
    def test_negative_matches(self, message):
        svc = _get_service()
        result = svc._check_summarize_pattern(message)
        assert result is None, f"Expected None for: {message!r}"


class TestSummarizePatternEdge:
    """Edge cases for pattern detection."""

    def test_empty_string(self):
        svc = _get_service()
        assert svc._check_summarize_pattern("") is None

    def test_whitespace_only(self):
        svc = _get_service()
        assert svc._check_summarize_pattern("   ") is None

    def test_leading_trailing_whitespace_trimmed(self):
        svc = _get_service()
        assert svc._check_summarize_pattern("  recap  ") == ClassifierIntentType.SUMMARIZE

    def test_emoji_does_not_match(self):
        svc = _get_service()
        assert svc._check_summarize_pattern("summarize 🤔") is None

    def test_multi_word_non_matching(self):
        svc = _get_service()
        assert svc._check_summarize_pattern("hello how are you") is None

    def test_partial_word_no_match(self):
        svc = _get_service()
        assert svc._check_summarize_pattern("summarization") is None

    def test_recap_embedded_no_match(self):
        svc = _get_service()
        assert svc._check_summarize_pattern("the quick recap was helpful") is None
