"""Comprehensive conversation encryption tests (NFR-S2).

Tests cover:
- Conversation content encryption/decryption (Fernet)
- Metadata field encryption/decryption
- Separate encryption keys for different data types
- Empty/null value handling
- Migration scenario (plaintext to encrypted)
- Encryption detection heuristics
"""

from __future__ import annotations

import pytest
from unittest.mock import patch
from cryptography.fernet import Fernet, InvalidToken

from app.core.encryption import (
    encrypt_conversation_content,
    decrypt_conversation_content,
    encrypt_metadata,
    decrypt_metadata,
    get_conversation_fernet,
    is_encrypted,
)


class TestConversationContentEncryption:
    """Comprehensive tests for conversation content encryption/decryption."""

    def test_encrypt_and_decrypt_content_success(self, monkeypatch):
        """Test successful encryption and decryption of conversation content."""
        key = Fernet.generate_key()
        monkeypatch.setenv("CONVERSATION_ENCRYPTION_KEY", key.decode())

        original_content = "Hello, I'd like to track my order #12345"
        encrypted = encrypt_conversation_content(original_content)
        decrypted = decrypt_conversation_content(encrypted)

        assert decrypted == original_content
        assert encrypted != original_content
        assert len(encrypted) > len(original_content)

    def test_encryption_produces_unique_ciphertext(self, monkeypatch):
        """Test that encrypting same content twice produces different ciphertext (IV)."""
        key = Fernet.generate_key()
        monkeypatch.setenv("CONVERSATION_ENCRYPTION_KEY", key.decode())

        content = "Where is my order?"
        encrypted1 = encrypt_conversation_content(content)
        encrypted2 = encrypt_conversation_content(content)

        # Same plaintext should produce different ciphertext due to IV
        assert encrypted1 != encrypted2

        # But both decrypt to same value
        assert decrypt_conversation_content(encrypted1) == content
        assert decrypt_conversation_content(encrypted2) == content

    def test_decrypt_with_wrong_key_returns_original(self, monkeypatch):
        """Test that decryption with wrong key returns original (migration support)."""
        key1 = Fernet.generate_key()
        key2 = Fernet.generate_key()

        content = "My order hasn't arrived yet"

        # Encrypt with key1
        monkeypatch.setenv("CONVERSATION_ENCRYPTION_KEY", key1.decode())
        encrypted = encrypt_conversation_content(content)

        # Try to decrypt with key2 - should return encrypted value (migration)
        monkeypatch.setenv("CONVERSATION_ENCRYPTION_KEY", key2.decode())
        result = decrypt_conversation_content(encrypted)
        # Current implementation returns original on decryption failure
        assert result == encrypted

    def test_missing_encryption_key_falls_back_to_facebook_key(self, monkeypatch):
        """Test that missing conversation key falls back to Facebook key."""
        facebook_key = Fernet.generate_key()
        monkeypatch.delenv("CONVERSATION_ENCRYPTION_KEY", raising=False)
        monkeypatch.setenv("FACEBOOK_ENCRYPTION_KEY", facebook_key.decode())

        content = "I need help with my order"
        encrypted = encrypt_conversation_content(content)
        decrypted = decrypt_conversation_content(encrypted)

        assert decrypted == content

    def test_missing_all_keys_raises_error(self, monkeypatch):
        """Test that missing all encryption keys raises ValueError."""
        monkeypatch.delenv("CONVERSATION_ENCRYPTION_KEY", raising=False)
        monkeypatch.delenv("FACEBOOK_ENCRYPTION_KEY", raising=False)

        with pytest.raises(ValueError, match="CONVERSATION_ENCRYPTION_KEY"):
            encrypt_conversation_content("test")

    def test_empty_content_encryption(self, monkeypatch):
        """Test encryption and decryption of empty content."""
        key = Fernet.generate_key()
        monkeypatch.setenv("CONVERSATION_ENCRYPTION_KEY", key.decode())

        original_content = ""
        encrypted = encrypt_conversation_content(original_content)
        decrypted = decrypt_conversation_content(encrypted)

        assert decrypted == original_content
        assert encrypted == original_content  # Empty returns empty

    def test_none_content_encryption(self, monkeypatch):
        """Test encryption and decryption of None content."""
        key = Fernet.generate_key()
        monkeypatch.setenv("CONVERSATION_ENCRYPTION_KEY", key.decode())

        encrypted = encrypt_conversation_content(None)
        decrypted = decrypt_conversation_content(None)

        assert encrypted is None
        assert decrypted is None

    def test_long_content_encryption(self, monkeypatch):
        """Test encryption and decryption of long conversation content."""
        key = Fernet.generate_key()
        monkeypatch.setenv("CONVERSATION_ENCRYPTION_KEY", key.decode())

        # Simulate long customer message
        long_content = "I'd like to return " + "my order " * 100
        encrypted = encrypt_conversation_content(long_content)
        decrypted = decrypt_conversation_content(encrypted)

        assert decrypted == long_content

    def test_content_with_special_characters(self, monkeypatch):
        """Test encryption of content with special characters."""
        key = Fernet.generate_key()
        monkeypatch.setenv("CONVERSATION_ENCRYPTION_KEY", key.decode())

        content = "Order #123-456! Email: test@example.com, Phone: +1-555-0123"
        encrypted = encrypt_conversation_content(content)
        decrypted = decrypt_conversation_content(encrypted)

        assert decrypted == content

    def test_content_with_unicode_characters(self, monkeypatch):
        """Test encryption of content with unicode characters."""
        key = Fernet.generate_key()
        monkeypatch.setenv("CONVERSATION_ENCRYPTION_KEY", key.decode())

        content = "Hello 你好 I'd like to track order #12345ありがとう"
        encrypted = encrypt_conversation_content(content)
        decrypted = decrypt_conversation_content(encrypted)

        assert decrypted == content

    def test_content_with_emoji(self, monkeypatch):
        """Test encryption of content with emoji."""
        key = Fernet.generate_key()
        monkeypatch.setenv("CONVERSATION_ENCRYPTION_KEY", key.decode())

        content = "My order is late! 😠 Where is it? 📦🚚"
        encrypted = encrypt_conversation_content(content)
        decrypted = decrypt_conversation_content(encrypted)

        assert decrypted == content

    def test_content_with_order_references(self, monkeypatch):
        """Test encryption preserves order references (they should be encrypted)."""
        key = Fernet.generate_key()
        monkeypatch.setenv("CONVERSATION_ENCRYPTION_KEY", key.decode())

        content = "Where is order #12345? I need tracking for order #67890."
        encrypted = encrypt_conversation_content(content)
        decrypted = decrypt_conversation_content(encrypted)

        assert decrypted == content
        assert "#12345" not in encrypted  # Order IDs should be encrypted
        assert "#67890" not in encrypted

    def test_get_conversation_fernet_returns_instance(self, monkeypatch):
        """Test that get_conversation_fernet returns valid Fernet instance."""
        key = Fernet.generate_key()
        monkeypatch.setenv("CONVERSATION_ENCRYPTION_KEY", key.decode())

        fernet1 = get_conversation_fernet()
        fernet2 = get_conversation_fernet()

        # Should return valid Fernet instances (not necessarily same instance)
        assert isinstance(fernet1, Fernet)
        assert isinstance(fernet2, Fernet)
        # Both can encrypt/decrypt with the same key
        content = "Order #12345"
        encrypted = fernet1.encrypt(content.encode())
        decrypted = fernet2.decrypt(encrypted)
        assert decrypted.decode() == content

    def test_plaintext_migration_scenario(self, monkeypatch):
        """Test that plaintext values are returned during migration."""
        key = Fernet.generate_key()
        monkeypatch.setenv("CONVERSATION_ENCRYPTION_KEY", key.decode())

        # Simulate old plaintext data in database
        plaintext_content = "This is old unencrypted data"
        result = decrypt_conversation_content(plaintext_content)

        # Should return original value (migration support)
        assert result == plaintext_content


