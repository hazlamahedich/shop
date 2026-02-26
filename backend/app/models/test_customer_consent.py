"""Tests for CustomerConsent aggregate model.

Story 6-1: Opt-In Consent Flow

Tests for the unified consent view aggregate model.
"""

from __future__ import annotations

import pytest

from app.models.consent import Consent, ConsentType, ConsentSource
from app.models.customer_consent import CustomerConsent
from app.schemas.consent import ConsentStatus


@pytest.fixture
def sample_consents() -> list[Consent]:
    """Create sample consent records for testing."""
    conversation_consent = Consent.create(
        session_id="test_session",
        merchant_id=1,
        consent_type=ConsentType.CONVERSATION,
        source_channel=ConsentSource.WIDGET.value,
    )
    conversation_consent.grant()

    cart_consent = Consent.create(
        session_id="test_session",
        merchant_id=1,
        consent_type=ConsentType.CART,
    )
    cart_consent.grant()

    marketing_consent = Consent.create(
        session_id="test_session",
        merchant_id=1,
        consent_type=ConsentType.MARKETING,
    )

    return [conversation_consent, cart_consent, marketing_consent]


def test_customer_consent_has_any_consent_true(sample_consents: list[Consent]) -> None:
    """Test has_any_consent returns True when any consent is granted."""
    customer_consent = CustomerConsent(
        session_id="test_session",
        merchant_id=1,
        consents=sample_consents,
    )

    assert customer_consent.has_any_consent() is True


def test_customer_consent_has_any_consent_false() -> None:
    """Test has_any_consent returns False when no consents granted."""
    ungranted_consent = Consent.create(
        session_id="test_session",
        merchant_id=1,
        consent_type=ConsentType.CART,
    )

    customer_consent = CustomerConsent(
        session_id="test_session",
        merchant_id=1,
        consents=[ungranted_consent],
    )

    assert customer_consent.has_any_consent() is False


def test_customer_consent_has_any_consent_empty() -> None:
    """Test has_any_consent returns False when no consents exist."""
    customer_consent = CustomerConsent(
        session_id="test_session",
        merchant_id=1,
        consents=[],
    )

    assert customer_consent.has_any_consent() is False


def test_customer_consent_can_store_conversation(sample_consents: list[Consent]) -> None:
    """Test can_store_conversation returns True when consent granted."""
    customer_consent = CustomerConsent(
        session_id="test_session",
        merchant_id=1,
        consents=sample_consents,
    )

    assert customer_consent.can_store_conversation() is True


def test_customer_consent_can_store_conversation_false() -> None:
    """Test can_store_conversation returns False when no consent."""
    customer_consent = CustomerConsent(
        session_id="test_session",
        merchant_id=1,
        consents=[],
    )

    assert customer_consent.can_store_conversation() is False


def test_customer_consent_can_store_conversation_revoked() -> None:
    """Test can_store_conversation returns False when consent revoked."""
    revoked_consent = Consent.create(
        session_id="test_session",
        merchant_id=1,
        consent_type=ConsentType.CONVERSATION,
    )
    revoked_consent.grant()
    revoked_consent.revoke()

    customer_consent = CustomerConsent(
        session_id="test_session",
        merchant_id=1,
        consents=[revoked_consent],
    )

    assert customer_consent.can_store_conversation() is False


def test_customer_consent_can_persist_cart(sample_consents: list[Consent]) -> None:
    """Test can_persist_cart returns True when consent granted."""
    customer_consent = CustomerConsent(
        session_id="test_session",
        merchant_id=1,
        consents=sample_consents,
    )

    assert customer_consent.can_persist_cart() is True


def test_customer_consent_can_persist_cart_false() -> None:
    """Test can_persist_cart returns False when no consent."""
    customer_consent = CustomerConsent(
        session_id="test_session",
        merchant_id=1,
        consents=[],
    )

    assert customer_consent.can_persist_cart() is False


def test_customer_consent_get_consent_status_opted_in(sample_consents: list[Consent]) -> None:
    """Test get_consent_status returns OPTED_IN for granted consent."""
    customer_consent = CustomerConsent(
        session_id="test_session",
        merchant_id=1,
        consents=sample_consents,
    )

    status = customer_consent.get_consent_status(ConsentType.CONVERSATION)
    assert status == ConsentStatus.OPTED_IN


def test_customer_consent_get_consent_status_pending() -> None:
    """Test get_consent_status returns PENDING for non-existent consent."""
    customer_consent = CustomerConsent(
        session_id="test_session",
        merchant_id=1,
        consents=[],
    )

    status = customer_consent.get_consent_status(ConsentType.CONVERSATION)
    assert status == ConsentStatus.PENDING


