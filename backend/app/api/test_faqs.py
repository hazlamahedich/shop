"""Tests for FAQ Management API endpoints.

Story 1.11: Business Info & FAQ Configuration

Tests FAQ CRUD operations.
"""

from __future__ import annotations

import pytest


class TestFaqListApi:
    """Tests for FAQ list endpoint."""

    @pytest.fixture
    def merchant_headers(self):
        """Get merchant authentication headers for DEBUG mode."""
        return {"X-Merchant-Id": "1"}

    @pytest.mark.asyncio
    async def test_list_faqs_success(
        self,
        async_client,
        merchant,
        merchant_headers: dict,
    ):
        """Test GET /api/v1/merchant/faqs returns list of FAQs."""
        response = await async_client.get(
            "/api/v1/merchant/faqs",
            headers=merchant_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "meta" in data
        assert isinstance(data["data"], list)

    @pytest.mark.asyncio
    async def test_list_faqs_returns_empty_list_initially(
        self,
        async_client,
        merchant,
        merchant_headers: dict,
    ):
        """Test GET returns empty list when no FAQs exist."""
        response = await async_client.get(
            "/api/v1/merchant/faqs",
            headers=merchant_headers,
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 0


class TestCreateFaqApi:
    """Tests for FAQ creation endpoint."""

    @pytest.fixture
    def merchant_headers(self):
        """Get merchant authentication headers for DEBUG mode."""
        return {"X-Merchant-Id": "1"}

    @pytest.mark.asyncio
    async def test_create_faq_success(
        self,
        async_client,
        merchant,
        merchant_headers: dict,
    ):
        """Test POST /api/v1/merchant/faqs creates new FAQ."""
        faq_data = {
            "question": "What are your hours?",
            "answer": "9 AM - 5 PM, Mon-Fri",
            "keywords": "hours, time, open",
        }

        response = await async_client.post(
            "/api/v1/merchant/faqs",
            headers=merchant_headers,
            json=faq_data,
        )

        assert response.status_code == 201
        data = response.json()["data"]
        assert data["question"] == "What are your hours?"
        assert data["answer"] == "9 AM - 5 PM, Mon-Fri"
        assert data["keywords"] == "hours, time, open"
        assert "id" in data
        assert "orderIndex" in data

    @pytest.mark.asyncio
    async def test_create_faq_with_minimal_fields(
        self,
        async_client,
        merchant,
        merchant_headers: dict,
    ):
        """Test POST with only required fields (question, answer)."""
        faq_data = {
            "question": "Do you accept returns?",
            "answer": "Yes, within 30 days.",
        }

        response = await async_client.post(
            "/api/v1/merchant/faqs",
            headers=merchant_headers,
            json=faq_data,
        )

        assert response.status_code == 201
        data = response.json()["data"]
        assert data["question"] == "Do you accept returns?"
        assert data["answer"] == "Yes, within 30 days."
        assert data["keywords"] is None
        assert data["orderIndex"] == 0  # First FAQ

    @pytest.mark.asyncio
    async def test_create_faq_validation_question_required(
        self,
        async_client,
        merchant,
        merchant_headers: dict,
    ):
        """Test POST validates question is required."""
        faq_data = {
            "answer": "Some answer",
        }

        response = await async_client.post(
            "/api/v1/merchant/faqs",
            headers=merchant_headers,
            json=faq_data,
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_create_faq_validation_answer_required(
        self,
        async_client,
        merchant,
        merchant_headers: dict,
    ):
        """Test POST validates answer is required."""
        faq_data = {
            "question": "What are your hours?",
        }

        response = await async_client.post(
            "/api/v1/merchant/faqs",
            headers=merchant_headers,
            json=faq_data,
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_create_faq_validation_max_lengths(
        self,
        async_client,
        merchant,
        merchant_headers: dict,
    ):
        """Test POST validates field max lengths."""
        faq_data = {
            "question": "Q" * 201,  # Max is 200
            "answer": "A" * 1001,  # Max is 1000
        }

        response = await async_client.post(
            "/api/v1/merchant/faqs",
            headers=merchant_headers,
            json=faq_data,
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_create_faq_whitespace_stripped(
        self,
        async_client,
        merchant,
        merchant_headers: dict,
    ):
        """Test POST strips whitespace from fields."""
        faq_data = {
            "question": "  What are your hours?  ",
            "answer": "  9 AM - 5 PM  ",
            "keywords": "  hours, time  ",
        }

        response = await async_client.post(
            "/api/v1/merchant/faqs",
            headers=merchant_headers,
            json=faq_data,
        )

        assert response.status_code == 201
        data = response.json()["data"]
        assert data["question"] == "What are your hours?"
        assert data["answer"] == "9 AM - 5 PM"
        assert data["keywords"] == "hours, time"


class TestUpdateFaqApi:
    """Tests for FAQ update endpoint."""

    @pytest.fixture
    def merchant_headers(self):
        """Get merchant authentication headers for DEBUG mode."""
        return {"X-Merchant-Id": "1"}

    @pytest.mark.asyncio
    async def test_update_faq_success(
        self,
        async_client,
        merchant,
        merchant_headers: dict,
    ):
        """Test PUT /api/v1/merchant/faqs/{faq_id} updates FAQ."""
        # First create an FAQ
        create_response = await async_client.post(
            "/api/v1/merchant/faqs",
            headers=merchant_headers,
            json={
                "question": "Original question?",
                "answer": "Original answer",
            },
        )
        faq_id = create_response.json()["data"]["id"]

        # Now update it
        update_data = {
            "question": "Updated question?",
            "answer": "Updated answer",
            "keywords": "test",
        }

        response = await async_client.put(
            f"/api/v1/merchant/faqs/{faq_id}",
            headers=merchant_headers,
            json=update_data,
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["question"] == "Updated question?"
        assert data["answer"] == "Updated answer"
        assert data["keywords"] == "test"

    @pytest.mark.asyncio
    async def test_update_faq_partial_update(
        self,
        async_client,
        merchant,
        merchant_headers: dict,
    ):
        """Test PUT with partial fields updates only provided fields."""
        # First create an FAQ
        create_response = await async_client.post(
            "/api/v1/merchant/faqs",
            headers=merchant_headers,
            json={
                "question": "Question?",
                "answer": "Answer",
                "keywords": "original",
            },
        )
        faq_id = create_response.json()["data"]["id"]

        # Update only answer
        response = await async_client.put(
            f"/api/v1/merchant/faqs/{faq_id}",
            headers=merchant_headers,
            json={
                "answer": "New answer",
            },
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["question"] == "Question?"  # Unchanged
        assert data["answer"] == "New answer"
        assert data["keywords"] == "original"  # Unchanged

    @pytest.mark.asyncio
    async def test_update_faq_not_found(
        self,
        async_client,
        merchant,
        merchant_headers: dict,
    ):
        """Test PUT with non-existent FAQ ID returns 404."""
        response = await async_client.put(
            "/api/v1/merchant/faqs/99999",
            headers=merchant_headers,
            json={
                "question": "Updated?",
                "answer": "Updated",
            },
        )

        assert response.status_code == 404


class TestDeleteFaqApi:
    """Tests for FAQ delete endpoint."""

    @pytest.fixture
    def merchant_headers(self):
        """Get merchant authentication headers for DEBUG mode."""
        return {"X-Merchant-Id": "1"}

    @pytest.mark.asyncio
    async def test_delete_faq_success(
        self,
        async_client,
        merchant,
        merchant_headers: dict,
    ):
        """Test DELETE /api/v1/merchant/faqs/{faq_id} deletes FAQ."""
        # First create an FAQ
        create_response = await async_client.post(
            "/api/v1/merchant/faqs",
            headers=merchant_headers,
            json={
                "question": "To be deleted?",
                "answer": "Will be deleted",
            },
        )
        faq_id = create_response.json()["data"]["id"]

        # Delete it
        response = await async_client.delete(
            f"/api/v1/merchant/faqs/{faq_id}",
            headers=merchant_headers,
        )

        assert response.status_code == 204

        # Verify it's deleted
        get_response = await async_client.get(
            "/api/v1/merchant/faqs",
            headers=merchant_headers,
        )
        faqs = get_response.json()["data"]
        assert len(faqs) == 0

    @pytest.mark.asyncio
    async def test_delete_faq_not_found(
        self,
        async_client,
        merchant,
        merchant_headers: dict,
    ):
        """Test DELETE with non-existent FAQ ID returns 404."""
        response = await async_client.delete(
            "/api/v1/merchant/faqs/99999",
            headers=merchant_headers,
        )

        assert response.status_code == 404


class TestReorderFaqsApi:
    """Tests for FAQ reorder endpoint."""

    @pytest.fixture
    def merchant_headers(self):
        """Get merchant authentication headers for DEBUG mode."""
        return {"X-Merchant-Id": "1"}

    @pytest.mark.asyncio
    async def test_reorder_faqs_success(
        self,
        async_client,
        merchant,
        merchant_headers: dict,
    ):
        """Test PUT /api/v1/merchant/faqs/reorder reorders FAQs."""
        # Create multiple FAQs
        faq_ids = []
        for i in range(3):
            response = await async_client.post(
                "/api/v1/merchant/faqs",
                headers=merchant_headers,
                json={
                    "question": f"Question {i}?",
                    "answer": f"Answer {i}",
                },
            )
            faq_ids.append(response.json()["data"]["id"])

        # Reorder in reverse
        reorder_data = {
            "faq_ids": [faq_ids[2], faq_ids[1], faq_ids[0]],
        }

        response = await async_client.put(
            "/api/v1/merchant/faqs/reorder",
            headers=merchant_headers,
            json=reorder_data,
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data[0]["id"] == faq_ids[2]
        assert data[1]["id"] == faq_ids[1]
        assert data[2]["id"] == faq_ids[0]

    @pytest.mark.asyncio
    async def test_reorder_faqs_empty_list_fails(
        self,
        async_client,
        merchant,
        merchant_headers: dict,
    ):
        """Test PUT with empty list returns validation error."""
        response = await async_client.put(
            "/api/v1/merchant/faqs/reorder",
            headers=merchant_headers,
            json={"faq_ids": []},
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_reorder_faqs_invalid_faq_id_fails(
        self,
        async_client,
        merchant,
        merchant_headers: dict,
    ):
        """Test PUT with invalid FAQ ID returns error."""
        response = await async_client.put(
            "/api/v1/merchant/faqs/reorder",
            headers=merchant_headers,
            json={"faq_ids": [99999]},
        )

        assert response.status_code == 404
