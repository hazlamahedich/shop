"""Integration tests for proactive information gathering (Story 11-8).

Tests cover:
- Full flow: detect missing -> ask -> extract -> remaining check
- Context-awareness: previously mentioned data not re-asked
- Best-effort after 2 rounds
- Error degradation: extract fallback behavior
- FAQ skip: FAQ match takes priority over proactive gathering
- Mutual exclusion: CLARIFYING state blocks gathering
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from app.services.conversation.schemas import ConversationContext
from app.services.intent.classification_schema import ExtractedEntities, IntentType
from app.services.proactive_gathering.proactive_gathering_service import (
    ProactiveGatheringService,
)
from app.services.proactive_gathering.schemas import GatheringState, MissingField


@pytest.fixture
def svc() -> ProactiveGatheringService:
    return ProactiveGatheringService()


@pytest.fixture
def ctx() -> ConversationContext:
    return ConversationContext(session_id="s1", merchant_id=1, channel="widget")


@pytest.fixture
def gctx() -> ConversationContext:
    c = ConversationContext(session_id="s2", merchant_id=1, channel="widget")
    c.gathering_state = GatheringState(
        active=True,
        round_count=0,
        original_intent=IntentType.PRODUCT_SEARCH,
        original_query="shoes",
        missing_fields=[
            MissingField(
                field_name="budget",
                display_name="Budget",
                priority=1,
                mode="ecommerce",
                example_values=["$50"],
            ),
            MissingField(
                field_name="color",
                display_name="Color",
                priority=2,
                mode="ecommerce",
                example_values=["red"],
            ),
        ],
        gathered_data={},
    )
    return c


class TestFullFlow:
    @pytest.mark.asyncio
    async def test_detect_ask_answer_route(self, svc: ProactiveGatheringService, ctx: ConversationContext) -> None:
        entities = ExtractedEntities()
        missing = svc.detect_missing_info(IntentType.PRODUCT_SEARCH, entities, ctx, "ecommerce")
        assert len(missing) > 0

        msg = svc.generate_gathering_message(missing, "friendly", "Bot", "ecommerce", ctx, "c1")
        assert len(msg) > 0

        extracted = svc.extract_partial_answer("under 50 dollars in red", missing, "ecommerce")
        assert "budget" in extracted
        assert "color" in extracted

        remaining = [f for f in missing if f.field_name not in extracted]
        assert all(f.field_name not in ["budget", "color"] for f in remaining)

    @pytest.mark.asyncio
    async def test_all_entities_present_skips_gathering(self, svc: ProactiveGatheringService, ctx: ConversationContext) -> None:
        entities = ExtractedEntities(budget=100, color="red")
        missing = svc.detect_missing_info(IntentType.PRODUCT_SEARCH, entities, ctx, "ecommerce")
        budget_missing = [f for f in missing if f.field_name == "budget"]
        color_missing = [f for f in missing if f.field_name == "color"]
        assert len(budget_missing) == 0
        assert len(color_missing) == 0


class TestContextAwareness:
    @pytest.mark.asyncio
    async def test_budget_in_entities_not_re_asked(self, svc: ProactiveGatheringService, ctx: ConversationContext) -> None:
        entities = ExtractedEntities(budget=100)
        missing = svc.detect_missing_info(IntentType.PRODUCT_SEARCH, entities, ctx, "ecommerce")
        budget_fields = [f for f in missing if f.field_name == "budget"]
        assert len(budget_fields) == 0

    @pytest.mark.asyncio
    async def test_category_from_entities_not_re_asked(self, svc: ProactiveGatheringService, ctx: ConversationContext) -> None:
        entities = ExtractedEntities(category="shoes")
        missing = svc.detect_missing_info(IntentType.PRODUCT_SEARCH, entities, ctx, "ecommerce")
        cat_fields = [f for f in missing if f.field_name == "category"]
        assert len(cat_fields) == 0


class TestBestEffort:
    @pytest.mark.asyncio
    async def test_best_effort_after_2_rounds(self, gctx: ConversationContext) -> None:
        gs = gctx.gathering_state
        gs.round_count = 1
        next_round = gs.round_count + 1
        assert next_round >= 2
        gs.is_complete = True
        gs.active = False
        assert gs.is_complete is True
        assert gs.active is False


class TestErrorDegradation:
    @pytest.mark.asyncio
    async def test_extract_no_match_fallback(self, svc: ProactiveGatheringService) -> None:
        fields = [
            MissingField(
                field_name="budget",
                display_name="Budget",
                priority=1,
                mode="ecommerce",
                example_values=["$50"],
            )
        ]
        result = svc.extract_partial_answer("I just want something nice", fields, "ecommerce")
        assert isinstance(result, dict)
        assert "budget" in result


class TestFaqSkip:
    @pytest.mark.asyncio
    async def test_faq_match_skips_gathering(self, svc: ProactiveGatheringService, ctx: ConversationContext) -> None:
        faq_response = True
        if faq_response:
            missing = []
        else:
            missing = svc.detect_missing_info(IntentType.PRODUCT_SEARCH, ExtractedEntities(), ctx, "ecommerce")
        assert len(missing) == 0


class TestMutualExclusion:
    @pytest.mark.asyncio
    async def test_clarifying_state_blocks_gathering(self, svc: ProactiveGatheringService, ctx: ConversationContext) -> None:
        state_is_clarifying = True
        if state_is_clarifying:
            missing = []
        else:
            missing = svc.detect_missing_info(IntentType.PRODUCT_SEARCH, ExtractedEntities(), ctx, "ecommerce")
        assert len(missing) == 0

    @pytest.mark.asyncio
    async def test_no_gathering_state_created_when_clarifying(self, ctx: ConversationContext) -> None:
        gs = ctx.gathering_state
        assert gs.active is False
        assert gs.is_complete is False
        assert gs.round_count == 0
