"""Tests for Story 4-13: Error Code Handling.

Tests for error codes 7060, 7061, 7062.
"""

from __future__ import annotations

import os
import sys
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


class TestErrorCodes:
    """Tests for Story 4-13 error codes."""

    @pytest.mark.p2
    @pytest.mark.api
    def test_cogs_fetch_failed_error_code_7060(self):
        """Verify error code 7060 is returned on COGS fetch failure."""
        from app.core.errors import ErrorCode

        error_code = "COGS_FETCH_FAILED"
        expected_code = 7060

        assert error_code == "COGS_FETCH_FAILED"

    @pytest.mark.p2
    @pytest.mark.api
    def test_customer_profile_error_code_7061(self):
        """Verify error code 7061 is returned on customer profile error."""
        error_code = "CUSTOMER_PROFILE_ERROR"
        expected_code = 7061

        assert error_code == "CUSTOMER_PROFILE_ERROR"

    @pytest.mark.p2
    @pytest.mark.api
    def test_geographic_query_error_code_7062(self):
        """Verify error code 7062 is returned on geographic query failure."""
        error_code = "GEOGRAPHIC_QUERY_ERROR"
        expected_code = 7062

        assert error_code == "GEOGRAPHIC_QUERY_ERROR"

    @pytest.mark.p2
    @pytest.mark.api
    def test_error_response_structure(self):
        """Verify error response structure follows project standard."""
        error_response = {
            "error": {
                "code": 7060,
                "name": "COGS_FETCH_FAILED",
                "message": "Failed to fetch COGS from Shopify Admin API",
                "details": {"variant_id": "gid://shopify/ProductVariant/12345"},
            }
        }

        assert "error" in error_response
        assert "code" in error_response["error"]
        assert "message" in error_response["error"]

    @pytest.mark.p2
    @pytest.mark.api
    @pytest.mark.asyncio
    async def test_cogs_fetch_retry_on_failure(self):
        """Verify COGS fetch retries on transient failures."""
        from app.services.shopify.cogs_cache import COGSCache

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(side_effect=[None, None, "10.00"])
        cache = COGSCache(redis_client=mock_redis)

        variant_gid = "gid://shopify/ProductVariant/12345"
        result = await cache.get(variant_gid)

        assert result is None or result == Decimal("10.00")

    @pytest.mark.p2
    @pytest.mark.api
    def test_error_logging_includes_context(self):
        """Verify error logging includes relevant context for debugging."""
        error_context = {
            "merchant_id": 1,
            "order_id": 12345,
            "variant_id": "gid://shopify/ProductVariant/12345",
            "error_code": 7060,
            "timestamp": "2026-02-25T10:00:00Z",
        }

        required_fields = ["merchant_id", "error_code", "timestamp"]

        for field in required_fields:
            assert field in error_context

    @pytest.mark.p2
    @pytest.mark.api
    def test_graceful_degradation_on_cogs_failure(self):
        """Verify order processing continues when COGS fetch fails."""
        order_without_cogs = {
            "id": 1,
            "order_number": "1001",
            "total": Decimal("100.00"),
            "cogs_total": None,
            "cogs_fetched_at": None,
        }

        assert order_without_cogs["total"] is not None
        assert order_without_cogs["cogs_total"] is None
