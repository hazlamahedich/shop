"""Export request and response schemas.

Provides Pydantic schemas for CSV export API with validation
for filter parameters and export limits.
"""

from __future__ import annotations

from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel

from app.schemas.base import BaseSchema


# Valid status and sentiment enum values (reused from conversation schema)
VALID_STATUS_VALUES = ["active", "handoff", "closed"]
VALID_SENTIMENT_VALUES = ["positive", "neutral", "negative"]


class ConversationExportRequest(BaseSchema):
    """Request schema for conversation export.

    Supports filtering by date range, search term, status, sentiment,
    and handoff presence. All filters are optional and combined with AND logic.

    Attributes:
        date_from: Start date filter (ISO 8601 format, e.g., 2026-02-01)
        date_to: End date filter (ISO 8601 format, e.g., 2026-02-28)
        search: Search term for customer ID or bot message content
        status: List of status values to filter by
        sentiment: List of sentiment values to filter by
        has_handoff: Filter by handoff presence (True=has, False=doesn't have)
    """

    date_from: Optional[str] = Field(
        None,
        description="Start date filter (ISO 8601 format, e.g., 2026-02-01)",
        examples=["2026-02-01"],
    )
    date_to: Optional[str] = Field(
        None,
        description="End date filter (ISO 8601 format, e.g., 2026-02-28)",
        examples=["2026-02-28"],
    )
    search: Optional[str] = Field(
        None,
        description="Search term for customer ID or bot message content",
        examples=["running shoes"],
    )
    status: Optional[List[str]] = Field(
        None,
        description=f"Filter by status. Valid values: {', '.join(VALID_STATUS_VALUES)}",
        examples=[["active", "handoff"]],
    )
    sentiment: Optional[List[str]] = Field(
        None,
        description=f"Filter by sentiment. Valid values: {', '.join(VALID_SENTIMENT_VALUES)}",
        examples=[["positive", "neutral"]],
    )
    has_handoff: Optional[bool] = Field(
        None,
        description="Filter by handoff presence. True=has handoff, False=no handoff",
        examples=[True, False],
    )

    @field_validator("date_from", "date_to")
    @classmethod
    def validate_date_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate ISO 8601 date format.

        Args:
            v: Date string to validate

        Returns:
            The validated date string

        Raises:
            ValueError: If date format is invalid
        """
        if v is None:
            return v
        try:
            from datetime import datetime

            datetime.fromisoformat(v)
            return v
        except ValueError:
            raise ValueError(
                f"Invalid date format: '{v}'. Expected ISO 8601 format (e.g., 2026-02-01)"
            )

    @field_validator("status")
    @classmethod
    def validate_status_values(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate status enum values.

        Args:
            v: List of status values to validate

        Returns:
            The validated status list

        Raises:
            ValueError: If any status value is invalid
        """
        if v is None:
            return v
        invalid = [s for s in v if s not in VALID_STATUS_VALUES]
        if invalid:
            raise ValueError(
                f"Invalid status values: {invalid}. "
                f"Valid values: {', '.join(VALID_STATUS_VALUES)}"
            )
        return v

    @field_validator("sentiment")
    @classmethod
    def validate_sentiment_values(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate sentiment enum values.

        Args:
            v: List of sentiment values to validate

        Returns:
            The validated sentiment list

        Raises:
            ValueError: If any sentiment value is invalid
        """
        if v is None:
            return v
        invalid = [s for s in v if s not in VALID_SENTIMENT_VALUES]
        if invalid:
            raise ValueError(
                f"Invalid sentiment values: {invalid}. "
                f"Valid values: {', '.join(VALID_SENTIMENT_VALUES)}"
            )
        return v


class ConversationExportMetadata(BaseSchema):
    """Metadata for export response.

    Includes export count and timestamp information.
    """

    export_count: int = Field(
        ...,
        description="Number of conversations exported",
        ge=0,
        le=10_000,  # MAX_EXPORT_CONVERSATIONS
    )
    export_date: str = Field(
        ...,
        description="ISO 8601 timestamp of export generation",
        examples=["2026-02-07T10:30:00Z"],
    )
    filename: str = Field(
        ...,
        description="Suggested filename for the export",
        examples=["conversations-2026-02-07.csv"],
    )
