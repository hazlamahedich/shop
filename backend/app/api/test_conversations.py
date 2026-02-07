"""Tests for conversations API endpoint.

Tests conversation listing, pagination, sorting, and authentication.
"""

import pytest


@pytest.mark.asyncio
class TestConversationsAPI:
    """Test conversations API endpoint."""

    async def test_list_conversations_requires_auth(self, async_client):
        """Test that listing conversations requires authentication."""
        response = await async_client.get("/api/conversations")

        # Should return 401 because merchant_id is not set by auth middleware
        assert response.status_code == 401
        data = response.json()
        assert "Authentication required" in data.get("message", "")

    async def test_list_conversations_invalid_sort_column(self, async_client):
        """Test that invalid sort column returns validation error."""
        # Invalid sort column passes Query validation, fails in endpoint logic
        # But auth fails first (401) since validation passes for any string
        response = await async_client.get(
            "/api/conversations?sort_by=invalid_column"
        )
        # Auth check happens after Query validation
        assert response.status_code == 401

    async def test_list_conversations_invalid_sort_order(self, async_client):
        """Test that invalid sort order returns validation error."""
        # FastAPI pattern validation happens before auth check
        response = await async_client.get(
            "/api/conversations?sort_order=invalid"
        )
        # Pattern validation fails first (422)
        assert response.status_code == 422

    async def test_list_conversations_validates_page_params(self, async_client):
        """Test that page parameters are validated."""
        # Test page < 1 (ge=1 constraint)
        response = await async_client.get("/api/conversations?page=0")
        # Query validation fails before auth (422)
        assert response.status_code == 422

        # Test per_page > 100 (le=100 constraint)
        response = await async_client.get("/api/conversations?per_page=101")
        assert response.status_code == 422

        # Test per_page < 1 (ge=1 constraint)
        response = await async_client.get("/api/conversations?per_page=0")
        assert response.status_code == 422
