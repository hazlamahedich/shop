"""Widget message service for LLM-powered chat responses.

Provides message processing with merchant's LLM configuration,
conversation history tracking, and response generation.

Story 5.1: Backend Widget API
"""

from __future__ import annotations

import asyncio
import os
import re
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import APIError, ErrorCode
from app.core.config import is_testing
from app.models.merchant import Merchant
from app.schemas.widget import WidgetSessionData
from app.services.widget.widget_session_service import WidgetSessionService
from app.services.llm.llm_factory import LLMProviderFactory
from app.services.llm.base_llm_service import LLMMessage, LLMResponse


logger = structlog.get_logger(__name__)

MAX_MESSAGE_LENGTH = 4000
RESPONSE_TIMEOUT_SECONDS = 3.0

SANITIZATION_PATTERNS = [
    (r"<script[^>]*>.*?</script>", ""),
    (r"javascript:", ""),
    (r"on\w+\s*=", ""),
]


class WidgetMessageService:
    """Service for processing widget messages with LLM integration.

    Message Processing:
    - Get merchant's LLM configuration
    - Build conversation context with history
    - Call LLM provider for response
    - Track token usage (not billed in widget)
    - Store message in session history
    """

    def __init__(
        self,
        db: Optional[AsyncSession] = None,
        session_service: Optional[WidgetSessionService] = None,
    ) -> None:
        """Initialize message service.

        Args:
            db: Optional database session for merchant config
            session_service: Optional session service instance
        """
        self.db = db
        self.session_service = session_service or WidgetSessionService()
        self.logger = structlog.get_logger(__name__)

    @staticmethod
    def sanitize_message(message: str) -> str:
        """Sanitize user message to prevent injection attacks.

        Args:
            message: Raw user message

        Returns:
            Sanitized message string
        """
        sanitized = message.strip()
        for pattern, replacement in SANITIZATION_PATTERNS:
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
        return sanitized[:MAX_MESSAGE_LENGTH]

    async def process_message(
        self,
        session: WidgetSessionData,
        message: str,
        merchant: Merchant,
    ) -> dict:
        """Process a user message and return bot response.

        Args:
            session: Widget session data
            message: User message text
            merchant: Merchant configuration

        Returns:
            Dictionary with message_id, content, sender, created_at

        Raises:
            APIError: If message processing fails
        """
        # Validate message length BEFORE sanitization (so user gets error, not silent truncation)
        if len(message) > MAX_MESSAGE_LENGTH:
            raise APIError(
                ErrorCode.WIDGET_MESSAGE_TOO_LONG,
                f"Message exceeds maximum length of {MAX_MESSAGE_LENGTH} characters",
            )

        sanitized_message = self.sanitize_message(message)

        if not sanitized_message:
            raise APIError(
                ErrorCode.VALIDATION_ERROR,
                "Message cannot be empty",
            )

        # Add user message to history
        await self.session_service.add_message_to_history(
            session.session_id,
            "user",
            sanitized_message,
        )

        try:
            # Get conversation history
            history = await self.session_service.get_message_history(session.session_id)

            # Build LLM messages
            llm_messages = await self._build_llm_messages(
                merchant=merchant,
                history=history,
                current_message=sanitized_message,
            )

            # Get merchant's LLM configuration
            provider_name = "ollama"
            llm_config = {}

            try:
                if hasattr(merchant, "llm_configuration") and merchant.llm_configuration:
                    llm_config_obj = merchant.llm_configuration
                    provider_name = llm_config_obj.provider or "ollama"

                    # Build config dict from LLMConfiguration model
                    llm_config = {
                        "model": llm_config_obj.ollama_model or llm_config_obj.cloud_model,
                    }

                    if provider_name == "ollama":
                        llm_config["ollama_url"] = llm_config_obj.ollama_url
                    else:
                        # Decrypt API key for cloud providers
                        if llm_config_obj.api_key_encrypted:
                            from app.core.security import decrypt_access_token

                            llm_config["api_key"] = decrypt_access_token(
                                llm_config_obj.api_key_encrypted
                            )
            except Exception:
                pass

            # Create LLM provider
            llm_service = LLMProviderFactory.create_provider(
                provider_name=provider_name,
                config=llm_config,
            )

            # Generate response with timeout (AC2: P95 < 3 seconds)
            try:
                llm_response = await asyncio.wait_for(
                    llm_service.chat(messages=llm_messages),
                    timeout=RESPONSE_TIMEOUT_SECONDS,
                )
                response_text = llm_response.content
            except asyncio.TimeoutError:
                self.logger.warning(
                    "widget_llm_timeout",
                    session_id=session.session_id,
                    merchant_id=merchant.id,
                    timeout_seconds=RESPONSE_TIMEOUT_SECONDS,
                )
                raise APIError(
                    ErrorCode.LLM_TIMEOUT,
                    f"LLM response timed out after {RESPONSE_TIMEOUT_SECONDS} seconds",
                )

            # Add bot response to history
            await self.session_service.add_message_to_history(
                session.session_id,
                "bot",
                response_text,
            )

            # Refresh session to extend expiry
            await self.session_service.refresh_session(session.session_id)

            self.logger.info(
                "widget_message_processed",
                session_id=session.session_id,
                merchant_id=merchant.id,
                message_length=len(sanitized_message),
                response_length=len(response_text),
            )

            return {
                "message_id": str(uuid4()),
                "content": response_text,
                "sender": "bot",
                "created_at": datetime.now(timezone.utc),
            }

        except APIError:
            raise
        except Exception as e:
            self.logger.error(
                "widget_message_processing_failed",
                session_id=session.session_id,
                merchant_id=merchant.id,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise APIError(
                ErrorCode.LLM_PROVIDER_ERROR,
                f"Failed to process message: {str(e)}",
            )

    async def _build_llm_messages(
        self,
        merchant: Merchant,
        history: list[dict],
        current_message: str,
    ) -> list[LLMMessage]:
        """Build LLM message list with context.

        Args:
            merchant: Merchant for system prompt
            history: Conversation history
            current_message: Current user message

        Returns:
            List of LLMMessage objects
        """
        messages = []

        # Build system prompt
        system_prompt = await self._get_system_prompt(merchant)
        messages.append(LLMMessage(role="system", content=system_prompt))

        # Add conversation history (last 5 messages for context)
        for msg in history[-5:]:
            role = "user" if msg.get("role") == "user" else "assistant"
            messages.append(LLMMessage(role=role, content=msg.get("content", "")))

        # Add current message if not already in history
        if not history or history[-1].get("content") != current_message:
            messages.append(LLMMessage(role="user", content=current_message))

        return messages

    async def _get_system_prompt(self, merchant: Merchant) -> str:
        """Build system prompt for widget chat.

        Args:
            merchant: Merchant configuration

        Returns:
            System prompt string
        """
        bot_name = merchant.bot_name or "Shopping Assistant"
        business_name = merchant.business_name or "our store"
        business_description = merchant.business_description or ""

        prompt_parts = [
            f"You are {bot_name}, a helpful shopping assistant for {business_name}.",
            "You are chatting via an embeddable website widget.",
            "Be helpful, friendly, and concise in your responses.",
        ]

        if business_description:
            prompt_parts.append(f"\nAbout the business: {business_description}")

        # Add FAQ context if available
        if self.db:
            try:
                from sqlalchemy import select
                from app.models.faq import Faq

                result = await self.db.execute(
                    select(Faq).where(Faq.merchant_id == merchant.id).limit(5)
                )
                faqs = list(result.scalars().all())

                if faqs:
                    faq_text = "\n".join([f"Q: {faq.question}\nA: {faq.answer}" for faq in faqs])
                    prompt_parts.append(f"\nFrequently Asked Questions:\n{faq_text}")
            except Exception:
                pass

        return "\n".join(prompt_parts)
