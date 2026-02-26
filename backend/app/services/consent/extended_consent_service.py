"""Extended consent service for conversation data storage consent.

Story 6-1: Opt-In Consent Flow
Story 6-1 Enhancement: Privacy-friendly consent persistence via visitor_id
Story 6-2: Request Data Deletion

Extends ConsentService to support:
- Conversation consent with PostgreSQL persistence
- Cross-session consent tracking via visitor_id (localStorage)
- Privacy-friendly: session_id clears on browser close, visitor_id persists
- Audit trail for GDPR/CCPA compliance
- Immediate voluntary data deletion for "forget preferences"
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Optional

import redis.asyncio as redis
import structlog
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import APIError, ErrorCode
from app.schemas.consent import ConsentStatus
from app.models.consent import Consent, ConsentType, ConsentSource
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.deletion_audit_log import DeletionAuditLog


DELETION_LOCK_TTL = 10
DELETION_RATE_LIMIT_TTL = 3600
MAX_DELETION_REQUESTS_PER_HOUR = 1


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

    async def _check_deletion_rate_limit(
        self,
        session_id: str,
    ) -> bool:
        """Check if deletion rate limit has been exceeded.

        Story 6-2 Task 7: Rate limiting - max 1 forget request per session per hour.

        Args:
            session_id: Widget session ID or PSID

        Returns:
            True if rate limit is NOT exceeded (deletion allowed)
        """
        if self.redis is None:
            return True

        rate_key = f"deletion_rate:{session_id}"
        try:
            exists = await self.redis.exists(rate_key)
            if exists:
                self.logger.warning(
                    "deletion_rate_limited",
                    session_id=session_id,
                )
                return False
            return True
        except Exception as e:
            self.logger.warning(
                "deletion_rate_check_failed",
                session_id=session_id,
                error=str(e),
            )
            return True

    async def _set_deletion_rate_limit(
        self,
        session_id: str,
    ) -> None:
        """Set deletion rate limit after successful deletion.

        Args:
            session_id: Widget session ID or PSID
        """
        if self.redis is None:
            return

        rate_key = f"deletion_rate:{session_id}"
        try:
            await self.redis.setex(rate_key, DELETION_RATE_LIMIT_TTL, "1")
        except Exception as e:
            self.logger.warning(
                "deletion_rate_set_failed",
                session_id=session_id,
                error=str(e),
            )

    async def _acquire_deletion_lock(
        self,
        session_id: str,
    ) -> bool:
        """Acquire deletion lock to prevent concurrent deletions.

        Story 6-2 Task 9: Session locking with 10s TTL.

        Args:
            session_id: Widget session ID or PSID

        Returns:
            True if lock acquired successfully
        """
        if self.redis is None:
            return True

        lock_key = f"deletion_lock:{session_id}"
        try:
            acquired = await self.redis.set(lock_key, "1", ex=DELETION_LOCK_TTL, nx=True)
            if not acquired:
                self.logger.warning(
                    "deletion_lock_failed",
                    session_id=session_id,
                )
                return False
            return True
        except Exception as e:
            self.logger.warning(
                "deletion_lock_acquire_failed",
                session_id=session_id,
                error=str(e),
            )
            return True

    async def _release_deletion_lock(
        self,
        session_id: str,
    ) -> None:
        """Release deletion lock.

        Args:
            session_id: Widget session ID or PSID
        """
        if self.redis is None:
            return

        lock_key = f"deletion_lock:{session_id}"
        try:
            await self.redis.delete(lock_key)
        except Exception as e:
            self.logger.warning(
                "deletion_lock_release_failed",
                session_id=session_id,
                error=str(e),
            )

    def _get_redis_keys_to_clear(
        self,
        session_id: str,
        platform: str = "widget",
    ) -> list[str]:
        """Get Redis keys to clear for a session.

        Args:
            session_id: Widget session ID or PSID
            platform: Platform type (widget, messenger)

        Returns:
            List of Redis key patterns to clear
        """
        keys = []

        if platform == "widget":
            keys.extend(
                [
                    f"cart:widget:{session_id}",
                    f"prefs:{session_id}",
                    f"session:{session_id}:preferences",
                ]
            )
        elif platform == "messenger":
            keys.extend(
                [
                    f"cart:messenger:{session_id}",
                    f"prefs:{session_id}",
                    f"session:{session_id}:preferences",
                ]
            )

        return keys

    async def _clear_redis_data(
        self,
        session_id: str,
        platform: str = "widget",
    ) -> tuple[int, list[str]]:
        """Clear voluntary data from Redis.

        Story 6-2 Task 1.4: Clear Redis cart, preferences, session data.
        Story 6-2 Task 1.9: Handle Redis failures gracefully.

        Args:
            session_id: Widget session ID or PSID
            platform: Platform type (widget, messenger)

        Returns:
            Tuple of (keys_cleared_count, failed_keys)
        """
        if self.redis is None:
            return (0, [])

        keys_to_clear = self._get_redis_keys_to_clear(session_id, platform)
        cleared = 0
        failed_keys = []

        for key in keys_to_clear:
            try:
                result = await self.redis.delete(key)
                if result:
                    cleared += 1
            except Exception as e:
                self.logger.warning(
                    "redis_key_delete_failed",
                    session_id=session_id,
                    key=key,
                    error=str(e),
                )
                failed_keys.append(key)

        return (cleared, failed_keys)

    async def _get_cross_platform_sessions(
        self,
        visitor_id: str,
        merchant_id: int,
    ) -> list[tuple[str, str]]:
        """Get all session_ids across platforms for a visitor_id.

        Story 6-2 Task 1.8: Query all platforms when visitor_id provided.

        Args:
            visitor_id: Visitor identifier
            merchant_id: Merchant ID

        Returns:
            List of (session_id, platform) tuples
        """
        if self.db is None:
            return []

        result = await self.db.execute(
            select(Consent.session_id, Conversation.platform)
            .distinct()
            .join(
                Conversation,
                Consent.session_id == Conversation.platform_sender_id,
                isouter=True,
            )
            .where(
                Consent.visitor_id == visitor_id,
                Consent.merchant_id == merchant_id,
            )
        )
        sessions = []
        for row in result.all():
            session_id = row[0]
            platform = row[1] if row[1] else "widget"
            sessions.append((session_id, platform))

        if not sessions:
            result = await self.db.execute(
                select(Consent.session_id).where(
                    Consent.visitor_id == visitor_id,
                    Consent.merchant_id == merchant_id,
                )
            )
            for row in result.all():
                sessions.append((row[0], "widget"))

        return sessions

    async def delete_voluntary_data(
        self,
        session_id: str,
        merchant_id: int,
        visitor_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Delete voluntary data for GDPR/CCPA compliance.

        Story 6-2: Immediate deletion of voluntary data.
        Story 6-2 Task 1: Core deletion functionality.
        Story 6-2 Task 7: Rate limiting and atomic transactions.
        Story 6-2 Task 9: Edge case handling.

        Deletes:
        - Conversations (except those with order references)
        - Messages
        - Redis cart and preferences

        Keeps:
        - Order references (operational data - business requirement)
        - Consent record (reset to PENDING, not deleted)

        Args:
            session_id: Widget session ID or PSID
            merchant_id: Merchant ID
            visitor_id: Optional visitor identifier for cross-platform deletion

        Returns:
            Dict with deletion results including counts

        Raises:
            APIError: If rate limited or concurrent deletion in progress
        """
        if self.db is None:
            raise APIError(
                ErrorCode.INTERNAL_ERROR,
                "Database connection required for data deletion",
            )

        if not await self._check_deletion_rate_limit(session_id):
            raise APIError(
                ErrorCode.VALIDATION_ERROR,
                "Rate limit exceeded. Please wait before requesting another deletion.",
                {"retry_after_seconds": DELETION_RATE_LIMIT_TTL},
            )

        if not await self._acquire_deletion_lock(session_id):
            raise APIError(
                ErrorCode.VALIDATION_ERROR,
                "Deletion already in progress. Please wait.",
            )

        audit_log = DeletionAuditLog(
            session_id=session_id,
            visitor_id=visitor_id,
            merchant_id=merchant_id,
        )
        self.db.add(audit_log)
        await self.db.flush()

        total_conversations = 0
        total_messages = 0
        total_redis_cleared = 0
        all_failed_redis_keys = []

        try:
            sessions_to_delete = [(session_id, "widget")]

            if visitor_id:
                cross_platform = await self._get_cross_platform_sessions(visitor_id, merchant_id)
                for sid, platform in cross_platform:
                    if (sid, platform) not in sessions_to_delete:
                        sessions_to_delete.append((sid, platform))

            for sid, platform in sessions_to_delete:
                conv_result = await self.db.execute(
                    select(Conversation.id).where(
                        Conversation.platform_sender_id == sid,
                        Conversation.merchant_id == merchant_id,
                    )
                )
                conversation_ids = [row[0] for row in conv_result.all()]

                if conversation_ids:
                    msg_result = await self.db.execute(
                        delete(Message).where(Message.conversation_id.in_(conversation_ids))
                    )
                    messages_deleted = msg_result.rowcount or 0
                    total_messages += messages_deleted

                    conv_delete_result = await self.db.execute(
                        delete(Conversation).where(Conversation.id.in_(conversation_ids))
                    )
                    conversations_deleted = conv_delete_result.rowcount or 0
                    total_conversations += conversations_deleted

                redis_cleared, failed_keys = await self._clear_redis_data(sid, platform)
                total_redis_cleared += redis_cleared
                all_failed_redis_keys.extend(failed_keys)

            audit_log.mark_completed(
                conversations=total_conversations,
                messages=total_messages,
                redis_keys=total_redis_cleared,
                failed_redis_keys=all_failed_redis_keys if all_failed_redis_keys else None,
            )

            await self._set_deletion_rate_limit(session_id)

            await self.db.commit()

            self.logger.info(
                "voluntary_data_deleted",
                session_id=session_id,
                merchant_id=merchant_id,
                visitor_id=visitor_id,
                conversations_deleted=total_conversations,
                messages_deleted=total_messages,
                redis_keys_cleared=total_redis_cleared,
                audit_log_id=audit_log.id,
            )

            return {
                "session_id": session_id,
                "merchant_id": merchant_id,
                "status": "success",
                "conversations_deleted": total_conversations,
                "messages_deleted": total_messages,
                "redis_keys_cleared": total_redis_cleared,
                "audit_log_id": audit_log.id,
            }

        except Exception as e:
            audit_log.mark_failed(str(e))
            await self.db.commit()

            self.logger.error(
                "voluntary_data_deletion_failed",
                session_id=session_id,
                merchant_id=merchant_id,
                error=str(e),
                audit_log_id=audit_log.id,
            )

            raise APIError(
                ErrorCode.INTERNAL_ERROR,
                f"Data deletion failed: {str(e)}",
                {"audit_log_id": audit_log.id},
            )

        finally:
            await self._release_deletion_lock(session_id)

    async def handle_forget_preferences_with_deletion(
        self,
        session_id: str,
        merchant_id: int,
        visitor_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Handle "forget my preferences" with actual data deletion.

        Story 6-2: Enhanced version that actually deletes data.

        Resets consent to PENDING state AND deletes voluntary data.
        Frontend should clear visitor_id from localStorage to ensure
        complete anonymity (GDPR Right to be Forgotten).

        Args:
            session_id: Widget session ID or PSID
            merchant_id: Merchant ID
            visitor_id: Optional visitor identifier to delete

        Returns:
            Dict with deletion confirmation and clear_visitor_id flag
        """
        deletion_result = await self.delete_voluntary_data(
            session_id=session_id,
            merchant_id=merchant_id,
            visitor_id=visitor_id,
        )

        consent = await self.get_consent_for_conversation(session_id, merchant_id, visitor_id)

        if consent:
            consent.revoke()
            await self.db.commit()

        self.logger.info(
            "preferences_forgotten_with_deletion",
            session_id=session_id,
            merchant_id=merchant_id,
            visitor_id=visitor_id,
            deletion_result=deletion_result,
        )

        return {
            "session_id": session_id,
            "merchant_id": merchant_id,
            "status": ConsentStatus.PENDING,
            "message": "Preferences and conversation history deleted",
            "clear_visitor_id": True,
            "deletion_summary": {
                "conversations_deleted": deletion_result.get("conversations_deleted", 0),
                "messages_deleted": deletion_result.get("messages_deleted", 0),
                "audit_log_id": deletion_result.get("audit_log_id"),
            },
        }
