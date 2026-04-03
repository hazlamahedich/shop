"""Tests for mid-conversation personality reinforcement (Story 11-5, AC3)."""

import pytest

from app.models.merchant import PersonalityType
from app.services.personality.personality_reinforcement import (
    REINFORCEMENT_TURN_THRESHOLD,
    get_personality_reinforcement,
)


class TestReinforcementThreshold:
    """Reinforcement only activates after turn threshold."""

    def test_returns_none_below_threshold(self):
        result = get_personality_reinforcement(PersonalityType.FRIENDLY, turn_number=1)
        assert result is None

    def test_returns_none_at_threshold_minus_one(self):
        result = get_personality_reinforcement(
            PersonalityType.PROFESSIONAL, turn_number=REINFORCEMENT_TURN_THRESHOLD - 1
        )
        assert result is None

    def test_returns_text_at_threshold(self):
        result = get_personality_reinforcement(
            PersonalityType.FRIENDLY, turn_number=REINFORCEMENT_TURN_THRESHOLD
        )
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0

    def test_returns_text_above_threshold(self):
        result = get_personality_reinforcement(PersonalityType.ENTHUSIASTIC, turn_number=20)
        assert result is not None


class TestReinforcementContent:
    """Reinforcement content is personality-specific."""

    def test_friendly_contains_warm_tone_rules(self):
        result = get_personality_reinforcement(PersonalityType.FRIENDLY, turn_number=6)
        assert "FRIENDLY" in result
        assert "casual" in result.lower()
        assert "emojis" in result.lower()

    def test_professional_contains_formal_tone_rules(self):
        result = get_personality_reinforcement(PersonalityType.PROFESSIONAL, turn_number=6)
        assert "PROFESSIONAL" in result
        assert "formal" in result.lower()
        assert "NO emojis" in result

    def test_enthusiastic_contains_energetic_tone_rules(self):
        result = get_personality_reinforcement(PersonalityType.ENTHUSIASTIC, turn_number=6)
        assert "ENTHUSIASTIC" in result
        assert "exclamation" in result.lower()
        assert "energetic" in result.lower()

    def test_all_reinforcements_mention_consistency(self):
        for personality in PersonalityType:
            result = get_personality_reinforcement(personality, turn_number=6)
            assert result is not None
            assert "CONSISTENCY" in result or "consistency" in result.lower()


class TestAdaptiveReinforcement:
    """Reinforcement adapts based on consistency score."""

    def test_low_score_adds_warning(self):
        result = get_personality_reinforcement(
            PersonalityType.FRIENDLY, turn_number=6, consistency_score=0.5
        )
        assert "WARNING" in result
        assert "declining" in result.lower()

    def test_high_score_no_warning(self):
        result = get_personality_reinforcement(
            PersonalityType.FRIENDLY, turn_number=6, consistency_score=0.9
        )
        assert "WARNING" not in result

    def test_no_score_no_warning(self):
        result = get_personality_reinforcement(
            PersonalityType.PROFESSIONAL, turn_number=6, consistency_score=None
        )
        assert "WARNING" not in result

    def test_threshold_score_no_warning(self):
        result = get_personality_reinforcement(
            PersonalityType.ENTHUSIASTIC, turn_number=6, consistency_score=0.7
        )
        assert "WARNING" not in result
