"""Consent middleware for unified conversation processing.

Story 5-10 Task 18: Consent Management Middleware

Checks user consent before cart operations (add to cart, checkout).
Returns consent prompt if consent is required but not yet granted.

GDPR/compliance requirement: Users must explicitly consent before
their data can be used for cart management.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.models.consent import Consent, ConsentType
from app.services.conversation.schemas import ConversationContext


logger = structlog.get_logger(__name__)


class ConsentRequiredError(Exception):
    """Raised when consent is required but not granted."""

    def __init__(self, consent_type: str, message: str):
        self.consent_type = consent_type
        self.message = message
        super().__init__(message)


class ConsentMiddleware:
    """Middleware for checking user consent before operations.

    Checks consent status before cart operations and data collection.
    Returns consent prompt if consent is required but not granted.

    Usage:
        middleware = ConsentMiddleware()

        # Check consent before cart operation
        has_consent, prompt = await middleware.check_consent(
            db=db,
            context=context,
            intent="cart_add",
        )

        if not has_consent:
            return ConversationResponse(message=prompt, ...)
    """

    CONSENT_REQUIRED_INTENTS = frozenset(
        [
            "cart_add",
            "checkout",
        ]
    )

    CONSENT_PROMPTS = {
        ConsentType.CART: (
            "I'd love to help you with your cart! "
            "To provide the best experience, I'll need to save your cart and preferences. "
            "Is that okay? (Reply 'yes' to continue)"
        ),
        ConsentType.DATA_COLLECTION: (
            "To help you better, I'd like to remember our conversation. "
            "Is that okay? (Reply 'yes' to continue)"
        ),
    }

    YES_RESPONSES = frozenset(
        [
            "yes",
            "yeah",
            "yep",
            "sure",
            "ok",
            "okay",
            "y",
            "please",
            "go ahead",
            "of course",
            "definitely",
            "absolutely",
        ]
    )

    async def check_consent(
        self,
        db: AsyncSession,
        context: ConversationContext,
        intent: str,
    ) -> tuple[bool, Optional[str]]:
        """Check if user has consent for the given intent.

        Args:
            db: Database session
            context: Conversation context with session info
            intent: Intent that requires consent

        Returns:
            Tuple of (has_consent, prompt_if_needed)
            - (True, None) if consent is granted
            - (False, prompt) if consent is needed
        """
        if intent not in self.CONSENT_REQUIRED_INTENTS:
            return True, None

        consent_type = self._get_consent_type(intent)

        has_consent = await self._check_consent_status(
            db=db,
            session_id=context.session_id,
            merchant_id=context.merchant_id,
            consent_type=consent_type,
        )

        if has_consent:
            logger.debug(
                "consent_already_granted",
                session_id=context.session_id[:8],
                consent_type=consent_type,
            )
            return True, None

        prompt = self.CONSENT_PROMPTS.get(
            consent_type,
            "I'll need your consent to continue. Is that okay?",
        )

        logger.info(
            "consent_required",
            session_id=context.session_id[:8],
            consent_type=consent_type,
            intent=intent,
        )

        return False, prompt

    async def check_consent_response(
        self,
        db: AsyncSession,
        context: ConversationContext,
        message: str,
    ) -> bool:
        """Check if message is a consent response and process it.

        Args:
            db: Database session
            context: Conversation context with session info
            message: User's message

        Returns:
            True if this was a consent response (positive or negative)
        """
        consent_state = context.metadata.get("consent_pending")

        if not consent_state:
            return False

        normalized = message.strip().lower()

        if normalized in self.YES_RESPONSES:
            await self._grant_consent(
                db=db,
                session_id=context.session_id,
                merchant_id=context.merchant_id,
                consent_type=consent_state,
            )
            logger.info(
                "consent_granted",
                session_id=context.session_id[:8],
                consent_type=consent_state,
            )
            return True

        if self._is_negative_response(normalized):
            logger.info(
                "consent_declined",
                session_id=context.session_id[:8],
                consent_type=consent_state,
            )
            return True

        return False

    async def get_consent_status(
        self,
        db: AsyncSession,
        session_id: str,
        merchant_id: int,
        consent_type: str,
    ) -> Optional[Consent]:
        """Get consent record for session.

        Args:
            db: Database session
            session_id: Widget session ID or PSID
            merchant_id: Merchant ID
            consent_type: Type of consent to check

        Returns:
            Consent record or None
        """
        result = await db.execute(
            select(Consent)
            .where(Consent.session_id == session_id)
            .where(Consent.merchant_id == merchant_id)
            .where(Consent.consent_type == consent_type)
            .order_by(Consent.granted_at.desc())
            .limit(1)
        )
        return result.scalars().first()

    async def _check_consent_status(
        self,
        db: AsyncSession,
        session_id: str,
        merchant_id: int,
        consent_type: str,
    ) -> bool:
        """Check if consent has been granted.

        Args:
            db: Database session
            session_id: Widget session ID or PSID
            merchant_id: Merchant ID
            consent_type: Type of consent to check

        Returns:
            True if consent is valid, False otherwise
        """
        consent = await self.get_consent_status(
            db=db,
            session_id=session_id,
            merchant_id=merchant_id,
            consent_type=consent_type,
        )

        if not consent:
            return False

        return consent.is_valid()

    async def _grant_consent(
        self,
        db: AsyncSession,
        session_id: str,
        merchant_id: int,
        consent_type: str,
    ) -> Consent:
        """Grant consent for a session.

        Args:
            db: Database session
            session_id: Widget session ID or PSID
            merchant_id: Merchant ID
            consent_type: Type of consent to grant

        Returns:
            Consent record
        """
        existing = await self.get_consent_status(
            db=db,
            session_id=session_id,
            merchant_id=merchant_id,
            consent_type=consent_type,
        )

        if existing:
            existing.grant()
            await db.commit()
            return existing

        consent = Consent.create(
            session_id=session_id,
            merchant_id=merchant_id,
            consent_type=consent_type,
        )
        consent.grant()
        db.add(consent)
        await db.commit()

        return consent

    def _get_consent_type(self, intent: str) -> str:
        """Map intent to consent type.

        Args:
            intent: Intent name

        Returns:
            Consent type constant
        """
        if intent in ("cart_add", "checkout"):
            return ConsentType.CART
        return ConsentType.DATA_COLLECTION

    def _is_negative_response(self, message: str) -> bool:
        """Check if message is a negative response.

        Args:
            message: Normalized message

        Returns:
            True if this is a negative response
        """
        negative_responses = {"no", "nope", "n", "never", "not really", "don't", "dont"}
        return message in negative_responses

    def get_pending_consent_type(self, context: ConversationContext) -> Optional[str]:
        """Get the pending consent type from context.

        Args:
            context: Conversation context

        Returns:
            Pending consent type or None
        """
        return context.metadata.get("consent_pending")
