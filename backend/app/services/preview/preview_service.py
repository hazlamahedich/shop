"""Preview conversation service (Story 1.13).

Provides isolated sandbox environment for merchants to test their bot
configuration before exposing it to real customers.

Preview conversations:
- Stored in memory only (NOT in database)
- NOT counted in cost tracking
- NEVER sent to real customers or Facebook Messenger
- Include confidence scoring for transparency
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional, Any
from uuid import uuid4
import difflib
import structlog

from sqlalchemy.ext.asyncio import AsyncSession
from app.models.merchant import Merchant
from app.schemas.preview import (
    PreviewMessageResponse,
    PreviewMessageMetadata,
    STARTER_PROMPTS,
)
from app.core.errors import APIError, ErrorCode


logger = structlog.get_logger(__name__)


@dataclass
class PreviewConversation:
    """A single preview conversation in memory.

    Preview conversations are isolated sandbox sessions that allow
    merchants to test their bot configuration safely.

    Attributes:
        merchant_id: The merchant ID who owns this preview
        preview_session_id: Unique session identifier
        created_at: When this session was created
        messages: List of messages in this conversation
        message_count: Number of messages exchanged
    """

    merchant_id: int
    preview_session_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    messages: list[dict[str, str]] = field(default_factory=list)
    message_count: int = 0

    def add_message(self, role: str, content: str) -> None:
        """Add a message to the conversation.

        Args:
            role: Either "user" or "bot"
            content: Message content
        """
        self.messages.append(
            {
                "role": role,
                "content": content,
            }
        )
        self.message_count += 1

    def reset(self) -> None:
        """Reset the conversation, clearing all messages."""
        self.messages.clear()
        self.message_count = 0

    def get_history(self) -> list[dict[str, str]]:
        """Get the conversation history.

        Returns:
            List of message dictionaries
        """
        return self.messages.copy()


class PreviewService:
    """Service for managing preview mode conversations.

    Provides isolated sandbox environment where merchants can test
    their bot configuration with simulated conversations.

    Story 1.13: Bot Preview Mode
    """

    # In-memory session storage (NOT persisted to database)
    sessions: dict[str, PreviewConversation] = {}

    def __init__(self, db: Optional[AsyncSession] = None) -> None:
        """Initialize the preview service.

        Args:
            db: Optional database session for loading merchant config
        """
        self.db = db
        self.logger = structlog.get_logger(__name__)

    def create_session(self, merchant: Merchant) -> dict[str, Any]:
        """Create a new preview session for a merchant.

        Args:
            merchant: The merchant creating the preview session

        Returns:
            Dictionary with session info and starter prompts
        """
        session = PreviewConversation(merchant_id=merchant.id)
        session_id = session.preview_session_id

        self.sessions[session_id] = session

        self.logger.info(
            "preview_session_created",
            merchant_id=merchant.id,
            session_id=session_id,
        )

        return {
            "preview_session_id": session_id,
            "merchant_id": merchant.id,
            "created_at": session.created_at.isoformat().replace("+00:00", "Z"),
            "starter_prompts": STARTER_PROMPTS.copy(),
        }

    def get_session(self, session_id: str) -> Optional[PreviewConversation]:
        """Get an existing preview session.

        Args:
            session_id: The preview session ID

        Returns:
            PreviewConversation if found, None otherwise
        """
        return self.sessions.get(session_id)

    async def send_message(
        self,
        session_id: str,
        message: str,
        merchant: Merchant,
    ) -> PreviewMessageResponse:
        """Send a message in preview mode and get bot response.

        This method:
        1. Adds the user message to conversation history
        2. Calls the bot response service with merchant config
        3. Adds bot response to conversation history
        4. Returns response with confidence score

        Args:
            session_id: The preview session ID
            message: User's message text
            merchant: The merchant's configuration

        Returns:
            PreviewMessageResponse with bot response and metadata

        Raises:
            ValueError: If session not found
            APIError: If bot response generation fails
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Preview session {session_id} not found")

        # Add user message to conversation
        session.add_message("user", message)

        # Get bot response using existing bot response service
        from app.services.personality.bot_response_service import BotResponseService
        from app.services.llm.llm_factory import LLMProviderFactory
        from app.services.llm.base_llm_service import LLMMessage

        bot_service = BotResponseService(db=self.db)

        # Build conversation history for context
        history = session.get_history()

        # Check if this is a greeting (must be actual greeting word AND first message)
        greeting_words = {
            "hi",
            "hello",
            "hey",
            "greetings",
            "howdy",
            "good morning",
            "good afternoon",
            "good evening",
            "hi there",
            "hello there",
        }
        normalized_message = message.lower().strip()
        is_first_message = len(history) <= 2  # Only user message so far
        is_greeting = normalized_message in greeting_words

        # Only return configured greeting for actual greeting words on first message
        if is_first_message and is_greeting:
            try:
                greeting = await bot_service.get_greeting(merchant.id, self.db)
                if greeting:
                    session.add_message("bot", greeting)
                    return PreviewMessageResponse(
                        response=greeting,
                        confidence=95,
                        confidence_level="high",
                        metadata=PreviewMessageMetadata(
                            intent="greeting",
                            faq_matched=False,
                            products_found=0,
                            llm_provider=None,
                        ),
                    )
            except Exception:
                pass  # Fall through to normal flow

        # Get system prompt with merchant's personality and config
        system_prompt = await bot_service.get_system_prompt(
            merchant_id=merchant.id,
            db=self.db,
        )

        # Build messages for LLM
        llm_messages = [
            LLMMessage(role="system", content=system_prompt),
        ]

        # Add recent conversation history (last 5 messages for context)
        for msg in history[-5:]:
            if msg["role"] == "user":
                llm_messages.append(LLMMessage(role="user", content=msg["content"]))
            else:
                llm_messages.append(LLMMessage(role="assistant", content=msg["content"]))

        try:
            # Check for FAQ match first (higher confidence for FAQ responses)
            from app.services.faq import match_faq
            from app.models.faq import Faq
            from sqlalchemy import select

            # Get merchant's FAQs
            faq_result = await self.db.execute(select(Faq).where(Faq.merchant_id == merchant.id))
            merchant_faqs = list(faq_result.scalars().all())

            # Try FAQ match
            faq_match = None
            if merchant_faqs:
                faq_match = await match_faq(customer_message=message, merchant_faqs=merchant_faqs)

            # Determine response source and calculate confidence
            if faq_match:
                # Use FAQ response
                response_text = faq_match.faq.answer
                confidence = int(faq_match.confidence * 100)  # Convert 0-1 to 0-100
                faq_matched = True
                intent = "faq_response"
                products_found = 0
                llm_provider = None
            else:
                # Initialize llm_provider for the else branch
                llm_provider = None
                # No FAQ match - use LLM
                # Get merchant's LLM configuration
                llm_config = {}
                provider_name = "ollama"  # Default provider

                # Safely try to access llm_configuration
                # In test environments, the relationship may not be loaded or may not exist
                # We catch any exception to avoid triggering lazy load in async context
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
                    # If accessing llm_configuration fails (e.g., lazy load in async context),
                    # use default ollama provider with empty config
                    pass

                # Set llm_provider for metadata
                llm_provider = provider_name

                # Get LLM provider and generate response
                llm_service = LLMProviderFactory.create_provider(
                    provider_name=provider_name,
                    config=llm_config,
                )

                # Call chat() method which returns LLMResponse
                llm_response = await llm_service.chat(messages=llm_messages)
                response_text = llm_response.content

                # Calculate confidence for LLM response
                # Use logprob if available, otherwise default to medium confidence
                if hasattr(llm_response, "logprobs") and llm_response.logprobs:
                    # Average logprob as confidence indicator (simplified)
                    avg_logprob = sum(llm_response.logprobs) / len(llm_response.logprobs)
                    # Convert logprob (-inf to 0) to confidence (0 to 100)
                    confidence = int(max(0, min(100, (avg_logprob + 1) * 50)))
                else:
                    # Default to medium confidence for LLM responses without logprobs
                    confidence = 70

                faq_matched = False
                intent = "llm_response"
                products_found = 0

                # Try to extract product count from response (basic pattern matching)
                import re

                product_patterns = [
                    r"(\d+)\s+product",
                    r"found\s+(\d+)",
                    r"showing\s+(\d+)",
                ]
                for pattern in product_patterns:
                    match = re.search(pattern, response_text.lower())
                    if match:
                        try:
                            products_found = int(match.group(1))
                            break
                        except (ValueError, IndexError):
                            pass

            # Add bot response to conversation
            session.add_message("bot", response_text)

            # Determine confidence level
            confidence_level = self.get_confidence_level(confidence)

            # Create response metadata
            metadata = PreviewMessageMetadata(
                intent=intent,
                faq_matched=faq_matched,
                products_found=products_found,
                llm_provider=llm_provider,
            )

            self.logger.info(
                "preview_message_sent",
                session_id=session_id,
                merchant_id=merchant.id,
                confidence=confidence,
                message_length=len(message),
            )

            return PreviewMessageResponse(
                response=response_text,
                confidence=confidence,
                confidence_level=confidence_level,
                metadata=metadata,
            )

        except Exception as e:
            self.logger.error(
                "preview_message_failed",
                session_id=session_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise APIError(
                ErrorCode.LLM_PROVIDER_ERROR,
                f"Failed to generate bot response: {str(e)}",
            )

    def reset_session(self, session_id: str) -> bool:
        """Reset a preview session, clearing all messages.

        Args:
            session_id: The preview session ID

        Returns:
            True if session was reset, False if not found
        """
        session = self.get_session(session_id)
        if session:
            session.reset()
            self.logger.info(
                "preview_session_reset",
                session_id=session_id,
            )
            return True
        return False

    def delete_session(self, session_id: str) -> bool:
        """Delete a preview session completely.

        Args:
            session_id: The preview session ID

        Returns:
            True if session was deleted, False if not found
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            self.logger.info(
                "preview_session_deleted",
                session_id=session_id,
            )
            return True
        return False

    @staticmethod
    def get_confidence_level(confidence: int) -> str:
        """Get confidence level label from score.

        Args:
            confidence: Confidence score (0-100)

        Returns:
            "high", "medium", or "low"
        """
        if confidence >= 80:
            return "high"
        elif confidence >= 50:
            return "medium"
        else:
            return "low"

    def calculate_faq_confidence(self, question: str, faq_question: str) -> int:
        """Calculate confidence score for FAQ matching.

        Uses string similarity to determine how well a question matches
        an FAQ entry.

        Args:
            question: The user's question
            faq_question: The FAQ question to compare against

        Returns:
            Confidence score (0-100)
        """
        # Use SequenceMatcher for string similarity
        similarity = difflib.SequenceMatcher(
            None,
            question.lower().strip(),
            faq_question.lower().strip(),
        ).ratio()

        return int(similarity * 100)

    def cleanup_old_sessions(self, max_age_seconds: int = 3600) -> int:
        """Remove old preview sessions from memory.

        Args:
            max_age_seconds: Maximum age of session to keep (default 1 hour)

        Returns:
            Number of sessions removed
        """
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=max_age_seconds)
        to_remove = []

        for session_id, session in self.sessions.items():
            if session.created_at < cutoff:
                to_remove.append(session_id)

        for session_id in to_remove:
            del self.sessions[session_id]

        if to_remove:
            self.logger.info(
                "preview_sessions_cleaned",
                count=len(to_remove),
            )

        return len(to_remove)
