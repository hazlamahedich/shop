"""Shared assertion helpers for transition phrase tests (Story 11-4).

Centralizes repeated assertion patterns used across handler transition tests
to reduce duplication and improve maintainability.
"""

from app.models.merchant import PersonalityType
from app.services.personality.transition_phrases import (
    TransitionCategory,
    get_phrases_for_mode,
)


def assert_starts_with_transition(
    result: str,
    category: TransitionCategory,
    personality: PersonalityType,
    mode: str = "ecommerce",
) -> None:
    valid = get_phrases_for_mode(category, personality, mode)
    matches = [p for p in valid if result.startswith(p)]
    assert matches, f"No transition prefix for {personality.value}: {result[:60]}"


def assert_no_double_transition(
    result: str,
    category: TransitionCategory,
    personality: PersonalityType,
    mode: str = "ecommerce",
) -> None:
    valid = get_phrases_for_mode(category, personality, mode)
    doubles = [p for p in valid if result.count(p) >= 2]
    assert not doubles, f"Double transition: {doubles} in {result[:80]}"


def assert_mode_includes_phrases(
    selector,
    category: TransitionCategory,
    personality: PersonalityType,
    mode: str,
    expected_phrases: list[str],
    conv_id_prefix: str = "mode-test",
    iterations: int = 30,
) -> None:
    results = set()
    for i in range(iterations):
        results.add(selector.select(category, personality, f"{conv_id_prefix}-{i}", mode))
    found = any(p in results for p in expected_phrases)
    assert found, f"{mode} phrases not found for {personality.value}"
