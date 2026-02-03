"""API tests for onboarding endpoints.

Tests prerequisite validation for merchant onboarding using httpx.AsyncClient.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_check_prerequisites_happy_path() -> None:
    """Test GET /prerequisites/check succeeds when all prerequisites complete."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/onboarding/prerequisites/check",
            params={
                "cloudAccount": True,
                "facebookAccount": True,
                "shopifyAccess": True,
                "llmProviderChoice": True,
            },
        )

        # Assert response structure
        assert response.status_code == 200
        data = response.json()
        
        # Validate envelope structure
        assert "data" in data
        assert "meta" in data
        
        # Validate response data
        assert data["data"]["isComplete"] is True
        assert data["data"]["missing"] == []
        
        # Validate metadata
        assert "requestId" in data["meta"]
        assert "timestamp" in data["meta"]
        assert data["meta"]["timestamp"].endswith("Z")  # ISO-8601 format


@pytest.mark.asyncio
async def test_check_prerequisites_single_missing() -> None:
    """Test GET /prerequisites/check raises error for single missing prerequisite."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/onboarding/prerequisites/check",
            params={
                "cloudAccount": True,
                "facebookAccount": True,
                "shopifyAccess": True,
                "llmProviderChoice": False,
            },
        )

        assert response.status_code == 400
        data = response.json()
        
        # Verify error structure
        assert "error_code" in data
        assert "message" in data
        assert "details" in data
        
        # Verify error code
        assert data["error_code"] == 2004  # PREREQUISITES_INCOMPLETE
        
        # Verify error message
        assert "Complete all prerequisites before deployment" in data["message"]
        
        # Verify missing prerequisites
        assert "missing" in data["details"]
        assert len(data["details"]["missing"]) == 1
        assert "llmProviderChoice" in data["details"]["missing"]


@pytest.mark.asyncio
async def test_check_prerequisites_multiple_missing() -> None:
    """Test GET /prerequisites/check raises error with multiple missing prerequisites."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/onboarding/prerequisites/check",
            params={
                "cloudAccount": False,
                "facebookAccount": True,
                "shopifyAccess": False,
                "llmProviderChoice": True,
            },
        )

        assert response.status_code == 400
        data = response.json()
        
        assert data["error_code"] == 2004
        assert len(data["details"]["missing"]) == 2
        expected_missing = {"cloudAccount", "shopifyAccess"}
        assert set(data["details"]["missing"]) == expected_missing


@pytest.mark.asyncio
async def test_check_prerequisites_all_missing() -> None:
    """Test GET /prerequisites/check raises error when no prerequisites complete."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/onboarding/prerequisites/check",
            params={
                "cloudAccount": False,
                "facebookAccount": False,
                "shopifyAccess": False,
                "llmProviderChoice": False,
            },
        )

        assert response.status_code == 400
        data = response.json()
        
        assert data["error_code"] == 2004
        assert len(data["details"]["missing"]) == 4
        expected_missing = {
            "cloudAccount",
            "facebookAccount", 
            "shopifyAccess",
            "llmProviderChoice"
        }
        assert set(data["details"]["missing"]) == expected_missing


@pytest.mark.asyncio
async def test_validate_prerequisites_happy_path() -> None:
    """Test POST /prerequisites/validate succeeds with all prerequisites complete."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/onboarding/prerequisites/validate",
            json={
                "cloudAccount": True,
                "facebookAccount": True,
                "shopifyAccess": True,
                "llmProviderChoice": True,
            },
        )

        assert response.status_code == 200
        data = response.json()
        
        # Validate envelope structure
        assert "data" in data
        assert "meta" in data
        
        # Validate response data
        assert data["data"]["isComplete"] is True
        assert data["data"]["missing"] == []
        
        # Validate metadata
        assert "requestId" in data["meta"]
        assert "timestamp" in data["meta"]


@pytest.mark.asyncio
async def test_validate_prerequisites_single_missing() -> None:
    """Test POST /prerequisites/validate returns single missing prerequisite."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/onboarding/prerequisites/validate",
            json={
                "cloudAccount": True,
                "facebookAccount": False,
                "shopifyAccess": True,
                "llmProviderChoice": True,
            },
        )

        assert response.status_code == 200
        data = response.json()
        
        assert data["data"]["isComplete"] is False
        assert len(data["data"]["missing"]) == 1
        assert "facebookAccount" in data["data"]["missing"]


@pytest.mark.asyncio
async def test_validate_prerequisites_multiple_missing() -> None:
    """Test POST /prerequisites/validate returns multiple missing prerequisites."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/onboarding/prerequisites/validate",
            json={
                "cloudAccount": False,
                "facebookAccount": True,
                "shopifyAccess": False,
                "llmProviderChoice": True,
            },
        )

        assert response.status_code == 200
        data = response.json()
        
        assert data["data"]["isComplete"] is False
        assert len(data["data"]["missing"]) == 2
        expected_missing = {"cloudAccount", "shopifyAccess"}
        assert set(data["data"]["missing"]) == expected_missing


