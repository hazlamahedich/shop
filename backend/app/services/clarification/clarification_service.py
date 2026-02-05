"""Clarification service for handling ambiguous user requests.

Orchestrates the clarification process:
1. Check confidence score and missing constraints
2. Generate focused question for missing constraints
3. Parse clarification response
4. Update context with refined constraints
5. Fallback to assumptions after max attempts
"""

from __future__ import annotations

from typing import Any

import structlog

from app.services.clarification.question_generator import QuestionGenerator
from app.services.intent import ClassificationResult, IntentType, IntentClassifier


logger = structlog.get_logger(__name__)


class ClarificationService:
    """Service for handling clarification flows when intent confidence is low.

    Orchestrates the clarification process:
    1. Check confidence score and missing constraints
    2. Generate focused question for missing constraints
    3. Parse clarification response
    4. Update context with refined constraints
    5. Fallback to assumptions after max attempts
    """

    CONFIDENCE_THRESHOLD: float = 0.80
    MAX_CLARIFICATION_ATTEMPTS: int = 3

    def __init__(self) -> None:
        """Initialize clarification service."""
        self.logger = structlog.get_logger(__name__)

    async def needs_clarification(
        self,
        classification: ClassificationResult,
        context: dict[str, Any],
    ) -> bool:
        """Check if clarification is needed based on confidence and constraints.

        Clarification is only triggered for PRODUCT_SEARCH intent when:
        - Confidence is below threshold (< 0.80), OR
        - Critical constraints are missing (budget, category)

        Args:
            classification: Intent classification from Story 2.1
            context: Conversation context with state tracking

        Returns:
            True if clarification is needed, False otherwise
        """
        # Only product search intent needs clarification
        if classification.intent != IntentType.PRODUCT_SEARCH:
            return False

        # Check confidence score
        if classification.confidence < self.CONFIDENCE_THRESHOLD:
            self.logger.info(
                "low_confidence_detected",
                confidence=classification.confidence,
                threshold=self.CONFIDENCE_THRESHOLD,
            )
            return True

        # Check for critical missing constraints
        missing = self._get_missing_constraints(classification.entities)
        if missing:
            self.logger.info(
                "missing_constraints_detected",
                missing=missing,
            )
            return True

        return False

    def _get_missing_constraints(self, entities: Any) -> list[str]:
        """Identify missing CRITICAL constraints for triggering clarification.

        NOTE: This only checks budget and category as CRITICAL constraints.
        QuestionGenerator checks ALL constraints for question generation.

        Args:
            entities: Extracted entities from intent classification

        Returns:
            List of missing CRITICAL constraint names (budget, category only)
        """
        missing = []

        # Budget is critical for pricing
        if not entities.budget:
            missing.append("budget")

        # Category is important for product type
        if not entities.category:
            missing.append("category")

        return missing

    async def process_clarification_response(
        self,
        message: str,
        context: dict[str, Any],
        classifier: IntentClassifier,
    ) -> ClassificationResult:
        """Process a clarification response with context-aware re-classification.

        This method handles the critical case where a user provides a short answer
        like "under 50" or "red" that could be misclassified without context.
        It combines the user's response with the conversation context to create
        an enriched prompt for re-classification.

        Args:
            message: The user's clarification response
            context: Conversation context including previous messages and clarification state
            classifier: Intent classifier instance

        Returns:
            Classification result with updated entities
        """
        clarification_state = context.get("clarification", {})
        questions_asked = clarification_state.get("questions_asked", [])
        previous_intents = context.get("previous_intents", [])
        extracted_entities = context.get("extracted_entities", {})

        # Build context-aware prompt for re-classification
        # This helps the classifier understand that "under 50" means "budget under 50"
        # when the bot just asked about budget
        context_prefix = ""

        if questions_asked:
            last_question = questions_asked[-1]
            context_prefix = f"(User was asked about: {last_question}) "

        # Include previous extracted entities for context
        if extracted_entities:
            entity_context = ", ".join([f"{k}={v}" for k, v in extracted_entities.items() if v])
            if entity_context:
                context_prefix += f"(Previous: {entity_context}) "

        enriched_message = f"{context_prefix}{message}".strip()

        self.logger.info(
            "clarification_reclassification",
            original_message=message,
            enriched_message=enriched_message,
            questions_asked=questions_asked,
        )

        # Classify with enriched prompt
        result = await classifier.classify(enriched_message, context)

        return result

    async def should_fallback_to_assumptions(
        self,
        context: dict[str, Any],
    ) -> bool:
        """Check if we should fallback to assumptions after max attempts.

        Args:
            context: Conversation context with clarification state

        Returns:
            True if should fallback, False otherwise
        """
        clarification_state = context.get("clarification", {})
        attempt_count = clarification_state.get("attempt_count", 0)

        return attempt_count >= self.MAX_CLARIFICATION_ATTEMPTS

    async def generate_assumption_message(
        self,
        classification: ClassificationResult,
        context: dict[str, Any],
    ) -> tuple[str, dict[str, Any]]:
        """Generate message when falling back to assumptions.

        Args:
            classification: Current intent classification
            context: Conversation context

        Returns:
            Tuple of (message_text, assumed_constraints)
        """
        entities = classification.entities

        # Make reasonable assumptions
        assumed: dict[str, Any] = {}

        # Default budget if missing
        if not entities.budget:
            assumed["budget"] = None  # No budget limit

        # Default size if missing
        if not entities.size:
            assumed["size"] = None  # Any size

        # Use category if present, otherwise generic
        category = entities.category or "items"

        # Generate assumption message
        if assumed.get("budget") is not None:
            message = f"I'll show you {category} options. Let me know if you want to adjust your budget or other preferences."
        else:
            message = f"I'll show you {category} options. Let me know if you'd like to narrow down by price, size, or other preferences."

        self.logger.info(
            "fallback_to_assumptions",
            assumed=assumed,
            message=message,
        )

        return message, assumed
