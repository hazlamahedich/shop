"""Tests for Consent ORM model.

Story 6-1: Opt-In Consent Flow

Tests for extended consent model including:
- CONVERSATION consent type
- source_channel field
- consent_message_shown field
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.models.consent import Consent, ConsentType, ConsentSource


def test_consent_type_constants() -> None:
    """Test consent type constants are defined."""
    assert ConsentType.CART == "cart"
    assert ConsentType.DATA_COLLECTION == "data_collection"
    assert ConsentType.MARKETING == "marketing"
    assert ConsentType.CONVERSATION == "conversation"


def test_consent_source_enum() -> None:
    """Test ConsentSource enum values."""
    assert ConsentSource.MESSENGER == "messenger"
    assert ConsentSource.WIDGET == "widget"
    assert ConsentSource.PREVIEW == "preview"


def test_consent_create_with_source_channel() -> None:
    """Test creating consent with source channel."""
    consent = Consent.create(
        session_id="test_session",
        merchant_id=1,
        consent_type=ConsentType.CONVERSATION,
        source_channel=ConsentSource.WIDGET.value,
    )

    assert consent.session_id == "test_session"
    assert consent.merchant_id == 1
    assert consent.consent_type == ConsentType.CONVERSATION
    assert consent.source_channel == ConsentSource.WIDGET.value
    assert consent.granted is False
    assert consent.consent_message_shown is False


def test_consent_create_without_source_channel() -> None:
    """Test creating consent without source channel (backwards compatible)."""
    consent = Consent.create(
        session_id="test_session",
        merchant_id=1,
        consent_type=ConsentType.CART,
    )

    assert consent.session_id == "test_session"
    assert consent.merchant_id == 1
    assert consent.consent_type == ConsentType.CART
    assert consent.source_channel is None
    assert consent.granted is False


def test_consent_grant_sets_timestamp() -> None:
    """Test granting consent sets granted_at timestamp."""
    consent = Consent.create(
        session_id="test_session",
        merchant_id=1,
        consent_type=ConsentType.CONVERSATION,
        source_channel=ConsentSource.WIDGET.value,
    )

    assert consent.granted_at is None

    consent.grant()

    assert consent.granted is True
    assert consent.granted_at is not None
    assert consent.revoked_at is None


def test_consent_grant_with_audit_info() -> None:
    """Test granting consent with IP address and user agent."""
    consent = Consent.create(
        session_id="test_session",
        merchant_id=1,
        consent_type=ConsentType.CONVERSATION,
        source_channel=ConsentSource.WIDGET.value,
    )

    consent.grant(
        ip_address="192.168.1.1",
        user_agent="Mozilla/5.0",
    )

    assert consent.ip_address == "192.168.1.1"
    assert consent.user_agent == "Mozilla/5.0"


def test_consent_revoke() -> None:
    """Test revoking consent sets revoked_at timestamp."""
    consent = Consent.create(
        session_id="test_session",
        merchant_id=1,
        consent_type=ConsentType.CONVERSATION,
    )

    consent.grant()
    assert consent.is_valid() is True

    consent.revoke()

    assert consent.granted is False
    assert consent.revoked_at is not None
    assert consent.is_valid() is False


def test_consent_is_valid() -> None:
    """Test is_valid checks both granted and not revoked."""
    consent = Consent.create(
        session_id="test_session",
        merchant_id=1,
        consent_type=ConsentType.CONVERSATION,
    )

    # Not granted
    assert consent.is_valid() is False

    # Granted
    consent.grant()
    assert consent.is_valid() is True

    # Revoked
    consent.revoke()
    assert consent.is_valid() is False


def test_consent_mark_message_shown() -> None:
    """Test marking consent message as shown."""
    consent = Consent.create(
        session_id="test_session",
        merchant_id=1,
        consent_type=ConsentType.CONVERSATION,
    )

    assert consent.consent_message_shown is False

    consent.mark_message_shown()

    assert consent.consent_message_shown is True


def test_consent_repr() -> None:
    """Test consent string representation."""
    consent = Consent.create(
        session_id="test_session_12345",
        merchant_id=1,
        consent_type=ConsentType.CONVERSATION,
    )

    repr_str = repr(consent)
    assert "Consent" in repr_str
    assert "test_ses" in repr_str  # First 8 chars of session_id
    assert "conversation" in repr_str
    assert "granted=False" in repr_str


def test_consent_timestamps_use_utc() -> None:
    """Test that timestamps use UTC timezone."""
    consent = Consent.create(
        session_id="test_session",
        merchant_id=1,
        consent_type=ConsentType.CONVERSATION,
    )

    consent.grant()

    assert consent.granted_at is not None
    assert consent.granted_at.tzinfo is not None
    # Verify it's UTC (offset should be 0)
    assert consent.granted_at.utcoffset().total_seconds() == 0

    consent.revoke()

    assert consent.revoked_at is not None
    assert consent.revoked_at.tzinfo is not None
    assert consent.revoked_at.utcoffset().total_seconds() == 0


def test_consent_grant_clears_revoked_at() -> None:
    """Test granting consent clears previous revocation."""
    consent = Consent.create(
        session_id="test_session",
        merchant_id=1,
        consent_type=ConsentType.CONVERSATION,
    )

    # Grant, then revoke
    consent.grant()
    consent.revoke()
    assert consent.revoked_at is not None

    # Grant again should clear revoked_at
    consent.grant()
    assert consent.revoked_at is None
    assert consent.granted is True
