"""RAG Query Log Model.

Story 10-7: Knowledge Effectiveness Widget

Tracks RAG queries for analytics - match rate, confidence, sources.
Used to measure knowledge base effectiveness over time.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import TIMESTAMP, Boolean, Column, Float, Index, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB

from app.core.database import Base


class RAGQueryLog(Base):
    """Log of RAG queries for effectiveness analytics.

    Tracks each query made against the knowledge base to measure:
    - Match rate (successful vs no-match)
    - Average confidence scores
    - Source attribution
    - Trend over time

    Story 10-7: Knowledge Effectiveness Widget
    """

    __tablename__ = "rag_query_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    merchant_id = Column(Integer, nullable=False, index=True)
    query = Column(Text, nullable=False)
    matched = Column(Boolean, default=False, nullable=False)
    confidence = Column(Float, nullable=True)
    sources = Column(JSONB, nullable=True)
    created_at = Column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    __table_args__ = (
        Index(
            "idx_rag_logs_merchant_date",
            "merchant_id",
            "created_at",
        ),
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "merchantId": self.merchant_id,
            "query": self.query,
            "matched": self.matched,
            "confidence": self.confidence,
            "sources": self.sources,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
        }
