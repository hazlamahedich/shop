"""Unit tests for input sanitization utilities.

Story 5-7: Security & Rate Limiting
AC5: Input Sanitization
"""

from __future__ import annotations

import pytest

from app.core.sanitization import sanitize_message, validate_message_length, MAX_MESSAGE_LENGTH


class TestSanitizeMessage:
    """Tests for sanitize_message function."""

    def test_html_tags_escaped(self):
        """HTML tags are escaped."""
        result = sanitize_message("<script>alert('xss')</script>")
        assert "<script>" not in result
        assert "&lt;script&gt;" in result

    def test_script_injection_neutralized(self):
        """Script injection is neutralized via escaping."""
        result = sanitize_message("<img src=x onerror=alert('xss')>")
        assert "<img" not in result
        assert "&lt;img" in result

    def test_null_bytes_removed(self):
        """Null bytes are removed."""
        result = sanitize_message("hello\x00world")
        assert "\x00" not in result
        assert result == "helloworld"

    def test_whitespace_trimmed(self):
        """Leading and trailing whitespace is trimmed."""
        result = sanitize_message("  hello world  ")
        assert result == "hello world"

    def test_empty_string_returns_empty(self):
        """Empty string returns empty."""
        result = sanitize_message("")
        assert result == ""

    def test_normal_text_unchanged(self):
        """Normal text passes through with trimming."""
        result = sanitize_message("Hello, how can I help?")
        assert result == "Hello, how can I help?"

    def test_special_chars_preserved(self):
        """Valid special characters are preserved."""
        result = sanitize_message("Price: $99.99! (50% off)")
        assert "$99.99" in result
        assert "50%" in result

    def test_ampersand_escaped(self):
        """Ampersand is escaped."""
        result = sanitize_message("Tom & Jerry")
        assert "&amp;" in result

    def test_quotes_escaped(self):
        """Quotes are escaped."""
        result = sanitize_message('He said "hello"')
        assert "&quot;" in result


class TestValidateMessageLength:
    """Tests for validate_message_length function."""

    def test_valid_message_returns_true(self):
        """Valid message length returns (True, None)."""
        is_valid, error = validate_message_length("Hello world")
        assert is_valid is True
        assert error is None

    def test_empty_message_rejected(self):
        """Empty message is rejected."""
        is_valid, error = validate_message_length("")
        assert is_valid is False
        assert "empty" in error.lower()

    def test_whitespace_only_rejected(self):
        """Whitespace-only message is rejected."""
        is_valid, error = validate_message_length("   ")
        assert is_valid is False
        assert "empty" in error.lower()

    def test_max_length_accepted(self):
        """Message at exactly max length is accepted."""
        message = "x" * MAX_MESSAGE_LENGTH
        is_valid, error = validate_message_length(message)
        assert is_valid is True
        assert error is None

    def test_exceeds_max_length_rejected(self):
        """Message exceeding max length is rejected."""
        message = "x" * (MAX_MESSAGE_LENGTH + 1)
        is_valid, error = validate_message_length(message)
        assert is_valid is False
        assert "exceeds" in error.lower()
        assert str(MAX_MESSAGE_LENGTH) in error

    def test_long_message_rejected(self):
        """Very long message is rejected."""
        message = "x" * 5000
        is_valid, error = validate_message_length(message)
        assert is_valid is False
        assert "exceeds" in error.lower()
