"""FAQ matching service for Story 1.11.

Provides keyword matching and relevance ranking for FAQ items.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import Optional

import structlog

from app.models.faq import Faq


logger = structlog.get_logger(__name__)


@dataclass
class FaqMatch:
    """Result of FAQ matching.

    Attributes:
        faq: The matched FAQ item
        confidence: Confidence score (0.0 to 1.0)
        match_type: Type of match (exact_question, contains_question, keyword)
    """

    faq: Faq
    confidence: float
    match_type: str


class FaqMatcher:
    """FAQ matching service with keyword and question matching.

    Implements the matching algorithm from Story 1.11 AC 6, 8:
    - Case-insensitive matching
    - Keyword partial matching
    - Relevance ranking (exact question > contains question > keyword)
    - Returns match only if confidence > 0.7
    """

    # Confidence thresholds
    EXACT_QUESTION_MATCH_CONFIDENCE = 1.0
    CONTAINS_QUESTION_MATCH_CONFIDENCE = 0.85
    EXACT_KEYWORD_MATCH_CONFIDENCE = 0.8
    PARTIAL_KEYWORD_MATCH_CONFIDENCE = 0.7

    def __init__(self) -> None:
        """Initialize FAQ matcher."""
        self.logger = structlog.get_logger(__name__)

    def normalize_text(self, text: str) -> str:
        """Normalize text for matching.

        Args:
            text: Input text to normalize

        Returns:
            Normalized text (lowercase, stripped, extra whitespace removed)
        """
        return re.sub(r"\s+", " ", text.lower().strip())

    def match_faq(
        self,
        customer_message: str,
        merchant_faqs: list[Faq],
    ) -> Optional[FaqMatch]:
        """Match customer message to FAQ items.

        Args:
            customer_message: Customer's question/message
            merchant_faqs: List of FAQ items to match against

        Returns:
            FaqMatch if confidence > 0.7, None otherwise

        Raises:
            ValueError: If customer_message is empty or merchant_faqs is empty
        """
        if not customer_message or not customer_message.strip():
            raise ValueError("customer_message cannot be empty")

        if not merchant_faqs:
            return None

        start_time = time.perf_counter()
        normalized_message = self.normalize_text(customer_message)

        best_match: Optional[FaqMatch] = None

        for faq in merchant_faqs:
            # Try exact question match
            exact_question_match = self._exact_question_match(
                normalized_message,
                faq,
            )
            if exact_question_match:
                if best_match is None or exact_question_match.confidence > best_match.confidence:
                    best_match = exact_question_match
                # Exact match is highest priority, can return immediately
                return exact_question_match

            # Try contains question match
            contains_question_match = self._contains_question_match(
                normalized_message,
                faq,
            )
            if contains_question_match:
                if best_match is None or contains_question_match.confidence > best_match.confidence:
                    best_match = contains_question_match

            # Try keyword match
            keyword_match = self._keyword_match(normalized_message, faq)
            if keyword_match:
                if best_match is None or keyword_match.confidence > best_match.confidence:
                    best_match = keyword_match

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        if best_match and best_match.confidence >= self.PARTIAL_KEYWORD_MATCH_CONFIDENCE:
            self.logger.info(
                "faq_matched",
                faq_id=best_match.faq.id,
                confidence=best_match.confidence,
                match_type=best_match.match_type,
                elapsed_ms=elapsed_ms,
            )
            return best_match

        self.logger.debug(
            "faq_no_match",
            customer_message=customer_message[:100],
            elapsed_ms=elapsed_ms,
        )
        return None

    def _exact_question_match(
        self,
        normalized_message: str,
        faq: Faq,
    ) -> Optional[FaqMatch]:
        """Check for exact question match.

        Args:
            normalized_message: Normalized customer message
            faq: FAQ item to check

        Returns:
            FaqMatch if exact match, None otherwise
        """
        normalized_question = self.normalize_text(faq.question)

        if normalized_message == normalized_question:
            return FaqMatch(
                faq=faq,
                confidence=self.EXACT_QUESTION_MATCH_CONFIDENCE,
                match_type="exact_question",
            )

        return None

    def _contains_question_match(
        self,
        normalized_message: str,
        faq: Faq,
    ) -> Optional[FaqMatch]:
        """Check if message contains FAQ question text.

        Args:
            normalized_message: Normalized customer message
            faq: FAQ item to check

        Returns:
            FaqMatch if contains match, None otherwise
        """
        normalized_question = self.normalize_text(faq.question)

        # Check if the full FAQ question is contained in the message
        if normalized_question in normalized_message:
            return FaqMatch(
                faq=faq,
                confidence=self.CONTAINS_QUESTION_MATCH_CONFIDENCE,
                match_type="contains_question",
            )

        # Check if message is contained in question (for short queries)
        # Only match if message is at least 4 chars to avoid false positives
        # like "hi" matching "shipping"
        if len(normalized_message) >= 4 and normalized_message in normalized_question:
            # Use word boundary check to avoid partial word matches
            # e.g., "ship" should match "ship" but not "relationship"
            import re

            pattern = r"\b" + re.escape(normalized_message) + r"\b"
            if re.search(pattern, normalized_question):
                return FaqMatch(
                    faq=faq,
                    confidence=self.CONTAINS_QUESTION_MATCH_CONFIDENCE
                    * 0.9,  # Slightly lower confidence
                    match_type="contains_question",
                )

        return None

    def _keyword_match(
        self,
        normalized_message: str,
        faq: Faq,
    ) -> Optional[FaqMatch]:
        """Check for keyword match.

        Args:
            normalized_message: Normalized customer message
            faq: FAQ item to check

        Returns:
            FaqMatch if keyword match, None otherwise
        """
        if not faq.keywords:
            return None

        # Parse keywords (comma-separated)
        keywords = [self.normalize_text(kw) for kw in faq.keywords.split(",") if kw.strip()]

        if not keywords:
            return None

        # Check for exact keyword matches
        exact_matches = 0
        partial_matches = 0

        for keyword in keywords:
            if keyword == normalized_message:
                exact_matches += 1
            elif keyword in normalized_message:
                partial_matches += 1

        if exact_matches > 0:
            return FaqMatch(
                faq=faq,
                confidence=self.EXACT_KEYWORD_MATCH_CONFIDENCE,
                match_type="keyword_exact",
            )

        if partial_matches > 0:
            # Calculate confidence based on number of matching keywords
            confidence = self.PARTIAL_KEYWORD_MATCH_CONFIDENCE + min(partial_matches * 0.05, 0.1)
            return FaqMatch(
                faq=faq,
                confidence=confidence,
                match_type="keyword_partial",
            )

        return None


# Singleton instance for convenience
_default_matcher: Optional[FaqMatcher] = None


def get_faq_matcher() -> FaqMatcher:
    """Get or create the default FAQ matcher instance.

    Returns:
        FaqMatcher singleton instance
    """
    global _default_matcher
    if _default_matcher is None:
        _default_matcher = FaqMatcher()
    return _default_matcher


async def match_faq(
    customer_message: str,
    merchant_faqs: list[Faq],
) -> Optional[FaqMatch]:
    """Match customer message to FAQ items.

    Convenience function that uses the default matcher.

    Args:
        customer_message: Customer's question/message
        merchant_faqs: List of FAQ items to match against

    Returns:
        FaqMatch if confidence > 0.7, None otherwise
    """
    matcher = get_faq_matcher()
    return matcher.match_faq(customer_message, merchant_faqs)
