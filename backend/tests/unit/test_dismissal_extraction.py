"""Unit tests for EcommerceContextExtractor._extract_dismissals (Story 11-6).

Tests dismissal phrase detection with parametrized test matrix covering
all enumerated phrases from AC4.
"""

from __future__ import annotations

import pytest

from app.services.context.ecommerce_extractor import EcommerceContextExtractor


@pytest.fixture
def extractor():
    return EcommerceContextExtractor()


@pytest.fixture
def context_with_viewed():
    return {
        "last_viewed_products": [{"id": 42, "title": "Test Product"}],
        "dismissed_products": [],
    }


@pytest.fixture
def context_empty():
    return {"last_viewed_products": [], "dismissed_products": []}


DISMISSAL_PHRASES = [
    "don't show me that",
    "don't recommend me this",
    "not interested",
    "don't like it",
    "no thanks",
    "skip that",
    "not for me",
    "not my style",
    "nope",
    "nah",
    "never mind",
    "forget about that",
    "something else",
    "anything else",
    "next",
    "no more",
]

NON_DISMISSAL_PHRASES = [
    "I love this product",
    "show me more like this",
    "what colors are available",
    "add to cart",
    "how much is this",
    "I want the red one",
    "yes please",
    "this looks great",
    "tell me more about this",
]


class TestDismissalPhraseDetection:
    @pytest.mark.parametrize("phrase", DISMISSAL_PHRASES)
    def test_dismissal_phrase_detected(self, extractor, phrase, context_with_viewed):
        result = extractor._extract_dismissals(phrase, context_with_viewed)
        assert result is not None
        assert isinstance(result, list)

    @pytest.mark.parametrize("phrase", NON_DISMISSAL_PHRASES)
    def test_non_dismissal_phrase_not_detected(self, extractor, phrase, context_with_viewed):
        result = extractor._extract_dismissals(phrase, context_with_viewed)
        assert result is None


class TestDismissalWithContext:
    def test_dismissal_adds_last_viewed_product(self, extractor, context_with_viewed):
        result = extractor._extract_dismissals("don't like it", context_with_viewed)
        assert 42 in result

    def test_dismissal_with_product_id_in_message(self, extractor, context_with_viewed):
        result = extractor._extract_dismissals("don't like product-99", context_with_viewed)
        assert 99 in result

    def test_dismissal_preserves_existing_dismissed(self, extractor):
        context = {
            "last_viewed_products": [{"id": 10, "title": "A"}],
            "dismissed_products": [5, 6],
        }
        result = extractor._extract_dismissals("not interested", context)
        assert 5 in result
        assert 6 in result

    def test_dismissal_no_viewed_products_no_product_id(self, extractor, context_empty):
        result = extractor._extract_dismissals("next", context_empty)
        assert result is None or result == []

    def test_dismissal_deduplicates_product_ids(self, extractor):
        context = {
            "last_viewed_products": [{"id": 42, "title": "Test"}],
            "dismissed_products": [42],
        }
        result = extractor._extract_dismissals("don't like it", context)
        assert result.count(42) <= 1


class TestDismissalCaseInsensitive:
    @pytest.mark.parametrize(
        "phrase",
        [
            "Don't Like It",
            "NOT INTERESTED",
            "Nope",
            "NEXT",
            "Skip That",
        ],
    )
    def test_case_insensitive_detection(self, extractor, phrase, context_with_viewed):
        result = extractor._extract_dismissals(phrase, context_with_viewed)
        assert result is not None


class TestDismissalWithExtraText:
    def test_dismissal_embedded_in_sentence(self, extractor, context_with_viewed):
        result = extractor._extract_dismissals(
            "Hmm, I'm not interested in that one", context_with_viewed
        )
        assert result is not None

    def test_dismissal_with_trailing_text(self, extractor, context_with_viewed):
        result = extractor._extract_dismissals(
            "no thanks, show me something else", context_with_viewed
        )
        assert result is not None
