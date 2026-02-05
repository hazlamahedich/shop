"""Pydantic schemas for consent management.

Defines ConsentRecord and related models for tracking user consent
for cart and session persistence.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field
from pydantic.alias_generators import to_camel


class ConsentStatus(str, Enum):
    """User consent status for data persistence."""

    OPTED_IN = "opted_in"
    OPTED_OUT = "opted_out"
    PENDING = "pending"


class ConsentRecord(BaseModel):
    """Record of user's consent choice."""

    model_config = {
        "alias_generator": to_camel,
        "populate_by_name": True,
    }

    status: ConsentStatus = Field(description="Current consent status")
    timestamp: str = Field(description="ISO timestamp when consent was recorded")
    psid: str = Field(description="Facebook Page-Scoped ID")
