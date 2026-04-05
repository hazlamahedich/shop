"""Input sanitization utilities for LLM processing (NFR-S6).

Sanitizes user input before LLM processing to prevent prompt injection
and other security issues.

Redesigned to use targeted patterns that block actual injection attempts
without breaking legitimate queries like "running shoes" or "promo code".
"""

from __future__ import annotations

import re

_TARGETED_INJECTION_PATTERNS = [
    (
        r"(?i)ignore\s+(all\s+)?(previous|above|prior)\s+(instructions|rules|prompts?|directives)",
        "[filtered]",
    ),
    (
        r"(?i)forget\s+(all\s+)?(previous|above|prior|your)\s+(instructions|rules|prompts?|directives)",
        "[filtered]",
    ),
    (
        r"(?i)disregard\s+(all\s+)?(previous|above|prior|your)\s+(instructions|rules|prompts?|directives)",
        "[filtered]",
    ),
    (
        r"(?i)you\s+are\s+now\s+(an?\s+)?(unfiltered|unrestricted|uncensored|jailbroken|DAN)",
        "[filtered]",
    ),
    (
        r"(?i)(pretend|act|roleplay)\s+(you\s+are|to\s+be|as)\s+(an?\s+)?(unfiltered|unrestricted|uncensored|jailbroken|DAN|system|admin)",
        "[filtered]",
    ),
    (r"(?i)new\s+(system\s+)?instructions?\s*:", "[filtered]"),
    (r"(?i)system\s*:\s*(you\s+are|from\s+now|ignore|forget|disregard|act)", "[filtered]"),
    (
        r"(?i)override\s+(your|the|all)\s+(instructions|rules|prompts?|directives|safety)",
        "[filtered]",
    ),
    (
        r"(?i)bypass\s+(your|the|all)\s+(instructions|rules|safety|filters?|restrictions)",
        "[filtered]",
    ),
    (
        r"(?i)(reveal|show|display|print|repeat|output)\s+(your|the|my|system)\s+(instructions?|prompt|system\s+prompt|original\s+prompt)",
        "[filtered]",
    ),
    (
        r"(?i)repeat\s+(the\s+)?(above|previous|prior|system)\s+(text|prompt|instructions?)\s*(word\s+for\s+word|verbatim|exactly)",
        "[filtered]",
    ),
    (r"(?i)<\|im_start\|>", "[filtered]"),
    (r"(?i)<\|im_end\|>", "[filtered]"),
    (r"(?i)\[INST\]", "[filtered]"),
    (r"(?i)<<SYS>>", "[filtered]"),
    (r"(?i)<</SYS>>", "[filtered]"),
    (r"(?i)Human:", ""),
    (r"(?i)Assistant:", ""),
    (r"(?i)System:", ""),
]

_REPEATED_SPECIAL_CHARS_PATTERN = re.compile(r"([<>\[\]{}]){4,}")
_EXCESSIVE_WHITESPACE_PATTERN = re.compile(r"\s+")
_NULL_BYTE_PATTERN = re.compile(r"\x00")


def sanitize_llm_input(text: str, max_length: int = 10000) -> str:
    """Sanitize user input before LLM processing (NFR-S6).

    Uses targeted patterns that block prompt injection attempts without
    breaking legitimate user queries.

    Args:
        text: Raw user input
        max_length: Maximum allowed length

    Returns:
        Sanitized text safe for LLM processing

    Security: Neutralizes prompt injection attempts while preserving
    legitimate content like "running shoes", "promo code", etc.
    """
    if not text:
        return ""

    text = _NULL_BYTE_PATTERN.sub("", text)

    text = text[:max_length]

    for pattern, replacement in _TARGETED_INJECTION_PATTERNS:
        text = re.sub(pattern, replacement, text)

    text = _REPEATED_SPECIAL_CHARS_PATTERN.sub(r"\1\1", text)

    text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<script[^>]*>.*?", "", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"javascript\s*:", "", text, flags=re.IGNORECASE)

    text = _EXCESSIVE_WHITESPACE_PATTERN.sub(" ", text)

    return text.strip()


def sanitize_user_message_for_llm(text: str) -> str:
    """Sanitize a user message specifically for inclusion in LLM prompts.

    This is the primary function for sanitizing user messages before they
    are sent to the LLM in the conversation pipeline.

    Args:
        text: User message from any channel (widget, messenger, preview)

    Returns:
        Sanitized message safe for LLM prompt inclusion
    """
    if not text:
        return ""

    text = sanitize_llm_input(text, max_length=4000)

    text = re.sub(r"[^\S\n]+", " ", text)

    return text.strip()


def sanitize_prompt_field(text: str, max_length: int = 500) -> str:
    """Sanitize a merchant-controlled field before interpolation into system prompt.

    Removes patterns that could override system prompt instructions.
    Used for bot_name, business_name, business_description, etc.

    Args:
        text: Merchant-controlled field value
        max_length: Maximum allowed length

    Returns:
        Sanitized field value safe for prompt interpolation
    """
    if not text:
        return ""

    text = text[:max_length]

    text = _NULL_BYTE_PATTERN.sub("", text)

    text = re.sub(
        r"(?i)(ignore|forget|disregard|override|bypass)\s+(all|previous|above|prior|your|the)\s+\w+",
        "",
        text,
    )
    text = re.sub(r"(?i)you\s+are\s+now\s+", "", text)
    text = re.sub(r"(?i)system\s*:", "", text)
    text = re.sub(r"(?i)instructions?\s*:", "", text)

    text = re.sub(r"<[^>]+>", "", text)

    text = _EXCESSIVE_WHITESPACE_PATTERN.sub(" ", text)

    return text.strip()


def sanitize_history_message(content: str) -> str:
    """Sanitize a conversation history message before replaying to LLM.

    Uses lighter sanitization since history messages were already sanitized
    when originally received, but adds defense-in-depth against accumulated
    injection across multiple turns.

    Args:
        content: Historical message content

    Returns:
        Sanitized message content
    """
    if not content:
        return ""

    content = _NULL_BYTE_PATTERN.sub("", content)

    content = re.sub(
        r"(?i)ignore\s+(all\s+)?(your|previous|above|prior)\s+(instructions|rules|prompts?)",
        "[filtered]",
        content,
    )
    content = re.sub(r"(?i)<\|im_start\|>", "[filtered]", content)
    content = re.sub(r"(?i)\[INST\]", "[filtered]", content)
    content = re.sub(r"(?i)<<SYS>>", "[filtered]", content)
    content = re.sub(r"(?i)<</SYS>>", "[filtered]", content)
    content = re.sub(r"(?i)^(Human|Assistant|System)\s*:", "", content, flags=re.MULTILINE)

    return content.strip()


def validate_test_prompt(prompt: str) -> tuple[bool, str | None]:
    """Validate test prompt is safe for LLM processing.

    Args:
        prompt: Test prompt to validate

    Returns:
        Tuple of (is_safe, error_message)
    """
    if not prompt or not prompt.strip():
        return False, "Test prompt cannot be empty"

    if len(prompt) > 1000:
        return False, "Test prompt too long (max 1000 characters)"

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

    text = sanitize_llm_input(text, max_length=5000)

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

    dangerous_patterns = [
        "http://",
        "https://",
        "javascript:",
        "data:",
        "<script",
        "</script>",
        "__import__",
        "eval(",
        "exec(",
    ]

    text_lower = text.lower()
    for pattern in dangerous_patterns:
        if pattern in text_lower:
            return False

    return True
