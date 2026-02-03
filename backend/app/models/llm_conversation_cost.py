"""LLM Conversation Cost ORM model.

Tracks token usage and costs per conversation for budget management
and cost transparency. Supports cost estimation and real-time tracking.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, Float, DateTime, ForeignKey as SQLForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class LLMConversationCost(Base):
    """Per-conversation LLM cost tracking model.

    Stores detailed token usage and cost information for each
    LLM request to enable:
    - Per-conversation cost tracking
    - Budget management and alerts
    - Cost optimization insights
    - Provider cost comparison
    """

    __tablename__ = "llm_conversation_costs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    conversation_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )  # Facebook PSID or unique ID
    merchant_id: Mapped[int] = mapped_column(
        Integer,
        SQLForeignKey("merchants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Request details
    provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    model: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    # Token usage
    prompt_tokens: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    completion_tokens: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    total_tokens: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # Cost calculation
    input_cost_usd: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    output_cost_usd: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    total_cost_usd: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    # Metadata
    request_timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )
    processing_time_ms: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )  # Response time in milliseconds

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<LLMConversationCost(id={self.id}, conversation_id={self.conversation_id}, "
            f"provider={self.provider}, total_cost=${self.total_cost_usd:.6f})>"
        )
