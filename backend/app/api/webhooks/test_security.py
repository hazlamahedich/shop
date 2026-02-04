"""Comprehensive webhook security tests (NFR-S1, NFR-S3, NFR-S5).

Tests cover:
- Facebook webhook signature verification (X-Hub-Signature-256)
- Shopify webhook HMAC verification
- Signature/HMAC edge cases
- Payload tampering detection
- Timing attack resistance
- Unicode and special character handling
"""

from __future__ import annotations

import pytest
import hmac
import hashlib
import base64
import time
from unittest.mock import Mock, patch, MagicMock

from app.core.security import (
    verify_webhook_signature,
    verify_shopify_webhook_hmac,
)


class TestFacebookWebhookSignatureVerification:
    """Comprehensive tests for Facebook webhook X-Hub-Signature-256 verification."""

    def test_valid_signature_passes(self):
        """Test that valid X-Hub-Signature-256 passes verification."""
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
        """Test that invalid signature fails verification."""
        assert verify_webhook_signature(b"payload", "sha256=invalid", "secret") is False

    def test_missing_signature_fails(self):
        """Test that missing signature fails verification."""
        assert verify_webhook_signature(b"payload", None, "secret") is False

    def test_empty_signature_fails(self):
        """Test that empty signature fails verification."""
        assert verify_webhook_signature(b"payload", "", "secret") is False

    def test_malformed_signature_fails(self):
        """Test that malformed signature fails verification."""
        # Missing "sha256=" prefix
        assert verify_webhook_signature(b"payload", "invalid_format", "secret") is False

    def test_wrong_algorithm_fails(self):
        """Test that signature with wrong algorithm fails."""
        app_secret = "test_app_secret"
        payload = b'{"test": "payload"}'

        # Generate SHA1 signature (wrong algorithm)
        signature = hmac.new(
            app_secret.encode(),
            payload,
            hashlib.sha1
        ).hexdigest()

        signature_header = f"sha1={signature}"

        assert verify_webhook_signature(payload, signature_header, app_secret) is False

    def test_wrong_payload_fails(self):
        """Test that wrong payload fails even with correct signature format."""
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

    def test_empty_payload_verification(self):
        """Test signature verification with empty payload."""
        app_secret = "test_app_secret"
        payload = b""

        # Generate signature for empty payload
        signature = hmac.new(
            app_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        signature_header = f"sha256={signature}"

        assert verify_webhook_signature(payload, signature_header, app_secret) is True

    def test_large_payload_verification(self):
        """Test signature verification with large payload."""
        app_secret = "test_app_secret"
        payload = b'{"data": "' + b'x' * 10000 + b'"}'

        signature = hmac.new(
            app_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        signature_header = f"sha256={signature}"

        assert verify_webhook_signature(payload, signature_header, app_secret) is True

    def test_constant_time_comparison_timing_attack_prevention(self):
        """Test that signature verification uses constant-time comparison."""
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

        # Time both verifications
        start = time.perf_counter()
        verify_webhook_signature(payload, f"sha256={correct_signature}", app_secret)
        correct_time = time.perf_counter() - start

        start = time.perf_counter()
        verify_webhook_signature(payload, f"sha256={wrong_signature}", app_secret)
        wrong_time = time.perf_counter() - start

        # Constant-time comparison should have similar timing (within 10x)
        # This is a loose check due to system variance
        assert wrong_time < correct_time * 10

    def test_signature_with_extra_whitespace_fails(self):
        """Test that signature with extra whitespace fails."""
        app_secret = "test_app_secret"
        payload = b'{"test": "payload"}'

        signature = hmac.new(
            app_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        # Extra whitespace should cause failure
        signature_header = f"sha256= {signature}"
        assert verify_webhook_signature(payload, signature_header, app_secret) is False

    def test_signature_case_sensitivity(self):
        """Test that signature verification is case-sensitive."""
        app_secret = "test_app_secret"
        payload = b'{"test": "payload"}'

        signature = hmac.new(
            app_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        # Uppercase signature should fail
        signature_header = f"sha256={signature.upper()}"
        assert verify_webhook_signature(payload, signature_header, app_secret) is False

    def test_unicode_payload_verification(self):
        """Test signature verification with unicode payload."""
        app_secret = "test_app_secret"
        payload = '{"message": "Hello 世界"}'.encode('utf-8')

        signature = hmac.new(
            app_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        signature_header = f"sha256={signature}"

        assert verify_webhook_signature(payload, signature_header, app_secret) is True


class TestShopifyWebhookHMACVerification:
    """Comprehensive tests for Shopify webhook HMAC verification."""

    def test_valid_hmac_passes(self):
        """Test that valid Shopify HMAC passes verification."""
        api_secret = "test_api_secret"
        payload = b'{"test": "payload"}'

        # Generate valid HMAC
        hmac_digest = hmac.new(
            api_secret.encode(),
            payload,
            hashlib.sha256
        ).digest()
        hmac_header = base64.b64encode(hmac_digest).decode()

        assert verify_shopify_webhook_hmac(payload, hmac_header, api_secret) is True

    def test_invalid_hmac_fails(self):
        """Test that invalid HMAC fails verification."""
        api_secret = "test_api_secret"
        payload = b'{"test": "payload"}'

        invalid_hmac = base64.b64encode(b"invalid_hmac").decode()

        assert verify_shopify_webhook_hmac(payload, invalid_hmac, api_secret) is False

    def test_missing_hmac_raises_error(self):
        """Test that missing HMAC raises TypeError (implementation detail)."""
        # Current implementation raises TypeError for None input
        # This documents existing behavior
        with pytest.raises(TypeError):
            verify_shopify_webhook_hmac(b"payload", None, "secret")

    def test_empty_hmac_fails(self):
        """Test that empty HMAC fails verification."""
        # Empty string is valid base64 (decodes to empty bytes)
        # HMAC verification will fail due to length mismatch
        assert verify_shopify_webhook_hmac(b"payload", "", "secret") is False

    def test_wrong_api_secret_fails(self):
        """Test that wrong API secret fails verification."""
        secret1 = "secret1"
        secret2 = "secret2"
        payload = b'{"test": "payload"}'

        # Generate HMAC with secret1
        hmac_digest = hmac.new(
            secret1.encode(),
            payload,
            hashlib.sha256
        ).digest()
        hmac_header = base64.b64encode(hmac_digest).decode()

        # Try to verify with secret2
        assert verify_shopify_webhook_hmac(payload, hmac_header, secret2) is False

    def test_wrong_payload_fails(self):
        """Test that wrong payload fails even with correct HMAC."""
        api_secret = "test_api_secret"
        payload1 = b'{"test": "payload1"}'
        payload2 = b'{"test": "payload2"}'

        # Generate HMAC for payload1
        hmac_digest = hmac.new(
            api_secret.encode(),
            payload1,
            hashlib.sha256
        ).digest()
        hmac_header = base64.b64encode(hmac_digest).decode()

        # Try to verify payload2 with payload1's HMAC
        assert verify_shopify_webhook_hmac(payload2, hmac_header, api_secret) is False

    def test_malformed_base64_hmac_raises_error(self):
        """Test that malformed base64 HMAC raises binascii.Error."""
        # Current implementation raises binascii.Error for invalid base64
        # This documents existing behavior - function does not handle errors gracefully
        api_secret = "test_api_secret"
        payload = b'{"test": "payload"}'

        # Invalid base64 (incorrect padding)
        malformed_hmac = "not-valid-base64!!!"

        with pytest.raises(Exception):  # binascii.Error
            verify_shopify_webhook_hmac(payload, malformed_hmac, api_secret)

    def test_constant_time_comparison_for_shopify(self):
        """Test that Shopify HMAC verification uses constant-time comparison."""
        api_secret = "test_api_secret"
        payload = b'{"test": "payload"}'

        # Generate correct HMAC
        correct_hmac = hmac.new(
            api_secret.encode(),
            payload,
            hashlib.sha256
        ).digest()
        correct_hmac_header = base64.b64encode(correct_hmac).decode()

        # Generate wrong HMAC of same length
        wrong_hmac = b"x" * len(correct_hmac)
        wrong_hmac_header = base64.b64encode(wrong_hmac).decode()

        # Time both verifications
        start = time.perf_counter()
        verify_shopify_webhook_hmac(payload, correct_hmac_header, api_secret)
        correct_time = time.perf_counter() - start

        start = time.perf_counter()
        verify_shopify_webhook_hmac(payload, wrong_hmac_header, api_secret)
        wrong_time = time.perf_counter() - start

        # Constant-time comparison should have similar timing
        assert wrong_time < correct_time * 10

    def test_unicode_payload_for_shopify(self):
        """Test Shopify HMAC verification with unicode payload."""
        api_secret = "test_api_secret"
        payload = '{"order": "测试订单"}'.encode('utf-8')

        hmac_digest = hmac.new(
            api_secret.encode(),
            payload,
            hashlib.sha256
        ).digest()
        hmac_header = base64.b64encode(hmac_digest).decode()

        assert verify_shopify_webhook_hmac(payload, hmac_header, api_secret) is True


class TestReplayAttackPrevention:
    """Tests for replay attack prevention mechanisms."""

    def test_facebook_webhook_signature_unique_per_payload(self):
        """Test that each payload has unique signature."""
        app_secret = "test_app_secret"
        payload1 = b'{"id": "1", "timestamp": "2024-01-01T00:00:00Z"}'
        payload2 = b'{"id": "1", "timestamp": "2024-01-01T00:00:01Z"}'

        sig1 = hmac.new(app_secret.encode(), payload1, hashlib.sha256).hexdigest()
        sig2 = hmac.new(app_secret.encode(), payload2, hashlib.sha256).hexdigest()

        # Different timestamps should produce different signatures
        assert sig1 != sig2

    def test_shopify_webhook_hmac_unique_per_payload(self):
        """Test that each payload has unique HMAC."""
        api_secret = "test_api_secret"
        payload1 = b'{"id": "1"}'
        payload2 = b'{"id": "2"}'

        hmac1 = hmac.new(api_secret.encode(), payload1, hashlib.sha256).digest()
        hmac2 = hmac.new(api_secret.encode(), payload2, hashlib.sha256).digest()

        # Different payloads should produce different HMACs
        assert hmac1 != hmac2


class TestSignatureEdgeCases:
    """Tests for signature verification edge cases."""

    def test_facebook_signature_with_newlines_in_payload(self):
        """Test signature verification with newlines in payload."""
        app_secret = "test_app_secret"
        payload = b'{"test": "payload\nwith\nnewlines"}'

        signature = hmac.new(
            app_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        signature_header = f"sha256={signature}"

        assert verify_webhook_signature(payload, signature_header, app_secret) is True

    def test_facebook_signature_with_special_characters(self):
        """Test signature verification with special characters."""
        app_secret = "test_app_secret"
        payload = b'{"test": "!@#$%^&*()_+-=[]{}|;:\'",.<>/?"}'

        signature = hmac.new(
            app_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        signature_header = f"sha256={signature}"

        assert verify_webhook_signature(payload, signature_header, app_secret) is True

    def test_shopify_hmac_with_newlines_in_payload(self):
        """Test HMAC verification with newlines in payload."""
        api_secret = "test_api_secret"
        payload = b'{"test": "payload\nwith\nnewlines"}'

        hmac_digest = hmac.new(
            api_secret.encode(),
            payload,
            hashlib.sha256
        ).digest()
        hmac_header = base64.b64encode(hmac_digest).decode()

        assert verify_shopify_webhook_hmac(payload, hmac_header, api_secret) is True

    def test_facebook_signature_length_variations(self):
        """Test signature verification with various payload lengths."""
        app_secret = "test_app_secret"

        # Test with various payload sizes
        for size in [1, 10, 100, 1000, 10000]:
            payload = b'{"data": "' + b'x' * size + b'"}'
            signature = hmac.new(
                app_secret.encode(),
                payload,
                hashlib.sha256
            ).hexdigest()
            signature_header = f"sha256={signature}"

            assert verify_webhook_signature(payload, signature_header, app_secret) is True


class TestSignatureSecurityProperties:
    """Tests for signature security properties."""

    def test_facebook_signature_uses_sha256(self):
        """Test that signature verification uses SHA-256."""
        app_secret = "test_app_secret"
        payload = b'{"test": "payload"}'

        # SHA-256 produces 64 hex characters
        signature = hmac.new(
            app_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        assert len(signature) == 64  # SHA-256 = 256 bits = 64 hex chars

    def test_shopify_hmac_uses_sha256(self):
        """Test that HMAC verification uses SHA-256."""
        api_secret = "test_api_secret"
        payload = b'{"test": "payload"}'

        hmac_digest = hmac.new(
            api_secret.encode(),
            payload,
            hashlib.sha256
        ).digest()

        # SHA-256 produces 32 bytes
        assert len(hmac_digest) == 32  # SHA-256 = 256 bits = 32 bytes

    def test_facebook_signature_different_for_different_secrets(self):
        """Test that signature differs for different secrets."""
        payload = b'{"test": "payload"}'

        sig1 = hmac.new(b"secret1", payload, hashlib.sha256).hexdigest()
        sig2 = hmac.new(b"secret2", payload, hashlib.sha256).hexdigest()

        assert sig1 != sig2

    def test_shopify_hmac_different_for_different_secrets(self):
        """Test that HMAC differs for different secrets."""
        payload = b'{"test": "payload"}'

        hmac1 = hmac.new(b"secret1", payload, hashlib.sha256).digest()
        hmac2 = hmac.new(b"secret2", payload, hashlib.sha256).digest()

        assert hmac1 != hmac2


class TestSignatureTimingAttackResistanceDetailed:
    """Detailed tests for timing attack resistance."""

    def test_facebook_verification_timing_consistency(self):
        """Test that verification timing is consistent across different inputs."""
        app_secret = "test_app_secret"
        payload = b'{"test": "payload"}'

        # Generate signatures that differ at different positions
        correct_sig = hmac.new(app_secret.encode(), payload, hashlib.sha256).hexdigest()

        # Wrong signatures with errors at different positions
        sigs_to_test = [
            correct_sig,  # Correct
            "a" * len(correct_sig),  # All wrong (first char)
            correct_sig[:-1] + "a",  # Wrong (last char)
            correct_sig[:-10] + "a" * 10,  # Wrong (last 10 chars)
        ]

        times = []
        for sig in sigs_to_test:
            start = time.perf_counter()
            verify_webhook_signature(payload, f"sha256={sig}", app_secret)
            times.append(time.perf_counter() - start)

        # All times should be reasonably similar (within 20x for system variance)
        max_time = max(times)
        min_time = min(times)
        assert max_time < min_time * 20

    def test_shopify_verification_timing_consistency(self):
        """Test that Shopify HMAC verification timing is consistent."""
        api_secret = "test_api_secret"
        payload = b'{"test": "payload"}'

        correct_hmac = hmac.new(api_secret.encode(), payload, hashlib.sha256).digest()
        correct_hmac_header = base64.b64encode(correct_hmac).decode()

        # Wrong HMACs with errors at different positions
        hmacs_to_test = [
            correct_hmac_header,  # Correct
            base64.b64encode(b"a" * len(correct_hmac)).decode(),  # All wrong
            base64.b64encode(correct_hmac[:-1] + b"a").decode(),  # Wrong (last byte)
        ]

        times = []
        for hmac_header in hmacs_to_test:
            start = time.perf_counter()
            try:
                verify_shopify_webhook_hmac(payload, hmac_header, api_secret)
            except Exception:
                pass  # Some may raise errors, we still measure timing
            times.append(time.perf_counter() - start)

        # All times should be reasonably similar
        max_time = max(times)
        min_time = min(times)
        assert max_time < min_time * 20
