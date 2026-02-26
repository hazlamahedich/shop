"""Pydantic schemas for consent management.

Defines ConsentRecord and related models for tracking user consent
for cart and session persistence.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field
from pydantic.alias_generators import to_camel


class ConsentStatus(str, Enum):
    """User consent status for data persistence."""

    OPTED_IN = "opted_in"
    OPTED_OUT = "opted_out"
    PENDING = "pending"


class ConsentSource(str, Enum):
    """Source channel for consent collection."""

    MESSENGER = "messenger"
    WIDGET = "widget"
    PREVIEW = "preview"


class ConsentRecord(BaseModel):
    """Record of user's consent choice."""

    model_config = {
        "alias_generator": to_camel,
        "populate_by_name": True,
    }

    status: ConsentStatus = Field(description="Current consent status")
    timestamp: str = Field(description="ISO timestamp when consent was recorded")
    psid: str = Field(description="Facebook Page-Scoped ID")


class ConversationConsentRecord(BaseModel):
    """Record of user's conversation data consent choice."""

    model_config = {
        "alias_generator": to_camel,
        "populate_by_name": True,
    }

    status: ConsentStatus = Field(description="Current consent status")
    source: ConsentSource = Field(description="Source channel for consent")
    consent_message_shown: bool = Field(
        default=False, description="Whether consent prompt was shown"
    )
    timestamp: str = Field(description="ISO timestamp when consent was recorded")
    session_id: str = Field(description="Session ID (widget session or PSID)")


class ConsentPromptResponse(BaseModel):
    """Response for consent prompt status check."""

    model_config = {
        "alias_generator": to_camel,
        "populate_by_name": True,
    }

    needs_consent: bool = Field(description="Whether user needs to provide consent")
    status: ConsentStatus = Field(description="Current consent status")
    consent_message_shown: bool = Field(
        default=False, description="Whether consent prompt was shown"
    )


class RecordConsentRequest(BaseModel):
    """Request to record user's consent choice.

    Story 6-1 Enhancement: Added visitor_id for privacy-friendly consent persistence.
    """

    model_config = {
        "alias_generator": to_camel,
        "populate_by_name": True,
    }

    session_id: str = Field(description="Widget session ID")
    consent_granted: bool = Field(description="Whether user granted consent")
    source: ConsentSource = Field(
        default=ConsentSource.WIDGET, description="Source channel for consent"
    )
    visitor_id: Optional[str] = Field(
        default=None, description="Visitor ID for cross-session consent tracking"
    )
