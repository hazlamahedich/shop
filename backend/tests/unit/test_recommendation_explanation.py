"""Unit tests for ExplanationGenerator (Story 11-6).

Tests template selection by personality, missing template vars fallback,
all reason types, and multi-match handling.
"""

from __future__ import annotations

import pytest

from app.models.merchant import PersonalityType
from app.services.recommendation.explanation_generator import ExplanationGenerator


class TestExplanationByPersonality:
    @pytest.mark.parametrize(
        "personality,reason_type,expected_substring",
        [
            (PersonalityType.FRIENDLY, "brand_match", "you like"),
            (PersonalityType.PROFESSIONAL, "brand_match", "stated preference"),
            (PersonalityType.ENTHUSIASTIC, "brand_match", "PERFECT"),
            (PersonalityType.FRIENDLY, "budget_match", "fits perfectly"),
            (PersonalityType.PROFESSIONAL, "budget_match", "specified budget"),
            (PersonalityType.ENTHUSIASTIC, "budget_match", "AMAZINGLY"),
            (PersonalityType.FRIENDLY, "category_match", "check this out"),
            (PersonalityType.PROFESSIONAL, "category_match", "Given your interest"),
            (PersonalityType.ENTHUSIASTIC, "category_match", "gonna ADORE"),
            (PersonalityType.FRIENDLY, "feature_match", "great pick"),
            (PersonalityType.PROFESSIONAL, "feature_match", "meets those specifications"),
            (PersonalityType.ENTHUSIASTIC, "feature_match", "has it ALL"),
            (PersonalityType.FRIENDLY, "novelty", "haven't seen yet"),
            (PersonalityType.PROFESSIONAL, "novelty", "not yet explored"),
            (PersonalityType.ENTHUSIASTIC, "novelty", "BRAND NEW"),
            (PersonalityType.FRIENDLY, "default", "great fit"),
            (PersonalityType.PROFESSIONAL, "default", "aligns well"),
            (PersonalityType.ENTHUSIASTIC, "default", "FANTASTIC"),
        ],
    )
    def test_personality_template_selection(self, personality, reason_type, expected_substring):
        result = ExplanationGenerator.generate_explanation(
            reason="test",
            reason_type=reason_type,
            personality=personality,
            brand="Nike",
            budget="$100",
            category="shoes",
            feature="cushioning",
            reasons="brand, price",
        )
        assert expected_substring.lower() in result.lower()

    def test_friendly_brand_match(self):
        result = ExplanationGenerator.generate_explanation(
            reason="brand_match:Nike",
            reason_type="brand_match",
            personality=PersonalityType.FRIENDLY,
            brand="Nike",
        )
        assert "Nike" in result

    def test_professional_budget_match(self):
        result = ExplanationGenerator.generate_explanation(
            reason="budget_match:$100",
            reason_type="budget_match",
            personality=PersonalityType.PROFESSIONAL,
            budget="$100",
        )
        assert "$100" in result

    def test_enthusiastic_feature_match(self):
        result = ExplanationGenerator.generate_explanation(
            reason="feature_match:cushioning",
            reason_type="feature_match",
            personality=PersonalityType.ENTHUSIASTIC,
            feature="cushioning",
        )
        assert "cushioning" in result


class TestMultiMatch:
    def test_multi_match_friendly(self):
        result = ExplanationGenerator.generate_explanation(
            reason="brand_match:Nike||budget_match:$100",
            reason_type="multi_match",
            personality=PersonalityType.FRIENDLY,
            reasons="Nike, $100 budget",
        )
        assert "checks all your boxes" in result
        assert "Nike" in result

    def test_multi_match_professional(self):
        result = ExplanationGenerator.generate_explanation(
            reason="multi",
            reason_type="multi_match",
            personality=PersonalityType.PROFESSIONAL,
            reasons="brand, budget",
        )
        assert "matches several" in result

    def test_multi_match_enthusiastic(self):
        result = ExplanationGenerator.generate_explanation(
            reason="multi",
            reason_type="multi_match",
            personality=PersonalityType.ENTHUSIASTIC,
            reasons="everything",
        )
        assert "EVERY mark" in result


class TestMissingTemplateVars:
    def test_missing_brand_var_falls_back_to_default(self):
        result = ExplanationGenerator.generate_explanation(
            reason="brand_match:Nike",
            reason_type="brand_match",
            personality=PersonalityType.FRIENDLY,
        )
        assert "great fit" in result

    def test_missing_budget_var_falls_back_to_default(self):
        result = ExplanationGenerator.generate_explanation(
            reason="budget_match:$100",
            reason_type="budget_match",
            personality=PersonalityType.FRIENDLY,
        )
        assert "great fit" in result

    def test_unknown_reason_type_falls_back_to_default(self):
        result = ExplanationGenerator.generate_explanation(
            reason="unknown_reason",
            reason_type="nonexistent_type",
            personality=PersonalityType.FRIENDLY,
        )
        assert "great fit" in result

    def test_unknown_personality_falls_back_to_friendly(self):
        result = ExplanationGenerator.generate_explanation(
            reason="test",
            reason_type="default",
            personality="nonexistent",
        )
        assert "great fit" in result


class TestDefaultBehavior:
    def test_default_reason_type_no_vars(self):
        result = ExplanationGenerator.generate_explanation(
            reason="default",
            reason_type="default",
            personality=PersonalityType.FRIENDLY,
        )
        assert len(result) > 0

    def test_returns_string(self):
        result = ExplanationGenerator.generate_explanation(
            reason="test",
            reason_type="brand_match",
            personality=PersonalityType.PROFESSIONAL,
            brand="Nike",
        )
        assert isinstance(result, str)
