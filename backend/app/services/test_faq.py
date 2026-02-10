"""Tests for FAQ matching service.

Story 1.11: Business Info & FAQ Configuration

Tests FAQ keyword matching and relevance ranking.
"""

from __future__ import annotations

import time
from datetime import datetime

import pytest

from app.models.faq import Faq
from app.models.merchant import Merchant
from app.services.faq import (
    FaqMatcher,
    FaqMatch,
    get_faq_matcher,
    match_faq,
)


class TestFaqMatcher:
    """Tests for FaqMatcher class."""

    def test_normalize_text(self):
        """Test text normalization for matching."""
        matcher = FaqMatcher()

        assert matcher.normalize_text("  Hello World  ") == "hello world"
        assert matcher.normalize_text("Multiple   Spaces") == "multiple spaces"
        assert matcher.normalize_text("UPPER CASE") == "upper case"
        assert matcher.normalize_text("MixEd CaSe") == "mixed case"

    def test_exact_question_match(self):
        """Test exact question matching (Story 1.11 AC 6, 8)."""
        matcher = FaqMatcher()

        faq = Faq(
            id=1,
            merchant_id=1,
            question="What are your shipping options?",
            answer="We offer free shipping on orders over $50.",
            keywords="shipping, delivery",
            order_index=0,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Exact match
        result = matcher._exact_question_match(
            "what are your shipping options?",
            faq,
        )
        assert result is not None
        assert result.confidence == 1.0
        assert result.match_type == "exact_question"

        # Not an exact match
        result = matcher._exact_question_match(
            "tell me about shipping",
            faq,
        )
        assert result is None

    def test_contains_question_match(self):
        """Test contains question matching (Story 1.11 AC 6, 8)."""
        matcher = FaqMatcher()

        faq = Faq(
            id=1,
            merchant_id=1,
            question="What are your shipping options?",
            answer="We offer free shipping on orders over $50.",
            keywords="shipping, delivery",
            order_index=0,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Message contains FAQ question
        result = matcher._contains_question_match(
            "can you tell me what are your shipping options?",
            faq,
        )
        assert result is not None
        assert result.confidence == 0.85
        assert result.match_type == "contains_question"

        # FAQ question contains message
        result = matcher._contains_question_match(
            "shipping options",
            faq,
        )
        assert result is not None
        assert result.confidence == 0.85

    def test_keyword_exact_match(self):
        """Test exact keyword matching (Story 1.11 AC 6, 8)."""
        matcher = FaqMatcher()

        faq = Faq(
            id=1,
            merchant_id=1,
            question="What are your shipping options?",
            answer="We offer free shipping on orders over $50.",
            keywords="shipping, delivery, returns",
            order_index=0,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Exact keyword match
        result = matcher._keyword_match("shipping", faq)
        assert result is not None
        assert result.confidence == 0.8
        assert result.match_type == "keyword_exact"

        # Another exact keyword match
        result = matcher._keyword_match("returns", faq)
        assert result is not None
        assert result.confidence == 0.8

    def test_keyword_partial_match(self):
        """Test partial keyword matching (Story 1.11 AC 6, 8)."""
        matcher = FaqMatcher()

        faq = Faq(
            id=1,
            merchant_id=1,
            question="What are your shipping options?",
            answer="We offer free shipping on orders over $50.",
            keywords="shipping, delivery, returns",
            order_index=0,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Partial keyword match (message contains keyword)
        result = matcher._keyword_match(
            "tell me about shipping options",
            faq,
        )
        assert result is not None
        assert result.confidence >= 0.7
        assert result.match_type == "keyword_partial"

    def test_match_faq_with_high_confidence(self):
        """Test FAQ matching returns match when confidence > 0.7 (Story 1.11 AC 8)."""
        matcher = FaqMatcher()

        faqs = [
            Faq(
                id=1,
                merchant_id=1,
                question="What are your shipping options?",
                answer="We offer free shipping on orders over $50.",
                keywords="shipping, delivery",
                order_index=0,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
        ]

        result = matcher.match_faq("shipping", faqs)
        assert result is not None
        assert result.confidence >= 0.7
        assert result.faq.id == 1

    def test_match_faq_no_match_below_threshold(self):
        """Test FAQ matching returns None when confidence < 0.7."""
        matcher = FaqMatcher()

        faqs = [
            Faq(
                id=1,
                merchant_id=1,
                question="How do I track my order?",
                answer="You can track your order using the link in your confirmation email.",
                keywords="tracking, order status",
                order_index=0,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
        ]

        # Unrelated message
        result = matcher.match_faq("what products do you sell?", faqs)
        assert result is None

    def test_match_faq_returns_best_match(self):
        """Test matching returns the highest confidence FAQ (Story 1.11 AC 8)."""
        matcher = FaqMatcher()

        faqs = [
            Faq(
                id=1,
                merchant_id=1,
                question="shipping",
                answer="Free shipping on orders over $50.",
                keywords="delivery",
                order_index=0,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
            Faq(
                id=2,
                merchant_id=1,
                question="What are your shipping options?",
                answer="We offer free shipping on orders over $50.",
                keywords="shipping, delivery",
                order_index=1,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
        ]

        # Exact question match should win over keyword match
        result = matcher.match_faq("what are your shipping options?", faqs)
        assert result is not None
        assert result.faq.id == 2  # Exact question match
        assert result.confidence == 1.0

    def test_match_faq_with_empty_faqs_list(self):
        """Test matching with empty FAQ list."""
        matcher = FaqMatcher()

        result = matcher.match_faq("shipping", [])
        assert result is None

    def test_match_faq_with_empty_message_raises_error(self):
        """Test matching with empty message raises error."""
        matcher = FaqMatcher()

        faqs = [
            Faq(
                id=1,
                merchant_id=1,
                question="Test?",
                answer="Test answer.",
                keywords=None,
                order_index=0,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
        ]

        with pytest.raises(ValueError):
            matcher.match_faq("", faqs)

        with pytest.raises(ValueError):
            matcher.match_faq("   ", faqs)

    def test_case_insensitive_matching(self):
        """Test case-insensitive matching (Story 1.11 AC 6)."""
        matcher = FaqMatcher()

        faqs = [
            Faq(
                id=1,
                merchant_id=1,
                question="What Are Your SHIPPING Options?",
                answer="Free shipping on orders over $50.",
                keywords="SHIPPING, DELIVERY",
                order_index=0,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
        ]

        # All should match regardless of case
        assert matcher.match_faq("shipping", faqs) is not None
        assert matcher.match_faq("SHIPPING", faqs) is not None
        assert matcher.match_faq("Shipping", faqs) is not None
        assert matcher.match_faq("what are your shipping options?", faqs) is not None

    def test_performance_with_50_faqs(self):
        """Test matching performance with 50 FAQs (< 100ms per check) (Story 1.11 AC 8)."""
        matcher = FaqMatcher()

        # Create 50 FAQ items
        faqs = [
            Faq(
                id=i,
                merchant_id=1,
                question=f"Question {i}?",
                answer=f"Answer {i}",
                keywords=f"keyword{i}, test{i}",
                order_index=i,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            for i in range(1, 51)
        ]

        # Test performance
        start_time = time.perf_counter()
        result = matcher.match_faq("keyword25", faqs)
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        assert result is not None
        assert result.faq.id == 25
        assert elapsed_ms < 100, f"Matching took {elapsed_ms:.2f}ms, expected < 100ms"

    def test_performance_multiple_checks(self):
        """Test multiple matching operations complete quickly."""
        matcher = FaqMatcher()

        faqs = [
            Faq(
                id=i,
                merchant_id=1,
                question=f"Question {i}?",
                answer=f"Answer {i}",
                keywords=f"keyword{i}, test{i}",
                order_index=i,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            for i in range(1, 51)
        ]

        # Test 10 different queries
        start_time = time.perf_counter()
        for i in range(1, 11):
            matcher.match_faq(f"keyword{i}", faqs)
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # All 10 checks should complete in reasonable time
        assert elapsed_ms < 500, f"10 matches took {elapsed_ms:.2f}ms"

    def test_faq_without_keywords(self):
        """Test FAQ matching when FAQ has no keywords."""
        matcher = FaqMatcher()

        faqs = [
            Faq(
                id=1,
                merchant_id=1,
                question="What are your hours?",
                answer="9 AM - 6 PM PST, Mon-Fri",
                keywords=None,
                order_index=0,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
        ]

        # Should still match on question text
        result = matcher.match_faq("what are your hours?", faqs)
        assert result is not None
        assert result.match_type == "exact_question"

    def test_multiple_keyword_matches(self):
        """Test matching when multiple keywords match."""
        matcher = FaqMatcher()

        faqs = [
            Faq(
                id=1,
                merchant_id=1,
                question="What are your shipping options?",
                answer="Free shipping on orders over $50.",
                keywords="shipping, delivery, express, overnight",
                order_index=0,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
        ]

        # Message contains multiple keywords
        result = matcher.match_faq("tell me about express shipping and delivery", faqs)
        assert result is not None
        assert result.match_type == "keyword_partial"
        # Confidence should be boosted for multiple matches
        assert result.confidence > 0.7


class TestFaqMatchDataclass:
    """Tests for FaqMatch dataclass."""

    def test_faq_match_creation(self):
        """Test creating FaqMatch instance."""
        faq = Faq(
            id=1,
            merchant_id=1,
            question="Test?",
            answer="Test answer.",
            keywords=None,
            order_index=0,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        match = FaqMatch(
            faq=faq,
            confidence=0.85,
            match_type="contains_question",
        )

        assert match.faq == faq
        assert match.confidence == 0.85
        assert match.match_type == "contains_question"


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_get_faq_matcher_singleton(self):
        """Test get_faq_matcher returns singleton instance."""
        matcher1 = get_faq_matcher()
        matcher2 = get_faq_matcher()

        assert matcher1 is matcher2

    async def test_match_faq_convenience_function(self):
        """Test match_faq convenience function."""
        faqs = [
            Faq(
                id=1,
                merchant_id=1,
                question="What are your shipping options?",
                answer="Free shipping on orders over $50.",
                keywords="shipping",
                order_index=0,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
        ]

        result = await match_faq("shipping", faqs)

        assert result is not None
        assert result.faq.id == 1
        assert result.confidence >= 0.7
