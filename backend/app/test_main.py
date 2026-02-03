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
        # Check that CORS middleware is added
        middleware_types = [type(m).__name__ for m in app.user_middleware]
        # CORSMiddleware should be present
        assert "CORSMiddleware" in middleware_types
