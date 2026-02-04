"""Data retention service for enforcing NFR-S11.

Implements automated cleanup of voluntary conversation data after configurable retention periods.
Operational data (order references) is kept indefinitely per business requirements.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy import select, delete, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

import structlog

from app.core.database import get_db
from app.models.conversation import Conversation
from app.models.message import Message

logger = structlog.get_logger(__name__)


class DataRetentionService:
    """Service for managing data retention and cleanup operations.

    Enforces NFR-S11: 30-day conversation retention limit with separate
    retention periods for different data tiers.

    Data Tiers:
    - Voluntary data (preferences, history): 30 days max
    - Operational data (order refs): Keep indefinitely
    - Session data (cart): 24 hours max
    """

    def __init__(
        self,
        voluntary_days: int = 30,
        session_hours: int = 24
    ) -> None:
        """Initialize data retention service with configurable retention periods.

        Args:
            voluntary_days: Days to retain voluntary conversation data (default: 30)
            session_hours: Hours to retain session/cart data (default: 24)
        """
        self.voluntary_days = voluntary_days
        self.session_hours = session_hours

    async def cleanup_voluntary_data(
        self,
        db: AsyncSession,
        dry_run: bool = False,
        before_date: Optional[datetime] = None
    ) -> Dict[str, int | str]:
        """Clean up voluntary conversation data older than retention period.

        Deletes conversations and their associated messages that haven't been
        updated within the retention period. This preserves user privacy while
        allowing for recent conversation history.

        Args:
            db: Database session
            dry_run: If True, only report what would be deleted
            before_date: Optional cutoff date (defaults to retention period)

        Returns:
            Dictionary with deletion statistics including:
            - conversations_deleted: Number of conversations deleted
            - messages_deleted: Number of messages deleted
            - cutoff_date: ISO timestamp of deletion threshold
            - conversations_to_delete: Count in dry run mode
        """
        cutoff_date = before_date or datetime.utcnow() - timedelta(days=self.voluntary_days)

        stats: Dict[str, int | str] = {
            "conversations_deleted": 0,
            "messages_deleted": 0,
            "cutoff_date": cutoff_date.isoformat(),
        }

        # Find conversations to delete (older than cutoff)
        result = await db.execute(
            select(Conversation).where(
                Conversation.updated_at < cutoff_date
            )
        )
        conversations = result.scalars().all()

        if dry_run:
            stats["conversations_to_delete"] = len(conversations)
            # Count messages that would be deleted
            conversation_ids = [c.id for c in conversations]
            if conversation_ids:
                msg_result = await db.execute(
                    select(func.count(Message.id)).where(
                        Message.conversation_id.in_(conversation_ids)
                    )
                )
                stats["messages_to_delete"] = msg_result.scalar() or 0
            else:
                stats["messages_to_delete"] = 0

            logger.info(
                "data_retention_dry_run",
                **stats
            )
            return stats

        # Delete messages first (foreign key constraint)
        for conv in conversations:
            result = await db.execute(
                delete(Message).where(
                    Message.conversation_id == conv.id
                )
            )
            stats["messages_deleted"] += result.rowcount or 0

        # Delete conversations
        result = await db.execute(
            delete(Conversation).where(
                Conversation.updated_at < cutoff_date
            )
        )
        stats["conversations_deleted"] = result.rowcount or 0

        await db.commit()

        logger.info(
            "data_retention_cleanup_completed",
            **stats
        )

        return stats

    async def cleanup_expired_sessions(
        self,
        db: AsyncSession,
        dry_run: bool = False,
        before_date: Optional[datetime] = None
    ) -> Dict[str, int | str]:
        """Clean up expired session data (cart data, temporary state).

        Session data is primarily stored in Redis with optional persistence.
        This method handles any persistent session storage cleanup.

        Args:
            db: Database session
            dry_run: If True, only report what would be deleted
            before_date: Optional cutoff time (defaults to session retention period)

        Returns:
            Dictionary with deletion statistics
        """
        cutoff_time = before_date or datetime.utcnow() - timedelta(hours=self.session_hours)

        stats: Dict[str, int | str] = {
            "sessions_expired": 0,
            "cutoff_time": cutoff_time.isoformat(),
        }

        # TODO: Implement when session persistence is added to PostgreSQL
        # Currently session data is in Redis with automatic TTL expiration
        # This placeholder exists for future persistent session storage

        logger.info(
            "data_retention_session_cleanup",
            note="Session data in Redis uses automatic TTL",
            **stats
        )

        return stats

    async def get_retention_stats(
        self,
        db: AsyncSession
    ) -> Dict[str, int | str]:
        """Get statistics about data that would be affected by retention policy.

        Provides visibility into data volume by age for operational monitoring.

        Args:
            db: Database session

        Returns:
            Dictionary with retention statistics including counts by age bracket
        """
        now = datetime.utcnow()

        # Count conversations by age
        age_brackets = {
            "0_7_days": now - timedelta(days=7),
            "7_30_days": now - timedelta(days=30),
            "30_90_days": now - timedelta(days=90),
            "90_plus_days": now - timedelta(days=90),
        }

        stats: Dict[str, int | str] = {
            "total_conversations": 0,
            "total_messages": 0,
            "conversations_by_age": {},
            "retention_policy": {
                "voluntary_days": self.voluntary_days,
                "session_hours": self.session_hours,
            },
        }

        # Total counts
        conv_result = await db.execute(select(func.count(Conversation.id)))
        stats["total_conversations"] = conv_result.scalar() or 0

        msg_result = await db.execute(select(func.count(Message.id)))
        stats["total_messages"] = msg_result.scalar() or 0

        # Count by age bracket
        for bracket_name, cutoff in age_brackets.items():
            if bracket_name == "0_7_days":
                # Younger than 7 days
                result = await db.execute(
                    select(func.count(Conversation.id)).where(
                        Conversation.updated_at >= cutoff
                    )
                )
            elif bracket_name == "7_30_days":
                # 7-30 days old
                result = await db.execute(
                    select(func.count(Conversation.id)).where(
                        and_(
                            Conversation.updated_at >= age_brackets["30_90_days"],
                            Conversation.updated_at < age_brackets["0_7_days"]
                        )
                    )
                )
            elif bracket_name == "30_90_days":
                # 30-90 days old
                result = await db.execute(
                    select(func.count(Conversation.id)).where(
                        and_(
                            Conversation.updated_at >= age_brackets["90_plus_days"],
                            Conversation.updated_at < age_brackets["30_90_days"]
                        )
                    )
                )
            else:  # 90_plus_days
                # Older than 90 days (would be deleted)
                result = await db.execute(
                    select(func.count(Conversation.id)).where(
                        Conversation.updated_at < cutoff
                    )
                )

            stats["conversations_by_age"][bracket_name] = result.scalar() or 0

        return stats

    async def get_conversations_to_delete(
        self,
        db: AsyncSession,
        limit: int = 100
    ) -> List[Dict[str, int | str]]:
        """Get list of conversations that would be deleted by retention policy.

        Useful for audit trails and pre-deletion verification.

        Args:
            db: Database session
            limit: Maximum number of conversations to return

        Returns:
            List of conversation details that would be deleted
        """
        cutoff_date = datetime.utcnow() - timedelta(days=self.voluntary_days)

        result = await db.execute(
            select(Conversation).where(
                Conversation.updated_at < cutoff_date
            ).limit(limit)
        )
        conversations = result.scalars().all()

        return [
            {
                "id": conv.id,
                "merchant_id": conv.merchant_id,
                "platform": conv.platform,
                "platform_sender_id": conv.platform_sender_id,
                "status": conv.status,
                "created_at": conv.created_at.isoformat(),
                "updated_at": conv.updated_at.isoformat(),
                "days_since_update": (datetime.utcnow() - conv.updated_at).days,
            }
            for conv in conversations
        ]
