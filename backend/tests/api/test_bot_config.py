"""API tests for greeting configuration endpoints (Story 1.14).

Tests greeting config GET/PUT endpoints, validation errors,
and authentication requirements.

Uses proper integration test patterns matching the project.
"""

from __future__ import annotations

import pytest
import httpx
from sqlalchemy import text

from app.main import app
from app.models.merchant import Merchant, PersonalityType
from tests.conftest import test_engine, TestingSessionLocal


# Test merchant fixture data matching merchant table schema
class TestMerchantData:
    """Test merchant data matching merchant model schema."""
    id = 1
    merchant_key = "test-greeting-config"
    platform = "facebook"
    merchant_status = "active"
    personality_type = PersonalityType.FRIENDLY
    bot_name = "TestBot"
    business_name = "Test Business"
    custom_greeting = "Hello! Welcome!"
    use_custom_greeting = False


@pytest.mark.asyncio
async def test_get_greeting_config_success():
    """Test GET greeting-config returns current configuration."""
    # Create test merchant using proper column names
    async with test_engine.begin() as conn:
        await conn.execute(text(
            "INSERT INTO merchants "
            "(id, merchant_key, platform, merchant_status, personality_type, bot_name, business_name, custom_greeting, use_custom_greeting) "
            "VALUES (:id, :merchant_key, :platform, :merchant_status, :personality, :bot_name, :business_name, :custom_greeting, :use_custom_greeting)"
        ), {
            "id": TestMerchantData.id,
            "merchant_key": TestMerchantData.merchant_key,
            "platform": TestMerchantData.platform,
            "merchant_status": TestMerchantData.merchant_status,
            "personality": TestMerchantData.personality_type.value,
            "bot_name": TestMerchantData.bot_name,
            "business_name": TestMerchantData.business_name,
            "custom_greeting": TestMerchantData.custom_greeting,
            "use_custom_greeting": TestMerchantData.use_custom_greeting,
        })
        await conn.commit()

    # Create client
    from app.core.database import get_db

    async def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            await session.close()

    app.dependency_overrides[get_db] = override_get_db

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/api/v1/merchant/greeting-config")

    app.dependency_overrides.clear()

    assert response.status_code == 200

    data = response.json()
    assert "data" in data
    assert "meta" in data

    # Validate response structure
    greeting_data = data["data"]
    assert greeting_data["greeting_template"] == "Hello! Welcome!"
    assert greeting_data["use_custom_greeting"] is False
    assert greeting_data["personality"] == "friendly"
    assert greeting_data["default_template"] is not None
    assert greeting_data["available_variables"] == ["bot_name", "business_name", "business_hours"]

    # Validate metadata
    meta = data["meta"]
    assert "requestId" in meta
    assert "timestamp" in meta


@pytest.mark.asyncio
async def test_get_greeting_config_without_authentication_fails():
    """Test GET greeting-config requires authentication."""
    async with httpx.AsyncClient(base_url="http://test") as client:
        response = await client.get("/api/v1/merchant/greeting-config")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_greeting_config_response_structure():
    """Test GET greeting-config response has correct envelope structure."""
    # Create test merchant
    async with test_engine.begin() as conn:
        await conn.execute(text(
            "INSERT INTO merchants "
            "(id, merchant_key, platform, merchant_status, personality_type, bot_name, business_name, custom_greeting, use_custom_greeting) "
            "VALUES (:id, :merchant_key, :platform, :merchant_status, :personality, :bot_name, :business_name, :custom_greeting, :use_custom_greeting)"
        ), {
            "id": TestMerchantData.id,
            "merchant_key": TestMerchantData.merchant_key,
            "platform": TestMerchantData.platform,
            "merchant_status": TestMerchantData.merchant_status,
            "personality": TestMerchantData.personality_type.value,
            "bot_name": TestMerchantData.bot_name,
            "business_name": TestMerchantData.business_name,
            "custom_greeting": TestMerchantData.custom_greeting,
            "use_custom_greeting": TestMerchantData.use_custom_greeting,
        })
        await conn.commit()

    # Create client
    from app.core.database import get_db

    async def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            await session.close()

    app.dependency_overrides[get_db] = override_get_db

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/api/v1/merchant/greeting-config")

    app.dependency_overrides.clear()

    # Verify envelope structure
    assert response.status_code == 200

    data = response.json()
    assert "data" in data
    assert "meta" in data
    assert "requestId" in data["meta"]
    assert "timestamp" in data["meta"]


@pytest.mark.asyncio
async def test_update_greeting_config_custom_greeting_success():
    """Test PUT greeting-config with custom greeting succeeds."""
    # Create test merchant
    async with test_engine.begin() as conn:
        await conn.execute(text(
            "INSERT INTO merchants "
            "(id, merchant_key, platform, merchant_status, personality_type, bot_name, business_name, custom_greeting, use_custom_greeting) "
            "VALUES (:id, :merchant_key, :platform, :merchant_status, :personality, :bot_name, :business_name, :custom_greeting, :use_custom_greeting)"
        ), {
            "id": TestMerchantData.id,
            "merchant_key": TestMerchantData.merchant_key,
            "platform": TestMerchantData.platform,
            "merchant_status": TestMerchantData.merchant_status,
            "personality": TestMerchantData.personality_type.value,
            "bot_name": TestMerchantData.bot_name,
            "business_name": TestMerchantData.business_name,
            "custom_greeting": TestMerchantData.custom_greeting,
            "use_custom_greeting": TestMerchantData.use_custom_greeting,
        })
        await conn.commit()

    # Create client
    from app.core.database import get_db

    async def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            await session.close()

    app.dependency_overrides[get_db] = override_get_db

    update_data = {
        "greeting_template": "Hi! Welcome to our store!",
        "use_custom_greeting": True,
    }

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.put("/api/v1/merchant/greeting-config", json=update_data)

    app.dependency_overrides.clear()

    assert response.status_code == 200

    data = response.json()
    assert "data" in data
    assert "meta" in data

    greeting_data = data["data"]
    assert greeting_data["greeting_template"] == "Hi! Welcome to our store!"
    assert greeting_data["use_custom_greeting"] is True


