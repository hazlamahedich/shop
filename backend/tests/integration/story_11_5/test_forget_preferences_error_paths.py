from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.models.merchant import PersonalityType
from app.services.conversation.handlers.forget_preferences_handler import ForgetPreferencesHandler

from .fixtures import count_emojis, make_context, make_llm_service, make_merchant


class TestForgetPreferencesHandlerErrorPaths:
    @pytest.mark.asyncio
    @pytest.mark.test_id("11-5-INT-028")
    async def test_rate_limited_uses_professional_template(self):
        from app.core.errors import APIError, ErrorCode

        handler = ForgetPreferencesHandler()
        merchant = make_merchant(PersonalityType.PROFESSIONAL)
        llm_svc = make_llm_service()
        ctx = make_context()
        db = AsyncMock()

        with patch(
            "app.services.conversation.handlers.forget_preferences_handler.ConversationConsentService"
        ) as MockSvc:
            MockSvc.return_value.handle_forget_preferences_with_deletion = AsyncMock(
                side_effect=APIError(
                    code=ErrorCode.VALIDATION_ERROR,
                    message="Rate limit exceeded. Please wait before trying again.",
                )
            )
            result = await handler.handle(db, merchant, llm_svc, "forget me", ctx)

        assert count_emojis(result.message) == 0
        assert result.metadata.get("rate_limited") is True

    @pytest.mark.asyncio
    @pytest.mark.test_id("11-5-INT-029")
    async def test_rate_limited_uses_friendly_template(self):
        from app.core.errors import APIError, ErrorCode

        handler = ForgetPreferencesHandler()
        merchant = make_merchant(PersonalityType.FRIENDLY)
        llm_svc = make_llm_service()
        ctx = make_context()
        db = AsyncMock()

        with patch(
            "app.services.conversation.handlers.forget_preferences_handler.ConversationConsentService"
        ) as MockSvc:
            MockSvc.return_value.handle_forget_preferences_with_deletion = AsyncMock(
                side_effect=APIError(
                    code=ErrorCode.VALIDATION_ERROR,
                    message="Rate limit exceeded. Please wait before trying again.",
                )
            )
            result = await handler.handle(db, merchant, llm_svc, "forget me", ctx)

        assert count_emojis(result.message) >= 1

    @pytest.mark.asyncio
    @pytest.mark.test_id("11-5-INT-030")
    async def test_api_error_uses_correct_template(self):
        from app.core.errors import APIError, ErrorCode

        handler = ForgetPreferencesHandler()
        merchant = make_merchant(PersonalityType.PROFESSIONAL)
        llm_svc = make_llm_service()
        ctx = make_context()
        db = AsyncMock()

        with patch(
            "app.services.conversation.handlers.forget_preferences_handler.ConversationConsentService"
        ) as MockSvc:
            MockSvc.return_value.handle_forget_preferences_with_deletion = AsyncMock(
                side_effect=APIError(
                    code=ErrorCode.INTERNAL_ERROR,
                    message="Internal error occurred.",
                )
            )
            result = await handler.handle(db, merchant, llm_svc, "forget me", ctx)

        assert count_emojis(result.message) == 0
        assert "error" in result.message.lower() or "try again" in result.message.lower()

    @pytest.mark.asyncio
    @pytest.mark.test_id("11-5-INT-031")
    async def test_generic_exception_uses_correct_template(self):
        handler = ForgetPreferencesHandler()
        merchant = make_merchant(PersonalityType.FRIENDLY)
        llm_svc = make_llm_service()
        ctx = make_context()
        db = AsyncMock()

        with patch(
            "app.services.conversation.handlers.forget_preferences_handler.ConversationConsentService"
        ) as MockSvc:
            MockSvc.return_value.handle_forget_preferences_with_deletion = AsyncMock(
                side_effect=RuntimeError("Unexpected crash")
            )
            result = await handler.handle(db, merchant, llm_svc, "forget me", ctx)

        assert (
            "unexpected" in result.message.lower()
            or "Oops" in result.message
            or "oops" in result.message
        )

    @pytest.mark.asyncio
    @pytest.mark.test_id("11-5-INT-032")
    async def test_generic_exception_enthusiastic_template(self):
        handler = ForgetPreferencesHandler()
        merchant = make_merchant(PersonalityType.ENTHUSIASTIC)
        llm_svc = make_llm_service()
        ctx = make_context()
        db = AsyncMock()

        with patch(
            "app.services.conversation.handlers.forget_preferences_handler.ConversationConsentService"
        ) as MockSvc:
            MockSvc.return_value.handle_forget_preferences_with_deletion = AsyncMock(
                side_effect=RuntimeError("Unexpected crash")
            )
            result = await handler.handle(db, merchant, llm_svc, "forget me", ctx)

        assert count_emojis(result.message) >= 1
