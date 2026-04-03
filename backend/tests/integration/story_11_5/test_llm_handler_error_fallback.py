from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.models.merchant import PersonalityType
from app.services.conversation.handlers.llm_handler import LLMHandler

from .fixtures import count_emojis, make_context, make_llm_service, make_merchant, unique_conv_id


@pytest.mark.parametrize(
    "personality, expect_no_emoji, expect_keyword",
    [
        (PersonalityType.PROFESSIONAL, True, "assist"),
        (PersonalityType.ENTHUSIASTIC, False, None),
    ],
    ids=["professional", "enthusiastic"],
)
@pytest.mark.asyncio
@pytest.mark.test_id("11-5-INT-019")
async def test_classification_leak_uses_personality_template(
    personality, expect_no_emoji, expect_keyword
):
    handler = LLMHandler()
    merchant = make_merchant(personality)
    llm_svc = make_llm_service('{"intent": "product_search", "confidence": 0.9}')
    ctx = make_context(conversation_id=unique_conv_id())
    db = AsyncMock()

    with (
        patch.object(handler, "_detect_product_mentions", return_value=None),
        patch.object(handler, "_get_conversation_context", return_value=None),
    ):
        result = await handler.handle(db, merchant, llm_svc, "hello", ctx)

    if expect_no_emoji:
        assert count_emojis(result.message) == 0
        assert expect_keyword in result.message.lower()
    else:
        assert "😊" in result.message or "🎉" in result.message or "LOVE" in result.message


@pytest.mark.parametrize(
    "personality, business_name, expect_emoji_count",
    [
        (PersonalityType.FRIENDLY, "Cool Shop", 1),
        (PersonalityType.PROFESSIONAL, "Formal Store", 0),
    ],
    ids=["friendly", "professional"],
)
@pytest.mark.asyncio
@pytest.mark.test_id("11-5-INT-020")
async def test_llm_exception_uses_personality_fallback(
    personality, business_name, expect_emoji_count
):
    handler = LLMHandler()
    merchant = make_merchant(personality, business_name=business_name)
    llm_svc = AsyncMock()
    llm_svc.chat = AsyncMock(side_effect=RuntimeError("LLM unavailable"))
    ctx = make_context(conversation_id=unique_conv_id())
    db = AsyncMock()

    with (
        patch.object(handler, "_detect_product_mentions", return_value=None),
        patch.object(handler, "_get_conversation_context", return_value=None),
    ):
        result = await handler.handle(db, merchant, llm_svc, "hello", ctx)

    assert business_name in result.message
    if expect_emoji_count == 0:
        assert count_emojis(result.message) == 0
    else:
        assert count_emojis(result.message) >= expect_emoji_count
