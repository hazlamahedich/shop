"""Tests for ConsentPromptService.

Story 6-1: Opt-In Consent Flow

Tests for consent prompt generation with personality-aware responses.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.models.merchant import PersonalityType
from app.schemas.consent import ConsentStatus
from app.services.consent.consent_prompt_service import ConsentPromptService


@pytest.fixture
def service() -> ConsentPromptService:
    """Create service instance."""
    return ConsentPromptService()


class TestGetConsentPromptMessage:
    """Tests for get_consent_prompt_message method."""

    def test_friendly_prompt(self, service: ConsentPromptService) -> None:
        """Test friendly personality consent prompt."""
        prompt = service.get_consent_prompt_message(PersonalityType.FRIENDLY)

        assert "remember your preferences" in prompt.lower()
        assert "faster" in prompt.lower()

    def test_professional_prompt(self, service: ConsentPromptService) -> None:
        """Test professional personality consent prompt."""
        prompt = service.get_consent_prompt_message(PersonalityType.PROFESSIONAL)

        assert "consent" in prompt.lower()

    def test_enthusiastic_prompt(self, service: ConsentPromptService) -> None:
        """Test enthusiastic personality consent prompt."""
        prompt = service.get_consent_prompt_message(PersonalityType.ENTHUSIASTIC)

        assert "remember" in prompt.lower()
        assert "faster" in prompt.lower()


class TestGetOptInConfirmMessage:
    """Tests for get_opt_in_confirm_message method."""

    def test_friendly_opt_in(self, service: ConsentPromptService) -> None:
        """Test friendly opt-in confirmation."""
        message = service.get_opt_in_confirm_message(PersonalityType.FRIENDLY)

        assert "great" in message.lower()
        assert "preferences" in message.lower()

    def test_professional_opt_in(self, service: ConsentPromptService) -> None:
        """Test professional opt-in confirmation."""
        message = service.get_opt_in_confirm_message(PersonalityType.PROFESSIONAL)

        assert "saved" in message.lower()

    def test_enthusiastic_opt_in(self, service: ConsentPromptService) -> None:
        """Test enthusiastic opt-in confirmation."""
        message = service.get_opt_in_confirm_message(PersonalityType.ENTHUSIASTIC)

        assert "awesome" in message.lower()


class TestGetOptOutConfirmMessage:
    """Tests for get_opt_out_confirm_message method."""

    def test_friendly_opt_out(self, service: ConsentPromptService) -> None:
        """Test friendly opt-out confirmation."""
        message = service.get_opt_out_confirm_message(PersonalityType.FRIENDLY)

        assert "no problem" in message.lower()

    def test_professional_opt_out(self, service: ConsentPromptService) -> None:
        """Test professional opt-out confirmation."""
        message = service.get_opt_out_confirm_message(PersonalityType.PROFESSIONAL)

        assert "recorded" in message.lower()

    def test_enthusiastic_opt_out(self, service: ConsentPromptService) -> None:
        """Test enthusiastic opt-out confirmation."""
        message = service.get_opt_out_confirm_message(PersonalityType.ENTHUSIASTIC)

        assert "no worries" in message.lower()


class TestGetForgetConfirmMessage:
    """Tests for get_forget_confirm_message method."""

    def test_friendly_forget(self, service: ConsentPromptService) -> None:
        """Test friendly forget confirmation."""
        message = service.get_forget_confirm_message(PersonalityType.FRIENDLY)

        assert "forgotten" in message.lower()

    def test_professional_forget(self, service: ConsentPromptService) -> None:
        """Test professional forget confirmation."""
        message = service.get_forget_confirm_message(PersonalityType.PROFESSIONAL)

        assert "deleted" in message.lower()

    def test_enthusiastic_forget(self, service: ConsentPromptService) -> None:
        """Test enthusiastic forget confirmation."""
        message = service.get_forget_confirm_message(PersonalityType.ENTHUSIASTIC)

        assert "poof" in message.lower()


class TestGetConsentQuickReplies:
    """Tests for get_consent_quick_replies method."""

    def test_returns_two_replies(self, service: ConsentPromptService) -> None:
        """Test returns two quick reply buttons."""
        replies = service.get_consent_quick_replies()

        assert len(replies) == 2

    def test_first_reply_is_opt_in(self, service: ConsentPromptService) -> None:
        """Test first quick reply is opt-in."""
        replies = service.get_consent_quick_replies()

        assert "Yes" in replies[0]["title"]
        assert replies[0]["payload"] == "CONSENT_OPT_IN"

    def test_second_reply_is_opt_out(self, service: ConsentPromptService) -> None:
        """Test second quick reply is opt-out."""
        replies = service.get_consent_quick_replies()

        assert "No" in replies[1]["title"]
        assert replies[1]["payload"] == "CONSENT_OPT_OUT"

    def test_replies_have_text_content_type(self, service: ConsentPromptService) -> None:
        """Test all replies have text content type."""
        replies = service.get_consent_quick_replies()

        for reply in replies:
            assert reply["content_type"] == "text"


class TestGetStatusCheckMessage:
    """Tests for get_status_check_message method."""

    def test_opted_in_friendly(self, service: ConsentPromptService) -> None:
        """Test opted_in status with friendly personality."""
        granted_at = datetime(2026, 3, 4, 12, 30, 0, tzinfo=UTC)
        message = service.get_status_check_message(
            personality=PersonalityType.FRIENDLY,
            status=ConsentStatus.OPTED_IN,
            granted_at=granted_at,
        )

        assert "saved" in message.lower()
        assert "march" in message.lower()

    def test_opted_in_professional(self, service: ConsentPromptService) -> None:
        """Test opted_in status with professional personality."""
        granted_at = datetime(2026, 3, 4, 12, 30, 0, tzinfo=UTC)
        message = service.get_status_check_message(
            personality=PersonalityType.PROFESSIONAL,
            status=ConsentStatus.OPTED_IN,
            granted_at=granted_at,
        )

        assert "opted in" in message.lower()
        assert "march" in message.lower()

    def test_opted_in_enthusiastic(self, service: ConsentPromptService) -> None:
        """Test opted_in status with enthusiastic personality."""
        granted_at = datetime(2026, 3, 4, 12, 30, 0, tzinfo=UTC)
        message = service.get_status_check_message(
            personality=PersonalityType.ENTHUSIASTIC,
            status=ConsentStatus.OPTED_IN,
            granted_at=granted_at,
        )

        assert "remember" in message.lower()
        assert "march" in message.lower()

    def test_opted_out_friendly(self, service: ConsentPromptService) -> None:
        """Test opted_out status with friendly personality."""
        message = service.get_status_check_message(
            personality=PersonalityType.FRIENDLY,
            status=ConsentStatus.OPTED_OUT,
        )

        assert "fresh start" in message.lower()

    def test_opted_out_professional(self, service: ConsentPromptService) -> None:
        """Test opted_out status with professional personality."""
        message = service.get_status_check_message(
            personality=PersonalityType.PROFESSIONAL,
            status=ConsentStatus.OPTED_OUT,
        )

        assert "fresh" in message.lower()

    def test_opted_out_enthusiastic(self, service: ConsentPromptService) -> None:
        """Test opted_out status with enthusiastic personality."""
        message = service.get_status_check_message(
            personality=PersonalityType.ENTHUSIASTIC,
            status=ConsentStatus.OPTED_OUT,
        )

        assert "adventure" in message.lower()

    def test_pending_friendly(self, service: ConsentPromptService) -> None:
        """Test pending status with friendly personality."""
        message = service.get_status_check_message(
            personality=PersonalityType.FRIENDLY,
            status=ConsentStatus.PENDING,
        )

        assert "haven't asked" in message.lower()

    def test_pending_professional(self, service: ConsentPromptService) -> None:
        """Test pending status with professional personality."""
        message = service.get_status_check_message(
            personality=PersonalityType.PROFESSIONAL,
            status=ConsentStatus.PENDING,
        )

        assert "no consent preference" in message.lower()

    def test_pending_enthusiastic(self, service: ConsentPromptService) -> None:
        """Test pending status with enthusiastic personality."""
        message = service.get_status_check_message(
            personality=PersonalityType.ENTHUSIASTIC,
            status=ConsentStatus.PENDING,
        )

        assert "haven't set up" in message.lower()

    def test_opted_in_without_date(self, service: ConsentPromptService) -> None:
        """Test opted_in status without granted_at date."""
        message = service.get_status_check_message(
            personality=PersonalityType.PROFESSIONAL,
            status=ConsentStatus.OPTED_IN,
            granted_at=None,
        )

        assert "recently" in message.lower()


class TestGetConsentManagementQuickReplies:
    """Tests for get_consent_management_quick_replies method."""

    def test_opted_in_returns_change_and_delete(self, service: ConsentPromptService) -> None:
        """Test opted_in status returns change and delete options."""
        replies = service.get_consent_management_quick_replies(ConsentStatus.OPTED_IN)

        assert len(replies) == 2
        assert replies[0]["payload"] == "CONSENT_CHANGE"
        assert replies[1]["payload"] == "CONSENT_DELETE"

    def test_opted_out_returns_save_option(self, service: ConsentPromptService) -> None:
        """Test opted_out status returns save option."""
        replies = service.get_consent_management_quick_replies(ConsentStatus.OPTED_OUT)

        assert len(replies) == 1
        assert replies[0]["payload"] == "CONSENT_OPT_IN"

    def test_pending_returns_yes_and_no(self, service: ConsentPromptService) -> None:
        """Test pending status returns yes and no options."""
        replies = service.get_consent_management_quick_replies(ConsentStatus.PENDING)

        assert len(replies) == 2
        assert replies[0]["payload"] == "CONSENT_OPT_IN"
        assert replies[1]["payload"] == "CONSENT_OPT_OUT"
