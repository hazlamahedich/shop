"""Knowledge Gap Model.

Tracks questions the bot couldn't answer for knowledge gap analysis.

A knowledge gap occurs when:
1. User asks a question AND
2. FAQ doesn't match AND
3. RAG returns no relevant documents AND/OR
4. LLM indicates it couldn't find information

Used by KnowledgeGapWidget to show merchants what to add to their knowledge base.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any

from sqlalchemy import TIMESTAMP, Boolean, ForeignKey, Index, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class GapType(str, Enum):
    """Type of knowledge gap detected."""

    NO_RAG_MATCH = "no_rag_match"
    NO_FAQ_MATCH = "no_faq_match"
    LOW_CONFIDENCE = "low_confidence"
    LLM_NO_INFO = "llm_no_info"


class SuggestedAction(str, Enum):
    """Suggested action to resolve the gap."""

    ADD_FAQ = "Add FAQ"
    UPLOAD_DOC = "Upload Document"
    IMPROVE_ANSWER = "Improve Answer"


class KnowledgeGap(Base):
    """Knowledge gap model.

    Tracks questions that the bot couldn't answer adequately.
    Similar questions are aggregated by question_hash to show occurrence count.

    Gap detection triggers:
    - NO_RAG_MATCH: RAG retrieval returned no chunks for a question
    - NO_FAQ_MATCH: FAQ matching failed for a question
    - LOW_CONFIDENCE: Intent classification confidence < 0.5
    - LLM_NO_INFO: LLM explicitly said it couldn't find information
    """

    __tablename__ = "knowledge_gaps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    merchant_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("merchants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    conversation_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("conversations.id", ondelete="SET NULL"),
        nullable=True,
    )
    question: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    question_hash: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        index=True,
    )
    gap_types: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )
    occurrence_count: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )
    first_occurred_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    last_occurred_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    resolved: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )
    resolved_by_type: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    resolved_by_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    sample_response: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    extra_data: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata",
        JSONB,
        nullable=True,
    )

    merchant: Mapped["Merchant"] = relationship(
        "Merchant",
        back_populates="knowledge_gaps",
    )

    __table_args__ = (
        Index(
            "idx_knowledge_gaps_merchant_resolved",
            "merchant_id",
            "resolved",
        ),
        Index(
            "idx_knowledge_gaps_merchant_hash",
            "merchant_id",
            "question_hash",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<KnowledgeGap("
            f"id={self.id}, "
            f"merchant_id={self.merchant_id}, "
            f"question={self.question[:30]}..., "
            f"occurrences={self.occurrence_count}"
            f")>"
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "intent": self.question,
            "count": self.occurrence_count,
            "lastOccurrence": self.last_occurred_at.isoformat() if self.last_occurred_at else None,
            "suggestedAction": self._get_suggested_action(),
            "gapTypes": self.gap_types,
            "resolved": self.resolved,
            "firstOccurred": self.first_occurred_at.isoformat() if self.first_occurred_at else None,
            "sampleResponse": self.sample_response,
        }

    def _get_suggested_action(self) -> str:
        """Determine suggested action based on gap types."""
        if GapType.NO_FAQ_MATCH.value in self.gap_types:
            return SuggestedAction.ADD_FAQ.value
        if GapType.NO_RAG_MATCH.value in self.gap_types:
            return SuggestedAction.UPLOAD_DOC.value
        if GapType.LOW_CONFIDENCE.value in self.gap_types:
            return SuggestedAction.IMPROVE_ANSWER.value
        return SuggestedAction.ADD_FAQ.value
