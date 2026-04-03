from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.models.merchant import PersonalityType
from app.services.conversation.handlers.llm_handler import LLMHandler
from app.services.personality.personality_tracker import get_personality_tracker

from .fixtures import make_merchant


class TestLLMHandlerMidConversationReinforcement:
    @pytest.mark.asyncio
    @pytest.mark.test_id("11-5-INT-006")
    async def test_reinforcement_injected_at_turn_5(self):
        handler = LLMHandler()
        conv_id = "reinforce-test-5"
        tracker = get_personality_tracker()
        for i in range(5):
            tracker.record_validation(conv_id, PersonalityType.PROFESSIONAL, True, i + 1)

        prompt = await handler._build_system_prompt(
            db=AsyncMock(),
            merchant=make_merchant(PersonalityType.PROFESSIONAL),
            bot_name="Bot",
            business_name="Store",
            personality_type=PersonalityType.PROFESSIONAL,
            pending_state=None,
            turn_number=5,
            conversation_id=conv_id,
        )

        assert "PERSONALITY CONSISTENCY REMINDER" in prompt
        assert "NO emojis anywhere" in prompt

    @pytest.mark.asyncio
    @pytest.mark.test_id("11-5-INT-007")
    async def test_no_reinforcement_below_threshold(self):
        handler = LLMHandler()
        prompt = await handler._build_system_prompt(
            db=AsyncMock(),
            merchant=make_merchant(PersonalityType.FRIENDLY),
            bot_name="Bot",
            business_name="Store",
            personality_type=PersonalityType.FRIENDLY,
            pending_state=None,
            turn_number=4,
            conversation_id="conv-low-turn",
        )

        assert "PERSONALITY CONSISTENCY REMINDER" not in prompt

    @pytest.mark.asyncio
    @pytest.mark.test_id("11-5-INT-008")
    async def test_reinforcement_with_low_consistency_adds_warning(self):
        handler = LLMHandler()
        conv_id = "reinforce-low-score"
        tracker = get_personality_tracker()
        for i in range(5):
            tracker.record_validation(conv_id, PersonalityType.FRIENDLY, i < 2, i + 1)

        prompt = await handler._build_system_prompt(
            db=AsyncMock(),
            merchant=make_merchant(PersonalityType.FRIENDLY),
            bot_name="Bot",
            business_name="Store",
            personality_type=PersonalityType.FRIENDLY,
            pending_state=None,
            turn_number=5,
            conversation_id=conv_id,
        )

        assert "PERSONALITY CONSISTENCY REMINDER" in prompt
        assert "consistency has been declining" in prompt

    @pytest.mark.asyncio
    @pytest.mark.test_id("11-5-INT-009")
    async def test_reinforcement_per_personality_type(self):
        handler = LLMHandler()
        tracker = get_personality_tracker()

        for ptype in PersonalityType:
            tracker.reset()
            conv_id = f"reinforce-{ptype.value}"
            for i in range(5):
                tracker.record_validation(conv_id, ptype, True, i + 1)

            prompt = await handler._build_system_prompt(
                db=AsyncMock(),
                merchant=make_merchant(ptype),
                bot_name="Bot",
                business_name="Store",
                personality_type=ptype,
                pending_state=None,
                turn_number=5,
                conversation_id=conv_id,
            )

            assert "PERSONALITY CONSISTENCY REMINDER" in prompt

    @pytest.mark.asyncio
    @pytest.mark.test_id("11-5-INT-010")
    async def test_no_reinforcement_without_conversation_id(self):
        handler = LLMHandler()
        prompt = await handler._build_system_prompt(
            db=AsyncMock(),
            merchant=make_merchant(PersonalityType.FRIENDLY),
            bot_name="Bot",
            business_name="Store",
            personality_type=PersonalityType.FRIENDLY,
            pending_state=None,
            turn_number=10,
            conversation_id=None,
        )

        assert "PERSONALITY CONSISTENCY REMINDER" not in prompt
