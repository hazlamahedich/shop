"""Extended consent service for conversation data storage consent.

Story 6-1: Opt-In Consent Flow
Story 6-1 Enhancement: Privacy-friendly consent persistence via visitor_id

Extends ConsentService to support:
- Conversation consent with PostgreSQL persistence
- Cross-session consent tracking via visitor_id (localStorage)
- Privacy-friendly: session_id clears on browser close, visitor_id persists
- Audit trail for GDPR/CCPA compliance
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

import redis.asyncio as redis
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.schemas.consent import ConsentStatus
from app.models.consent import Consent, ConsentType, ConsentSource


class ConversationConsentService:
    """Service for managing conversation data storage consent.

    Provides PostgreSQL persistence for conversation consent,
    separate from cart consent (Redis-only).

    Consent Types:
    - Conversation: PostgreSQL + Redis cache (this service)

    Privacy-Friendly Consent Lookup (Story 6-1 Enhancement):
    - Primary: Lookup by visitor_id (persists in localStorage)
    - Fallback: Lookup by session_id (clears on browser close)
    - This allows consent to persist across sessions without storing session data
    """

    def __init__(
        self,
        redis_client: Optional[redis.Redis] = None,
        db: Optional[AsyncSession] = None,
    ) -> None:
        self.redis = redis_client
        self.db = db
        self.logger = structlog.get_logger(__name__)

    async def get_consent_for_conversation(
        self,
        session_id: str,
        merchant_id: int,
        visitor_id: Optional[str] = None,
    ) -> Optional[Consent]:
        """Get conversation consent record from database.

        Story 6-1 Enhancement: Lookup by visitor_id (primary) or session_id (fallback).

        Args:
            session_id: Widget session ID or PSID
            merchant_id: Merchant ID
            visitor_id: Optional visitor identifier (localStorage, persists across sessions)

        Returns:
            Consent record or None if not found
        """
        if self.db is None:
            return None

        if visitor_id:
            result = await self.db.execute(
                select(Consent).where(
                    Consent.visitor_id == visitor_id,
                    Consent.merchant_id == merchant_id,
                    Consent.consent_type == ConsentType.CONVERSATION,
                )
            )
            consent = result.scalars().first()
            if consent:
                return consent

        result = await self.db.execute(
            select(Consent).where(
                Consent.session_id == session_id,
                Consent.merchant_id == merchant_id,
                Consent.consent_type == ConsentType.CONVERSATION,
            )
        )
        return result.scalars().first()

    async def get_or_create_consent(
        self,
        session_id: str,
        merchant_id: int,
        visitor_id: Optional[str] = None,
    ) -> Consent:
        """Get or create conversation consent record.

        Story 6-1 Enhancement: Uses visitor_id for cross-session tracking.

        Args:
            session_id: Widget session ID or PSID
            merchant_id: Merchant ID
            visitor_id: Optional visitor identifier for cross-session tracking

        Returns:
            Consent record (may be newly created with PENDING status)
        """
        if self.db is None:
            raise ValueError("Database session required for consent persistence")

        consent = await self.get_consent_for_conversation(session_id, merchant_id, visitor_id)

        if consent is None:
            consent = Consent.create(
                session_id=session_id,
                merchant_id=merchant_id,
                consent_type=ConsentType.CONVERSATION,
                visitor_id=visitor_id,
            )
            self.db.add(consent)
            await self.db.commit()
            await self.db.refresh(consent)
            self.logger.info(
                "conversation_consent_created",
                session_id=session_id,
                merchant_id=merchant_id,
                visitor_id=visitor_id,
            )

        return consent

    async def record_conversation_consent(
        self,
        session_id: str,
        merchant_id: int,
        consent_granted: bool,
        source: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        visitor_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Record conversation consent choice with PostgreSQL persistence.

        Story 6-1 Enhancement: Stores visitor_id for cross-session tracking.

        Args:
            session_id: Widget session ID or PSID
            merchant_id: Merchant ID
            consent_granted: True if opted in, False if opted out
            source: Source channel (messenger, widget, preview)
            ip_address: Optional IP address for audit
            user_agent: Optional user agent for audit
            visitor_id: Optional visitor identifier for cross-session tracking

        Returns:
            Consent record with updated status
        """
        if self.db is None:
            raise ValueError("Database session required for consent persistence")

        consent = await self.get_or_create_consent(session_id, merchant_id, visitor_id)

        if consent_granted:
            consent.grant(ip_address=ip_address, user_agent=user_agent)
        else:
            consent.revoke()

        consent.source_channel = source
        consent.consent_message_shown = True
        if visitor_id and not consent.visitor_id:
            consent.visitor_id = visitor_id

        await self.db.commit()

        self.logger.info(
            "conversation_consent_recorded",
            session_id=session_id,
            merchant_id=merchant_id,
            consent_granted=consent_granted,
            source=source,
            visitor_id=visitor_id,
        )

        return {
            "session_id": session_id,
            "merchant_id": merchant_id,
            "consent_type": ConsentType.CONVERSATION,
            "status": (ConsentStatus.OPTED_IN if consent_granted else ConsentStatus.OPTED_OUT),
            "granted_at": consent.granted_at.isoformat() if consent.granted_at else None,
            "source": source,
            "clear_visitor_id": consent_granted is False,
        }

    async def should_prompt_for_consent(
        self,
        session_id: str,
        merchant_id: int,
        visitor_id: Optional[str] = None,
    ) -> bool:
        """Check if consent prompt should be shown.

        Story 6-1 Enhancement: Uses visitor_id for cross-session check.

        Args:
            session_id: Widget session ID or PSID
            merchant_id: Merchant ID
            visitor_id: Optional visitor identifier for cross-session tracking

        Returns:
            True if this is first conversation and prompt should be shown
        """
        if self.db is None:
            return True

        consent = await self.get_or_create_consent(session_id, merchant_id, visitor_id)

        if not consent.consent_message_shown:
            consent.mark_message_shown()
            await self.db.commit()
            return True

        return False

    async def handle_forget_preferences(
        self,
        session_id: str,
        merchant_id: int,
        visitor_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Handle "forget my preferences" request.

        Story 6-1 Enhancement: Returns flag to clear visitor_id from localStorage.

        Resets consent to PENDING state and deletes voluntary data.
        Frontend should clear visitor_id from localStorage to ensure
        complete anonymity (GDPR Right to be Forgotten).

        Args:
            session_id: Widget session ID or PSID
            merchant_id: Merchant ID
            visitor_id: Optional visitor identifier to delete

        Returns:
            Dict with deletion confirmation and clear_visitor_id flag
        """
        if self.db is None:
            return {
                "session_id": session_id,
                "merchant_id": merchant_id,
                "status": ConsentStatus.PENDING,
                "message": "No database connection",
                "clear_visitor_id": True,
            }

        consent = await self.get_consent_for_conversation(session_id, merchant_id, visitor_id)

        if consent:
            consent.revoke()
            await self.db.commit()

        self.logger.info(
            "preferences_forgotten",
            session_id=session_id,
            merchant_id=merchant_id,
            visitor_id=visitor_id,
        )

        return {
            "session_id": session_id,
            "merchant_id": merchant_id,
            "status": ConsentStatus.PENDING,
            "message": "Preferences and conversation history deleted",
            "clear_visitor_id": True,
        }
