"""Tests for FAQ schemas.

Story 1.11: Business Info & FAQ Configuration

Tests Pydantic schema validation for FAQ management.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from app.schemas.faq import (
    FaqRequest,
    FaqResponse,
    FaqListEnvelope,
    FaqEnvelope,
    FaqReorderRequest,
)
from app.schemas.base import MetaData


class TestFaqRequest:
    """Tests for FaqRequest schema."""

    def test_faq_request_with_all_fields(self):
        """Test creating request with all fields (Story 1.11 AC 3, 4, 7)."""
        request = FaqRequest(
            question="What are your shipping options?",
            answer="We offer free shipping on orders over $50.",
            keywords="shipping, delivery, how long",
            order_index=1,
        )

        assert request.question == "What are your shipping options?"
        assert request.answer == "We offer free shipping on orders over $50."
        assert request.keywords == "shipping, delivery, how long"
        assert request.order_index == 1

    def test_faq_request_with_required_fields_only(self):
        """Test creating request with only required fields (Story 1.11 AC 3)."""
        request = FaqRequest(
            question="Do you accept returns?",
            answer="Yes! Returns accepted within 30 days.",
        )

        assert request.question == "Do you accept returns?"
        assert request.answer == "Yes! Returns accepted within 30 days."
        assert request.keywords is None
        assert request.order_index == 0  # Default value

    def test_faq_request_question_required(self):
        """Test question is required (Story 1.11 AC 3)."""
        with pytest.raises(ValidationError) as exc_info:
            FaqRequest(
                question="",
                answer="Some answer",
            )

        assert "question" in str(exc_info.value).lower()

    def test_faq_request_answer_required(self):
        """Test answer is required (Story 1.11 AC 3)."""
        with pytest.raises(ValidationError) as exc_info:
            FaqRequest(
                question="Some question?",
                answer="",
            )

        assert "answer" in str(exc_info.value).lower()

    def test_faq_question_max_length(self):
        """Test question respects 200 character limit (Story 1.11 AC 3)."""
        question_200 = "Q" * 200
        request = FaqRequest(
            question=question_200,
            answer="Test answer",
        )
        assert len(request.question) == 200

    def test_faq_question_exceeds_max_length(self):
        """Test question exceeds 200 characters raises validation error."""
        question_201 = "Q" * 201
        with pytest.raises(ValidationError) as exc_info:
            FaqRequest(
                question=question_201,
                answer="Test answer",
            )

        assert "question" in str(exc_info.value).lower()

    def test_faq_answer_max_length(self):
        """Test answer respects 1000 character limit (Story 1.11 AC 3)."""
        answer_1000 = "A" * 1000
        request = FaqRequest(
            question="Test question?",
            answer=answer_1000,
        )
        assert len(request.answer) == 1000

    def test_faq_answer_exceeds_max_length(self):
        """Test answer exceeds 1000 characters raises validation error."""
        answer_1001 = "A" * 1001
        with pytest.raises(ValidationError) as exc_info:
            FaqRequest(
                question="Test question?",
                answer=answer_1001,
            )

        assert "answer" in str(exc_info.value).lower()

    def test_faq_keywords_max_length(self):
        """Test keywords respects 500 character limit (Story 1.11 AC 3)."""
        keywords_500 = "k" * 500
        request = FaqRequest(
            question="Test question?",
            answer="Test answer",
            keywords=keywords_500,
        )
        assert len(request.keywords) == 500

    def test_faq_keywords_exceeds_max_length(self):
        """Test keywords exceeds 500 characters raises validation error."""
        keywords_501 = "k" * 501
        with pytest.raises(ValidationError) as exc_info:
            FaqRequest(
                question="Test question?",
                answer="Test answer",
                keywords=keywords_501,
            )

        assert "keywords" in str(exc_info.value).lower()

    def test_faq_order_index_minimum(self):
        """Test order_index minimum value is 0."""
        request = FaqRequest(
            question="Test question?",
            answer="Test answer",
            order_index=0,
        )
        assert request.order_index == 0

    def test_faq_order_index_negative_raises_error(self):
        """Test negative order_index raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            FaqRequest(
                question="Test question?",
                answer="Test answer",
                order_index=-1,
            )

        assert "order_index" in str(exc_info.value).lower()

    def test_strip_whitespace_from_fields(self):
        """Test that leading/trailing whitespace is stripped from string fields."""
        request = FaqRequest(
            question="  What are your hours?  ",
            answer="  9 AM - 6 PM  ",
            keywords="  hours, time, open  ",
        )

        assert request.question == "What are your hours?"
        assert request.answer == "9 AM - 6 PM"
        assert request.keywords == "hours, time, open"


