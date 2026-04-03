"""Unit tests for EcommerceContextExtractor dismissal phrases (Story 11-6, AC4).

Parametrized tests covering all 17 dismissal phrase patterns extracted
from ecommerce_extractor.py to ensure each phrase correctly triggers
product dismissal.
"""

from __future__ import annotations

import pytest

from app.services.context.ecommerce_extractor import EcommerceContextExtractor


@pytest.fixture
def extractor():
    return EcommerceContextExtractor()


@pytest.fixture
def context_with_last_viewed():
    return {
        "last_viewed_products": [{"id": 42, "title": "Nike Air Max"}],
        "dismissed_products": [],
    }


DISMISSAL_PHRASES = [
    ("don't show me that", "don't show me"),
    ("don't recommend me this", "don't recommend me"),
    ("don't suggest me anything", "don't suggest me"),
    ("not interested in this", "not interested"),
    ("don't like this one", "don't like"),
    ("no thanks", "no thanks"),
    ("skip that", "skip that"),
    ("skip this", "skip this"),
    ("skip it", "skip it"),
    ("not for me", "not for me"),
    ("not my style", "not my style"),
    ("nope", "nope"),
    ("nah", "nah"),
    ("never mind", "never mind"),
    ("forget about that", "forget about that"),
    ("something else", "something else"),
    ("anything else", "anything else"),
    ("next", "next"),
    ("no more", "no more"),
    ("no longer", "no longer"),
    ("not that one", "not that one"),
    ("show me different", "show me different"),
    ("too expensive", "too expensive"),
]


class TestDismissalPhraseDetection:
    @pytest.mark.parametrize("phrase,expected_match", DISMISSAL_PHRASES)
    @pytest.mark.asyncio
    async def test_dismissal_phrase_triggers_extraction(
        self, extractor, context_with_last_viewed, phrase, expected_match
    ):
        result = await extractor.extract(phrase, context_with_last_viewed)
        assert "dismissed_products" in result, (
            f"Phrase '{phrase}' did not trigger dismissal extraction"
        )
        assert len(result["dismissed_products"]) > 0

    @pytest.mark.asyncio
    async def test_non_dismissal_phrase_no_extraction(self, extractor, context_with_last_viewed):
        result = await extractor.extract(
            "I love this product, tell me more!", context_with_last_viewed
        )
        assert "dismissed_products" not in result

    @pytest.mark.asyncio
    async def test_question_not_treated_as_dismissal(self, extractor, context_with_last_viewed):
        result = await extractor.extract("Can you show me more options?", context_with_last_viewed)
        assert "dismissed_products" not in result

    @pytest.mark.asyncio
    async def test_dismissal_with_product_id(self, extractor, context_with_last_viewed):
        result = await extractor.extract("don't show me product-99", context_with_last_viewed)
        assert "dismissed_products" in result
        assert 99 in result["dismissed_products"]

    @pytest.mark.asyncio
    async def test_dismissal_appends_to_existing(self, extractor):
        context = {
            "last_viewed_products": [{"id": 10, "title": "Shirt"}],
            "dismissed_products": [5],
        }
        result = await extractor.extract("not interested", context)
        assert "dismissed_products" in result
        assert 5 in result["dismissed_products"]

    @pytest.mark.asyncio
    async def test_dismissal_deduplicates(self, extractor):
        context = {
            "last_viewed_products": [{"id": 5, "title": "Shirt"}],
            "dismissed_products": [5],
        }
        result = await extractor.extract("skip that", context)
        assert "dismissed_products" in result
        assert result["dismissed_products"].count(5) == 1

    @pytest.mark.asyncio
    async def test_dismissal_no_viewed_products_no_crash(self, extractor):
        context = {
            "last_viewed_products": [],
            "dismissed_products": [],
        }
        result = await extractor.extract("nope", context)
        assert "dismissed_products" not in result

    @pytest.mark.asyncio
    async def test_dismissal_case_insensitive(self, extractor, context_with_last_viewed):
        result = await extractor.extract("NOPE", context_with_last_viewed)
        assert "dismissed_products" in result

    @pytest.mark.asyncio
    async def test_dismissal_with_leading_whitespace(self, extractor, context_with_last_viewed):
        result = await extractor.extract("  nah  ", context_with_last_viewed)
        assert "dismissed_products" in result

    @pytest.mark.asyncio
    async def test_too_expensive_with_context(self, extractor, context_with_last_viewed):
        result = await extractor.extract("That's too expensive", context_with_last_viewed)
        assert "dismissed_products" in result


class TestDismissalIntegrationWithContext:
    @pytest.mark.asyncio
    async def test_dismissal_updates_turn_count(self, extractor, context_with_last_viewed):
        result = await extractor.extract("skip that", context_with_last_viewed)
        assert result["turn_count"] == 1

    @pytest.mark.asyncio
    async def test_dismissal_preserves_search_history(self, extractor, context_with_last_viewed):
        result = await extractor.extract("next", context_with_last_viewed)
        assert "search_history" in result
        assert "next" in result["search_history"]
