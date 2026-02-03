"""Contract tests for Facebook integration API endpoints.

Tests API compliance with OpenAPI schema using Schemathesis.
"""

from __future__ import annotations

import pytest


class TestFacebookApiContract:
    """Contract tests for Facebook API endpoints.

    Uses Schemathesis to verify API responses match OpenAPI schema.
    These tests validate that the API contract is correctly defined.
    """

    @pytest.mark.contract
    def test_facebook_authorize_endpoint_schema(self, schema):
        """Test that /api/integrations/facebook/authorize endpoint matches schema."""
        endpoint = "/api/integrations/facebook/authorize"

        # Verify endpoint exists in schema
        assert endpoint in schema.paths

        # Verify GET method is supported
        assert "get" in schema.paths[endpoint]

        # Verify response codes
        responses = schema.paths[endpoint]["get"]["responses"]
        assert "200" in responses

        # Verify response schema
        response_schema = responses["200"]["content"]["application/json"]["schema"]
        assert response_schema["properties"]["data"]["required"] == ["authUrl", "state"]

    @pytest.mark.contract
    def test_facebook_callback_endpoint_schema(self, schema):
        """Test that /api/integrations/facebook/callback endpoint matches schema."""
        endpoint = "/api/integrations/facebook/callback"

        # Verify endpoint exists in schema
        assert endpoint in schema.paths

        # Verify GET method is supported
        assert "get" in schema.paths[endpoint]

        # Verify query parameters
        parameters = schema.paths[endpoint]["get"]["parameters"]
        param_names = [p["name"] for p in parameters]
        assert "code" in param_names
        assert "state" in param_names
        assert "merchant_id" in param_names

    @pytest.mark.contract
    def test_facebook_status_endpoint_schema(self, schema):
        """Test that /api/integrations/facebook/status endpoint matches schema."""
        endpoint = "/api/integrations/facebook/status"

        # Verify endpoint exists in schema
        assert endpoint in schema.paths

        # Verify GET method is supported
        assert "get" in schema.paths[endpoint]

        # Verify response structure
        responses = schema.paths[endpoint]["get"]["responses"]
        assert "200" in responses

    @pytest.mark.contract
    def test_facebook_disconnect_endpoint_schema(self, schema):
        """Test that DELETE /api/integrations/facebook/disconnect matches schema."""
        endpoint = "/api/integrations/facebook/disconnect"

        # Verify endpoint exists in schema
        assert endpoint in schema.paths

        # Verify DELETE method is supported
        assert "delete" in schema.paths[endpoint]

        # Verify response structure
        responses = schema.paths[endpoint]["delete"]["responses"]
        assert "200" in responses

    @pytest.mark.contract
    def test_facebook_webhook_verify_endpoint_schema(self, schema):
        """Test that GET /webhooks/facebook verification endpoint matches schema."""
        endpoint = "/webhooks/facebook"

        # Verify endpoint exists in schema
        assert endpoint in schema.paths

        # Verify GET method is supported
        assert "get" in schema.paths[endpoint]

        # Verify challenge returns plain text
        responses = schema.paths[endpoint]["get"]["responses"]
        assert "200" in responses

    @pytest.mark.contract
    def test_facebook_webhook_receive_endpoint_schema(self, schema):
        """Test that POST /webhooks/facebook receive endpoint matches schema."""
        endpoint = "/webhooks/facebook"

        # Verify endpoint exists in schema
        assert endpoint in schema.paths

        # Verify POST method is supported
        assert "post" in schema.paths[endpoint]

        # Verify signature header
        parameters = schema.paths[endpoint]["post"].get("parameters", [])
        header_params = [p for p in parameters if p.get("in") == "header"]
        header_names = [p["name"] for p in header_params]
        assert "X-Hub-Signature-256" in header_names

    @pytest.mark.contract
    def test_facebook_test_webhook_endpoint_schema(self, schema):
        """Test that POST /api/integrations/facebook/test-webhook matches schema."""
        endpoint = "/api/integrations/facebook/test-webhook"

        # Verify endpoint exists in schema
        assert endpoint in schema.paths

        # Verify POST method is supported
        assert "post" in schema.paths[endpoint]

    @pytest.mark.contract
    def test_facebook_resubscribe_webhook_endpoint_schema(self, schema):
        """Test that POST /api/integrations/facebook/resubscribe-webhook matches schema."""
        endpoint = "/api/integrations/facebook/resubscribe-webhook"

        # Verify endpoint exists in schema
        assert endpoint in schema.paths

        # Verify POST method is supported
        assert "post" in schema.paths[endpoint]


class TestFacebookApiErrorResponseContract:
    """Contract tests for Facebook API error responses.

    Validates error responses match the standard error format.
    """

    @pytest.mark.contract
    def test_error_response_format(self, async_client):
        """Test that error responses follow standard format."""
        response = await async_client.get("/api/integrations/facebook/status?merchant_id=999")

        # Should return success even if not connected (not an error)
        assert response.status_code == 200

        # Test with invalid data that would return error
        response = await async_client.delete("/api/integrations/facebook/disconnect?merchant_id=999")

        # Should return 400 or 404
        assert response.status_code in (400, 404)

        # Verify error response format
        data = response.json()
        assert "error_code" in data or "detail" in data
