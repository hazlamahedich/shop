"""Handoff schemas for human assistance detection.

Provides Pydantic models for handoff status, reasons, and API responses.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import Field

from app.schemas.base import BaseSchema


class HandoffStatus(str, Enum):
    """Handoff status for conversation sub-state tracking.

    Used alongside Conversation.status to provide granular handoff state.
    - none: Normal conversation, no handoff
    - pending: Handoff triggered, awaiting merchant response
    - active: Merchant actively responding
    - resolved: Handoff complete, ready to return to bot
    """

    NONE = "none"
    PENDING = "pending"
    ACTIVE = "active"
    RESOLVED = "resolved"


class HandoffReason(str, Enum):
    """Reason for handoff trigger.

    Tracks why handoff was initiated for analytics and logging.
    """

    KEYWORD = "keyword"
    LOW_CONFIDENCE = "low_confidence"
    CLARIFICATION_LOOP = "clarification_loop"


class HandoffResult(BaseSchema):
    """Result of handoff detection check.

    Returned by HandoffDetector.detect() to indicate if handoff should trigger.
    """

    should_handoff: bool = Field(default=False, description="Whether handoff should be triggered")
    reason: HandoffReason | None = Field(
        default=None, description="Reason for handoff if triggered"
    )
    confidence_count: int = Field(default=0, description="Current consecutive low confidence count")
    matched_keyword: str | None = Field(
        default=None, description="Keyword that triggered handoff (if applicable)"
    )
    loop_count: int = Field(default=0, description="Clarification loop count if applicable")


class HandoffResponse(BaseSchema):
    """API response for handoff status updates.

    Used when returning handoff information to the frontend.
    """

    conversation_id: int
    handoff_status: HandoffStatus
    handoff_reason: HandoffReason | None = None
    handoff_triggered_at: datetime | None = None
    message: str | None = None


class HandoffDetectionRequest(BaseSchema):
    """Request for handoff detection check.

    Used internally to pass detection parameters.
    """

    message: str = Field(..., description="Customer message to analyze")
    conversation_id: int = Field(..., description="Conversation ID for state tracking")
    confidence_score: float | None = Field(
        default=None, description="LLM confidence score (0.0-1.0)"
    )
    clarification_type: str | None = Field(
        default=None, description="Current clarification type if in flow"
    )


DEFAULT_HANDOFF_MESSAGE = (
    "I'm having trouble understanding. Sorry! "
    "Let me get someone who can help. "
    "I've flagged this - our team will respond within 12 hours."
)


__all__ = [
    "HandoffStatus",
    "HandoffReason",
    "HandoffResult",
    "HandoffResponse",
    "HandoffDetectionRequest",
    "DEFAULT_HANDOFF_MESSAGE",
]
