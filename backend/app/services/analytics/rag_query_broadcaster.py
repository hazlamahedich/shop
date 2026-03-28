"""RAG Query Log Broadcast Service.

Broadcasts real-time updates when RAG query logs are created/updated.
Triggers WebSocket updates for connected dashboard clients.

Story 10.7: Knowledge Effectiveness Widget - Real-time Updates
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dashboard_ws import broadcast_knowledge_effectiveness_update
from app.services.analytics.aggregated_analytics_service import (
    AggregatedAnalyticsService,
)

logger = structlog.get_logger(__name__)


class RAGQueryBroadcaster:
    """Service for broadcasting RAG query updates to dashboard clients.

    Called after RAG query logs are created to push real-time updates
    to connected dashboard WebSocket clients.
    """

    @staticmethod
    async def broadcast_on_query_create(
        db: AsyncSession,
        merchant_id: int,
        query_id: int | None = None,
    ) -> dict[str, Any] | None:
        """Broadcast knowledge effectiveness update after RAG query is created.

        Args:
            db: Database session
            merchant_id: Merchant identifier
            query_id: Optional RAG query log ID (for logging)

        Returns:
            Broadcast data if successful, None otherwise
        """
        try:
            # Fetch fresh knowledge effectiveness metrics
            service = AggregatedAnalyticsService(db)
            effectiveness_data = await service.get_knowledge_effectiveness(
                merchant_id, days=7
            )

            # Broadcast to connected dashboard clients
            connections = await broadcast_knowledge_effectiveness_update(
                merchant_id, effectiveness_data
            )

            if connections > 0:
                logger.info(
                    "rag_query_broadcast_success",
                    merchant_id=merchant_id,
                    query_id=query_id,
                    connections=connections,
                    total_queries=effectiveness_data.get("totalQueries"),
                    no_match_rate=effectiveness_data.get("noMatchRate"),
                )

                return effectiveness_data
            else:
                # No connected dashboards - log but don't fail
                logger.debug(
                    "rag_query_broadcast_no_connections",
                    merchant_id=merchant_id,
                    query_id=query_id,
                )
                return effectiveness_data

        except Exception as e:
            # Don't fail the request if broadcast fails
            logger.error(
                "rag_query_broadcast_failed",
                merchant_id=merchant_id,
                query_id=query_id,
                error=str(e),
            )
            return None

    @staticmethod
    async def broadcast_on_batch_create(
        db: AsyncSession,
        merchant_id: int,
        query_count: int,
    ) -> dict[str, Any] | None:
        """Broadcast knowledge effectiveness update after batch RAG query creation.

        Args:
            db: Database session
            merchant_id: Merchant identifier
            query_count: Number of queries created

        Returns:
            Broadcast data if successful, None otherwise
        """
        try:
            # Fetch fresh knowledge effectiveness metrics
            service = AggregatedAnalyticsService(db)
            effectiveness_data = await service.get_knowledge_effectiveness(
                merchant_id, days=7
            )

            # Broadcast to connected dashboard clients
            connections = await broadcast_knowledge_effectiveness_update(
                merchant_id, effectiveness_data
            )

            if connections > 0:
                logger.info(
                    "rag_query_batch_broadcast_success",
                    merchant_id=merchant_id,
                    query_count=query_count,
                    connections=connections,
                    total_queries=effectiveness_data.get("totalQueries"),
                    no_match_rate=effectiveness_data.get("noMatchRate"),
                )

                return effectiveness_data
            else:
                logger.debug(
                    "rag_query_batch_broadcast_no_connections",
                    merchant_id=merchant_id,
                    query_count=query_count,
                )
                return effectiveness_data

        except Exception as e:
            logger.error(
                "rag_query_batch_broadcast_failed",
                merchant_id=merchant_id,
                query_count=query_count,
                error=str(e),
            )
            return None


# Convenience function for easy importing
async def broadcast_rag_query_update(
    db: AsyncSession,
    merchant_id: int,
    query_id: int | None = None,
) -> dict[str, Any] | None:
    """Convenience function to broadcast RAG query update.

    Args:
        db: Database session
        merchant_id: Merchant identifier
        query_id: Optional RAG query log ID

    Returns:
        Broadcast data if successful, None otherwise
    """
    return await RAGQueryBroadcaster.broadcast_on_query_create(
        db, merchant_id, query_id
    )
