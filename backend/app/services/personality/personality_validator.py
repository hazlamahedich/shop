"""Personality validation rules engine (Story 11-5, AC4, AC5).

Provides runtime validation of bot responses to ensure personality compliance.
Validation is advisory-only — logs warnings but NEVER blocks responses.

Rules per personality:
- Professional: no emojis, no slang, formal language
- Friendly: max 2 emojis per message, casual tone, contractions welcome
- Enthusiastic: at least 1 exclamation, energetic language, emojis encouraged

AC5: Critical content (prices, order numbers, URLs) is always preserved
regardless of personality style applied.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.models.merchant import PersonalityType

EMOJI_PATTERN = re.compile(
    "["
    "\U0001f600-\U0001f64f"
    "\U0001f300-\U0001f5ff"
    "\U0001f680-\U0001f6ff"
    "\U0001f1e0-\U0001f1ff"
    "\U0001f900-\U0001f9ff"
    "\U0001fa00-\U0001fa6f"
    "\U0001fa70-\U0001faff"
    "\U00002600-\U000026ff"
    "\U00002702-\U000027b0"
    "\U000024c2-\U0001f251"
    "\U0000fe00-\U0000fe0f"
    "]",
    flags=re.UNICODE,
)

CRITICAL_CONTENT_PATTERNS = [
    re.compile(r"\$\d+[\d.,]*"),
    re.compile(r"#\d{3,}"),
    re.compile(r"https?://\S+"),
    re.compile(r"order\s*#?\s*\d+", re.I),
    re.compile(r"\d+\.\d{2}"),
]

SLANG_WORDS = re.compile(
    r"\b(awesome|cool|gonna|wanna|yeah|yep|nope|omg|lol|brb|btw|tbh|yolo)\b",
    re.I,
)


@dataclass
class ValidationResult:
    """Result of personality validation check."""

    passed: bool
    violations: list[str] = field(default_factory=list)
    severity: str = "none"
    critical_content_preserved: bool = True


def _count_emojis(text: str) -> int:
    """Count emoji characters in text."""
    return len(EMOJI_PATTERN.findall(text))


def _check_critical_content(text: str) -> bool:
    if not text.strip():
        return False
    for pattern in CRITICAL_CONTENT_PATTERNS:
        if pattern.search(text):
            return True
    return False


def _validate_professional(text: str) -> list[str]:
    """Professional: no emojis, no slang, formal language."""
    violations = []
    emoji_count = _count_emojis(text)
    if emoji_count > 0:
        violations.append(f"Professional personality contains {emoji_count} emoji(s) — expected 0")
    slang_matches = SLANG_WORDS.findall(text)
    if slang_matches:
        violations.append(f"Professional personality contains slang: {', '.join(slang_matches)}")
    return violations


def _validate_friendly(text: str) -> list[str]:
    """Friendly: max 2 emojis per message, casual tone."""
    violations = []
    emoji_count = _count_emojis(text)
    if emoji_count > 2:
        violations.append(f"Friendly personality has {emoji_count} emojis — max 2 allowed")
    return violations


def _validate_enthusiastic(text: str) -> list[str]:
    """Enthusiastic: at least 1 exclamation, energetic language, emojis encouraged."""
    violations = []
    exclamation_count = text.count("!")
    if exclamation_count < 1:
        violations.append("Enthusiastic personality has no exclamation marks — expected at least 1")
    emoji_count = _count_emojis(text)
    if emoji_count > 10:
        violations.append(f"Enthusiastic personality has {emoji_count} emojis — max 10 allowed")
    return violations


_VALIDATORS = {
    PersonalityType.PROFESSIONAL: _validate_professional,
    PersonalityType.FRIENDLY: _validate_friendly,
    PersonalityType.ENTHUSIASTIC: _validate_enthusiastic,
}


def validate_personality(text: str, personality: PersonalityType) -> ValidationResult:
    """Validate a response text against personality rules.

    Advisory-only — logs violations but never blocks the response.

    Args:
        text: Response text to validate
        personality: Target personality type

    Returns:
        ValidationResult with pass/fail status and violation details
    """
    if not text or not text.strip():
        return ValidationResult(passed=True)

    validator = _VALIDATORS.get(personality)
    if validator is None:
        return ValidationResult(passed=True)

    violations = validator(text)
    critical_preserved = _check_critical_content(text)

    severity = "none"
    if violations:
        if personality == PersonalityType.PROFESSIONAL and any(
            "emoji" in v.lower() for v in violations
        ):
            severity = "high"
        elif len(violations) > 1:
            severity = "medium"
        else:
            severity = "low"

    return ValidationResult(
        passed=len(violations) == 0,
        violations=violations,
        severity=severity,
        critical_content_preserved=critical_preserved,
    )
