"""Question generation service for focused clarifying questions.

Generates ONE focused question at a time based on missing constraints
and priority ordering.

Story 11-2: Extended with General mode templates and mode-aware question generation.
Story 11-11: Natural clarification questions — template rotation, context-aware,
             combined questions, mode-specific natural variants.
"""

from __future__ import annotations

from typing import Any

import structlog

from app.services.intent import ClassificationResult
from app.services.intent.classification_schema import IntentType
from app.services.proactive_gathering.intent_requirements import INTENT_REQUIREMENTS

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
            "I'd love to help narrow things down — do you have a price range in mind?",
            "So I can show you the best options, what's your budget?",
        ],
        "category": [
            "What type of product are you looking for?",
            "What category are you interested in?",
            "I'd love to help you find exactly what you need — what kind of item is it?",
            "What sort of thing are you after?",
        ],
        "size": [
            "What size do you need?",
            "What size should I look for?",
            "Do you know what size would work best?",
            "What's your preferred size?",
        ],
        "color": [
            "Do you have a color preference?",
            "What color are you looking for?",
            "Any particular color you'd like?",
            "Were you thinking of a specific color?",
        ],
        "brand": [
            "Do you have a preferred brand?",
            "Any specific brand you're looking for?",
            "Is there a particular brand you'd like to go with?",
            "Any brand preference, or are you open to suggestions?",
        ],
    }

    QUESTION_PRIORITY: list[str] = ["budget", "category", "size", "color", "brand"]

    GENERAL_MODE_TEMPLATES: dict[str, list[str]] = {
        "issue_type": [
            "Could you tell me more about what kind of issue you're "
            "experiencing? (e.g., login problem, payment issue, shipping delay)",
            "What type of problem are you facing? (e.g., account access, billing, delivery)",
            "I want to make sure I help you effectively — "
            "could you describe the issue you're running into?",
            "To get you the right support, what seems to be the trouble?",
        ],
        "severity": [
            "How urgent is this? Is it preventing you from completing "
            "something, or more of an inconvenience?",
            "Would you say this is critical, important, or minor?",
            "Is this something that's blocking you right now, or more of a minor hiccup?",
            "How much is this affecting you — is it urgent or can it wait a bit?",
        ],
        "timeframe": [
            "When did this issue start? Is it happening right now or was it a one-time occurrence?",
            "How long has this been going on?",
            "Can you tell me when you first noticed this? Is it still happening?",
            "When did this start, and is it ongoing?",
        ],
        "specifics": [
            "Can you share any additional details? For example, error messages, "
            "order numbers, or steps you've already tried?",
            "Any extra info that might help — like error codes or what you've tried so far?",
            "To help me look into this further, could you share any details "
            "like error messages or order numbers?",
            "Anything else that might be helpful — "
            "like what you've already tried or any error messages?",
        ],
    }

    GENERAL_QUESTION_PRIORITY: list[str] = ["issue_type", "severity", "timeframe", "specifics"]

    def __init__(self) -> None:
        self.logger = structlog.get_logger(__name__)

    async def generate_next_question(
        self,
        classification: ClassificationResult,
        questions_asked: list[str],
        *,
        used_indices: dict[str, int] | None = None,
    ) -> tuple[str, str]:
        entities = classification.entities
        missing_constraints = self.get_missing_constraints(entities)
        remaining = [c for c in missing_constraints if c not in questions_asked]

        if not remaining:
            raise ValueError("No more questions to ask")

        next_constraint = remaining[0]
        question = self._select_question_template(next_constraint, used_indices=used_indices)

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

    def _select_question_template(
        self,
        constraint: str,
        *,
        used_indices: dict[str, int] | None = None,
    ) -> str:
        templates = self.QUESTION_TEMPLATES.get(constraint, [])
        if not templates:
            return f"What {constraint} are you looking for?"
        if used_indices is None:
            return templates[0]
        last_index = used_indices.get(constraint, -1)
        next_index = (last_index + 1) % len(templates)
        return templates[next_index]

    async def generate_context_aware_question(
        self,
        constraint: str,
        accumulated_constraints: dict[str, Any],
        mode: str = "ecommerce",
        *,
        used_indices: dict[str, int] | None = None,
    ) -> str:
        templates = self.GENERAL_MODE_TEMPLATES if mode == "general" else self.QUESTION_TEMPLATES
        template_list = templates.get(constraint, [])

        if not template_list:
            display_name = self._get_display_name(constraint, mode)
            return f"What {display_name} are you looking for?"

        if used_indices is not None:
            last_index = used_indices.get(constraint, -1)
            next_index = (last_index + 1) % len(template_list)
            question = template_list[next_index]
        else:
            question = template_list[0]

        context_ref = self._build_context_reference(accumulated_constraints, mode)
        if context_ref:
            question = question.rstrip("?.! ") + f" {context_ref}?"

        self.logger.info(
            "context_aware_question_generated",
            constraint=constraint,
            mode=mode,
            has_context=bool(context_ref),
        )

        return question

    def generate_combined_question(
        self,
        constraints: list[str],
        accumulated_constraints: dict[str, Any] | None = None,
        mode: str = "ecommerce",
        *,
        max_length: int = 200,
    ) -> str:
        if not constraints:
            raise ValueError("No constraints to combine")

        if len(constraints) == 1:
            display = self._get_display_name(constraints[0], mode)
            return f"What {display} are you looking for?"

        names = [self._get_display_name(c, mode) for c in constraints]

        if len(names) == 2:
            question = f"Do you have a preference for {names[0]} or {names[1]}?"
        else:
            all_but_last = ", ".join(names[:-1])
            question = (
                f"To help narrow things down — any thoughts on {all_but_last}, or {names[-1]}?"
            )

        if accumulated_constraints:
            context_ref = self._build_context_reference(accumulated_constraints, mode)
            if context_ref and len(question) + len(context_ref) + 3 <= max_length:
                question = question.rstrip("?.! ") + f" ({context_ref})?"

        if len(question) > max_length:
            question = question[: max_length - 3].rstrip("?.! ") + "..."

        return question

    def _build_context_reference(
        self,
        accumulated_constraints: dict[str, Any],
        mode: str = "ecommerce",
    ) -> str:
        if mode == "ecommerce":
            parts: list[str] = []
            if "category" in accumulated_constraints:
                parts.append(accumulated_constraints["category"])
            if "brand" in accumulated_constraints:
                parts.append(f"from {accumulated_constraints['brand'].title()}")
            if "budget_max" in accumulated_constraints:
                parts.append(f"under ${accumulated_constraints['budget_max']}")
            if "color" in accumulated_constraints:
                parts.append(f"in {accumulated_constraints['color']}")
            if "size" in accumulated_constraints:
                parts.append(f"size {accumulated_constraints['size']}")
            return f"for {' '.join(parts)}" if parts else ""
        else:
            if "issue_type" in accumulated_constraints:
                return f"regarding your {accumulated_constraints['issue_type']} issue"
            return ""

    def _get_display_name(self, constraint: str, mode: str = "ecommerce") -> str:
        intent = IntentType.PRODUCT_SEARCH if mode == "ecommerce" else IntentType.GENERAL
        requirements = INTENT_REQUIREMENTS.get(intent, [])
        for req in requirements:
            if req.field_name == constraint:
                return req.display_name
        return constraint.replace("_", " ")

    def _get_examples_for_constraint(self, constraint: str, mode: str = "ecommerce") -> list[str]:
        intent = IntentType.PRODUCT_SEARCH if mode == "ecommerce" else IntentType.GENERAL
        requirements = INTENT_REQUIREMENTS.get(intent, [])
        for req in requirements:
            if req.field_name == constraint:
                return req.example_values
        return []
