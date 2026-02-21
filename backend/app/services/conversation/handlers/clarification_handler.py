"""Clarification handler for unified conversation processing.

Story 5-10 Task 16: ClarificationHandler

Handles CLARIFICATION intent when user input is ambiguous or
missing critical constraints. Generates focused clarifying questions
and manages the clarification flow.
"""

from __future__ import annotations

from typing import Any, Optional

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.merchant import Merchant
from app.services.conversation.schemas import (
    ConversationContext,
    ConversationResponse,
)
from app.services.conversation.handlers.base_handler import BaseHandler
from app.services.llm.base_llm_service import BaseLLMService
from app.services.clarification import ClarificationService
from app.services.clarification.question_generator import QuestionGenerator
from app.services.intent.classification_schema import (
    ClassificationResult,
    ExtractedEntities,
    IntentType,
)


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
        entities: Optional[dict[str, Any]] = None,
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
            )

        return await self._ask_first_question(
            merchant=merchant,
            llm_service=llm_service,
            entities=entities,
            context=context_dict,
            question_generator=question_generator,
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
        )

    async def _ask_first_question(
        self,
        merchant: Merchant,
        llm_service: BaseLLMService,
        entities: Optional[dict[str, Any]],
        context: dict[str, Any],
        question_generator: QuestionGenerator,
    ) -> ConversationResponse:
        """Ask the first clarification question.

        Args:
            merchant: Merchant configuration
            llm_service: LLM service for personality-based questions
            entities: Extracted entities
            context: Conversation context
            question_generator: Question generator

        Returns:
            ConversationResponse with clarifying question
        """
        extracted = self._dict_to_entities(entities)

        dummy_classification = ClassificationResult(
            intent=IntentType.PRODUCT_SEARCH,
            confidence=0.5,
            entities=extracted,
            raw_message="",
            llm_provider="unknown",
            model="unknown",
            processing_time_ms=0,
        )

        try:
            question, constraint = await question_generator.generate_next_question(
                classification=dummy_classification,
                questions_asked=[],
            )
        except ValueError:
            return ConversationResponse(
                message="I'm not sure what you're looking for. Could you tell me more?",
                intent="clarification",
                confidence=0.5,
                metadata={"error": "no_questions"},
            )

        personalized_question = await self._personalize_question(
            question=question,
            constraint=constraint,
            merchant=merchant,
            llm_service=llm_service,
        )

        logger.info(
            "clarification_question_asked",
            merchant_id=merchant.id,
            constraint=constraint,
            question=personalized_question,
        )

        return ConversationResponse(
            message=personalized_question,
            intent="clarification",
            confidence=1.0,
            metadata={
                "clarification_active": True,
                "constraint": constraint,
                "attempt": 1,
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
    ) -> ConversationResponse:
        """Ask the next clarification question.

        Args:
            merchant: Merchant configuration
            llm_service: LLM service for personality-based questions
            context: Conversation context
            result: Re-classification result
            question_generator: Question generator
            clarification_service: Clarification service

        Returns:
            ConversationResponse with next clarifying question
        """
        clarification_state = context.get("clarification", {})
        questions_asked = clarification_state.get("questions_asked", [])
        attempt_count = clarification_state.get("attempt_count", 0) + 1

        try:
            question, constraint = await question_generator.generate_next_question(
                classification=result,
                questions_asked=questions_asked,
            )
        except ValueError:
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

        personalized_question = await self._personalize_question(
            question=question,
            constraint=constraint,
            merchant=merchant,
            llm_service=llm_service,
        )

        logger.info(
            "clarification_followup_asked",
            merchant_id=merchant.id,
            constraint=constraint,
            attempt=attempt_count,
        )

        return ConversationResponse(
            message=personalized_question,
            intent="clarification",
            confidence=result.confidence,
            metadata={
                "clarification_active": True,
                "constraint": constraint,
                "attempt": attempt_count,
            },
        )

    async def _personalize_question(
        self,
        question: str,
        constraint: str,
        merchant: Merchant,
        llm_service: BaseLLMService,
    ) -> str:
        """Personalize question with merchant's personality.

        Args:
            question: Base question template
            constraint: Constraint being asked about
            merchant: Merchant configuration
            llm_service: LLM service

        Returns:
            Personalized question string
        """
        personality_type = getattr(merchant, "personality_type", "friendly")
        business_name = getattr(merchant, "business_name", None)

        if personality_type == "professional":
            prefix = "To help you better, "
        elif personality_type == "enthusiastic":
            prefix = "Great question! "
        else:
            prefix = ""

        if business_name and constraint == "budget":
            prefix = f"At {business_name}, we have options for every budget. "

        return f"{prefix}{question}"

    def _context_to_dict(
        self,
        context: ConversationContext,
        entities: Optional[dict[str, Any]],
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

    def _dict_to_entities(self, entities: Optional[dict[str, Any]]) -> ExtractedEntities:
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
