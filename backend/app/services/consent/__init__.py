"""Consent service package.

Manages user consent for cart and session persistence with GDPR/CCPA compliance.
"""

from app.services.consent.consent_service import ConsentService, ConsentStatus

__all__ = ["ConsentService", "ConsentStatus"]
