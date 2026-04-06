"""Shared keyword matching utilities with word boundary enforcement.

Prevents false positives from substring matching (e.g., 'humanity' matching 'human').
Action item from Epic 11 retrospective: word boundary regex enforcement.

Usage:
    from app.services.shared.keyword_match import keyword_matches, compile_keyword_pattern

    # Instead of:
    any(kw in text for kw in KEYWORDS)          # FALSE POSITIVES

    # Use:
    any(keyword_matches(text, kw) for kw in KEYWORDS)  # CORRECT
    # Or better:
    pattern = compile_keyword_pattern(KEYWORDS)
    if pattern.search(text): ...
"""

from __future__ import annotations

import re


def keyword_matches(text: str, keyword: str) -> bool:
    """Check if keyword appears in text with word boundary enforcement.

    Args:
        text: The text to search in (should be lowercase).
        keyword: The keyword to look for.

    Returns:
        True if keyword found at word boundary, False otherwise.
    """
    pattern = r"\b" + re.escape(keyword) + r"\b"
    return re.search(pattern, text, re.IGNORECASE) is not None


def compile_keyword_pattern(keywords: set[str] | frozenset[str] | list[str]) -> re.Pattern:
    """Compile a set of keywords into a single regex with word boundaries.

    Uses the same pattern as app.services.handoff.detector.KEYWORD_PATTERN.

    Args:
        keywords: Collection of keywords to match.

    Returns:
        Compiled regex pattern matching any keyword at word boundaries.
    """
    escaped = "|".join(re.escape(kw) for kw in sorted(keywords))
    return re.compile(r"\b(" + escaped + r")\b", re.IGNORECASE)
