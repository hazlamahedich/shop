"""Clarification service for handling ambiguous user requests.

Orchestrates the clarification process:
1. Check confidence score and missing constraints
2. Generate focused question for missing constraints
3. Parse clarification response
4. Update context with refined constraints
5. Fallback to assumptions after max attempts

Story 11-2: Extended with multi-turn support, General mode, and configurable turn limits.
"""

from __future__ import annotations

from typing import Any

import structlog

from app.services.intent import ClassificationResult, IntentClassifier, IntentType

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
    GENERAL_MODE_CONFIDENCE_THRESHOLD: float = 0.75
    MAX_CLARIFICATION_ATTEMPTS: int = 3

    def __init__(self) -> None:
        self.logger = structlog.get_logger(__name__)

    async def needs_clarification(
        self,
        classification: ClassificationResult,
        context: dict[str, Any],
    ) -> bool:
        if classification.intent != IntentType.PRODUCT_SEARCH:
            return False

        if classification.confidence < self.CONFIDENCE_THRESHOLD:
            self.logger.info(
                "low_confidence_detected",
                confidence=classification.confidence,
                threshold=self.CONFIDENCE_THRESHOLD,
            )
            return True

        missing = self._get_missing_constraints(classification.entities)
        if missing:
            self.logger.info(
                "missing_constraints_detected",
                missing=missing,
            )
            return True

        return False

    async def is_general_mode_clarification(
        self,
        classification: ClassificationResult,
        context: dict[str, Any],
    ) -> bool:
        if classification.confidence < self.GENERAL_MODE_CONFIDENCE_THRESHOLD:
            self.logger.info(
                "general_mode_low_confidence",
                confidence=classification.confidence,
                threshold=self.GENERAL_MODE_CONFIDENCE_THRESHOLD,
            )
            return True

        return False

    async def process_multi_turn_clarification(
        self,
        message: str,
        context: dict[str, Any],
        classifier: IntentClassifier,
        multi_turn_state: dict[str, Any],
    ) -> tuple[ClassificationResult, dict[str, Any]]:
        clarification_state = context.get("clarification", {})
        questions_asked = clarification_state.get("questions_asked", [])
        previous_intents = context.get("previous_intents", [])
        extracted_entities = context.get("extracted_entities", {})

        context_prefix = ""
        if questions_asked:
            last_question = questions_asked[-1]
            context_prefix = f"(User was asked about: {last_question}) "

        if extracted_entities:
            entity_context = ", ".join([f"{k}={v}" for k, v in extracted_entities.items() if v])
            if entity_context:
                context_prefix += f"(Previous: {entity_context}) "

        enriched_message = f"{context_prefix}{message}".strip()

        self.logger.info(
            "multi_turn_clarification_reclassification",
            original_message=message,
            enriched_message=enriched_message,
            turn_count=multi_turn_state.get("turn_count", 0),
        )

        result = await classifier.classify(enriched_message, context)

        return result, multi_turn_state

    async def check_clarification_timeout(
        self,
        multi_turn_state: dict[str, Any],
        max_turns: int = 3,
    ) -> tuple[bool, str]:
        turn_count = multi_turn_state.get("turn_count", 0)

        if turn_count >= max_turns:
            return True, "max_turns_reached"

        if turn_count >= max_turns - 1:
            return False, "near_limit"

        return False, "continuing"

    def _get_missing_constraints(self, entities: Any) -> list[str]:
        missing = []
        if not entities.budget:
            missing.append("budget")
        if not entities.category:
            missing.append("category")
        return missing

    async def process_clarification_response(
        self,
        message: str,
        context: dict[str, Any],
        classifier: IntentClassifier,
    ) -> ClassificationResult:
        clarification_state = context.get("clarification", {})
        questions_asked = clarification_state.get("questions_asked", [])
        previous_intents = context.get("previous_intents", [])
        extracted_entities = context.get("extracted_entities", {})

        context_prefix = ""

        if questions_asked:
            last_question = questions_asked[-1]
            context_prefix = f"(User was asked about: {last_question}) "

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

        result = await classifier.classify(enriched_message, context)

        return result

    async def should_fallback_to_assumptions(
        self,
        context: dict[str, Any],
    ) -> bool:
        clarification_state = context.get("clarification", {})
        attempt_count = clarification_state.get("attempt_count", 0)
        return attempt_count >= self.MAX_CLARIFICATION_ATTEMPTS

    async def generate_assumption_message(
        self,
        classification: ClassificationResult,
        context: dict[str, Any],
    ) -> tuple[str, dict[str, Any]]:
        entities = classification.entities
        assumed: dict[str, Any] = {}

        if not entities.budget:
            assumed["budget"] = None

        if not entities.size:
            assumed["size"] = None

        category = entities.category or "items"

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