class TestMetadataEncryption:
    """Comprehensive tests for metadata field encryption/decryption."""

    def test_encrypt_metadata_with_user_input(self, monkeypatch):
        """Test encryption of metadata with user_input field."""
        key = Fernet.generate_key()
        monkeypatch.setenv("CONVERSATION_ENCRYPTION_KEY", key.decode())

        metadata = {
            "user_input": "I want to return my order #12345",
            "message_type": "text",
        }

        encrypted = encrypt_metadata(metadata)

        assert encrypted["user_input"] != metadata["user_input"]
        assert encrypted["message_type"] == metadata["message_type"]  # Unchanged

        # Verify decryption
        decrypted_user_input = decrypt_conversation_content(encrypted["user_input"])
        assert decrypted_user_input == metadata["user_input"]

    def test_encrypt_metadata_with_voluntary_memory(self, monkeypatch):
        """Test encryption of metadata with voluntary_memory field."""
        key = Fernet.generate_key()
        monkeypatch.setenv("CONVERSATION_ENCRYPTION_KEY", key.decode())

        metadata = {
            "voluntary_memory": {
                "preferences": "size: large, color: blue",
                "history": "previous orders: #111, #222",
            },
            "source": "facebook",
        }

        encrypted = encrypt_metadata(metadata)

        assert encrypted["voluntary_memory"]["preferences"] != metadata["voluntary_memory"]["preferences"]
        assert encrypted["voluntary_memory"]["history"] != metadata["voluntary_memory"]["history"]
        assert encrypted["source"] == metadata["source"]  # Unchanged

    def test_decrypt_metadata_with_user_input(self, monkeypatch):
        """Test decryption of metadata with user_input field."""
        key = Fernet.generate_key()
        monkeypatch.setenv("CONVERSATION_ENCRYPTION_KEY", key.decode())

        original_metadata = {
            "user_input": "Where is my order #12345?",
            "message_type": "text",
        }

        # Encrypt then decrypt
        encrypted = encrypt_metadata(original_metadata)
        decrypted = decrypt_metadata(encrypted)

        assert decrypted["user_input"] == original_metadata["user_input"]
        assert decrypted["message_type"] == original_metadata["message_type"]

    def test_decrypt_metadata_with_voluntary_memory(self, monkeypatch):
        """Test decryption of metadata with voluntary_memory field."""
        key = Fernet.generate_key()
        monkeypatch.setenv("CONVERSATION_ENCRYPTION_KEY", key.decode())

        original_metadata = {
            "voluntary_memory": {
                "preferences": "size: large",
                "history": "order #111",
            },
            "source": "facebook",
        }

        # Encrypt then decrypt
        encrypted = encrypt_metadata(original_metadata)
        decrypted = decrypt_metadata(encrypted)

        assert decrypted["voluntary_memory"]["preferences"] == original_metadata["voluntary_memory"]["preferences"]
        assert decrypted["voluntary_memory"]["history"] == original_metadata["voluntary_memory"]["history"]
        assert decrypted["source"] == original_metadata["source"]

    def test_encrypt_empty_metadata(self, monkeypatch):
        """Test encryption of empty metadata."""
        key = Fernet.generate_key()
        monkeypatch.setenv("CONVERSATION_ENCRYPTION_KEY", key.decode())

        assert encrypt_metadata({}) == {}
        assert encrypt_metadata(None) is None

    def test_encrypt_metadata_without_sensitive_fields(self, monkeypatch):
        """Test encryption of metadata without sensitive fields."""
        key = Fernet.generate_key()
        monkeypatch.setenv("CONVERSATION_ENCRYPTION_KEY", key.decode())

        metadata = {
            "message_type": "text",
            "platform": "facebook",
            "timestamp": "2024-01-01T00:00:00Z",
        }

        encrypted = encrypt_metadata(metadata)

        # Should be unchanged (no sensitive fields)
        assert encrypted == metadata

    def test_decrypt_metadata_with_invalid_encrypted_field(self, monkeypatch):
        """Test decryption handles invalid encrypted values gracefully."""
        key = Fernet.generate_key()
        monkeypatch.setenv("CONVERSATION_ENCRYPTION_KEY", key.decode())

        metadata = {
            "user_input": "invalid_encrypted_data_not_real_fernet",
            "message_type": "text",
        }

        # Should not raise error, return original value
        decrypted = decrypt_metadata(metadata)
        assert decrypted["user_input"] == "invalid_encrypted_data_not_real_fernet"

    def test_encrypt_metadata_with_empty_user_input(self, monkeypatch):
        """Test encryption of metadata with empty user_input."""
        key = Fernet.generate_key()
        monkeypatch.setenv("CONVERSATION_ENCRYPTION_KEY", key.decode())

        metadata = {"user_input": "", "message_type": "text"}
        encrypted = encrypt_metadata(metadata)

        # Empty string should remain empty
        assert encrypted["user_input"] == ""

    def test_encrypt_metadata_preserves_original(self, monkeypatch):
        """Test that encryption doesn't modify original metadata dict."""
        key = Fernet.generate_key()
        monkeypatch.setenv("CONVERSATION_ENCRYPTION_KEY", key.decode())

        original_metadata = {
            "user_input": "Order #12345",
            "message_type": "text",
        }

        encrypted = encrypt_metadata(original_metadata)

        # Original should be unchanged
        assert original_metadata["user_input"] == "Order #12345"
        # Encrypted should have different user_input
        assert encrypted["user_input"] != original_metadata["user_input"]