@pytest.mark.asyncio
async def test_update_greeting_config_empty_greeting_raises_validation_error():
    """Test PUT greeting-config with empty template raises validation error."""
    # Create test merchant
    async with test_engine.begin() as conn:
        await conn.execute(text(
            "INSERT INTO merchants "
            "(id, merchant_key, platform, merchant_status, personality_type, bot_name, business_name) "
            "VALUES (:id, :merchant_key, :platform, :merchant_status, :personality, :bot_name, :business_name)"
        ), {
            "id": TestMerchantData.id,
            "merchant_key": TestMerchantData.merchant_key,
            "platform": TestMerchantData.platform,
            "merchant_status": TestMerchantData.merchant_status,
            "personality": TestMerchantData.personality_type.value,
            "bot_name": TestMerchantData.bot_name,
            "business_name": TestMerchantData.business_name,
        })
        await conn.commit()

    # Create client
    from app.core.database import get_db

    async def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            await session.close()

    app.dependency_overrides[get_db] = override_get_db

    update_data = {
        "greeting_template": "   ",  # Whitespace only
        "use_custom_greeting": True,
    }

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.put("/api/v1/merchant/greeting-config", json=update_data)

    app.dependency_overrides.clear()

    # Should return validation error
    assert response.status_code == 400

    data = response.json()
    assert "error_code" in data


@pytest.mark.asyncio
async def test_update_greeting_config_too_long_raises_validation_error():
    """Test PUT greeting-config with greeting > 500 chars raises error."""
    long_greeting = "A" * 501  # 501 'A's

    # Create client
    from app.core.database import get_db

    async def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            await session.close()

    app.dependency_overrides[get_db] = override_get_db

    update_data = {
        "greeting_template": long_greeting,
        "use_custom_greeting": True,
    }

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.put("/api/v1/merchant/greeting-config", json=update_data)

    app.dependency_overrides.clear()

    assert response.status_code == 400

    data = response.json()
    assert "error_code" in data
    assert "message" in data
    # Should mention character limit
    assert "500" in data["message"].lower() or "too long" in data["message"].lower()


@pytest.mark.asyncio
async def test_update_greeting_config_without_authentication_fails():
    """Test PUT greeting-config requires authentication."""
    async with httpx.AsyncClient(base_url="http://test") as client:
        response = await client.put("/api/v1/merchant/greeting-config", json={})

        assert response.status_code == 401


@pytest.mark.asyncio
async def test_put_greeting_config_response_structure():
    """Test PUT greeting-config response has correct envelope structure."""
    # Create test merchant
    async with test_engine.begin() as conn:
        await conn.execute(text(
            "INSERT INTO merchants "
            "(id, merchant_key, platform, merchant_status, personality_type, bot_name, business_name) "
            "VALUES (:id, :merchant_key, :platform, :merchant_status, :personality, :bot_name, :business_name)"
        ), {
            "id": TestMerchantData.id,
            "merchant_key": TestMerchantData.merchant_key,
            "platform": TestMerchantData.platform,
            "merchant_status": TestMerchantData.merchant_status,
            "personality": TestMerchantData.personality_type.value,
            "bot_name": TestMerchantData.bot_name,
            "business_name": TestMerchantData.business_name,
        })
        await conn.commit()

    # Create client
    from app.core.database import get_db

    async def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            await session.close()

    app.dependency_overrides[get_db] = override_get_db

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.put(
            "/api/v1/merchant/greeting-config",
            json={"greeting_template": "Test greeting"}
        )

    app.dependency_overrides.clear()

    # Verify envelope structure
    assert response.status_code == 200

    data = response.json()
    assert "data" in data
    assert "meta" in data
    assert "requestId" in data["meta"]
    assert "timestamp" in data["meta"]


@pytest.mark.asyncio
async def test_greeting_config_available_variables_list():
    """Test available_variables contains expected variables."""
    # Create test merchant
    async with test_engine.begin() as conn:
        await conn.execute(text(
            "INSERT INTO merchants "
            "(id, merchant_key, platform, merchant_status, personality_type, bot_name, business_name) "
            "VALUES (:id, :merchant_key, :platform, :merchant_status, :personality, :bot_name, :business_name)"
        ), {
            "id": TestMerchantData.id,
            "merchant_key": TestMerchantData.merchant_key,
            "platform": TestMerchantData.platform,
            "merchant_status": TestMerchantData.merchant_status,
            "personality": TestMerchantData.personality_type.value,
            "bot_name": TestMerchantData.bot_name,
            "business_name": TestMerchantData.business_name,
        })
        await conn.commit()

    # Create client
    from app.core.database import get_db

    async def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            await session.close()

    app.dependency_overrides[get_db] = override_get_db

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/api/v1/merchant/greeting-config")

    app.dependency_overrides.clear()

    assert response.status_code == 200

    data = response.json()
    greeting_data = data["data"]
    assert "available_variables" in greeting_data
    assert set(greeting_data["available_variables"]) == {"bot_name", "business_name", "business_hours"}
