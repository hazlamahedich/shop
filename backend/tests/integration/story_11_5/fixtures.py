from __future__ import annotations

import re
from itertools import count
from typing import Any
from unittest.mock import AsyncMock, MagicMock

from app.models.merchant import PersonalityType
from app.services.conversation.schemas import (
    Channel,
    ConsentState,
    ConversationContext,
)
from app.services.personality.conversation_templates import register_conversation_templates

register_conversation_templates()

EMOJI_REGEX = re.compile(
    "["
    "\U0001f600-\U0001f64f"
    "\U0001f300-\U0001f5ff"
    "\U0001f680-\U0001f6ff"
    "\U0001f1e0-\U0001f1ff"
    "\U0001f900-\U0001f9ff"
    "\U0001fa00-\U0001fa6f"
    "\U0001fa70-\U0001faff"
    "\U00002600-\U000026ff"
    "\U00002702-\U000027b0"
    "\U000024c2-\U0001f251"
    "\U0000fe00-\U0000fe0f"
    "]",
    flags=re.UNICODE,
)

_conv_counter = count(1)


def count_emojis(text: str) -> int:
    return len(EMOJI_REGEX.findall(text))


def make_merchant(
    personality: PersonalityType = PersonalityType.FRIENDLY,
    business_name: str = "Test Store",
    bot_name: str = "TestBot",
    onboarding_mode: str = "ecommerce",
    merchant_id: int = 1,
) -> MagicMock:
    merchant = MagicMock()
    merchant.id = merchant_id
    merchant.personality = personality
    merchant.business_name = business_name
    merchant.bot_name = bot_name
    merchant.onboarding_mode = onboarding_mode
    return merchant


def make_context(
    session_id: str = "test-session",
    conversation_id: int | None = None,
    history: list[dict[str, Any]] | None = None,
    channel: Channel = Channel.WIDGET,
) -> ConversationContext:
    return ConversationContext(
        session_id=session_id,
        merchant_id=1,
        channel=channel,
        conversation_id=conversation_id,
        conversation_history=history or [],
        consent_state=ConsentState(),
        metadata={},
    )


def make_llm_service(response_text: str = "Here is a helpful response.") -> AsyncMock:
    llm_response = MagicMock()
    llm_response.content = response_text
    svc = AsyncMock()
    svc.chat = AsyncMock(return_value=llm_response)
    return svc


def unique_conv_id() -> int:
    return next(_conv_counter)
