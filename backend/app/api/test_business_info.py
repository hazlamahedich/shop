"""Tests for Business Info API endpoints.

Story 1.11: Business Info & FAQ Configuration

Tests business info CRUD operations.
"""

from __future__ import annotations

import pytest


class TestBusinessInfoApi:
    """Tests for business info API endpoints."""

    @pytest.fixture
    def merchant_headers(self):
        """Get merchant authentication headers for DEBUG mode."""
        return {"X-Merchant-Id": "1"}

    @pytest.mark.asyncio
    async def test_get_business_info_success(
        self,
        async_client,
        merchant,
        merchant_headers: dict,
    ):
        """Test GET /api/v1/merchant/business-info returns business information."""
        response = await async_client.get(
            "/api/v1/merchant/business-info",
            headers=merchant_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "meta" in data
        assert "requestId" in data["meta"]
        assert "timestamp" in data["meta"]

    @pytest.mark.asyncio
    async def test_get_business_info_returns_merchant_data(
        self,
        async_client,
        merchant,
        merchant_headers: dict,
    ):
        """Test GET returns merchant's business information."""
        response = await async_client.get(
            "/api/v1/merchant/business-info",
            headers=merchant_headers,
        )

        assert response.status_code == 200
        data = response.json()["data"]
        # Fields may be None initially
        assert "businessName" in data
        assert "businessDescription" in data
        assert "businessHours" in data

    @pytest.mark.asyncio
    async def test_update_business_info_success(
        self,
        async_client,
        merchant,
        merchant_headers: dict,
    ):
        """Test PUT /api/v1/merchant/business-info updates business information."""
        update_data = {
            "business_name": "Test Store",
            "business_description": "We sell test products",
            "business_hours": "9 AM - 5 PM",
        }

        response = await async_client.put(
            "/api/v1/merchant/business-info",
            headers=merchant_headers,
            json=update_data,
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["businessName"] == "Test Store"
        assert data["businessDescription"] == "We sell test products"
        assert data["businessHours"] == "9 AM - 5 PM"

    @pytest.mark.asyncio
    async def test_update_business_info_partial_update(
        self,
        async_client,
        merchant,
        merchant_headers: dict,
    ):
        """Test PUT with partial fields updates only provided fields."""
        update_data = {
            "business_name": "Partial Update Store",
        }

        response = await async_client.put(
            "/api/v1/merchant/business-info",
            headers=merchant_headers,
            json=update_data,
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["businessName"] == "Partial Update Store"

    @pytest.mark.asyncio
    async def test_update_business_info_whitespace_stripped(
        self,
        async_client,
        merchant,
        merchant_headers: dict,
    ):
        """Test PUT strips whitespace from field values."""
        update_data = {
            "business_name": "  Whitespace Store  ",
            "business_description": "  Description with spaces  ",
        }

        response = await async_client.put(
            "/api/v1/merchant/business-info",
            headers=merchant_headers,
            json=update_data,
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["businessName"] == "Whitespace Store"
        assert data["businessDescription"] == "Description with spaces"

    @pytest.mark.asyncio
    async def test_update_business_info_validation_max_length(
        self,
        async_client,
        merchant,
        merchant_headers: dict,
    ):
        """Test PUT validates field max lengths."""
        update_data = {
            "business_name": "A" * 101,  # Max is 100
        }

        response = await async_client.put(
            "/api/v1/merchant/business-info",
            headers=merchant_headers,
            json=update_data,
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_update_business_info_empty_string_becomes_none(
        self,
        async_client,
        merchant,
        merchant_headers: dict,
    ):
        """Test PUT with empty strings converts them to None."""
        # First set some values
        await async_client.put(
            "/api/v1/merchant/business-info",
            headers=merchant_headers,
            json={
                "business_name": "Test",
                "business_description": "Test description",
            },
        )

        # Then clear with empty strings
        response = await async_client.put(
            "/api/v1/merchant/business-info",
            headers=merchant_headers,
            json={
                "business_name": "   ",
                "business_description": "",
            },
        )

        assert response.status_code == 200
        data = response.json()["data"]
        # Empty strings after stripping should become None
        assert data.get("businessName") is None or data.get("businessName") == ""
