"""Unit tests for input validation utilities.

Story 5-7: Security & Rate Limiting
AC3: Session ID Validation
"""

from __future__ import annotations

import pytest

from app.core.validators import is_valid_session_id


class TestIsValidSessionId:
    """Tests for is_valid_session_id function."""

    def test_valid_uuid_v4_accepted(self):
        """Valid UUID v4 format is accepted."""
        valid_uuid = "550e8400-e29b-41d4-a716-446655440000"
        assert is_valid_session_id(valid_uuid) is True

    def test_valid_uuid_with_uppercase_accepted(self):
        """Valid UUID with uppercase letters is accepted."""
        valid_uuid = "550E8400-E29B-41D4-A716-446655440000"
        assert is_valid_session_id(valid_uuid) is True

    def test_valid_uuid_with_mixed_case_accepted(self):
        """Valid UUID with mixed case is accepted."""
        valid_uuid = "550e8400-E29b-41D4-a716-446655440000"
        assert is_valid_session_id(valid_uuid) is True

    def test_valid_uuid_with_leading_trailing_whitespace(self):
        """Valid UUID with whitespace is trimmed and accepted."""
        valid_uuid = "  550e8400-e29b-41d4-a716-446655440000  "
        assert is_valid_session_id(valid_uuid) is True

    def test_invalid_uuid_format_rejected(self):
        """Invalid UUID format is rejected."""
        invalid_uuid = "not-a-uuid"
        assert is_valid_session_id(invalid_uuid) is False

    def test_empty_string_rejected(self):
        """Empty string is rejected."""
        assert is_valid_session_id("") is False

    def test_whitespace_only_rejected(self):
        """Whitespace-only string is rejected."""
        assert is_valid_session_id("   ") is False

    def test_none_rejected(self):
        """None is rejected."""
        assert is_valid_session_id(None) is False

    def test_non_string_rejected(self):
        """Non-string types are rejected."""
        assert is_valid_session_id(123) is False
        assert is_valid_session_id(["uuid"]) is False
        assert is_valid_session_id({"uuid": "test"}) is False

    def test_uuid_missing_hyphens_rejected(self):
        """UUID without hyphens is rejected."""
        invalid_uuid = "550e8400e29b41d4a716446655440000"
        assert is_valid_session_id(invalid_uuid) is False

    def test_uuid_too_short_rejected(self):
        """UUID that is too short is rejected."""
        invalid_uuid = "550e8400-e29b-41d4-a716"
        assert is_valid_session_id(invalid_uuid) is False

    def test_uuid_too_long_rejected(self):
        """UUID that is too long is rejected."""
        invalid_uuid = "550e8400-e29b-41d4-a716-446655440000-extra"
        assert is_valid_session_id(invalid_uuid) is False

    def test_sql_injection_attempt_rejected(self):
        """SQL injection attempt in session_id is rejected."""
        sql_injection = "550e8400'; DROP TABLE sessions;--"
        assert is_valid_session_id(sql_injection) is False

    def test_xss_attempt_rejected(self):
        """XSS attempt in session_id is rejected."""
        xss_attempt = "550e8400<script>alert('xss')</script>"
        assert is_valid_session_id(xss_attempt) is False

    def test_path_traversal_attempt_rejected(self):
        """Path traversal attempt in session_id is rejected."""
        path_traversal = "../../../etc/passwd"
        assert is_valid_session_id(path_traversal) is False
