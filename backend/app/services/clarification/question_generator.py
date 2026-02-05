"""Question generation service for focused clarifying questions.

Generates ONE focused question at a time based on missing constraints
and priority ordering.
"""

from __future__ import annotations

from typing import Any

import structlog

from app.services.intent import ClassificationResult


logger = structlog.get_logger(__name__)


class QuestionGenerator:
    """Generate focused clarifying questions for missing constraints.

    Priority order:
    1. Budget (most critical for pricing)
    2. Category (determines product type)
    3. Size (important for fit)
    4. Color (preference)
    5. Brand (preference)
    """

    # Question templates for each constraint
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

    # Priority order for asking questions
    QUESTION_PRIORITY: list[str] = ["budget", "category", "size", "color", "brand"]

    def __init__(self) -> None:
        """Initialize question generator."""
        self.logger = structlog.get_logger(__name__)

    async def generate_next_question(
        self,
        classification: ClassificationResult,
        questions_asked: list[str],
    ) -> tuple[str, str]:
        """Generate the next focused clarifying question.

        Args:
            classification: Intent classification with entities
            questions_asked: List of questions already asked

        Returns:
            Tuple of (question_text, constraint_name)

        Raises:
            ValueError: If no questions can be generated
        """
        entities = classification.entities

        # Find missing constraints in priority order
        missing_constraints = self.get_missing_constraints(entities)

        # Filter out already-asked questions
        remaining = [c for c in missing_constraints if c not in questions_asked]

        if not remaining:
            raise ValueError("No more questions to ask")

        # Get highest priority remaining question
        next_constraint = remaining[0]

        # Generate question from template
        question = self._select_question_template(next_constraint)

        self.logger.info(
            "question_generated",
            constraint=next_constraint,
            question=question,
        )

        return question, next_constraint

    def get_missing_constraints(self, entities: Any) -> list[str]:
        """Get list of missing constraints in priority order (public API).

        This is a public method used by both QuestionGenerator and ClarificationService
        to ensure consistent constraint detection across the clarification flow.

        Args:
            entities: Extracted entities from classification

        Returns:
            List of missing constraint names in priority order
        """
        missing = []

        for constraint in self.QUESTION_PRIORITY:
            entity_value = getattr(entities, constraint, None)
            if not entity_value:
                missing.append(constraint)

        return missing

    def _get_missing_constraints(self, entities: Any) -> list[str]:
        """Get list of missing constraints in priority order.

        Args:
            entities: Extracted entities from classification

        Returns:
            List of missing constraint names
        """
        missing = []

        for constraint in self.QUESTION_PRIORITY:
            entity_value = getattr(entities, constraint, None)
            if not entity_value:
                missing.append(constraint)

        return missing

    def _select_question_template(self, constraint: str) -> str:
        """Select a question template for the given constraint.

        Args:
            constraint: Constraint name

        Returns:
            Question template string
        """
        templates = self.QUESTION_TEMPLATES.get(constraint, [])

        if not templates:
            return f"What {constraint} are you looking for?"

        # Simple selection - use first template
        return templates[0]
