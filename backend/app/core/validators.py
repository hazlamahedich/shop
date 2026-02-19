"""Input validation utilities for API endpoints.

Story 5-7: Security & Rate Limiting
AC3: Session ID Validation
"""

from __future__ import annotations

import re
from typing import Optional


UUID_V4_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def is_valid_session_id(session_id: Optional[str]) -> bool:
    """Validate session_id is a properly formatted UUID v4.

    Performs format validation only - does not check if session exists.

    Args:
        session_id: Session identifier to validate

    Returns:
        True if valid UUID format, False otherwise
    """
    if session_id is None:
        return False

    if not isinstance(session_id, str):
        return False

    if not session_id or not session_id.strip():
        return False

    return bool(UUID_V4_PATTERN.match(session_id.strip()))
