"""Pydantic schemas for session persistence.

Defines SessionActivity and related models for tracking
shopper session activity and returning shopper detection.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field
from pydantic.alias_generators import to_camel


class SessionActivity(BaseModel):
    """Record of user's last activity timestamp."""

    model_config = {
        "alias_generator": to_camel,
        "populate_by_name": True,
    }

    timestamp: str = Field(description="ISO timestamp of last activity")
    psid: str = Field(description="Facebook Page-Scoped ID")
