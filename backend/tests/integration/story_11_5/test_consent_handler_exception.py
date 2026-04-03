from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.models.merchant import PersonalityType
from app.services.conversation.handlers.check_consent_handler import CheckConsentHandler

from .fixtures import count_emojis, make_context, make_llm_service, make_merchant


@pytest.mark.parametrize(
    "personality, min_emojis, max_emojis, has_exclamation, keyword",
    [
        (PersonalityType.PROFESSIONAL, 0, 0, False, "unable"),
        (PersonalityType.FRIENDLY, 1, 99, False, None),
        (PersonalityType.ENTHUSIASTIC, 1, 99, True, None),
    ],
    ids=["professional", "friendly", "enthusiastic"],
)
@pytest.mark.asyncio
@pytest.mark.test_id("11-5-INT-027")
async def test_exception_uses_correct_personality_template(
    personality, min_emojis, max_emojis, has_exclamation, keyword
):
    handler = CheckConsentHandler()
    merchant = make_merchant(personality)
    llm_svc = make_llm_service()
    ctx = make_context()
    db = AsyncMock()

    with patch(
        "app.services.conversation.handlers.check_consent_handler.ConversationConsentService"
    ) as MockSvc:
        MockSvc.return_value.get_consent_for_conversation = AsyncMock(
            side_effect=RuntimeError("DB connection lost")
        )
        result = await handler.handle(db, merchant, llm_svc, "check consent", ctx)

    emoji_count = count_emojis(result.message)
    assert min_emojis <= emoji_count <= max_emojis
    if has_exclamation:
        assert "!" in result.message
    if keyword:
        assert keyword in result.message.lower() or "try again" in result.message.lower()
