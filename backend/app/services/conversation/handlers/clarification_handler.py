"""Clarification handler for unified conversation processing.

Story 5-10 Task 16: ClarificationHandler

Handles CLARIFICATION intent when user input is ambiguous or
missing critical constraints. Generates focused clarifying questions
and manages the clarification flow.

Story 11-11: Enhanced with natural question formatting, template rotation,
             context-aware follow-ups, and partial response handling.
"""

from __future__ import annotations

from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.merchant import Merchant, PersonalityType
from app.services.clarification import ClarificationService
from app.services.clarification.question_generator import QuestionGenerator
from app.services.conversation.handlers.base_handler import BaseHandler
from app.services.conversation.schemas import (
    ConversationContext,
    ConversationResponse,
)
from app.services.intent.classification_schema import (
    ClassificationResult,
    ExtractedEntities,
    IntentType,
)
from app.services.llm.base_llm_service import BaseLLMService
from app.services.personality.conversation_templates import register_conversation_templates
from app.services.personality.response_formatter import PersonalityAwareResponseFormatter
from app.services.personality.transition_phrases import TransitionCategory
from app.services.personality.transition_selector import get_transition_selector

register_conversation_templates()

logger = structlog.get_logger(__name__)


class ClarificationHandler(BaseHandler):
    """Handler for CLARIFICATION intent.

    Manages the clarification flow:
    1. Detect missing constraints from entities
    2. Generate focused question for highest priority missing constraint
    3. Handle clarification response with context-aware re-classification
    4. Fallback to assumptions after max attempts

    Question priority: budget > category > size > color > brand
    """

    MAX_CLARIFICATION_ATTEMPTS = 3

    async def handle(
        self,
        db: AsyncSession,
        merchant: Merchant,
        llm_service: BaseLLMService,
        message: str,
        context: ConversationContext,
        entities: dict[str, Any] | None = None,
    ) -> ConversationResponse:
        """Handle clarification intent.

        Args:
            db: Database session
            merchant: Merchant configuration
            llm_service: LLM service for this merchant
            message: User's message
            context: Conversation context with clarification state
            entities: Extracted entities from intent classification

        Returns:
            ConversationResponse with clarifying question or fallback
        """
        clarification_service = ClarificationService()
        question_generator = QuestionGenerator()

        context_dict = self._context_to_dict(context, entities)
        conversation_id = str(context.session_id)
        clarification_state = context_dict.get("clarification", {})

        if clarification_state.get("active"):
            return await self._handle_clarification_response(
                db=db,
                merchant=merchant,
                llm_service=llm_service,
                message=message,
                context=context_dict,
                clarification_service=clarification_service,
                question_generator=question_generator,
                conversation_id=conversation_id,
            )

        return await self._ask_first_question(
            merchant=merchant,
            llm_service=llm_service,
            entities=entities,
            context=context_dict,
            question_generator=question_generator,
            conversation_id=conversation_id,
        )

    async def _handle_clarification_response(
        self,
        db: AsyncSession,
        merchant: Merchant,
        llm_service: BaseLLMService,
        message: str,
        context: dict[str, Any],
        clarification_service: ClarificationService,
        question_generator: QuestionGenerator,
        conversation_id: str | None = None,
    ) -> ConversationResponse:
        """Handle response to a clarification question.

        Args:
            db: Database session
            merchant: Merchant configuration
            llm_service: LLM service for re-classification
            message: User's clarification response
            context: Conversation context with clarification state
            clarification_service: Clarification service
            question_generator: Question generator

        Returns:
            ConversationResponse - either next question, search, or fallback
        """
        from app.services.intent.intent_classifier import IntentClassifier

        classifier = IntentClassifier(llm_service=llm_service)

        should_fallback = await clarification_service.should_fallback_to_assumptions(context)

        if should_fallback:
            classification = context.get("last_classification")
            if classification:
                message_text, assumed = await clarification_service.generate_assumption_message(
                    classification,
                    context,
                )
                return ConversationResponse(
                    message=message_text,
                    intent="clarification",
                    confidence=1.0,
                    metadata={
                        "fallback": True,
                        "assumed_constraints": assumed,
                        "action": "proceed_to_search",
                    },
                )

        result = await clarification_service.process_clarification_response(
            message=message,
            context=context,
            classifier=classifier,
        )

        if result.confidence >= clarification_service.CONFIDENCE_THRESHOLD:
            return ConversationResponse(
                message="Got it! Let me search for that.",
                intent="clarification",
                confidence=result.confidence,
                metadata={
                    "resolved": True,
                    "action": "proceed_to_search",
                    "entities": result.entities.model_dump(),
                },
            )

        return await self._ask_next_question(
            merchant=merchant,
            llm_service=llm_service,
            context=context,
            result=result,
            question_generator=question_generator,
            clarification_service=clarification_service,
            conversation_id=conversation_id,
        )

    async def _ask_first_question(
        self,
        merchant: Merchant,
        llm_service: BaseLLMService,
        entities: dict[str, Any] | None,
        context: dict[str, Any],
        question_generator: QuestionGenerator,
        conversation_id: str | None = None,
    ) -> ConversationResponse:
        """Ask the first clarification question.

        Uses combined question when multiple constraints are missing (AC2),
        with template rotation for variety (AC1).

        Args:
            merchant: Merchant configuration
            llm_service: LLM service for personality-based questions
            entities: Extracted entities
            context: Conversation context
            question_generator: Question generator
            conversation_id: Conversation ID for anti-repetition

        Returns:
            ConversationResponse with clarifying question
        """
        extracted = self._dict_to_entities(entities)
        mode = getattr(merchant, "onboarding_mode", "ecommerce") or "ecommerce"
        accumulated_constraints = context.get("clarification", {}).get(
            "accumulated_constraints", {}
        )

        dummy_classification = ClassificationResult(
            intent=IntentType.PRODUCT_SEARCH,
            confidence=0.5,
            entities=extracted,
            raw_message="",
            llm_provider="unknown",
            model="unknown",
            processing_time_ms=0,
            reasoning="",
        )

        missing_constraints = question_generator.get_missing_constraints(extracted)

        try:
            if len(missing_constraints) > 1:
                question = question_generator.generate_combined_question(
                    constraints=missing_constraints,
                    accumulated_constraints=accumulated_constraints or None,
                    mode=mode,
                )
                constraint = missing_constraints[0]
            else:
                question, constraint = await question_generator.generate_next_question(
                    classification=dummy_classification,
                    questions_asked=[],
                )
        except ValueError:
            try:
                fallback_msg = PersonalityAwareResponseFormatter.format_response(
                    "conversation",
                    "clarification_fallback",
                    merchant.personality or PersonalityType.FRIENDLY,
                )
            except Exception:
                fallback_msg = "Could you tell me more about what you're looking for?"
            return ConversationResponse(
                message=fallback_msg,
                intent="clarification",
                confidence=0.5,
                metadata={"error": "no_questions"},
            )

        personalized_question = await self._personalize_question(
            question=question,
            constraint=constraint,
            merchant=merchant,
            llm_service=llm_service,
            conversation_id=conversation_id,
            mode=mode,
            accumulated_constraints=accumulated_constraints or None,
            is_combined=len(missing_constraints) > 1,
        )

        logger.info(
            "clarification_question_asked",
            merchant_id=merchant.id,
            constraint=constraint,
            question=personalized_question,
            combined=len(missing_constraints) > 1,
        )

        return ConversationResponse(
            message=personalized_question,
            intent="clarification",
            confidence=1.0,
            metadata={
                "clarification_active": True,
                "constraint": constraint,
                "attempt": 1,
                "combined_constraints": (
                    missing_constraints if len(missing_constraints) > 1 else None
                ),
            },
        )

    async def _ask_next_question(
        self,
        merchant: Merchant,
        llm_service: BaseLLMService,
        context: dict[str, Any],
        result: ClassificationResult,
        question_generator: QuestionGenerator,
        clarification_service: ClarificationService,
        conversation_id: str | None = None,
    ) -> ConversationResponse:
        """Ask the next clarification question.

        Uses context-aware generation (AC3), template rotation (AC1),
        and partial response acknowledgment when appropriate.

        Args:
            merchant: Merchant configuration
            llm_service: LLM service for personality-based questions
            context: Conversation context
            result: Re-classification result
            question_generator: Question generator
            clarification_service: Clarification service
            conversation_id: Conversation ID for anti-repetition tracking

        Returns:
            ConversationResponse with next clarifying question
        """
        clarification_state = context.get("clarification", {})
        questions_asked = clarification_state.get("questions_asked", [])
        accumulated_constraints = clarification_state.get("accumulated_constraints", {})
        attempt_count = clarification_state.get("attempt_count", 0) + 1
        mode = getattr(merchant, "onboarding_mode", "ecommerce") or "ecommerce"

        missing_constraints = question_generator.get_missing_constraints(result.entities)
        remaining = [c for c in missing_constraints if c not in questions_asked]

        if not remaining:
            message_text, assumed = await clarification_service.generate_assumption_message(
                result,
                context,
            )
            return ConversationResponse(
                message=message_text,
                intent="clarification",
                confidence=1.0,
                metadata={
                    "fallback": True,
                    "assumed_constraints": assumed,
                    "action": "proceed_to_search",
                },
            )

        next_constraint = remaining[0]

        used_indices = clarification_state.get("used_indices", {})

        partial_field = self._detect_partial_response(result)
        if partial_field:
            follow_up = await question_generator.generate_context_aware_question(
                constraint=next_constraint,
                accumulated_constraints=accumulated_constraints,
                mode=mode,
                used_indices=used_indices,
            )
            updated_indices = self._advance_used_index(
                used_indices, next_constraint, question_generator, mode
            )
            message = self._handle_partial_response(
                accepted_field=partial_field,
                follow_up_question=follow_up,
                merchant=merchant,
            )
            logger.info(
                "clarification_partial_response",
                merchant_id=merchant.id,
                accepted=partial_field,
                next_constraint=next_constraint,
                attempt=attempt_count,
            )
            return ConversationResponse(
                message=message,
                intent="clarification",
                confidence=result.confidence,
                metadata={
                    "clarification_active": True,
                    "constraint": next_constraint,
                    "attempt": attempt_count,
                    "partial_response": True,
                    "accepted_field": partial_field,
                    "used_indices": updated_indices,
                },
            )

        question = await question_generator.generate_context_aware_question(
            constraint=next_constraint,
            accumulated_constraints=accumulated_constraints,
            mode=mode,
            used_indices=used_indices,
        )
        updated_indices = self._advance_used_index(
            used_indices, next_constraint, question_generator, mode
        )

        personalized_question = await self._personalize_question(
            question=question,
            constraint=next_constraint,
            merchant=merchant,
            llm_service=llm_service,
            conversation_id=conversation_id,
            mode=mode,
            accumulated_constraints=accumulated_constraints,
        )

        logger.info(
            "clarification_followup_asked",
            merchant_id=merchant.id,
            constraint=next_constraint,
            attempt=attempt_count,
            context_aware=True,
        )

        return ConversationResponse(
            message=personalized_question,
            intent="clarification",
            confidence=result.confidence,
            metadata={
                "clarification_active": True,
                "constraint": next_constraint,
                "attempt": attempt_count,
                "used_indices": updated_indices,
            },
        )

    @staticmethod
    def _advance_used_index(
        used_indices: dict[str, int],
        constraint: str,
        question_generator: QuestionGenerator,
        mode: str,
    ) -> dict[str, int]:
        """Advance and return the used index for a constraint after template selection."""
        templates = (
            question_generator.GENERAL_MODE_TEMPLATES.get(constraint, [])
            if mode == "general"
            else question_generator.QUESTION_TEMPLATES.get(constraint, [])
        )
        current = used_indices.get(constraint, -1)
        updated = dict(used_indices)
        updated[constraint] = (current + 1) % max(len(templates), 1)
        return updated

    @staticmethod
    def _compute_used_indices(
        questions_asked: list[str],
        question_generator: QuestionGenerator,
        mode: str,
    ) -> dict[str, int]:
        """Compute template rotation indices from questions asked."""
        used_indices: dict[str, int] = {}
        for q in questions_asked:
            templates = (
                question_generator.GENERAL_MODE_TEMPLATES.get(q, [])
                if mode == "general"
                else question_generator.QUESTION_TEMPLATES.get(q, [])
            )
            current = used_indices.get(q, -1)
            used_indices[q] = (current + 1) % max(len(templates), 1)
        return used_indices

    @staticmethod
    def _detect_partial_response(result: ClassificationResult) -> str | None:
        """Detect if the user gave a partial response with one resolved entity."""
        entity_fields = ["category", "budget", "size", "color", "brand"]
        resolved = [f for f in entity_fields if getattr(result.entities, f, None) is not None]
        if len(resolved) == 1:
            return resolved[0]
        return None

    async def _personalize_question(
        self,
        question: str,
        constraint: str,
        merchant: Merchant,
        llm_service: BaseLLMService,
        conversation_id: str | None = None,
        mode: str = "ecommerce",
        skip_transition: bool = False,
        accumulated_constraints: dict[str, Any] | None = None,
        is_combined: bool = False,
    ) -> str:
        personality = merchant.personality or PersonalityType.FRIENDLY
        business_name = getattr(merchant, "business_name", None)

        prefix = ""
        if business_name and constraint == "budget" and not is_combined:
            prefix = f"At {business_name}, we have options for every budget. "

        if skip_transition:
            return f"{prefix}{question}"

        selector = get_transition_selector()
        transition = selector.select(
            TransitionCategory.CLARIFYING,
            personality,
            conversation_id=conversation_id,
            mode=mode,
        )

        return f"{transition} {prefix}{question}"

    def _handle_partial_response(
        self,
        accepted_field: str,
        follow_up_question: str,
        merchant: Merchant,
    ) -> str:
        personality = merchant.personality or PersonalityType.FRIENDLY

        try:
            return PersonalityAwareResponseFormatter.format_response(
                "clarification_natural",
                "partial_response_acknowledge",
                personality,
                accepted_field=accepted_field,
                follow_up_question=follow_up_question,
            )
        except Exception:
            return f"Thanks for sharing the {accepted_field}! {follow_up_question}"

    def _context_to_dict(
        self,
        context: ConversationContext,
        entities: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Convert ConversationContext to dict for clarification service.

        Args:
            context: Conversation context
            entities: Extracted entities

        Returns:
            Dict representation for clarification service
        """
        return {
            "conversation_history": context.conversation_history,
            "clarification": context.metadata.get("clarification", {}),
            "extracted_entities": entities or {},
            "previous_intents": context.metadata.get("previous_intents", []),
            "last_classification": context.metadata.get("last_classification"),
        }

    def _dict_to_entities(self, entities: dict[str, Any] | None) -> ExtractedEntities:
        """Convert dict to ExtractedEntities.

        Args:
            entities: Dict of extracted entities

        Returns:
            ExtractedEntities instance
        """
        if not entities:
            return ExtractedEntities()

        return ExtractedEntities(
            category=entities.get("category"),
            budget=entities.get("budget"),
            budget_currency=entities.get("budget_currency", "USD"),
            size=entities.get("size"),
            color=entities.get("color"),
            brand=entities.get("brand"),
            constraints=entities.get("constraints", {}),
        )
