"""Comprehensive CSRF protection tests (NFR-S8).

Tests cover:
- Token generation
- Token validation
- Token rejection on mismatch
- State-changing operations require token
- Safe methods (GET, HEAD, OPTIONS) bypass CSRF
- Webhook endpoints bypass CSRF
- Cookie security attributes
- Double-submit cookie pattern
- Constant-time comparison (timing attack prevention)
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch
from fastapi import Request, Response
from starlette.datastructures import Headers

from app.core.csrf import (
    CSRFProtection,
    CSRFTokenError,
    get_csrf_protection,
    init_csrf_protection,
)


class TestCSRFTokenGeneration:
    """Tests for CSRF token generation."""

    def test_generate_token_with_valid_session(self):
        """Test token generation with valid session ID."""
        csrf = CSRFProtection("test-secret-key-12345678901234567890")
        session_id = "test-session-123"

        token = csrf.generate_token(session_id)

        assert token is not None
        assert session_id in token
        assert ":" in token
        assert len(token) > len(session_id)

    def test_generate_token_is_unique(self):
        """Test that tokens are unique for same session."""
        csrf = CSRFProtection("test-secret-key-12345678901234567890")
        session_id = "test-session-123"

        token1 = csrf.generate_token(session_id)
        token2 = csrf.generate_token(session_id)

        # Tokens should be different due to random component
        assert token1 != token2
        # But both should contain session ID
        assert session_id in token1
        assert session_id in token2

    def test_generate_token_with_empty_session_raises_error(self):
        """Test that empty session ID raises error."""
        csrf = CSRFProtection("test-secret-key-12345678901234567890")

        with pytest.raises(ValueError, match="session_id cannot be empty"):
            csrf.generate_token("")

    def test_generate_token_is_url_safe(self):
        """Test that generated token is URL-safe."""
        csrf = CSRFProtection("test-secret-key-12345678901234567890")
        session_id = "test-session-123"

        token = csrf.generate_token(session_id)

        # Should not contain characters that need URL encoding
        assert "%" not in token
        assert " " not in token
        assert "/" not in token
        # Should be alphanumeric plus - and _
        assert all(c.isalnum() or c in ":-_" for c in token)

    def test_generate_token_with_dev_key_raises_error(self):
        """Test that dev key raises error."""
        with pytest.raises(ValueError, match="secure SECRET_KEY"):
            CSRFProtection("dev-secret-key-DO-NOT-USE-IN-PRODUCTION")

    def test_generate_token_with_empty_key_raises_error(self):
        """Test that empty key raises error."""
        with pytest.raises(ValueError, match="secure SECRET_KEY"):
            CSRFProtection("")


class TestCSRFTokenValidation:
    """Tests for CSRF token validation."""

    def test_validate_token_with_valid_token(self):
        """Test validation with valid token."""
        csrf = CSRFProtection("test-secret-key-12345678901234567890")
        session_id = "test-session-123"
        token = csrf.generate_token(session_id)

        # Create mock request with token in cookie
        request = MagicMock(spec=Request)
        request.cookies.get.return_value = token

        # Validate token from header
        is_valid = csrf.validate_token(request, token)

        assert is_valid is True

    def test_validate_token_with_missing_token(self):
        """Test validation with missing token."""
        csrf = CSRFProtection("test-secret-key-12345678901234567890")

        # Create mock request without token in cookie
        request = MagicMock(spec=Request)
        request.cookies.get.return_value = None

        is_valid = csrf.validate_token(request, None)

        assert is_valid is False

    def test_validate_token_with_mismatched_token(self):
        """Test validation with mismatched token."""
        csrf = CSRFProtection("test-secret-key-12345678901234567890")
        session_id = "test-session-123"
        token1 = csrf.generate_token(session_id)
        token2 = csrf.generate_token(session_id)

        # Create mock request with token1 in cookie
        request = MagicMock(spec=Request)
        request.cookies.get.return_value = token1

        # Try to validate with token2
        is_valid = csrf.validate_token(request, token2)

        assert is_valid is False

    def test_validate_token_with_empty_cookie(self):
        """Test validation with empty cookie."""
        csrf = CSRFProtection("test-secret-key-12345678901234567890")

        # Create mock request with empty cookie
        request = MagicMock(spec=Request)
        request.cookies.get.return_value = ""

        is_valid = csrf.validate_token(request, "some-token")

        assert is_valid is False

    def test_validate_token_constant_time_comparison(self):
        """Test that validation uses constant-time comparison."""
        import time

        csrf = CSRFProtection("test-secret-key-12345678901234567890")
        session_id = "test-session-123"
        correct_token = csrf.generate_token(session_id)

        # Create mock request
        request = MagicMock(spec=Request)

        # Time correct token validation
        request.cookies.get.return_value = correct_token
        start = time.perf_counter()
        csrf.validate_token(request, correct_token)
        correct_time = time.perf_counter() - start

        # Time wrong token validation (same length)
        wrong_token = csrf.generate_token("different-session")
        request.cookies.get.return_value = correct_token
        start = time.perf_counter()
        csrf.validate_token(request, wrong_token)
        wrong_time = time.perf_counter() - start

        # Constant-time comparison should have similar timing
        # (within 10x due to system variance)
        assert wrong_time < correct_time * 10


class TestCSRFCookieManagement:
    """Tests for CSRF cookie management."""

    def test_set_csrf_cookie_security_attributes(self):
        """Test that CSRF cookie has correct security attributes."""
        csrf = CSRFProtection("test-secret-key-12345678901234567890")
        token = csrf.generate_token("test-session")

        # Create mock response
        response = MagicMock(spec=Response)
        response.set_cookie = MagicMock()

        csrf.set_csrf_cookie(response, token)

        # Verify set_cookie was called with correct attributes
        response.set_cookie.assert_called_once_with(
            key="csrf_token",
            value=token,
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=3600,
        )

    def test_clear_csrf_cookie(self):
        """Test clearing CSRF cookie."""
        csrf = CSRFProtection("test-secret-key-12345678901234567890")

        # Create mock response
        response = MagicMock(spec=Response)
        response.delete_cookie = MagicMock()

        csrf.clear_csrf_cookie(response)

        # Verify delete_cookie was called
        response.delete_cookie.assert_called_once_with(
            key="csrf_token",
            httponly=True,
            secure=True,
            samesite="strict",
        )

    def test_cookie_max_age_from_settings(self):
        """Test that cookie max age respects settings."""
        csrf = CSRFProtection(
            "test-secret-key-12345678901234567890",
            max_age=1800,  # 30 minutes
        )
        token = csrf.generate_token("test-session")

        # Create mock response
        response = MagicMock(spec=Response)
        response.set_cookie = MagicMock()

        csrf.set_csrf_cookie(response, token)

        # Verify max_age was set correctly
        call_kwargs = response.set_cookie.call_args.kwargs
        assert call_kwargs["max_age"] == 1800


class TestCSRFTokenExtraction:
    """Tests for CSRF token extraction from headers."""

    def test_extract_token_from_x_csrf_token_header(self):
        """Test extraction from X-CSRF-Token header."""
        csrf = CSRFProtection("test-secret-key-12345678901234567890")
        headers = Headers({"x-csrf-token": "test-token-123"})

        token = csrf.extract_token_from_headers(headers)

        assert token == "test-token-123"

    def test_extract_token_from_alternative_header(self):
        """Test extraction from CSRF-Token header."""
        csrf = CSRFProtection("test-secret-key-12345678901234567890")
        headers = Headers({"csrf-token": "test-token-456"})

        token = csrf.extract_token_from_headers(headers)

        assert token == "test-token-456"

    def test_extract_token_returns_none_when_missing(self):
        """Test that None is returned when token is missing."""
        csrf = CSRFProtection("test-secret-key-12345678901234567890")
        headers = Headers({})

        token = csrf.extract_token_from_headers(headers)

        assert token is None

    def test_extract_token_case_insensitive(self):
        """Test that header name matching is case-insensitive."""
        csrf = CSRFProtection("test-secret-key-12345678901234567890")
        headers = Headers({"X-CSRF-TOKEN": "test-token-789"})

        token = csrf.extract_token_from_headers(headers)

        assert token == "test-token-789"


class TestCSRFSessionParsing:
    """Tests for session ID parsing from tokens."""

    def test_parse_session_id_from_valid_token(self):
        """Test parsing session ID from valid token."""
        csrf = CSRFProtection("test-secret-key-12345678901234567890")
        session_id = "test-session-123"
        token = csrf.generate_token(session_id)

        parsed_session_id = csrf.parse_session_id_from_token(token)

        assert parsed_session_id == session_id

    def test_parse_session_id_from_invalid_token(self):
        """Test parsing session ID from invalid token."""
        csrf = CSRFProtection("test-secret-key-12345678901234567890")

        parsed_session_id = csrf.parse_session_id_from_token("invalid-token")

        assert parsed_session_id is None

    def test_parse_session_id_from_empty_token(self):
        """Test parsing session ID from empty token."""
        csrf = CSRFProtection("test-secret-key-12345678901234567890")

        parsed_session_id = csrf.parse_session_id_from_token("")

        assert parsed_session_id is None

    def test_parse_session_id_from_token_without_separator(self):
        """Test parsing session ID from token without separator."""
        csrf = CSRFProtection("test-secret-key-12345678901234567890")

        parsed_session_id = csrf.parse_session_id_from_token("nosessionid")

        assert parsed_session_id is None


class TestCSRFMiddleware:
    """Tests for CSRF middleware."""

    @pytest.mark.asyncio
    async def test_middleware_bypasses_safe_methods(self):
        """Test that GET requests bypass CSRF validation."""
        from app.middleware.csrf import CSRFMiddleware

        csrf = CSRFProtection("test-secret-key-12345678901234567890")
        middleware = CSRFMiddleware(None, "test-secret-key-12345678901234567890")

        # Mock GET request
        request = MagicMock(spec=Request)
        request.method = "GET"
        request.url.path = "/api/test"
        request.headers = Headers({})

        # Should bypass CSRF (no exception raised)
        should_bypass = middleware._should_bypass_csrf(request)
        assert should_bypass is False  # Path not in bypass list

        # But safe methods bypass in dispatch
        async def mock_call_next(req):
            return MagicMock()

        response = await middleware.dispatch(request, mock_call_next)

        # Should proceed without CSRF check
        assert response is not None

    @pytest.mark.asyncio
    async def test_middleware_bypasses_webhook_paths(self):
        """Test that webhook paths bypass CSRF validation."""
        from app.middleware.csrf import CSRFMiddleware

        middleware = CSRFMiddleware(None, "test-secret-key-12345678901234567890")

        # Mock webhook request
        request = MagicMock(spec=Request)
        request.method = "POST"
        request.url.path = "/api/webhooks/facebook"
        request.headers = Headers({})

        should_bypass = middleware._should_bypass_csrf(request)
        assert should_bypass is True

    @pytest.mark.asyncio
    async def test_middleware_bypasses_oauth_paths(self):
        """Test that OAuth paths bypass CSRF validation."""
        from app.middleware.csrf import CSRFMiddleware

        middleware = CSRFMiddleware(None, "test-secret-key-12345678901234567890")

        # Mock OAuth request
        request = MagicMock(spec=Request)
        request.method = "POST"
        request.url.path = "/api/oauth/callback"
        request.headers = Headers({})

        should_bypass = middleware._should_bypass_csrf(request)
        assert should_bypass is True

    @pytest.mark.asyncio
    async def test_middleware_requires_csrf_for_post(self):
        """Test that POST requests require CSRF token."""
        from app.middleware.csrf import CSRFMiddleware
        from fastapi import HTTPException

        middleware = CSRFMiddleware(None, "test-secret-key-12345678901234567890")

        # Mock POST request without CSRF token
        request = MagicMock(spec=Request)
        request.method = "POST"
        request.url.path = "/api/checkout"
        request.headers = Headers({})
        request.cookies.get.return_value = None

        async def mock_call_next(req):
            return MagicMock()

        # Should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await middleware.dispatch(request, mock_call_next)

        assert exc_info.value.status_code == 403
        assert "CSRF" in str(exc_info.value.detail["message"])

    @pytest.mark.asyncio
    async def test_middleware_validates_csrf_for_put(self):
        """Test that PUT requests require valid CSRF token."""
        from app.middleware.csrf import CSRFMiddleware
        from fastapi import HTTPException

        middleware = CSRFMiddleware(None, "test-secret-key-12345678901234567890")

        # Mock PUT request with invalid CSRF token
        request = MagicMock(spec=Request)
        request.method = "PUT"
        request.url.path = "/api/users/123"
        request.headers = Headers({"x-csrf-token": "invalid-token"})
        request.cookies.get.return_value = "different-token"

        async def mock_call_next(req):
            return MagicMock()

        # Should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await middleware.dispatch(request, mock_call_next)

        assert exc_info.value.status_code == 403


class TestCSRFProtectionSingleton:
    """Tests for CSRF protection singleton pattern."""

    def test_get_csrf_protection_before_init_raises_error(self):
        """Test that getting protection before init raises error."""
        # Reset singleton
        import app.core.csrf
        app.core.csrf._csrf_protection = None

        with pytest.raises(ValueError, match="CSRF protection not initialized"):
            get_csrf_protection()

    def test_init_csrf_protection_creates_instance(self):
        """Test that init creates and returns instance."""
        # Reset singleton
        import app.core.csrf
        app.core.csrf._csrf_protection = None

        csrf = init_csrf_protection("test-secret-key-12345678901234567890")

        assert isinstance(csrf, CSRFProtection)
        assert get_csrf_protection() is csrf

    def test_get_csrf_protection_returns_same_instance(self):
        """Test that get returns same instance."""
        # Reset singleton
        import app.core.csrf
        app.core.csrf._csrf_protection = None

        csrf1 = init_csrf_protection("test-secret-key-12345678901234567890")
        csrf2 = get_csrf_protection()

        assert csrf1 is csrf2


class TestCSRFDoubleSubmitPattern:
    """Tests for double-submit cookie pattern."""

    def test_double_submit_pattern_valid(self):
        """Test valid double-submit pattern (token in header and cookie)."""
        csrf = CSRFProtection("test-secret-key-12345678901234567890")
        session_id = "test-session-123"
        token = csrf.generate_token(session_id)

        # Create mock request with token in both cookie and header
        request = MagicMock(spec=Request)
        request.cookies.get.return_value = token

        # Validate with same token
        is_valid = csrf.validate_token(request, token)

        assert is_valid is True

    def test_double_submit_pattern_mismatch(self):
        """Test invalid double-submit pattern (token mismatch)."""
        csrf = CSRFProtection("test-secret-key-12345678901234567890")
        session_id = "test-session-123"
        token1 = csrf.generate_token(session_id)
        token2 = csrf.generate_token(session_id)

        # Create mock request with token1 in cookie but token2 in header
        request = MagicMock(spec=Request)
        request.cookies.get.return_value = token1

        # Should fail validation
        is_valid = csrf.validate_token(request, token2)

        assert is_valid is False


class TestCSRFEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_token_with_special_characters_in_session_id(self):
        """Test token generation with special characters in session ID."""
        csrf = CSRFProtection("test-secret-key-12345678901234567890")
        session_id = "session-with-special-chars-!@#$%"

        token = csrf.generate_token(session_id)

        # Should handle special characters
        assert session_id in token

    def test_token_with_unicode_session_id(self):
        """Test token generation with unicode session ID."""
        csrf = CSRFProtection("test-secret-key-12345678901234567890")
        session_id = "session-世界-123"

        token = csrf.generate_token(session_id)

        # Should handle unicode
        assert session_id in token

    def test_token_with_very_long_session_id(self):
        """Test token generation with very long session ID."""
        csrf = CSRFProtection("test-secret-key-12345678901234567890")
        session_id = "a" * 1000

        token = csrf.generate_token(session_id)

        # Should handle long session IDs
        assert session_id in token
        assert len(token) > len(session_id)

    def test_token_with_numeric_session_id(self):
        """Test token generation with numeric session ID."""
        csrf = CSRFProtection("test-secret-key-12345678901234567890")
        session_id = "123456789"

        token = csrf.generate_token(session_id)

        # Should handle numeric session IDs
        assert session_id in token

    def test_validate_token_with_none_request(self):
        """Test validation with None token."""
        csrf = CSRFProtection("test-secret-key-12345678901234567890")
        request = MagicMock(spec=Request)
        request.cookies.get.return_value = "some-token"

        is_valid = csrf.validate_token(request, None)

        assert is_valid is False

    def test_validate_token_with_invalid_token_format(self):
        """Test validation with invalid token format."""
        csrf = CSRFProtection("test-secret-key-12345678901234567890")
        request = MagicMock(spec=Request)
        request.cookies.get.return_value = "valid-token"

        # Invalid token should not crash
        is_valid = csrf.validate_token(request, "invalid-format-without-separator")

        assert is_valid is False


class TestCSRFConfiguration:
    """Tests for CSRF configuration options."""

    def test_custom_token_length(self):
        """Test custom token length configuration."""
        csrf = CSRFProtection(
            "test-secret-key-12345678901234567890",
            token_length=16,
        )
        session_id = "test-session"

        token = csrf.generate_token(session_id)

        # Token should contain session ID plus random part
        assert session_id in token
        # Random part should be present (16 bytes = ~22 chars in base64url)
        assert len(token) > len(session_id)

    def test_custom_max_age(self):
        """Test custom max age configuration."""
        csrf = CSRFProtection(
            "test-secret-key-12345678901234567890",
            max_age=7200,  # 2 hours
        )

        assert csrf.max_age == 7200

    def test_default_configuration(self):
        """Test default configuration values."""
        csrf = CSRFProtection("test-secret-key-12345678901234567890")

        assert csrf.token_length == 32
        assert csrf.max_age == 3600
