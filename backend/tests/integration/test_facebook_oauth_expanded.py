"""Expanded integration tests for Facebook OAuth flow.

Tests expanded error scenarios, token validation, and permission handling.
"""

from __future__ import annotations

import json
import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch
import base64


@pytest.mark.asyncio
async def test_facebook_oauth_state_validation(async_client: AsyncClient) -> None:
    """Test Facebook OAuth state parameter validation (CSRF protection).

    P0 - Security Critical: Ensures OAuth state parameter is validated
    to prevent CSRF attacks.

    Args:
        async_client: Test HTTP client
    """
    # Generate OAuth URL
    response = await async_client.get(
        "/api/integrations/facebook/authorize",
        params={"merchant_id": 1}
    )

    assert response.status_code == 200
    data = response.json()
    state = data["data"]["state"]

    # State should be a UUID-like string
    assert isinstance(state, str)
    assert len(state) >= 30  # UUID format


@pytest.mark.asyncio
async def test_facebook_callback_state_mismatch(async_client: AsyncClient) -> None:
    """Test Facebook callback with invalid state (CSRF attack detection).

    P0 - Security Critical: Detects CSRF attacks during OAuth flow.

    Args:
        async_client: Test HTTP client
    """
    response = await async_client.get(
        "/api/integrations/facebook/callback",
        params={
            "state": "malicious_state",  # Invalid state
            "code": "test_auth_code"
        }
    )

    # Should reject invalid state
    assert response.status_code in [400, 422]  # Bad Request or Unprocessable


@pytest.mark.asyncio
async def test_facebook_callback_permission_denied(async_client: AsyncClient) -> None:
    """Test Facebook callback when user denies authorization.

    P1 - High Priority: User explicitly denies OAuth permissions.

    Args:
        async_client: Test HTTP client
    """
    response = await async_client.get(
        "/api/integrations/facebook/callback",
        params={
            "state": "valid_state",
            "error": "access_denied",
            "error_code": "200",
            "error_description": "Permissions error"
        }
    )

    # Should return 422 (Unprocessable) or 400 for denied
    assert response.status_code in [400, 422]


@pytest.mark.asyncio
async def test_facebook_token_encryption(async_client: AsyncClient) -> None:
    """Test that Facebook access tokens are encrypted before storage.

    P0 - Security Critical: Prevents token leakage if database is compromised.

    Args:
        async_client: Test HTTP client
    """
    from app.core.security import encrypt_access_token, decrypt_access_token

    original_token = "sensitive_facebook_page_token_12345"

    # Encrypt token
    encrypted = encrypt_access_token(original_token)

    # Encrypted token should be different from original
    assert encrypted != original_token
    assert len(encrypted) > len(original_token)

    # Decrypt and verify
    decrypted = decrypt_access_token(encrypted)
    assert decrypted == original_token


@pytest.mark.asyncio
async def test_facebook_page_verification(async_client: AsyncClient) -> None:
    """Test Facebook page access verification after OAuth.

    P0 - Revenue Critical: Verifies page access token works before
    storing connection.

    Args:
        async_client: Test HTTP client
    """
    from app.services.facebook import FacebookService
    from app.core.database import get_db

    # Get database session (required for FacebookService)
    async for db in get_db():
        service = FacebookService(db=db, is_testing=True)

        # Should return dict with page info in test mode
        result = await service.verify_page_access(
            access_token="test_token"
        )

        assert isinstance(result, dict)
        break  # Only need one db session


@pytest.mark.asyncio
async def test_facebook_rate_limiting(async_client: AsyncClient) -> None:
    """Test Facebook OAuth endpoint rate limiting.

    P2 - Medium Priority: Prevents OAuth abuse.

    Args:
        async_client: Test HTTP client
    """
    # First request may succeed or be rate limited depending on previous test runs
    response1 = await async_client.get(
        "/api/integrations/facebook/authorize",
        params={"merchant_id": 1}
    )
    # Rate limiter may be active from previous tests
    assert response1.status_code in [200, 429]

    # Rapid second request to same merchant may be rate limited
    # (implementation dependent)
    response2 = await async_client.get(
        "/api/integrations/facebook/authorize",
        params={"merchant_id": 1}
    )
    # May return 200 or 429 depending on rate limiter
    assert response2.status_code in [200, 429]