def test_customer_consent_get_consent_status_opted_out() -> None:
    """Test get_consent_status returns OPTED_OUT for revoked consent."""
    revoked_consent = Consent.create(
        session_id="test_session",
        merchant_id=1,
        consent_type=ConsentType.CONVERSATION,
    )
    revoked_consent.grant()
    revoked_consent.revoke()

    customer_consent = CustomerConsent(
        session_id="test_session",
        merchant_id=1,
        consents=[revoked_consent],
    )

    status = customer_consent.get_consent_status(ConsentType.CONVERSATION)
    assert status == ConsentStatus.OPTED_OUT


def test_customer_consent_get_conversation_consent_status(sample_consents: list[Consent]) -> None:
    """Test get_conversation_consent_status convenience method."""
    customer_consent = CustomerConsent(
        session_id="test_session",
        merchant_id=1,
        consents=sample_consents,
    )

    status = customer_consent.get_conversation_consent_status()
    assert status == ConsentStatus.OPTED_IN


def test_customer_consent_get_all_consents(sample_consents: list[Consent]) -> None:
    """Test get_all_consents returns copy of consents list."""
    customer_consent = CustomerConsent(
        session_id="test_session",
        merchant_id=1,
        consents=sample_consents,
    )

    all_consents = customer_consent.get_all_consents()

    assert len(all_consents) == 3
    assert all_consents is not sample_consents


def test_customer_consent_get_consents_by_status(sample_consents: list[Consent]) -> None:
    """Test get_consents_by_status filters correctly."""
    customer_consent = CustomerConsent(
        session_id="test_session",
        merchant_id=1,
        consents=sample_consents,
    )

    opted_in = customer_consent.get_consents_by_status(ConsentStatus.OPTED_IN)
    pending = customer_consent.get_consents_by_status(ConsentStatus.PENDING)

    assert len(opted_in) == 2
    assert len(pending) == 1


def test_customer_consent_has_consent_message_been_shown_true() -> None:
    """Test has_consent_message_been_shown returns True when shown."""
    consent = Consent.create(
        session_id="test_session",
        merchant_id=1,
        consent_type=ConsentType.CONVERSATION,
    )
    consent.mark_message_shown()

    customer_consent = CustomerConsent(
        session_id="test_session",
        merchant_id=1,
        consents=[consent],
    )

    assert customer_consent.has_consent_message_been_shown() is True


def test_customer_consent_has_consent_message_been_shown_false() -> None:
    """Test has_consent_message_been_shown returns False when not shown."""
    consent = Consent.create(
        session_id="test_session",
        merchant_id=1,
        consent_type=ConsentType.CONVERSATION,
    )

    customer_consent = CustomerConsent(
        session_id="test_session",
        merchant_id=1,
        consents=[consent],
    )

    assert customer_consent.has_consent_message_been_shown() is False


def test_customer_consent_get_consent_source() -> None:
    """Test get_consent_source returns source channel."""
    consent = Consent.create(
        session_id="test_session",
        merchant_id=1,
        consent_type=ConsentType.CONVERSATION,
        source_channel=ConsentSource.WIDGET.value,
    )

    customer_consent = CustomerConsent(
        session_id="test_session",
        merchant_id=1,
        consents=[consent],
    )

    assert customer_consent.get_consent_source() == ConsentSource.WIDGET.value


def test_customer_consent_get_consent_source_none() -> None:
    """Test get_consent_source returns None when no consent."""
    customer_consent = CustomerConsent(
        session_id="test_session",
        merchant_id=1,
        consents=[],
    )

    assert customer_consent.get_consent_source() is None


def test_customer_consent_from_consents(sample_consents: list[Consent]) -> None:
    """Test from_consents factory method."""
    customer_consent = CustomerConsent.from_consents(
        session_id="test_session",
        merchant_id=1,
        consents=sample_consents,
    )

    assert customer_consent.session_id == "test_session"
    assert customer_consent.merchant_id == 1
    assert len(customer_consent.consents) == 3
    assert customer_consent.has_any_consent() is True


def test_customer_consent_multiple_consent_types() -> None:
    """Test handling multiple consent types correctly."""
    conversation_consent = Consent.create(
        session_id="test_session",
        merchant_id=1,
        consent_type=ConsentType.CONVERSATION,
    )
    conversation_consent.grant()

    cart_consent = Consent.create(
        session_id="test_session",
        merchant_id=1,
        consent_type=ConsentType.CART,
    )

    customer_consent = CustomerConsent(
        session_id="test_session",
        merchant_id=1,
        consents=[conversation_consent, cart_consent],
    )

    assert customer_consent.can_store_conversation() is True
    assert customer_consent.can_persist_cart() is False
    assert customer_consent.has_any_consent() is True
