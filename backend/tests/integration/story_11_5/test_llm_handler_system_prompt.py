from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.models.merchant import PersonalityType
from app.services.conversation.handlers.llm_handler import LLMHandler

from .fixtures import make_merchant


@pytest.mark.parametrize(
    "personality, bot_name, business_name, keyword",
    [
        (PersonalityType.PROFESSIONAL, "AcmeBot", "Acme Corp", "professional"),
        (PersonalityType.FRIENDLY, "FriendlyBot", "Happy Store", "friendly"),
        (PersonalityType.ENTHUSIASTIC, "ExcitedBot", "Fun Store", "enthusiastic"),
    ],
    ids=["professional", "friendly", "enthusiastic"],
)
@pytest.mark.asyncio
@pytest.mark.test_id("11-5-INT-034")
async def test_system_prompt_contains_personality_guidance(
    personality, bot_name, business_name, keyword
):
    handler = LLMHandler()
    prompt = await handler._build_system_prompt(
        db=AsyncMock(),
        merchant=make_merchant(personality, business_name=business_name),
        bot_name=bot_name,
        business_name=business_name,
        personality_type=personality,
        pending_state=None,
        turn_number=1,
        conversation_id=None,
    )

    assert keyword in prompt.lower()
