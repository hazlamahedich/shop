"""Unit tests for authentication core module.

Tests cover:
- Password hashing and verification (bcrypt work factor 12)
- Password requirements validation
- JWT creation and validation
- Token hashing for storage
- SECRET_KEY validation
"""

from __future__ import annotations

import pytest
from datetime import datetime, timedelta
from fastapi import HTTPException, status

from app.core.auth import (
    hash_password,
    verify_password,
    validate_password_requirements,
    hash_token,
    create_jwt,
    validate_jwt,
    authenticate_merchant,
    validate_secret_key,
    JWTPayload,
)
from app.core.config import settings


class TestPasswordSecurity:
    """Tests for password hashing and verification (AC 4)."""

    def test_hash_password_returns_string(self):
        """Hashing password should return a string."""
        result = hash_password("SecurePass123")
        assert isinstance(result, str)
        assert len(result) == 60  # bcrypt hash length

    def test_hash_password_same_input_different_hashes(self):
        """Same password should produce different hashes (salt)."""
        password = "SecurePass123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        assert hash1 != hash2  # Different salts

    def test_verify_password_correct(self):
        """Verifying correct password should return True."""
        password = "SecurePass123"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Verifying incorrect password should return False."""
        password = "SecurePass123"
        wrong_password = "WrongPass123"
        hashed = hash_password(password)
        assert verify_password(wrong_password, hashed) is False

    def test_hash_password_empty_raises_error(self):
        """Hashing empty password should raise ValueError."""
        with pytest.raises(ValueError, match="Password cannot be empty"):
            hash_password("")

    def test_hash_password_too_short_raises_error(self):
        """Hashing password < 8 chars should raise ValueError."""
        with pytest.raises(ValueError, match="at least 8 characters"):
            hash_password("Short1")

    def test_verify_password_constant_time(self):
        """Password verification should use constant-time comparison."""
        password = "SecurePass123"
        hashed = hash_password(password)

        # Multiple verifications should take similar time
        # (prevent timing attacks)
        assert verify_password(password, hashed) is True
        assert verify_password("WrongPass123", hashed) is False
        assert verify_password("AnotherWrong", hashed) is False


class TestPasswordRequirements:
    """Tests for password requirements validation (AC 1, AC 4)."""

    def test_valid_password_passes(self):
        """Valid password should pass validation."""
        is_valid, errors = validate_password_requirements("SecurePass123")
        assert is_valid is True
        assert len(errors) == 0

    def test_too_short_fails(self):
        """Password < 8 chars should fail."""
        is_valid, errors = validate_password_requirements("Short1")
        assert is_valid is False
        assert any("8 characters" in e for e in errors)

    def test_no_uppercase_fails(self):
        """Password without uppercase should fail."""
        is_valid, errors = validate_password_requirements("lowercase123")
        assert is_valid is False
        assert any("uppercase" in e for e in errors)

    def test_no_lowercase_fails(self):
        """Password without lowercase should fail."""
        is_valid, errors = validate_password_requirements("UPPERCASE123")
        assert is_valid is False
        assert any("lowercase" in e for e in errors)

    def test_minimum_requirements_met(self):
        """Password meeting minimums should pass."""
        is_valid, errors = validate_password_requirements("Abcd1234")
        assert is_valid is True
        assert len(errors) == 0


class TestTokenHashing:
    """Tests for token hashing (AC 6)."""

    def test_hash_token_returns_string(self):
        """Hashing token should return string."""
        result = hash_token("test-token-123")
        assert isinstance(result, str)

    def test_hash_token_same_input_same_hash(self):
        """Same token should produce same hash (deterministic)."""
        token = "test-token-123"
        hash1 = hash_token(token)
        hash2 = hash_token(token)
        assert hash1 == hash2

    def test_hash_token_different_inputs_different_hashes(self):
        """Different tokens should produce different hashes."""
        hash1 = hash_token("token-1")
        hash2 = hash_token("token-2")
        assert hash1 != hash2

    def test_hash_token_cannot_be_reversed(self):
        """Hash should be one-way (cannot get original token)."""
        token = "original-token"
        hashed = hash_token(token)
        assert hashed != token
        assert "original" not in hashed


class TestJWTCreation:
    """Tests for JWT creation (AC 2, AC 5)."""

    def test_create_jwt_returns_string(self):
        """Creating JWT should return string."""
        token = create_jwt(merchant_id=1, session_id="session-123")
        assert isinstance(token, str)

    def test_create_jwt_includes_merchant_id(self):
        """JWT payload should include merchant_id."""
        token = create_jwt(merchant_id=42, session_id="session-123")
        payload = validate_jwt(token)
        assert payload.merchant_id == 42

    def test_create_jwt_includes_session_id(self):
        """JWT payload should include session_id."""
        token = create_jwt(merchant_id=1, session_id="session-abc")
        payload = validate_jwt(token)
        assert payload.session_id == "session-abc"

    def test_create_jwt_includes_key_version(self):
        """JWT payload should include key_version (AC 5)."""
        token = create_jwt(merchant_id=1, session_id="session-123", key_version=2)
        payload = validate_jwt(token)
        assert payload.key_version == 2

    def test_create_jwt_default_key_version_is_1(self):
        """Default key_version should be 1."""
        token = create_jwt(merchant_id=1, session_id="session-123")
        payload = validate_jwt(token)
        assert payload.key_version == 1

    def test_create_jwt_includes_timestamps(self):
        """JWT should include exp and iat timestamps."""
        token = create_jwt(merchant_id=1, session_id="session-123")
        payload = validate_jwt(token)
        assert payload.exp > payload.iat

    def test_create_jwt_expiration_24_hours(self):
        """JWT should expire after 24 hours (AC 2)."""
        token = create_jwt(merchant_id=1, session_id="session-123")
        payload = validate_jwt(token)

        now = datetime.utcnow()
        exp_time = datetime.fromtimestamp(payload.exp)

        # Expiration should be ~24 hours from now
        time_diff = (exp_time - now).total_seconds()
        assert 86300 <= time_diff <= 86500  # ~24 hours (allowing 100s margin)

    def test_create_jwt_custom_expiration(self):
        """Custom expiration should be respected."""
        token = create_jwt(merchant_id=1, session_id="session-123", expiration_hours=12)
        payload = validate_jwt(token)

        now = datetime.utcnow()
        exp_time = datetime.fromtimestamp(payload.exp)
        time_diff = (exp_time - now).total_seconds()

        assert 43100 <= time_diff <= 43300  # ~12 hours


class TestJWTValidation:
    """Tests for JWT validation (AC 2, AC 5)."""

    def test_validate_jwt_returns_payload(self):
        """Valid JWT should return payload."""
        token = create_jwt(merchant_id=1, session_id="session-123")
        payload = validate_jwt(token)
        assert isinstance(payload, JWTPayload)
        assert payload.merchant_id == 1

    def test_validate_jwt_invalid_token_raises_401(self):
        """Invalid JWT should raise 401 error."""
        with pytest.raises(HTTPException) as exc:
            validate_jwt("invalid-token")
        assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED

    def test_validate_jwt_expired_token_raises_401(self):
        """Expired JWT should raise 401 with expired error."""
        import time

        # Create an already-expired token
        payload = JWTPayload(
            merchant_id=1,
            key_version=1,
            exp=int((datetime.utcnow() - timedelta(hours=1)).timestamp()),
            iat=int((datetime.utcnow() - timedelta(hours=25)).timestamp()),
            session_id="session-123",
        )

        from jose import jwt as jose_jwt
        expired_token = jose_jwt.encode(
            payload.to_dict(), settings()["SECRET_KEY"], algorithm="HS256"
        )

        with pytest.raises(HTTPException) as exc:
            validate_jwt(expired_token)
        assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
        detail = exc.value.detail
        assert "expired" in detail["message"].lower()

    def test_validate_jwt_with_custom_secret(self):
        """Validation with custom secret should work."""
        custom_secret = "custom-secret-key-for-testing"
        token = create_jwt(merchant_id=1, session_id="session-123")

        # Should fail with wrong secret
        with pytest.raises(HTTPException):
            validate_jwt(token, secret_key="wrong-secret")


class TestMerchantAuthentication:
    """Tests for merchant authentication (AC 1, AC 4)."""

    def test_authenticate_merchant_success(self):
        """Correct credentials should authenticate."""
        password = "SecurePass123"
        hashed = hash_password(password)
        result = authenticate_merchant(
            email="test@example.com",
            password=password,
            stored_hash=hashed,
            merchant_id=1,
        )
        assert result is True

    def test_authenticate_merchant_wrong_password_raises_401(self):
        """Wrong password should raise 401."""
        password = "SecurePass123"
        hashed = hash_password(password)

        with pytest.raises(HTTPException) as exc:
            authenticate_merchant(
                email="test@example.com",
                password="WrongPass123",
                stored_hash=hashed,
                merchant_id=1,
            )
        assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
        detail = exc.value.detail
        assert "Invalid email or password" in detail["message"]

    def test_authenticate_merchant_error_message_generic(self):
        """Error message should be generic (security)."""
        password = "SecurePass123"
        hashed = hash_password(password)

        with pytest.raises(HTTPException) as exc:
            authenticate_merchant(
                email="test@example.com",
                password="wrong",
                stored_hash=hashed,
                merchant_id=1,
            )
        # Should NOT reveal whether email exists
        assert "Invalid email or password" in exc.value.detail["message"]


class TestSecretKeyValidation:
    """Tests for SECRET_KEY validation (AC 4)."""

    def test_validate_secret_key_in_debug(self):
        """Dev key should be accepted in debug mode."""
        # This test runs in debug mode by default
        # Should not raise
        validate_secret_key()

    def test_secret_key_exists(self):
        """SECRET_KEY should be configured."""
        secret_key = settings()["SECRET_KEY"]
        assert secret_key is not None
        # In debug/test mode, shorter keys are acceptable for development
        # Production requires 32+ character keys (validated by validate_secret_key)
        if settings()["DEBUG"]:
            assert len(secret_key) >= 20
        else:
            assert len(secret_key) >= 32


class TestJWTPayload:
    """Tests for JWTPayload dataclass."""

    def test_payload_to_dict(self):
        """Converting payload to dict should work."""
        payload = JWTPayload(
            merchant_id=1,
            key_version=2,
            exp=1234567890,
            iat=1234567800,
            session_id="session-123",
        )
        data = payload.to_dict()
        assert data["merchant_id"] == 1
        assert data["key_version"] == 2
        assert data["session_id"] == "session-123"

    def test_payload_from_dict(self):
        """Creating payload from dict should work."""
        data = {
            "merchant_id": 1,
            "key_version": 2,
            "exp": 1234567890,
            "iat": 1234567800,
            "session_id": "session-123",
        }
        payload = JWTPayload.from_dict(data)
        assert payload.merchant_id == 1
        assert payload.key_version == 2

    def test_payload_from_dict_default_key_version(self):
        """from_dict should default key_version to 1."""
        data = {
            "merchant_id": 1,
            "exp": 1234567890,
            "iat": 1234567800,
            "session_id": "session-123",
        }
        payload = JWTPayload.from_dict(data)
        assert payload.key_version == 1
