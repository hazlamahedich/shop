"""LLM-based intent classifier for product discovery.

Uses LLM to classify user intent and extract structured entities
from natural language messages.
"""

from __future__ import annotations

import json
import time
from typing import Any, Optional

import structlog

from app.core.config import settings
from app.core.errors import APIError, ErrorCode
from app.core.input_sanitizer import sanitize_llm_input
from app.services.llm.base_llm_service import BaseLLMService, LLMMessage, LLMResponse
from app.services.llm.llm_factory import LLMProviderFactory
from app.services.llm.llm_router import LLMRouter
from app.services.intent.classification_schema import (
    ClassificationResult,
    ExtractedEntities,
    IntentType,
)
from app.services.intent.prompt_templates import get_classification_system_prompt


logger = structlog.get_logger(__name__)


class IntentClassifier:
    """LLM-based intent classifier for product discovery.

    Uses LLM to classify user intent and extract structured entities
    from natural language messages.

    Supports merchant-specific LLM configuration via injected service.
    """

    # System prompt for classification
    SYSTEM_PROMPT = get_classification_system_prompt()

    def __init__(
        self,
        llm_router: Optional[LLMRouter] = None,
        llm_service: Optional[BaseLLMService] = None,
    ) -> None:
        """Initialize intent classifier with LLM support.

        Args:
            llm_router: LLM router for classification (uses default if not provided)
            llm_service: Direct LLM service for merchant-specific config (preferred)
        """
        self.llm_service = llm_service
        self.llm_router = llm_router
        self.logger = structlog.get_logger(__name__)

        if llm_service is None and llm_router is None:
            config = {
                "primary_provider": settings()["LLM_PROVIDER"],
                "primary_config": {
                    "api_key": settings()["LLM_API_KEY"],
                    "api_base": settings()["LLM_API_BASE"],
                    "model": settings()["LLM_MODEL"],
                },
                "backup_provider": "openai"
                if settings()["LLM_PROVIDER"] != "openai"
                else "anthropic",
                "backup_config": {
                    "api_key": settings()["OPENAI_API_KEY"]
                    if settings()["LLM_PROVIDER"] != "openai"
                    else settings()["ANTHROPIC_API_KEY"],
                    "model": settings()["OPENAI_DEFAULT_MODEL"]
                    if settings()["LLM_PROVIDER"] != "openai"
                    else settings()["ANTHROPIC_DEFAULT_MODEL"],
                },
            }
            self.llm_router = LLMRouter(config)

    @classmethod
    def with_external_llm(cls, llm_service: BaseLLMService) -> "IntentClassifier":
        """Create classifier with an external LLM service.

        Story 5-10 Code Review Fix (C2):
        Proper factory method instead of __new__ hack.

        Args:
            llm_service: LLM service to use for classification

        Returns:
            IntentClassifier configured with the given LLM service
        """
        instance = cls.__new__(cls)
        instance.llm_service = llm_service
        instance.llm_router = None
        instance.logger = structlog.get_logger(__name__)
        return instance

    @classmethod
    def for_merchant(
        cls,
        merchant: Any,
        db: Optional[Any] = None,
    ) -> "IntentClassifier":
        """Create classifier with merchant's LLM configuration.

        Factory method that creates an IntentClassifier configured
        with the merchant's specific LLM provider and settings.

        Args:
            merchant: Merchant model with llm_configuration attribute
            db: Database session (unused, kept for future use)

        Returns:
            IntentClassifier with merchant's LLM config
        """
        llm_service = None

        try:
            if hasattr(merchant, "llm_configuration") and merchant.llm_configuration:
                llm_config = merchant.llm_configuration
                provider_name = llm_config.provider or "ollama"

                config = {
                    "model": llm_config.ollama_model or llm_config.cloud_model,
                }

                if provider_name == "ollama":
                    config["ollama_url"] = llm_config.ollama_url
                else:
                    if llm_config.api_key_encrypted:
                        from app.core.security import decrypt_access_token

                        config["api_key"] = decrypt_access_token(llm_config.api_key_encrypted)

                llm_service = LLMProviderFactory.create_provider(
                    provider_name=provider_name,
                    config=config,
                )
        except Exception as e:
            logger.warning(
                "intent_classifier_merchant_llm_failed",
                merchant_id=getattr(merchant, "id", None),
                error=str(e),
            )

        return cls(llm_service=llm_service)

    async def classify(
        self,
        message: str,
        conversation_context: Optional[dict[str, Any]] = None,
    ) -> ClassificationResult:
        """Classify user message and extract entities.

        Args:
            message: User's natural language message
            conversation_context: Previous conversation context (optional)

        Returns:
            Classification result with intent, entities, and confidence

        Raises:
            APIError: If LLM classification fails
        """
        start_time = time.time()

        # Sanitize input (NFR-S6)
        sanitized_message = sanitize_llm_input(message, max_length=10000)

        # Build messages with conversation context if available
        messages: list[LLMMessage] = [LLMMessage(role="system", content=self.SYSTEM_PROMPT)]

        # Add conversation context if available (for clarification scenarios)
        if conversation_context:
            context_str = self._format_context(conversation_context)
            messages.append(
                LLMMessage(
                    role="user",
                    content=f"Previous context: {context_str}\n\nCurrent message: {sanitized_message}",
                )
            )
        else:
            messages.append(LLMMessage(role="user", content=sanitized_message))

        try:
            # Call LLM with low temperature for consistent classification
            # Prefer injected service, fall back to router
            if self.llm_service:
                response = await self.llm_service.chat(
                    messages=messages,
                    temperature=0.3,
                    max_tokens=500,
                )
            elif self.llm_router:
                response = await self.llm_router.chat(
                    messages=messages,
                    temperature=0.3,
                    max_tokens=500,
                )
            else:
                raise ValueError("No LLM service or router configured")

            # Parse LLM response
            result = self._parse_classification_response(
                response.content,
                message,
                response.provider,
                response.model,
            )

            processing_time = (time.time() - start_time) * 1000
            result.processing_time_ms = processing_time

            # Log classification
            self.logger.info(
                "intent_classification_complete",
                intent=result.intent.value,
                confidence=result.confidence,
                entities=result.entities.model_dump(exclude_none=True),
                provider=response.provider,
                model=response.model,
                processing_time_ms=processing_time,
            )

            return result

        except Exception as e:
            self.logger.error("intent_classification_failed", error=str(e), message=message)
            # Return unknown intent with 0 confidence on failure
            return ClassificationResult(
                intent=IntentType.UNKNOWN,
                confidence=0.0,
                entities=ExtractedEntities(),
                raw_message=message,
                llm_provider="error",
                model="error",
                processing_time_ms=(time.time() - start_time) * 1000,
            )

    def _format_context(self, context: dict[str, Any]) -> str:
        """Format conversation context for LLM.

        Args:
            context: Conversation context dict

        Returns:
            Formatted context string
        """
        parts: list[str] = []

        if "previous_intent" in context:
            parts.append(f"Previous intent: {context['previous_intent']}")

        if "extracted_entities" in context:
            entities = context["extracted_entities"]
            entity_parts: list[str] = []
            for key, value in entities.items():
                if value:
                    entity_parts.append(f"{key}={value}")
            if entity_parts:
                parts.append(f"Known entities: {', '.join(entity_parts)}")

        if "missing_constraints" in context:
            parts.append(f"Missing: {context['missing_constraints']}")

        return "; ".join(parts)

    def _parse_classification_response(
        self,
        llm_response: str,
        original_message: str,
        provider: str,
        model: str,
    ) -> ClassificationResult:
        """Parse LLM response into ClassificationResult.

        Args:
            llm_response: Raw LLM response
            original_message: Original user message
            provider: LLM provider used
            model: LLM model used

        Returns:
            Parsed classification result
        """
        try:
            # Extract JSON from response (LLMs sometimes add markdown code blocks)
            json_str = llm_response.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0].strip()

            data = json.loads(json_str)

            # Map intent string to enum
            intent_str = data.get("intent", "unknown").lower().replace("-", "_")
            try:
                intent = IntentType(intent_str)
            except ValueError:
                intent = IntentType.UNKNOWN

            # Extract entities
            entities_data = data.get("entities", {})
            entities = ExtractedEntities(
                category=entities_data.get("category"),
                budget=entities_data.get("budget"),
                budget_currency=entities_data.get("budgetCurrency", "USD"),
                size=entities_data.get("size"),
                color=entities_data.get("color"),
                brand=entities_data.get("brand"),
                constraints=entities_data.get("constraints", {}),
            )

            return ClassificationResult(
                intent=intent,
                confidence=float(data.get("confidence", 0.0)),
                entities=entities,
                raw_message=original_message,
                reasoning=data.get("reasoning"),
                llm_provider=provider,
                model=model,
                processing_time_ms=0,  # Will be set by caller
            )

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            self.logger.warning("classification_parse_failed", error=str(e), response=llm_response)
            # Return unknown intent on parse failure
            return ClassificationResult(
                intent=IntentType.UNKNOWN,
                confidence=0.0,
                entities=ExtractedEntities(),
                raw_message=original_message,
                reasoning=f"Parse failed: {str(e)}",
                llm_provider=provider,
                model=model,
                processing_time_ms=0,
            )
