"""Tests for main FastAPI application."""

import pytest

from app.main import app


class TestMainApp:
    """Test FastAPI application initialization."""

    def test_app_exists(self):
        """Test that FastAPI app is created."""
        assert app is not None
        assert app.title == "Shopping Assistant Bot"

    def test_app_has_routes(self):
        """Test that basic routes are registered."""
        # Note: Full API routes will be added in feature sprints
        assert "/" in [route.path for route in app.routes]
        assert "/health" in [route.path for route in app.routes]

    def test_openapi_schema(self):
        """Test that OpenAPI schema can be generated."""
        schema = app.openapi()
        assert schema is not None
        assert schema["openapi"] == "3.1.0"
        assert "info" in schema

    def test_cors_middleware(self):
        """Test CORS middleware is configured."""
        # Check that CORS middleware is working by making a request
        import httpx
        from httpx import ASGITransport
        import asyncio

        async def check_cors():
            async with httpx.AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                response = await client.get("/", headers={"Origin": "http://localhost:3000"})
                # CORS headers should be present
                return response.headers.get("access-control-allow-credentials") == "true"

        result = asyncio.run(check_cors())
        assert result is True
