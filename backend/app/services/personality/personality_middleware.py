"""Personality enforcement middleware (Story 11-5, AC11).

Provides a `with_personality` decorator that acts as a safety net,
catching handlers that return unformatted raw strings and applying
personality heuristics. Logs warnings identifying bypassing handlers.
"""

from __future__ import annotations

import functools
from typing import Any, Callable

import structlog

from app.models.merchant import PersonalityType

logger = structlog.get_logger(__name__)

_PROFESSIONAL_PREFIXES = (
    "Certainly.",
    "I would be happy to",
    "Thank you for",
    "Please note",
    "We apologize",
    "Unfortunately,",
)

_FRIENDLY_PREFIXES = (
    "No worries!",
    "Sure thing!",
    "Happy to help!",
    "No problem!",
    "Oops,",
    "Hey there!",
)

_ENTHUSIASTIC_MARKERS = ("!!!", "AMAZING", "AWESOME", "LOVE", "FANTASTIC", "🔥", "✨", "🎉")


def _detect_raw_personality(text: str) -> PersonalityType:
    """Heuristic detection of personality tone in a raw string."""
    text_lower = text.lower()

    enthusiastic_count = sum(1 for m in _ENTHUSIASTIC_MARKERS if m in text)
    if enthusiastic_count >= 2 or text.count("!") >= 3:
        return PersonalityType.ENTHUSIASTIC

    for prefix in _PROFESSIONAL_PREFIXES:
        if text.startswith(prefix):
            return PersonalityType.PROFESSIONAL

    for prefix in _FRIENDLY_PREFIXES:
        if text.startswith(prefix):
            return PersonalityType.FRIENDLY

    friendly_words = ["sure", "awesome", "cool", "gonna", "wanna", "yeah"]
    if any(w in text_lower for w in friendly_words):
        return PersonalityType.FRIENDLY

    formal_words = ["certainly", "regarding", "however", "therefore", "accordingly"]
    if any(w in text_lower for w in formal_words):
        return PersonalityType.PROFESSIONAL

    return PersonalityType.FRIENDLY


def _apply_personality_heuristic(text: str, personality: PersonalityType) -> str:
    """Apply lightweight personality adjustment to a raw string.

    This is a best-effort heuristic for strings that bypassed the formatter.
    It does NOT replace proper template formatting.
    """
    if not text or not text.strip():
        return text

    if personality == PersonalityType.PROFESSIONAL:
        emoji_removed = _strip_emojis(text)
        return emoji_removed

    if personality == PersonalityType.ENTHUSIASTIC:
        if "!" not in text:
            text = text.rstrip(".") + "!"
        return text

    return text


def _strip_emojis(text: str) -> str:
    """Remove common emojis from text for professional personality."""
    import re

    emoji_pattern = re.compile(
        "["
        "\U0001f600-\U0001f64f"
        "\U0001f300-\U0001f5ff"
        "\U0001f680-\U0001f6ff"
        "\U0001f1e0-\U0001f1ff"
        "\U00002702-\U000027b0"
        "\U000024c2-\U0001f251"
        "\U0001f900-\U0001f9ff"
        "\U0001fa00-\U0001fa6f"
        "\U0001fa70-\U0001faff"
        "\U00002600-\U000026ff"
        "\U0000fe00-\U0000fe0f"
        "\U0000200d"
        "]",
        flags=re.UNICODE,
    )
    return emoji_pattern.sub("", text).strip()


def with_personality(
    personality: PersonalityType = PersonalityType.FRIENDLY,
) -> Callable:
    """Decorator that enforces personality on handler return values.

    If a handler returns a raw string or a ConversationResponse with a
    message that appears unformatted, this decorator applies personality
    heuristics and logs a warning.

    This is opt-in and backward compatible — handlers must explicitly
    register for enforcement.

    Args:
        personality: The personality type to enforce

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            result = await func(*args, **kwargs)
            return _enforce_personality(result, personality, func.__qualname__)

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            result = func(*args, **kwargs)
            return _enforce_personality(result, personality, func.__qualname__)

        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def _enforce_personality(result: Any, personality: PersonalityType, handler_name: str) -> Any:
    """Apply personality enforcement to a handler result."""
    from app.services.conversation.schemas import ConversationResponse

    if isinstance(result, str):
        logger.warning(
            "personality_bypass_detected",
            handler=handler_name,
            return_type="str",
            hint="Handler returned raw string instead of using PersonalityAwareResponseFormatter",
        )
        return _apply_personality_heuristic(result, personality)

    if isinstance(result, ConversationResponse):
        message = result.message
        if message and _looks_unformatted(message, personality):
            logger.warning(
                "personality_bypass_detected",
                handler=handler_name,
                return_type="ConversationResponse",
                hint="Response message appears to bypass personality formatter",
            )
            result.message = _apply_personality_heuristic(message, personality)
        return result

    return result


def _looks_unformatted(text: str, personality: PersonalityType) -> bool:
    """Heuristic check if a response looks like it bypassed the formatter."""
    if not text:
        return False

    detected = _detect_raw_personality(text)

    if personality == PersonalityType.PROFESSIONAL:
        import re

        if re.search(
            "[\U0001f600-\U0001f64f\U0001f300-\U0001f5ff\U0001f680-\U0001f6ff\U0001f900-\U0001f9ff]",
            text,
        ):
            return True

    if personality == PersonalityType.ENTHUSIASTIC:
        if "!" not in text:
            return True

    if personality == PersonalityType.FRIENDLY:
        if detected == PersonalityType.PROFESSIONAL:
            return True
        return False

    return False