class TestFaqResponse:
    """Tests for FaqResponse schema."""

    def test_faq_response_structure(self):
        """Test response structure (Story 1.11 AC 2, 3, 7)."""
        now = datetime.now()
        response = FaqResponse(
            id=1,
            question="What are your shipping options?",
            answer="We offer free shipping on orders over $50.",
            keywords="shipping, delivery",
            order_index=1,
            created_at=now,
            updated_at=now,
        )

        assert response.id == 1
        assert response.question == "What are your shipping options?"
        assert response.answer == "We offer free shipping on orders over $50."
        assert response.keywords == "shipping, delivery"
        assert response.order_index == 1
        assert response.created_at == now
        assert response.updated_at == now

    def test_faq_response_optional_keywords(self):
        """Test response without keywords (optional field)."""
        response = FaqResponse(
            id=1,
            question="Test question?",
            answer="Test answer",
            keywords=None,
            order_index=0,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        assert response.keywords is None


class TestFaqReorderRequest:
    """Tests for FaqReorderRequest schema."""

    def test_faq_reorder_request(self):
        """Test reorder request structure (Story 1.11 AC 2, 7)."""
        request = FaqReorderRequest(faq_ids=[3, 1, 2])

        assert request.faq_ids == [3, 1, 2]

    def test_faq_reorder_request_empty_list_raises_error(self):
        """Test empty list raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            FaqReorderRequest(faq_ids=[])

        assert "faq_ids" in str(exc_info.value).lower()

    def test_faq_reorder_request_single_item(self):
        """Test reorder request with single FAQ."""
        request = FaqReorderRequest(faq_ids=[1])

        assert request.faq_ids == [1]


class TestFaqEnvelope:
    """Tests for FAQ envelope schemas."""

    def test_faq_list_envelope(self):
        """Test FAQ list envelope structure (Story 1.11 AC 2, 7)."""
        faqs = [
            FaqResponse(
                id=1,
                question="Question 1?",
                answer="Answer 1",
                keywords=None,
                order_index=0,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
            FaqResponse(
                id=2,
                question="Question 2?",
                answer="Answer 2",
                keywords="test",
                order_index=1,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
        ]

        envelope = FaqListEnvelope(
            data=faqs,
            meta=MetaData(
                request_id="test-123",
                timestamp="2026-02-10T12:00:00Z",
            ),
        )

        assert len(envelope.data) == 2
        assert envelope.data[0].question == "Question 1?"
        assert envelope.data[1].question == "Question 2?"
        assert envelope.meta.request_id == "test-123"

    def test_faq_envelope_single_item(self):
        """Test single FAQ envelope structure (Story 1.11 AC 7)."""
        faq = FaqResponse(
            id=1,
            question="Test question?",
            answer="Test answer",
            keywords=None,
            order_index=0,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        envelope = FaqEnvelope(
            data=faq,
            meta=MetaData(
                request_id="test-456",
                timestamp="2026-02-10T12:00:00Z",
            ),
        )

        assert envelope.data.id == 1
        assert envelope.data.question == "Test question?"
        assert envelope.meta.request_id == "test-456"
