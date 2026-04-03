from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.models.merchant import PersonalityType
from app.services.conversation.handlers.clarification_handler import ClarificationHandler

from .fixtures import count_emojis, make_context, make_llm_service, make_merchant


@pytest.mark.parametrize(
    "personality, min_emojis, has_exclamation, extra_text",
    [
        (PersonalityType.PROFESSIONAL, 0, False, "additional details"),
        (PersonalityType.FRIENDLY, 1, False, None),
        (PersonalityType.ENTHUSIASTIC, 1, True, None),
    ],
    ids=["professional", "friendly", "enthusiastic"],
)
@pytest.mark.asyncio
@pytest.mark.test_id("11-5-INT-021")
async def test_valueerror_fallback_uses_correct_template(
    personality, min_emojis, has_exclamation, extra_text
):
    handler = ClarificationHandler()
    merchant = make_merchant(personality)
    llm_svc = make_llm_service()
    ctx = make_context()
    db = AsyncMock()

    with patch(
        "app.services.conversation.handlers.clarification_handler.QuestionGenerator"
    ) as MockQG:
        mock_qg = MockQG.return_value
        mock_qg.generate_next_question = AsyncMock(side_effect=ValueError("no questions"))
        result = await handler.handle(db, merchant, llm_svc, "I want shoes", ctx, {})

    if min_emojis == 0:
        assert count_emojis(result.message) == 0
    else:
        assert count_emojis(result.message) >= min_emojis
    if has_exclamation:
        assert "!" in result.message
    if extra_text:
        assert extra_text in result.message.lower()