class TestEncryptionDetection:
    """Tests for encryption detection heuristics."""

    def test_is_encrypted_detects_fernet_token(self, monkeypatch):
        """Test that is_encrypted detects valid Fernet tokens."""
        key = Fernet.generate_key()
        monkeypatch.setenv("CONVERSATION_ENCRYPTION_KEY", key.decode())

        plaintext = "Order #12345"
        encrypted = encrypt_conversation_content(plaintext)

        assert is_encrypted(encrypted) is True
        assert is_encrypted(plaintext) is False

    def test_is_encrypted_with_empty_string(self):
        """Test that is_encrypted returns False for empty string."""
        assert is_encrypted("") is False

    def test_is_encrypted_with_none(self):
        """Test that is_encrypted returns False for None."""
        assert is_encrypted(None) is False

    def test_is_encrypted_with_invalid_base64(self):
        """Test that is_encrypted returns False for invalid base64."""
        assert is_encrypted("not-valid-base64!!!") is False

    def test_is_encrypted_with_short_string(self):
        """Test that is_encrypted returns False for short strings."""
        assert is_encrypted("short") is False

    def test_is_encrypted_with_plaintext_order_reference(self):
        """Test that is_encrypted returns False for plaintext order references."""
        assert is_encrypted("Order #12345") is False
        assert is_encrypted("#12345") is False

    def test_is_encrypted_with_special_characters(self):
        """Test is_encrypted with special characters (should be False)."""
        assert is_encrypted("Hello! @#$%^&*()") is False


