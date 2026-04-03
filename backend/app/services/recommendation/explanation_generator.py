"""Explanation generator for contextual recommendations (Story 11-6).

Generates personality-aware explanations referencing conversation context.
"""

from __future__ import annotations

import structlog

from app.models.merchant import PersonalityType

logger = structlog.get_logger(__name__)


class ExplanationGenerator:
    REASON_TEMPLATES: dict[PersonalityType, dict[str, str]] = {
        PersonalityType.FRIENDLY: {
            "brand_match": "I noticed you like {brand}, so I thought you'd love this!",
            "budget_match": "This fits perfectly within your {budget} budget!",
            "category_match": "Since you're into {category}, check this out!",
            "feature_match": "Based on what you mentioned about {feature}, this is a great pick!",
            "multi_match": "This checks all your boxes — {reasons}!",
            "novelty": "Here's something new you haven't seen yet!",
            "default": "I think this would be a great fit for you!",
        },
        PersonalityType.PROFESSIONAL: {
            "brand_match": (
                "Based on your stated preference for {brand}, "
                "this product aligns with your criteria."
            ),
            "budget_match": "This product falls within your specified budget of {budget}.",
            "category_match": "Given your interest in {category}, this product is relevant.",
            "feature_match": (
                "Considering your requirements for {feature}, "
                "this product meets those specifications."
            ),
            "multi_match": "This product matches several of your criteria: {reasons}.",
            "novelty": "This is a new option not yet explored.",
            "default": "This product aligns well with your stated preferences.",
        },
        PersonalityType.ENTHUSIASTIC: {
            "brand_match": "You mentioned {brand} and THIS is PERFECT for you!",
            "budget_match": "Fits your {budget} budget AMAZINGLY well!",
            "category_match": "Since you LOVE {category}, you're gonna ADORE this!",
            "feature_match": "You mentioned {feature} and THIS has it ALL!",
            "multi_match": "This hits EVERY mark — {reasons}!",
            "novelty": "Here's something BRAND NEW you haven't seen yet!",
            "default": "This is a FANTASTIC match for what you're looking for!",
        },
    }

    @classmethod
    def generate_explanation(
        cls,
        reason: str,
        reason_type: str = "default",
        personality: PersonalityType = PersonalityType.FRIENDLY,
        **template_vars: str,
    ) -> str:
        templates = cls.REASON_TEMPLATES.get(
            personality, cls.REASON_TEMPLATES[PersonalityType.FRIENDLY]
        )
        template = templates.get(reason_type, templates["default"])
        try:
            return template.format(**template_vars)
        except KeyError:
            logger.warning(
                "explanation_template_missing_keys",
                reason_type=reason_type,
                available_vars=list(template_vars.keys()),
            )
            return templates["default"]
