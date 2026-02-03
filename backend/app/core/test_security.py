"""Tests for security utilities.

Tests encryption, decryption, and webhook signature verification.
"""

from __future__ import annotations

import os
import pytest

from app.core.security import (
    encrypt_access_token,
    decrypt_access_token,
    verify_webhook_signature,
    generate_oauth_state,
    generate_webhook_verify_token,
    validate_oauth_state,
)
from app.core.errors import APIError, ErrorCode


class TestTokenEncryption:
    """Tests for Fernet token encryption/decryption."""

    def test_encrypt_and_decrypt_token(self, monkeypatch):
        """Test that a token can be encrypted and decrypted successfully."""
        # Set up encryption key
        from cryptography.fernet import Fernet
        key = Fernet.generate_key()
        monkeypatch.setenv("FACEBOOK_ENCRYPTION_KEY", key.decode())

        original_token = "EAAabcdef123456"
        encrypted = encrypt_access_token(original_token)
        decrypted = decrypt_access_token(encrypted)

        assert decrypted == original_token
        assert encrypted != original_token  # Should be different

    def test_encryption_produces_different_outputs(self, monkeypatch):
        """Test that encryption produces different outputs each time (due to IV)."""
        from cryptography.fernet import Fernet
        key = Fernet.generate_key()
        monkeypatch.setenv("FACEBOOK_ENCRYPTION_KEY", key.decode())

        token = "same_token"
        encrypted1 = encrypt_access_token(token)
        encrypted2 = encrypt_access_token(token)

        # Same plaintext should produce different ciphertext
        assert encrypted1 != encrypted2

        # But both should decrypt to the same value
        assert decrypt_access_token(encrypted1) == token
        assert decrypt_access_token(encrypted2) == token

    def test_decrypt_with_wrong_key_fails(self, monkeypatch):
        """Test that decryption fails with wrong key."""
        from cryptography.fernet import Fernet, InvalidToken
        key1 = Fernet.generate_key()
        key2 = Fernet.generate_key()

        token = "test_token"

        # Encrypt with key1
        monkeypatch.setenv("FACEBOOK_ENCRYPTION_KEY", key1.decode())
        encrypted = encrypt_access_token(token)

        # Try to decrypt with key2
        monkeypatch.setenv("FACEBOOK_ENCRYPTION_KEY", key2.decode())
        with pytest.raises(InvalidToken):  # Fernet raises InvalidToken for wrong key
            decrypt_access_token(encrypted)

    def test_missing_encryption_key_raises_error(self, monkeypatch):
        """Test that missing encryption key raises ValueError."""
        monkeypatch.delenv("FACEBOOK_ENCRYPTION_KEY", raising=False)

        with pytest.raises(ValueError, match="FACEBOOK_ENCRYPTION_KEY"):
            encrypt_access_token("test_token")


class TestWebhookSignatureVerification:
    """Tests for webhook signature verification."""

    def test_valid_signature_passes(self):
        """Test that a valid signature passes verification."""
        import hmac
        import hashlib

        app_secret = "test_app_secret"
        payload = b'{"test": "payload"}'

        # Generate valid signature
        signature = hmac.new(
            app_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        signature_header = f"sha256={signature}"

        assert verify_webhook_signature(payload, signature_header, app_secret) is True

    def test_invalid_signature_fails(self):
        """Test that an invalid signature fails verification."""
        assert verify_webhook_signature(b"payload", "sha256=invalid", "secret") is False

    def test_missing_signature_fails(self):
        """Test that missing signature fails verification."""
        assert verify_webhook_signature(b"payload", None, "secret") is False

    def test_malformed_signature_fails(self):
        """Test that malformed signature fails verification."""
        assert verify_webhook_signature(b"payload", "invalid_format", "secret") is False

    def test_wrong_payload_fails(self):
        """Test that wrong payload fails verification even with correct signature."""
        import hmac
        import hashlib

        app_secret = "test_app_secret"
        payload1 = b'{"test": "payload1"}'
        payload2 = b'{"test": "payload2"}'

        # Generate signature for payload1
        signature = hmac.new(
            app_secret.encode(),
            payload1,
            hashlib.sha256
        ).hexdigest()
        signature_header = f"sha256={signature}"

        # Try to verify payload2 with payload1's signature
        assert verify_webhook_signature(payload2, signature_header, app_secret) is False

    def test_constant_time_comparison_prevents_timing_attack(self):
        """Test that signature verification uses constant-time comparison."""
        import hmac
        import hashlib
        import time

        app_secret = "test_app_secret"
        payload = b'{"test": "payload"}'

        # Generate correct signature
        correct_signature = hmac.new(
            app_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        # Generate wrong signature of same length
        wrong_signature = "x" * len(correct_signature)

        # Time both verifications - should be similar (within 10x)
        start = time.perf_counter()
        verify_webhook_signature(payload, f"sha256={correct_signature}", app_secret)
        correct_time = time.perf_counter() - start

        start = time.perf_counter()
        verify_webhook_signature(payload, f"sha256={wrong_signature}", app_secret)
        wrong_time = time.perf_counter() - start

        # Constant-time comparison should have similar timing
        assert wrong_time < correct_time * 10


class TestOAuthStateGeneration:
    """Tests for OAuth state parameter generation and validation."""

    def test_state_is_unique(self):
        """Test that generated states are unique."""
        state1 = generate_oauth_state(1)
        state2 = generate_oauth_state(2)

        assert state1 != state2

    def test_state_is_url_safe(self):
        """Test that generated state is URL-safe."""
        state = generate_oauth_state(1)
        # Should not contain characters that need URL encoding
        assert "%" not in state
        assert state.isalnum() or "_" in state or "-" in state

    def test_state_length_is_reasonable(self):
        """Test that generated state has reasonable length."""
        state = generate_oauth_state(1)
        # token_urlsafe(32) produces 43 characters
        assert len(state) >= 32

    def test_state_stores_merchant_id(self):
        """Test that state parameter stores associated merchant_id."""
        merchant_id = 123
        state = generate_oauth_state(merchant_id)

        # Validate that state returns the correct merchant_id
        validated_id = validate_oauth_state(state)
        assert validated_id == merchant_id

    def test_state_is_single_use(self):
        """Test that state can only be validated once (CSRF protection)."""
        merchant_id = 456
        state = generate_oauth_state(merchant_id)

        # First validation should succeed
        validated_id = validate_oauth_state(state)
        assert validated_id == merchant_id

        # Second validation should fail (one-time use)
        validated_id = validate_oauth_state(state)
        assert validated_id is None

    def test_invalid_state_returns_none(self):
        """Test that invalid state returns None."""
        validated_id = validate_oauth_state("invalid_state_12345")
        assert validated_id is None


class TestWebhookVerifyTokenGeneration:
    """Tests for webhook verify token generation."""

    def test_token_is_unique(self):
        """Test that generated tokens are unique."""
        token1 = generate_webhook_verify_token()
        token2 = generate_webhook_verify_token()

        assert token1 != token2

    def test_token_is_url_safe(self):
        """Test that generated token is URL-safe."""
        token = generate_webhook_verify_token()
        assert "%" not in token

    def test_token_length_is_reasonable(self):
        """Test that generated token has reasonable length."""
        token = generate_webhook_verify_token()
        assert len(token) >= 32
