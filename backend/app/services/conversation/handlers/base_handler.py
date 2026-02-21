"""Base handler for unified conversation processing.

Story 5-10: Widget Full App Integration
Task 1: Create UnifiedConversationService
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.merchant import Merchant
from app.services.conversation.schemas import (
    ConversationContext,
    ConversationResponse,
)
from app.services.llm.base_llm_service import BaseLLMService


class BaseHandler(ABC):
    """Abstract base class for intent handlers.

    All handlers must implement the handle method to process
    their specific intent type.
    """

    @abstractmethod
    async def handle(
        self,
        db: AsyncSession,
        merchant: Merchant,
        llm_service: BaseLLMService,
        message: str,
        context: ConversationContext,
        entities: Optional[dict[str, Any]] = None,
    ) -> ConversationResponse:
        """Handle the intent and return a response.

        Args:
            db: Database session
            merchant: Merchant configuration
            llm_service: LLM service for this merchant
            message: User's message
            context: Conversation context
            entities: Extracted entities from intent classification

        Returns:
            ConversationResponse with the handler's output
        """
        pass

    def _get_merchant_llm_config(self, merchant: Merchant) -> dict[str, Any]:
        """Extract LLM configuration from merchant.

        Args:
            merchant: Merchant model instance

        Returns:
            Dict with model name and other LLM config
        """
        config = {"model": "llama3.2"}

        try:
            if hasattr(merchant, "llm_configuration") and merchant.llm_configuration:
                llm_config = merchant.llm_configuration
                config["model"] = llm_config.ollama_model or llm_config.cloud_model or "llama3.2"
        except Exception:
            pass

        return config