@pytest.mark.asyncio
async def test_validate_prerequisites_all_missing() -> None:
    """Test POST /prerequisites/validate returns all missing prerequisites."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/onboarding/prerequisites/validate",
            json={
                "cloudAccount": False,
                "facebookAccount": False,
                "shopifyAccess": False,
                "llmProviderChoice": False,
            },
        )

        assert response.status_code == 200
        data = response.json()
        
        assert data["data"]["isComplete"] is False
        assert len(data["data"]["missing"]) == 4
        expected_missing = {
            "cloudAccount",
            "facebookAccount",
            "shopifyAccess",
            "llmProviderChoice"
        }
        assert set(data["data"]["missing"]) == expected_missing


@pytest.mark.asyncio
async def test_validate_prerequisites_empty_request() -> None:
    """Test POST /prerequisites/validate with empty JSON body returns validation error."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/onboarding/prerequisites/validate",
            json={},
        )

        # Should fail with 422 due to validation error
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data


@pytest.mark.asyncio
async def test_check_prerequisites_defaults_to_false() -> None:
    """Test GET /prerequisites/check with no params defaults all to False."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/onboarding/prerequisites/check")

        assert response.status_code == 400
        data = response.json()
        
        assert data["error_code"] == 2004
        assert len(data["details"]["missing"]) == 4
        expected_missing = {
            "cloudAccount",
            "facebookAccount",
            "shopifyAccess",
            "llmProviderChoice"
        }
        assert set(data["details"]["missing"]) == expected_missing


@pytest.mark.asyncio
async def test_response_metadata_consistency_success_path() -> None:
    """Test that metadata is consistent across requests for successful responses."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Make two requests and compare metadata structure
        response1 = await client.get(
            "/api/onboarding/prerequisites/check",
            params={"cloudAccount": True, "facebookAccount": True, "shopifyAccess": True, "llmProviderChoice": True}
        )
        response2 = await client.post(
            "/api/onboarding/prerequisites/validate",
            json={"cloudAccount": True, "facebookAccount": True, "shopifyAccess": True, "llmProviderChoice": True}
        )

        data1 = response1.json()
        data2 = response2.json()

        # Both should have the same metadata structure
        for key in ["requestId", "timestamp"]:
            assert key in data1["meta"]
            assert key in data2["meta"]
        
        # Timestamps should be different
        assert data1["meta"]["timestamp"] != data2["meta"]["timestamp"]
        
        # Request IDs should be different
        assert data1["meta"]["requestId"] != data2["meta"]["requestId"]


@pytest.mark.asyncio
async def test_check_prerequisites_error_details_structure() -> None:
    """Test that error details have correct structure."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/onboarding/prerequisites/check",
            params={
                "cloudAccount": False,
                "facebookAccount": True,
                "shopifyAccess": False,
                "llmProviderChoice": True,
            },
        )

        assert response.status_code == 400
        data = response.json()
        
        # Verify error details structure
        assert "error_code" in data
        assert "message" in data
        assert "details" in data
        assert "missing" in data["details"]
        
        # Error code should be integer
        assert isinstance(data["error_code"], int)
        
        # Message should be string
        assert isinstance(data["message"], str)
        
        # Missing should be list
        assert isinstance(data["details"]["missing"], list)


@pytest.mark.asyncio
async def test_validate_string_boolean_conversion() -> None:
    """Test that string booleans are properly converted by Pydantic."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Test with string representations of booleans
        response = await client.post(
            "/api/onboarding/prerequisites/validate",
            json={
                "cloudAccount": "true",  # String "true" becomes True
                "facebookAccount": "false",  # String "false" becomes False
                "shopifyAccess": True,
                "llmProviderChoice": "1",  # String "1" is truthy
            },
        )

        assert response.status_code == 200
        data = response.json()
        
        # "true" -> True, "false" -> False, True -> True, "1" -> True
        # Only facebookAccount should be missing
        assert data["data"]["isComplete"] is False
        assert len(data["data"]["missing"]) == 1
        assert "facebookAccount" in data["data"]["missing"]


@pytest.mark.asyncio
async def test_check_prerequisites_individual_prerequisites() -> None:
    """Test each prerequisite individually in the check endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Test each missing prerequisite one by one
        prerequisites = ["cloudAccount", "facebookAccount", "shopifyAccess", "llmProviderChoice"]
        
        for prereq in prerequisites:
            # Set all to True except the current one
            params = {
                "cloudAccount": True,
                "facebookAccount": True,
                "shopifyAccess": True,
                "llmProviderChoice": True,
            }
            params[prereq] = False
            
            response = await client.get("/api/onboarding/prerequisites/check", params=params)
            assert response.status_code == 400
            data = response.json()
            assert data["error_code"] == 2004
            assert data["details"]["missing"] == [prereq]
