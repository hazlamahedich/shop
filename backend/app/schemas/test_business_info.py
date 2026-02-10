"""Tests for Business Info schemas.

Story 1.11: Business Info & FAQ Configuration

Tests Pydantic schema validation for business information.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from app.schemas.business_info import (
    BusinessInfoRequest,
    BusinessInfoResponse,
    BusinessInfoEnvelope,
)
from app.schemas.base import MetaData


class TestBusinessInfoRequest:
    """Tests for BusinessInfoRequest schema."""

    def test_business_info_request_with_all_fields(self):
        """Test creating request with all fields (Story 1.11 AC 1, 4, 7)."""
        request = BusinessInfoRequest(
            business_name="Alex's Athletic Gear",
            business_description="Premium athletic equipment for serious athletes",
            business_hours="9 AM - 6 PM PST, Mon-Fri",
        )

        assert request.business_name == "Alex's Athletic Gear"
        assert request.business_description == "Premium athletic equipment for serious athletes"
        assert request.business_hours == "9 AM - 6 PM PST, Mon-Fri"

    def test_business_info_request_with_partial_fields(self):
        """Test creating request with partial fields (Story 1.11 AC 1)."""
        request = BusinessInfoRequest(
            business_name="Test Store",
            business_hours="10 AM - 7 PM EST",
        )

        assert request.business_name == "Test Store"
        assert request.business_description is None
        assert request.business_hours == "10 AM - 7 PM EST"

    def test_business_info_request_all_optional(self):
        """Test creating request with no fields (all optional)."""
        request = BusinessInfoRequest()

        assert request.business_name is None
        assert request.business_description is None
        assert request.business_hours is None

    def test_business_name_max_length(self):
        """Test business_name respects 100 character limit (Story 1.11 AC 1)."""
        # Exactly 100 characters should pass
        name_100 = "A" * 100
        request = BusinessInfoRequest(business_name=name_100)
        assert len(request.business_name) == 100

    def test_business_name_exceeds_max_length(self):
        """Test business_name exceeds 100 characters raises validation error."""
        name_101 = "A" * 101
        with pytest.raises(ValidationError) as exc_info:
            BusinessInfoRequest(business_name=name_101)

        assert "business_name" in str(exc_info.value).lower()

    def test_business_description_max_length(self):
        """Test business_description respects 500 character limit (Story 1.11 AC 1)."""
        description_500 = "B" * 500
        request = BusinessInfoRequest(business_description=description_500)
        assert len(request.business_description) == 500

    def test_business_description_exceeds_max_length(self):
        """Test business_description exceeds 500 characters raises validation error."""
        description_501 = "B" * 501
        with pytest.raises(ValidationError) as exc_info:
            BusinessInfoRequest(business_description=description_501)

        assert "business_description" in str(exc_info.value).lower()

    def test_business_hours_max_length(self):
        """Test business_hours respects 200 character limit (Story 1.11 AC 1)."""
        hours_200 = "H" * 200
        request = BusinessInfoRequest(business_hours=hours_200)
        assert len(request.business_hours) == 200

    def test_business_hours_exceeds_max_length(self):
        """Test business_hours exceeds 200 characters raises validation error."""
        hours_201 = "H" * 201
        with pytest.raises(ValidationError) as exc_info:
            BusinessInfoRequest(business_hours=hours_201)

        assert "business_hours" in str(exc_info.value).lower()

    def test_strip_whitespace_from_fields(self):
        """Test that leading/trailing whitespace is stripped from fields."""
        request = BusinessInfoRequest(
            business_name="  Alex's Athletic Gear  ",
            business_description="  Premium equipment  ",
            business_hours="  9 AM - 6 PM  ",
        )

        assert request.business_name == "Alex's Athletic Gear"
        assert request.business_description == "Premium equipment"
        assert request.business_hours == "9 AM - 6 PM"

    def test_empty_string_becomes_none(self):
        """Test that empty strings (after stripping) become None."""
        request = BusinessInfoRequest(
            business_name="   ",
            business_description="",
            business_hours="\t\n",
        )

        assert request.business_name is None
        assert request.business_description is None
        assert request.business_hours is None


class TestBusinessInfoResponse:
    """Tests for BusinessInfoResponse schema."""

    def test_business_info_response_with_all_fields(self):
        """Test response with all fields (Story 1.11 AC 1, 7)."""
        response = BusinessInfoResponse(
            business_name="Alex's Athletic Gear",
            business_description="Premium athletic equipment",
            business_hours="9 AM - 6 PM PST",
        )

        assert response.business_name == "Alex's Athletic Gear"
        assert response.business_description == "Premium athletic equipment"
        assert response.business_hours == "9 AM - 6 PM PST"

    def test_business_info_response_with_none_values(self):
        """Test response with None values (fields not set)."""
        response = BusinessInfoResponse(
            business_name=None,
            business_description=None,
            business_hours=None,
        )

        assert response.business_name is None
        assert response.business_description is None
        assert response.business_hours is None


class TestBusinessInfoEnvelope:
    """Tests for BusinessInfoEnvelope schema."""

    def test_business_info_envelope_structure(self):
        """Test envelope follows MinimalEnvelope pattern (Story 1.11 AC 7)."""
        business_info = BusinessInfoResponse(
            business_name="Test Store",
            business_description="Test description",
        )

        envelope = BusinessInfoEnvelope(
            data=business_info,
            meta=MetaData(
                request_id="test-123",
                timestamp="2026-02-10T12:00:00Z",
            ),
        )

        assert envelope.data.business_name == "Test Store"
        assert envelope.meta.request_id == "test-123"
        assert envelope.meta.timestamp == "2026-02-10T12:00:00Z"
