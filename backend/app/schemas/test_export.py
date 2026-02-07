"""Tests for Export Schemas.

Tests request validation, export limits, and field validation.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.export import (
    ConversationExportRequest,
    ConversationExportMetadata,
    VALID_STATUS_VALUES,
    VALID_SENTIMENT_VALUES,
)


class TestConversationExportRequest:
    """Test suite for ConversationExportRequest schema."""

    def test_empty_request(self) -> None:
        """Test request with no filters (valid)."""
        request = ConversationExportRequest()
        assert request.date_from is None
        assert request.date_to is None
        assert request.search is None
        assert request.status is None
        assert request.sentiment is None
        assert request.has_handoff is None

    def test_valid_date_format(self) -> None:
        """Test valid ISO 8601 date format."""
        request = ConversationExportRequest(
            date_from="2026-02-01", date_to="2026-02-28"
        )
        assert request.date_from == "2026-02-01"
        assert request.date_to == "2026-02-28"

    def test_invalid_date_format(self) -> None:
        """Test that invalid date format raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ConversationExportRequest(date_from="02/01/2026")

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "Invalid date format" in errors[0]["msg"]

    def test_valid_status_values(self) -> None:
        """Test valid status values."""
        request = ConversationExportRequest(status=["active", "handoff"])
        assert request.status == ["active", "handoff"]

    def test_invalid_status_values(self) -> None:
        """Test that invalid status values raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ConversationExportRequest(status=["invalid", "active"])

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "Invalid status values" in errors[0]["msg"]

    def test_valid_sentiment_values(self) -> None:
        """Test valid sentiment values."""
        request = ConversationExportRequest(sentiment=["positive", "neutral"])
        assert request.sentiment == ["positive", "neutral"]

    def test_invalid_sentiment_values(self) -> None:
        """Test that invalid sentiment values raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ConversationExportRequest(sentiment=["invalid", "positive"])

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "Invalid sentiment values" in errors[0]["msg"]

    def test_has_handoff_true(self) -> None:
        """Test has_handoff filter set to true."""
        request = ConversationExportRequest(has_handoff=True)
        assert request.has_handoff is True

    def test_has_handoff_false(self) -> None:
        """Test has_handoff filter set to false."""
        request = ConversationExportRequest(has_handoff=False)
        assert request.has_handoff is False

    def test_search_term(self) -> None:
        """Test search term filter."""
        request = ConversationExportRequest(search="running shoes")
        assert request.search == "running shoes"

    def test_all_filters_combined(self) -> None:
        """Test request with all filters combined."""
        request = ConversationExportRequest(
            date_from="2026-02-01",
            date_to="2026-02-28",
            search="shoes",
            status=["active"],
            sentiment=["positive"],
            has_handoff=False,
        )

        assert request.date_from == "2026-02-01"
        assert request.date_to == "2026-02-28"
        assert request.search == "shoes"
        assert request.status == ["active"]
        assert request.sentiment == ["positive"]
        assert request.has_handoff is False

    def test_camel_case_serialization(self) -> None:
        """Test that request serializes with camelCase."""
        request = ConversationExportRequest(
            date_from="2026-02-01",
            has_handoff=True,
        )

        # Convert to dict (should use camelCase)
        data = request.model_dump(by_alias=True)

        assert "dateFrom" in data
        assert "hasHandoff" in data
        assert "date_from" not in data  # snake_case not present

    def test_snake_case_deserialization(self) -> None:
        """Test that request accepts both snake_case and camelCase."""
        # Both should work
        request1 = ConversationExportRequest(**{"date_from": "2026-02-01"})
        request2 = ConversationExportRequest(**{"dateFrom": "2026-02-01"})

        assert request1.date_from == "2026-02-01"
        assert request2.date_from == "2026-02-01"


class TestConversationExportMetadata:
    """Test suite for ConversationExportMetadata schema."""

    def test_metadata_creation(self) -> None:
        """Test metadata object creation."""
        metadata = ConversationExportMetadata(
            export_count=150,
            export_date="2026-02-07T10:30:00Z",
            filename="conversations-2026-02-07.csv",
        )

        assert metadata.export_count == 150
        assert metadata.export_date == "2026-02-07T10:30:00Z"
        assert metadata.filename == "conversations-2026-02-07.csv"

    def test_export_count_validation_minimum(self) -> None:
        """Test that export count must be >= 0."""
        with pytest.raises(ValidationError):
            ConversationExportMetadata(
                export_count=-1,
                export_date="2026-02-07T10:30:00Z",
                filename="conversations.csv",
            )

    def test_export_count_validation_maximum(self) -> None:
        """Test that export count must be <= 10,000."""
        with pytest.raises(ValidationError):
            ConversationExportMetadata(
                export_count=10_001,
                export_date="2026-02-07T10:30:00Z",
                filename="conversations.csv",
            )

    def test_export_count_at_maximum(self) -> None:
        """Test that export count of 10,000 is valid."""
        metadata = ConversationExportMetadata(
            export_count=10_000,
            export_date="2026-02-07T10:30:00Z",
            filename="conversations.csv",
        )

        assert metadata.export_count == 10_000

    def test_camel_case_serialization(self) -> None:
        """Test that metadata serializes with camelCase."""
        metadata = ConversationExportMetadata(
            export_count=100,
            export_date="2026-02-07T10:30:00Z",
            filename="conversations.csv",
        )

        data = metadata.model_dump(by_alias=True)

        assert "exportCount" in data
        assert "exportDate" in data
        # "filename" has no underscore, so it stays the same
        assert "filename" in data
