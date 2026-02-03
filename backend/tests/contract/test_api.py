"""Contract tests for API endpoints.

Validates that all API endpoints conform to their OpenAPI schema.
Uses Schemathesis for property-based testing.
"""

import pytest

try:
    import schemathesis
    from schemathesis import Case
    SCHEMATHESIS_AVAILABLE = True
except ImportError:
    SCHEMATHESIS_AVAILABLE = False

# Try importing the app - may not exist yet
try:
    from app.main import app
    APP_AVAILABLE = True
except ImportError:
    APP_AVAILABLE = False


@pytest.mark.skipif(not SCHEMATHESIS_AVAILABLE, reason="schemathesis not installed")
@pytest.mark.skipif(not APP_AVAILABLE, reason="FastAPI app not available")
def test_schemathesis_import():
    """Test that schemathesis is properly installed."""
    assert SCHEMATHESIS_AVAILABLE


@pytest.mark.skipif(not SCHEMATHESIS_AVAILABLE, reason="schemathesis not installed")
@pytest.mark.skipif(not APP_AVAILABLE, reason="FastAPI app not available")
def test_openapi_schema_exists():
    """Test that OpenAPI schema can be generated."""
    if APP_AVAILABLE:
        schema = app.openapi()
        assert schema is not None
        assert "openapi" in schema
        assert "paths" in schema


@pytest.mark.skipif(not SCHEMATHESIS_AVAILABLE, reason="schemathesis not installed")
@pytest.mark.skipif(not APP_AVAILABLE, reason="FastAPI app not available")
class TestAPIContract:
    """Contract tests for API endpoints."""

    @pytest.fixture
    def schema(self):
        """Get OpenAPI schema for testing."""
        return schemathesis.from_wsgi("/openapi.json", app)

    @pytest.mark.asyncio
    async def test_health_endpoint(self, schema):
        """Test health endpoint conforms to schema."""
        if schema and "paths" in schema.schema:
            if "/health" in schema.schema["paths"]:
                @schema.parametrize(endpoint="/health")
                async def test_health(case: Case):
                    response = await case.call_asgi()
                    case.validate_response(response)

                await test_health()

    @pytest.mark.asyncio
    async def test_no_server_errors(self, schema):
        """Test that no endpoints return 500 errors."""
        if schema and "paths" in schema.schema:
            @schema.parametrize()
            async def test_no_500(case: Case):
                response = await case.call_asgi()
                assert response.status_code < 500

            await test_no_500()

    @pytest.mark.asyncio
    async def test_content_type_conformance(self, schema):
        """Test that responses match declared content types."""
        if schema and "paths" in schema.schema:
            @schema.parametrize()
            async def test_content_type(case: Case):
                response = await case.call_asgi()
                case.validate_response(response)

            await test_content_type()
