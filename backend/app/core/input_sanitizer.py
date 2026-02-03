"""Input sanitization utilities for LLM processing (NFR-S6).

Sanitizes user input before LLM processing to prevent prompt injection
and other security issues.
"""

from __future__ import annotations

import re
import html
from typing import List


# Blocked prompt injection patterns
_INJECTION_PATTERNS = [
    r"(?i)(ignore\s+(previous|all\s+above|forget))",
    r"(?i)(print|execute|eval|run|code|script)",
    r"(?i)(system|admin|root|privileged)",
    r"(?i)(override|bypass|circumvent)",
    r"(?i)(no\s+filter|skip\s+check)",
]


def sanitize_llm_input(text: str, max_length: int = 10000) -> str:
    """Sanitize user input before LLM processing (NFR-S6).

    Args:
        text: Raw user input
        max_length: Maximum allowed length

    Returns:
        Sanitized text safe for LLM processing

    Security: Removes or neutralizes prompt injection attempts.
    """
    if not text:
        return ""

    # Truncate to max length
    text = text[:max_length]

    # Remove potential prompt injection patterns
    for pattern in _INJECTION_PATTERNS:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    # Remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)

    # Remove excessive whitespace
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def validate_test_prompt(prompt: str) -> tuple[bool, str | None]:
    """Validate test prompt is safe for LLM processing.

    Args:
        prompt: Test prompt to validate

    Returns:
        Tuple of (is_safe, error_message)
    """
    if not prompt or not prompt.strip():
        return False, "Test prompt cannot be empty"

    # Check total length
    if len(prompt) > 1000:
        return False, "Test prompt too long (max 1000 characters)"

    # Block common injection attempts in test prompts
    blocked_patterns = [
        "ignore previous instructions",
        "forget all above",
        "disregard everything",
        'print("',
        "eval(",
        "__import__",
        "exec(",
        "system(",
    ]

    prompt_lower = prompt.lower()
    for pattern in blocked_patterns:
        if pattern.lower() in prompt_lower:
            return False, f"Test prompt contains blocked pattern: {pattern[:30]}"

    return True, None


def sanitize_conversation_input(text: str) -> str:
    """Sanitize conversation input with stricter rules.

    Args:
        text: User message from conversation

    Returns:
        Sanitized text
    """
    if not text:
        return ""

    # Apply sanitization
    text = sanitize_llm_input(text, max_length=5000)

    # Additional conversation-specific checks
    # Remove potential command injection
    text = re.sub(r"[;&|`$]", "", text)

    return text


def is_safe_conversation_input(text: str) -> bool:
    """Quick check if input appears safe for processing.

    Args:
        text: Input to check

    Returns:
        True if input appears safe
    """
    if not text:
        return True

    # Quick checks for obvious issues
    dangerous_patterns = [
        "http://", "https://",  # URLs (unless allowed)
        "javascript:", "data:",  # Protocol injection
        "<script", "</script>",  # Script tags
        "__import__", "eval(", "exec(",  # Code execution
    ]

    text_lower = text.lower()
    for pattern in dangerous_patterns:
        if pattern in text_lower:
            return False

    return True
