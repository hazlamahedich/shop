"""CustomerConsent aggregate model for unified consent view.

Story 6-1: Opt-In Consent Flow

Provides a unified view of all consent types for a customer,
enabling easy consent status checks across the application.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from app.models.consent import Consent, ConsentType, ConsentSource
from app.schemas.consent import ConsentStatus


@dataclass
class CustomerConsent:
    """Aggregate model for unified consent view.

    Aggregates all consent records for a customer (session) and provides
    convenient methods for checking consent status.

    Attributes:
        session_id: Widget session ID or PSID
        merchant_id: Merchant ID
        consents: List of all consent records for this customer
    """

    session_id: str
    merchant_id: int
    consents: list[Consent] = field(default_factory=list)

    def has_any_consent(self) -> bool:
        """Check if customer has any valid consent.

        Returns:
            True if any consent is granted and not revoked
        """
        return any(consent.is_valid() for consent in self.consents)

    def can_store_conversation(self) -> bool:
        """Check if customer has consented to conversation data storage.

        Returns:
            True if conversation consent is granted and not revoked
        """
        conversation_consent = self._get_consent_by_type(ConsentType.CONVERSATION)
        if conversation_consent is None:
            return False
        return conversation_consent.is_valid()

    def can_persist_cart(self) -> bool:
        """Check if customer has consented to cart persistence.

        Returns:
            True if cart consent is granted and not revoked
        """
        cart_consent = self._get_consent_by_type(ConsentType.CART)
        if cart_consent is None:
            return False
        return cart_consent.is_valid()

    def get_consent_status(self, consent_type: str) -> ConsentStatus:
        """Get consent status for a specific consent type.

        Args:
            consent_type: Type of consent to check

        Returns:
            ConsentStatus enum value
        """
        consent = self._get_consent_by_type(consent_type)
        if consent is None:
            return ConsentStatus.PENDING

        return self._get_consent_status_for_record(consent)

    def get_conversation_consent_status(self) -> ConsentStatus:
        """Get conversation consent status.

        Returns:
            ConsentStatus for conversation consent
        """
        return self.get_consent_status(ConsentType.CONVERSATION)

    def get_all_consents(self) -> list[Consent]:
        """Get all consent records.

        Returns:
            List of all consent records
        """
        return self.consents.copy()

    def get_consents_by_status(self, status: ConsentStatus) -> list[Consent]:
        """Get consent records matching a specific status.

        Args:
            status: ConsentStatus to filter by

        Returns:
            List of consent records with matching status
        """
        result = []
        for consent in self.consents:
            consent_status = self._get_consent_status_for_record(consent)
            if consent_status == status:
                result.append(consent)
        return result

    def has_consent_message_been_shown(self) -> bool:
        """Check if consent message has been shown for conversation consent.

        Returns:
            True if consent prompt was shown for conversation
        """
        conversation_consent = self._get_consent_by_type(ConsentType.CONVERSATION)
        if conversation_consent is None:
            return False
        return conversation_consent.consent_message_shown

    def get_consent_source(self) -> Optional[str]:
        """Get the source channel for conversation consent.

        Returns:
            Source channel (messenger, widget, preview) or None
        """
        conversation_consent = self._get_consent_by_type(ConsentType.CONVERSATION)
        if conversation_consent is None:
            return None
        return conversation_consent.source_channel

    def _get_consent_by_type(self, consent_type: str) -> Optional[Consent]:
        """Get consent record by type.

        Args:
            consent_type: Type of consent to find

        Returns:
            Consent record or None if not found
        """
        for consent in self.consents:
            if consent.consent_type == consent_type:
                return consent
        return None

    def _get_consent_status_for_record(self, consent: Consent) -> ConsentStatus:
        """Get ConsentStatus for a specific consent record.

        Args:
            consent: Consent record to check

        Returns:
            ConsentStatus enum value
        """
        if consent.is_valid():
            return ConsentStatus.OPTED_IN

        if consent.revoked_at is not None:
            return ConsentStatus.OPTED_OUT

        return ConsentStatus.PENDING

    @classmethod
    def from_consents(
        cls,
        session_id: str,
        merchant_id: int,
        consents: list[Consent],
    ) -> "CustomerConsent":
        """Create CustomerConsent from a list of consent records.

        Args:
            session_id: Widget session ID or PSID
            merchant_id: Merchant ID
            consents: List of consent records

        Returns:
            CustomerConsent instance
        """
        return cls(
            session_id=session_id,
            merchant_id=merchant_id,
            consents=consents,
        )
