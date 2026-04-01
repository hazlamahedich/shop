"""Question generation service for focused clarifying questions.

Generates ONE focused question at a time based on missing constraints
and priority ordering.

Story 11-2: Extended with General mode templates and mode-aware question generation.
"""

from __future__ import annotations

from typing import Any

import structlog

from app.services.intent import ClassificationResult

logger = structlog.get_logger(__name__)


class QuestionGenerator:
    """Generate focused clarifying questions for missing constraints.

    Priority order (E-commerce):
    1. Budget (most critical for pricing)
    2. Category (determines product type)
    3. Size (important for fit)
    4. Color (preference)
    5. Brand (preference)

    Priority order (General):
    1. Issue type (most critical for routing)
    2. Severity (determines urgency)
    3. Timeframe (context for resolution)
    4. Specifics (details for resolution)
    """

    QUESTION_TEMPLATES: dict[str, list[str]] = {
        "budget": [
            "What's your budget for this?",
            "How much are you looking to spend?",
            "What price range works for you?",
        ],
        "category": [
            "What type of product are you looking for?",
            "What category are you interested in?",
        ],
        "size": [
            "What size do you need?",
            "What size should I look for?",
        ],
        "color": [
            "Do you have a color preference?",
            "What color are you looking for?",
        ],
        "brand": [
            "Do you have a preferred brand?",
            "Any specific brand you're looking for?",
        ],
    }

    QUESTION_PRIORITY: list[str] = ["budget", "category", "size", "color", "brand"]

    GENERAL_MODE_TEMPLATES: dict[str, list[str]] = {
        "issue_type": [
            "Could you tell me more about what kind of issue you're experiencing? (e.g., login problem, payment issue, shipping delay)",
            "What type of problem are you facing? (e.g., account access, billing, delivery)",
        ],
        "severity": [
            "How urgent is this? Is it preventing you from completing something, or more of an inconvenience?",
            "Would you say this is critical, important, or minor?",
        ],
        "timeframe": [
            "When did this issue start? Is it happening right now or was it a one-time occurrence?",
            "How long has this been going on?",
        ],
        "specifics": [
            "Can you share any additional details? For example, error messages, order numbers, or steps you've already tried?",
            "Any extra info that might help — like error codes or what you've tried so far?",
        ],
    }

    GENERAL_QUESTION_PRIORITY: list[str] = ["issue_type", "severity", "timeframe", "specifics"]

    def __init__(self) -> None:
        self.logger = structlog.get_logger(__name__)

    async def generate_next_question(
        self,
        classification: ClassificationResult,
        questions_asked: list[str],
    ) -> tuple[str, str]:
        entities = classification.entities
        missing_constraints = self.get_missing_constraints(entities)
        remaining = [c for c in missing_constraints if c not in questions_asked]

        if not remaining:
            raise ValueError("No more questions to ask")

        next_constraint = remaining[0]
        question = self._select_question_template(next_constraint)

        self.logger.info(
            "question_generated",
            constraint=next_constraint,
            question=question,
        )

        return question, next_constraint

    async def generate_mode_aware_question(
        self,
        pending_questions: list[str],
        questions_asked: list[str],
        mode: str = "ecommerce",
        accumulated_constraints: dict[str, Any] | None = None,
    ) -> tuple[str, str]:
        remaining = [q for q in pending_questions if q not in questions_asked]

        if not remaining:
            raise ValueError("No more questions to ask")

        next_constraint = remaining[0]

        if mode == "general":
            templates = self.GENERAL_MODE_TEMPLATES
        else:
            templates = self.QUESTION_TEMPLATES

        template_list = templates.get(next_constraint, [])
        if template_list:
            question = template_list[0]
        else:
            question = f"What {next_constraint.replace('_', ' ')} are you looking for?"

        context_ref = ""
        if accumulated_constraints:
            if mode == "ecommerce":
                if "category" in accumulated_constraints:
                    context_ref = f" (for {accumulated_constraints['category']})"
                elif "brand" in accumulated_constraints:
                    context_ref = f" (from {accumulated_constraints['brand'].title()})"
            elif mode == "general":
                if "issue_type" in accumulated_constraints:
                    context_ref = f" (regarding your {accumulated_constraints['issue_type']} issue)"

        if context_ref:
            question = question.rstrip("?") + context_ref + "?"

        self.logger.info(
            "mode_aware_question_generated",
            constraint=next_constraint,
            question=question,
            mode=mode,
        )

        return question, next_constraint

    def generate_summary_of_understanding(
        self,
        accumulated_constraints: dict[str, Any],
        mode: str = "ecommerce",
    ) -> str:
        clean = {
            k: v
            for k, v in accumulated_constraints.items()
            if not k.endswith("_conflict") and v is not None
        }

        if not clean:
            return "Let me help you find what you're looking for."

        parts: list[str] = []

        if mode == "ecommerce":
            if "category" in clean:
                parts.append(clean["category"])
            if "product_type" in clean:
                parts.append(clean["product_type"])
            if "brand" in clean:
                parts.append(f"from {clean['brand'].title()}")
            if "budget_max" in clean:
                parts.append(f"under ${clean['budget_max']}")
            if "size" in clean:
                parts.append(f"size {clean['size']}")
            if "color" in clean:
                parts.append(f"in {clean['color']}")

            if parts:
                return f"So you're looking for {' '.join(parts)}. Let me search for that."
            return "Let me help you find what you're looking for."
        else:
            if "issue_type" in clean:
                parts.append(f"a {clean['issue_type']} issue")
            if "severity" in clean:
                parts.append(f"that's {clean['severity']}")
            if "timeframe" in clean:
                parts.append(f"started {clean['timeframe']}")

            if parts:
                return f"So you're dealing with {' '.join(parts)}. Let me help you with that."
            return "Let me help you with your question."

    def get_missing_constraints(self, entities: Any) -> list[str]:
        missing = []
        for constraint in self.QUESTION_PRIORITY:
            entity_value = getattr(entities, constraint, None)
            if not entity_value:
                missing.append(constraint)
        return missing

    def _select_question_template(self, constraint: str) -> str:
        templates = self.QUESTION_TEMPLATES.get(constraint, [])
        if not templates:
            return f"What {constraint} are you looking for?"
        return templates[0]
