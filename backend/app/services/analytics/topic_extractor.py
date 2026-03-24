"""Topic Extraction Service.

Story 10-8: Top Topics Widget

Simplified MVP topic extraction from RAG query logs.
Uses simple frequency ranking instead of NLP clustering.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rag_query_log import RAGQueryLog

logger = structlog.get_logger(__name__)

STOP_WORDS = {
    "the",
    "a",
    "an",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "have",
    "has",
    "had",
    "do",
    "does",
    "did",
    "will",
    "would",
    "could",
    "should",
    "may",
    "might",
    "must",
    "shall",
    "can",
    "need",
    "dare",
    "ought",
    "used",
    "to",
    "of",
    "in",
    "for",
    "on",
    "with",
    "at",
    "by",
    "from",
    "as",
    "into",
    "through",
    "during",
    "before",
    "after",
    "above",
    "below",
    "between",
    "under",
    "again",
    "further",
    "then",
    "once",
    "here",
    "there",
    "when",
    "where",
    "why",
    "how",
    "all",
    "each",
    "few",
    "more",
    "most",
    "other",
    "some",
    "such",
    "no",
    "nor",
    "not",
    "only",
    "own",
    "same",
    "so",
    "than",
    "too",
    "very",
    "just",
    "and",
    "but",
    "if",
    "or",
    "because",
    "until",
    "while",
    "what",
    "which",
    "who",
    "whom",
    "this",
    "that",
    "these",
    "those",
    "am",
    "i",
    "me",
    "my",
    "myself",
    "we",
    "our",
    "ours",
    "ourselves",
    "you",
    "your",
    "yours",
    "yourself",
    "yourselves",
    "he",
    "him",
    "his",
    "himself",
    "she",
    "her",
    "hers",
    "herself",
    "it",
    "its",
    "itself",
    "they",
    "them",
    "their",
    "theirs",
    "themselves",
    "get",
    "got",
    "getting",
    "want",
    "like",
    "hi",
    "hello",
    "hey",
    "thanks",
    "thank",
    "please",
    "ok",
    "okay",
    "yes",
    "no",
    "im",
    "i'm",
    "dont",
    "don't",
}


def calculate_trend(current_count: int, previous_count: int | None) -> str:
    """Calculate trend indicator based on count change.

    Args:
        current_count: Current period query count
        previous_count: Previous period query count (None if no data)

    Returns:
        Trend indicator: "up", "down", "stable", or "new"
    """
    if previous_count is None or previous_count == 0:
        return "new"

    change_percent = ((current_count - previous_count) / previous_count) * 100

    if change_percent > 10:
        return "up"
    elif change_percent < -10:
        return "down"
    else:
        return "stable"


def is_valid_topic(query: str) -> bool:
    """Check if a query is a valid topic (not just stop words).

    Args:
        query: The query string to check

    Returns:
        True if the query contains meaningful words
    """
    if not query or not query.strip():
        return False

    words = query.lower().strip().split()
    meaningful_words = [w for w in words if w not in STOP_WORDS and len(w) > 1]

    return len(meaningful_words) > 0


class TopicExtractor:
    """Service for extracting topics from RAG query logs.

    Story 10-8: Top Topics Widget

    Uses simplified frequency-based extraction:
    1. Get unique queries from rag_query_logs
    2. Count frequency per query
    3. Return top N by count
    4. Calculate trend by comparing to previous period
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def extract_topics(
        self,
        merchant_id: int,
        days: int = 7,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Extract top topics from RAG query logs.

        Args:
            merchant_id: Merchant ID
            days: Number of days to analyze
            limit: Maximum number of topics to return

        Returns:
            List of topic dicts with name, queryCount, trend
        """
        try:
            now = datetime.now(UTC)
            current_period_start = now.replace(
                hour=0, minute=0, second=0, microsecond=0
            ) - __import__("datetime").timedelta(days=days)
            previous_period_start = current_period_start - __import__("datetime").timedelta(
                days=days
            )
            previous_period_end = current_period_start

            current_result = await self.db.execute(
                select(
                    RAGQueryLog.query,
                    func.count(RAGQueryLog.id).label("query_count"),
                )
                .where(RAGQueryLog.merchant_id == merchant_id)
                .where(RAGQueryLog.created_at >= current_period_start)
                .group_by(RAGQueryLog.query)
                .order_by(func.count(RAGQueryLog.id).desc())
                .limit(limit * 2)
            )
            current_rows = current_result.all()

            previous_counts: dict[str, int] = {}
            previous_result = await self.db.execute(
                select(
                    RAGQueryLog.query,
                    func.count(RAGQueryLog.id).label("query_count"),
                )
                .where(RAGQueryLog.merchant_id == merchant_id)
                .where(RAGQueryLog.created_at >= previous_period_start)
                .where(RAGQueryLog.created_at < previous_period_end)
                .group_by(RAGQueryLog.query)
            )
            for row in previous_result.all():
                previous_counts[row.query] = row.query_count

            topics = []
            seen_topics: set[str] = set()

            for row in current_rows:
                query = row.query
                if not is_valid_topic(query):
                    continue

                normalized = query.lower().strip()
                if normalized in seen_topics:
                    continue

                seen_topics.add(normalized)
                current_count = row.query_count
                previous_count = previous_counts.get(query)

                topics.append(
                    {
                        "name": query,
                        "queryCount": current_count,
                        "trend": calculate_trend(current_count, previous_count),
                    }
                )

                if len(topics) >= limit:
                    break

            logger.info(
                "topics_extracted",
                merchant_id=merchant_id,
                days=days,
                topic_count=len(topics),
            )

            return topics

        except Exception as e:
            logger.error(
                "topic_extraction_failed",
                merchant_id=merchant_id,
                error=str(e),
            )
            raise

    async def get_topic_counts(
        self,
        merchant_id: int,
        days: int = 7,
    ) -> dict[str, int]:
        """Get raw topic counts for a merchant.

        Args:
            merchant_id: Merchant ID
            days: Number of days to analyze

        Returns:
            Dict mapping query strings to counts
        """
        try:
            now = datetime.now(UTC)
            cutoff_date = now - __import__("datetime").timedelta(days=days)

            result = await self.db.execute(
                select(
                    RAGQueryLog.query,
                    func.count(RAGQueryLog.id).label("query_count"),
                )
                .where(RAGQueryLog.merchant_id == merchant_id)
                .where(RAGQueryLog.created_at >= cutoff_date)
                .group_by(RAGQueryLog.query)
            )

            counts = {row.query: row.query_count for row in result.all()}

            logger.info(
                "topic_counts_retrieved",
                merchant_id=merchant_id,
                days=days,
                unique_queries=len(counts),
            )

            return counts

        except Exception as e:
            logger.error(
                "topic_counts_failed",
                merchant_id=merchant_id,
                error=str(e),
            )
            raise