class TestSeparateEncryptionKeys:
    """Tests for separate encryption keys for different data types."""

    def test_conversation_key_different_from_facebook_key(self, monkeypatch):
        """Test that conversation encryption uses different key from Facebook."""
        conversation_key = Fernet.generate_key()
        facebook_key = Fernet.generate_key()

        # Encrypt with conversation key
        monkeypatch.setenv("CONVERSATION_ENCRYPTION_KEY", conversation_key.decode())
        monkeypatch.setenv("FACEBOOK_ENCRYPTION_KEY", facebook_key.decode())

        content = "My order #12345"
        encrypted_content = encrypt_conversation_content(content)

        # Now remove conversation key and try to decrypt with Facebook key
        # This simulates having different keys
        monkeypatch.delenv("CONVERSATION_ENCRYPTION_KEY", raising=False)
        # Now it will fall back to Facebook key (different key)
        result = decrypt_conversation_content(encrypted_content)

        # Should return encrypted value (decryption failed with wrong key)
        assert result == encrypted_content

    def test_fallback_to_facebook_key_when_conversation_key_missing(self, monkeypatch):
        """Test fallback to Facebook key when conversation key is missing."""
        facebook_key = Fernet.generate_key()
        monkeypatch.delenv("CONVERSATION_ENCRYPTION_KEY", raising=False)
        monkeypatch.setenv("FACEBOOK_ENCRYPTION_KEY", facebook_key.decode())

        content = "Order #12345"
        encrypted = encrypt_conversation_content(content)
        decrypted = decrypt_conversation_content(encrypted)

        assert decrypted == content


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_encrypt_very_long_content(self, monkeypatch):
        """Test encryption of very long content (10,000+ characters)."""
        key = Fernet.generate_key()
        monkeypatch.setenv("CONVERSATION_ENCRYPTION_KEY", key.decode())

        long_content = "x" * 10000
        encrypted = encrypt_conversation_content(long_content)
        decrypted = decrypt_conversation_content(encrypted)

        assert decrypted == long_content

    def test_encrypt_content_with_newlines(self, monkeypatch):
        """Test encryption of content with newlines."""
        key = Fernet.generate_key()
        monkeypatch.setenv("CONVERSATION_ENCRYPTION_KEY", key.decode())

        content = "Line 1\nLine 2\nLine 3\nOrder #12345"
        encrypted = encrypt_conversation_content(content)
        decrypted = decrypt_conversation_content(encrypted)

        assert decrypted == content

    def test_encrypt_content_with_tabs(self, monkeypatch):
        """Test encryption of content with tabs."""
        key = Fernet.generate_key()
        monkeypatch.setenv("CONVERSATION_ENCRYPTION_KEY", key.decode())

        content = "Column1\tColumn2\tOrder #12345"
        encrypted = encrypt_conversation_content(content)
        decrypted = decrypt_conversation_content(encrypted)

        assert decrypted == content

    def test_encrypt_metadata_with_nested_structure(self, monkeypatch):
        """Test encryption of metadata with nested voluntary_memory."""
        key = Fernet.generate_key()
        monkeypatch.setenv("CONVERSATION_ENCRYPTION_KEY", key.decode())

        metadata = {
            "voluntary_memory": {
                "preferences": "size: large",
                "history": "order #111",
                "nested": {
                    "deep": "value",
                },
            },
            "user_input": "Order #12345",
        }

        encrypted = encrypt_metadata(metadata)
        decrypted = decrypt_metadata(encrypted)

        # Check sensitive fields are encrypted/decrypted
        assert decrypted["voluntary_memory"]["preferences"] == metadata["voluntary_memory"]["preferences"]
        assert decrypted["voluntary_memory"]["history"] == metadata["voluntary_memory"]["history"]
        assert decrypted["user_input"] == metadata["user_input"]
        # Nested non-sensitive should be unchanged
        assert decrypted["voluntary_memory"]["nested"]["deep"] == "value"

    def test_concurrent_encryption(self, monkeypatch):
        """Test that concurrent encryption produces unique results."""
        import concurrent.futures

        key = Fernet.generate_key()
        monkeypatch.setenv("CONVERSATION_ENCRYPTION_KEY", key.decode())

        content = "Order #12345"

        def encrypt_content():
            return encrypt_conversation_content(content)

        # Encrypt concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            encrypted_list = list(executor.map(lambda _: encrypt_content(), range(100)))

        # All should be different (due to random IV)
        assert len(set(encrypted_list)) == 100

        # But all should decrypt to same value
        decrypted_list = [decrypt_conversation_content(e) for e in encrypted_list]
        assert all(d == content for d in decrypted_list)
