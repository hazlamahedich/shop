"""Input sanitization utilities for user-provided content.

Story 5-7: Security & Rate Limiting
AC5: Input Sanitization
"""

from __future__ import annotations

import html
from typing import Optional, Tuple


MAX_MESSAGE_LENGTH = 2000


def sanitize_message(content: str) -> str:
    """Sanitize message content for safe processing.

    Performs:
    - Whitespace trimming
    - HTML escaping for XSS prevention
    - Null byte removal

    Args:
        content: Raw message content from user

    Returns:
        Sanitized message content
    """
    if not content:
        return ""

    sanitized = content.strip()

    sanitized = sanitized.replace("\x00", "")

    sanitized = html.escape(sanitized)

    return sanitized


def validate_message_length(content: str) -> Tuple[bool, Optional[str]]:
    """Validate message length is within limits.

    Args:
        content: Message content to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not content or not content.strip():
        return False, "Message cannot be empty"

    if len(content) > MAX_MESSAGE_LENGTH:
        return False, f"Message exceeds maximum length of {MAX_MESSAGE_LENGTH} characters"

    return True, None
