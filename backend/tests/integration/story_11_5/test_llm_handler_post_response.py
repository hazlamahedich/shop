from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.models.merchant import PersonalityType
from app.services.conversation.handlers.llm_handler import LLMHandler
from app.services.personality.personality_tracker import get_personality_tracker

from .fixtures import make_context, make_llm_service, make_merchant, unique_conv_id


class TestLLMHandlerPostResponseValidation:
    @pytest.mark.asyncio
    @pytest.mark.test_id("11-5-INT-001")
    async def test_validation_recorded_on_successful_response(self):
        handler = LLMHandler()
        merchant = make_merchant(PersonalityType.PROFESSIONAL)
        llm_svc = make_llm_service("Here are the available products for your consideration.")
        conv_id = unique_conv_id()
        ctx = make_context(conversation_id=conv_id)
        db = AsyncMock()

        with (
            patch.object(handler, "_detect_product_mentions", return_value=None),
            patch.object(handler, "_get_conversation_context", return_value=None),
        ):
            await handler.handle(db, merchant, llm_svc, "show me products", ctx)

        tracker = get_personality_tracker()
        report = tracker.get_consistency_report(str(conv_id))
        assert report.turn_count == 1
        assert report.consistency_score == 1.0
        assert not report.is_drifting

    @pytest.mark.asyncio
    @pytest.mark.test_id("11-5-INT-002")
    async def test_validation_records_failure_for_personality_violation(self):
        handler = LLMHandler()
        merchant = make_merchant(PersonalityType.PROFESSIONAL)
        llm_svc = make_llm_service("Check these out! 😊🎉 Here's what I found!")
        conv_id = unique_conv_id()
        ctx = make_context(conversation_id=conv_id)
        db = AsyncMock()

        with (
            patch.object(handler, "_detect_product_mentions", return_value=None),
            patch.object(handler, "_get_conversation_context", return_value=None),
        ):
            await handler.handle(db, merchant, llm_svc, "show me products", ctx)

        tracker = get_personality_tracker()
        report = tracker.get_consistency_report(str(conv_id))
        assert report.turn_count == 1
        assert report.violation_count == 1
        assert report.consistency_score == 0.0

    @pytest.mark.asyncio
    @pytest.mark.test_id("11-5-INT-003")
    async def test_drift_detected_after_consecutive_failures(self):
        handler = LLMHandler()
        merchant = make_merchant(PersonalityType.PROFESSIONAL)
        db = AsyncMock()
        conv_id = unique_conv_id()

        for turn in range(4):
            llm_svc = make_llm_service("Awesome! Check these out! 😊🎉")
            history = [{"role": "user", "content": f"msg {i}"} for i in range(turn)]
            ctx = make_context(conversation_id=conv_id, history=history)

            with (
                patch.object(handler, "_detect_product_mentions", return_value=None),
                patch.object(handler, "_get_conversation_context", return_value=None),
            ):
                await handler.handle(db, merchant, llm_svc, f"query {turn}", ctx)

        tracker = get_personality_tracker()
        assert tracker.is_drifting(str(conv_id))

    @pytest.mark.asyncio
    @pytest.mark.test_id("11-5-INT-004")
    async def test_no_validation_when_no_conversation_id(self):
        handler = LLMHandler()
        merchant = make_merchant(PersonalityType.FRIENDLY)
        llm_svc = make_llm_service("Sure thing! Here to help! 😊")
        ctx = make_context(conversation_id=None)
        db = AsyncMock()

        with (
            patch.object(handler, "_detect_product_mentions", return_value=None),
            patch.object(handler, "_get_conversation_context", return_value=None),
        ):
            await handler.handle(db, merchant, llm_svc, "hello", ctx)

        tracker = get_personality_tracker()
        assert tracker.active_conversation_count == 0

    @pytest.mark.asyncio
    @pytest.mark.test_id("11-5-INT-005")
    async def test_no_validation_when_empty_response(self):
        handler = LLMHandler()
        merchant = make_merchant(PersonalityType.FRIENDLY)
        llm_svc = make_llm_service("")
        conv_id = unique_conv_id()
        ctx = make_context(conversation_id=conv_id)
        db = AsyncMock()

        with (
            patch.object(handler, "_detect_product_mentions", return_value=None),
            patch.object(handler, "_get_conversation_context", return_value=None),
        ):
            await handler.handle(db, merchant, llm_svc, "hello", ctx)

        tracker = get_personality_tracker()
        assert tracker.get_turn_count(str(conv_id)) == 0
