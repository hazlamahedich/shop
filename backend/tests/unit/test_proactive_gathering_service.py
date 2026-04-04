from __future__ import annotations

from typing import Any

import pytest

from app.models.merchant import PersonalityType
from app.services.conversation.schemas import Channel, ConversationContext
from app.services.intent.classification_schema import ExtractedEntities, IntentType
from app.services.proactive_gathering.intent_requirements import (
    INTENT_REQUIREMENTS,
    _SKIP_INTENTS,
    IntentRequirement,
    get_requirements_for_intent,
    is_skip_intent,
)
from app.services.proactive_gathering.proactive_gathering_service import (
    _BRAND_KNOWN,
    _BUDGET_PATTERN,
    _COLOR_PATTERN,
    _ORDER_NUMBER_PATTERN,
    _SIZE_PATTERN,
    ProactiveGatheringService,
)
from app.services.proactive_gathering.schemas import GatheringState, MissingField
from app.services.multi_turn.schemas import MultiTurnConfig, MultiTurnState, MultiTurnStateEnum
from app.services.multi_turn.state_machine import ConversationStateMachine


@pytest.fixture
def service() -> ProactiveGatheringService:
    return ProactiveGatheringService()


@pytest.fixture
def context() -> ConversationContext:
    return ConversationContext(
        session_id="test-session",
        merchant_id=1,
        channel=Channel.WIDGET,
    )


@pytest.fixture
def empty_entities() -> ExtractedEntities:
    return ExtractedEntities()


def _context_with_constraints(**constraints: object) -> ConversationContext:
    ctx = ConversationContext(
        session_id="test-session",
        merchant_id=1,
        channel=Channel.WIDGET,
    )
    ctx.metadata = {"constraints": constraints}
    return ctx


class TestDetectMissingInfo:
    def test_skip_intents_return_empty(
        self, service: ProactiveGatheringService, context: ConversationContext
    ) -> None:
        for intent in _SKIP_INTENTS:
            result = service.detect_missing_info(intent, ExtractedEntities(), context, "ecommerce")
            assert result == []

    def test_product_search_missing_all(
        self, service: ProactiveGatheringService, context: ConversationContext
    ) -> None:
        result = service.detect_missing_info(
            IntentType.PRODUCT_SEARCH, ExtractedEntities(), context, "ecommerce"
        )
        field_names = [f.field_name for f in result]
        assert "budget" in field_names
        assert "size" in field_names
        assert "color" in field_names
        assert "brand" in field_names
        assert "category" in field_names

    def test_product_search_with_budget_entity(
        self, service: ProactiveGatheringService, context: ConversationContext
    ) -> None:
        entities = ExtractedEntities(budget=50.0)
        result = service.detect_missing_info(
            IntentType.PRODUCT_SEARCH, entities, context, "ecommerce"
        )
        field_names = [f.field_name for f in result]
        assert "budget" not in field_names

    def test_product_search_with_context_constraint(
        self, service: ProactiveGatheringService
    ) -> None:
        ctx = _context_with_constraints(color="red")
        result = service.detect_missing_info(
            IntentType.PRODUCT_SEARCH, ExtractedEntities(), ctx, "ecommerce"
        )
        field_names = [f.field_name for f in result]
        assert "color" not in field_names

    def test_general_mode_excludes_ecommerce_only(
        self, service: ProactiveGatheringService, context: ConversationContext
    ) -> None:
        result = service.detect_missing_info(
            IntentType.PRODUCT_SEARCH, ExtractedEntities(), context, "general"
        )
        field_names = [f.field_name for f in result]
        assert "budget" not in field_names

    def test_general_mode_includes_general_fields(
        self, service: ProactiveGatheringService, context: ConversationContext
    ) -> None:
        result = service.detect_missing_info(
            IntentType.GENERAL, ExtractedEntities(), context, "general"
        )
        field_names = [f.field_name for f in result]
        assert "topic_category" in field_names

    def test_order_tracking_needs_order_number(
        self, service: ProactiveGatheringService, context: ConversationContext
    ) -> None:
        result = service.detect_missing_info(
            IntentType.ORDER_TRACKING, ExtractedEntities(), context, "ecommerce"
        )
        assert len(result) == 1
        assert result[0].field_name == "order_number"

    def test_order_tracking_with_order_number_entity(
        self, service: ProactiveGatheringService, context: ConversationContext
    ) -> None:
        entities = ExtractedEntities(order_number="#1234")
        result = service.detect_missing_info(
            IntentType.ORDER_TRACKING, entities, context, "ecommerce"
        )
        assert result == []

    def test_cart_add_needs_product_identifier(
        self, service: ProactiveGatheringService, context: ConversationContext
    ) -> None:
        result = service.detect_missing_info(
            IntentType.CART_ADD, ExtractedEntities(), context, "ecommerce"
        )
        assert len(result) == 1
        assert result[0].field_name == "product_identifier"

    def test_human_handoff_needs_issue_type_and_urgency(
        self, service: ProactiveGatheringService, context: ConversationContext
    ) -> None:
        result = service.detect_missing_info(
            IntentType.HUMAN_HANDOFF, ExtractedEntities(), context, "ecommerce"
        )
        field_names = [f.field_name for f in result]
        assert "issue_type" in field_names
        assert "urgency" in field_names

    def test_intent_not_in_requirements_returns_empty(
        self, service: ProactiveGatheringService, context: ConversationContext
    ) -> None:
        result = service.detect_missing_info(
            IntentType.FORGET_PREFERENCES, ExtractedEntities(), context, "ecommerce"
        )
        assert result == []

    def test_missing_fields_sorted_by_priority(
        self, service: ProactiveGatheringService, context: ConversationContext
    ) -> None:
        result = service.detect_missing_info(
            IntentType.PRODUCT_SEARCH, ExtractedEntities(), context, "ecommerce"
        )
        priorities = [f.priority for f in result]
        assert priorities == sorted(priorities)

    def test_constraints_entity_field_detected(
        self, service: ProactiveGatheringService, context: ConversationContext
    ) -> None:
        entities = ExtractedEntities(constraints={"budget": 100})
        result = service.detect_missing_info(
            IntentType.PRODUCT_SEARCH, entities, context, "ecommerce"
        )
        field_names = [f.field_name for f in result]
        assert "budget" not in field_names

    def test_category_from_last_search_category(self, service: ProactiveGatheringService) -> None:
        ctx = ConversationContext(
            session_id="test-session",
            merchant_id=1,
            channel=Channel.WIDGET,
        )
        ctx.shopping_state.last_search_category = "shoes"
        result = service.detect_missing_info(
            IntentType.PRODUCT_SEARCH, ExtractedEntities(), ctx, "ecommerce"
        )
        field_names = [f.field_name for f in result]
        assert "category" not in field_names


class TestGenerateGatheringMessage:
    def test_empty_fields_returns_empty(
        self, service: ProactiveGatheringService, context: ConversationContext
    ) -> None:
        result = service.generate_gathering_message(
            [], "friendly", "Bot", "ecommerce", context, "conv-1"
        )
        assert result == ""

    def test_single_field_generates_message(
        self, service: ProactiveGatheringService, context: ConversationContext
    ) -> None:
        fields = [
            MissingField(
                field_name="order_number",
                display_name="order number",
                priority=1,
                mode="ecommerce",
                example_values=["#1234"],
            )
        ]
        result = service.generate_gathering_message(
            fields, "friendly", "Bot", "ecommerce", context, "conv-1"
        )
        assert "order number" in result.lower()
        assert len(result) > 0

    def test_multiple_fields_generates_combined(
        self, service: ProactiveGatheringService, context: ConversationContext
    ) -> None:
        fields = [
            MissingField(
                field_name="budget",
                display_name="budget",
                priority=1,
                mode="ecommerce",
                example_values=["$50"],
            ),
            MissingField(
                field_name="color",
                display_name="color",
                priority=2,
                mode="ecommerce",
                example_values=["red"],
            ),
        ]
        result = service.generate_gathering_message(
            fields, "friendly", "Bot", "ecommerce", context, "conv-1"
        )
        assert len(result) > 0
        assert isinstance(result, str)

    def test_context_prefix_included_when_constraints(
        self, service: ProactiveGatheringService
    ) -> None:
        ctx = _context_with_constraints(budget=100)
        fields = [
            MissingField(
                field_name="color",
                display_name="color",
                priority=1,
                mode="ecommerce",
                example_values=["red"],
            )
        ]
        result = service.generate_gathering_message(
            fields, "friendly", "Bot", "ecommerce", ctx, "conv-1"
        )
        assert "budget" in result.lower()

    def test_professional_personality(
        self, service: ProactiveGatheringService, context: ConversationContext
    ) -> None:
        fields = [
            MissingField(
                field_name="order_number",
                display_name="order number",
                priority=1,
                mode="ecommerce",
                example_values=["#1234"],
            )
        ]
        result = service.generate_gathering_message(
            fields, "professional", "Bot", "ecommerce", context, "conv-1"
        )
        assert len(result) > 0

    def test_enthusiastic_personality(
        self, service: ProactiveGatheringService, context: ConversationContext
    ) -> None:
        fields = [
            MissingField(
                field_name="order_number",
                display_name="order number",
                priority=1,
                mode="ecommerce",
                example_values=["#1234"],
            )
        ]
        result = service.generate_gathering_message(
            fields, "enthusiastic", "Bot", "ecommerce", context, "conv-1"
        )
        assert len(result) > 0

    def test_fallback_on_invalid_personality(
        self, service: ProactiveGatheringService, context: ConversationContext
    ) -> None:
        fields = [
            MissingField(
                field_name="budget",
                display_name="budget",
                priority=1,
                mode="ecommerce",
                example_values=["$50"],
            )
        ]
        result = service.generate_gathering_message(
            fields, "nonexistent", "Bot", "ecommerce", context, "conv-1"
        )
        assert len(result) > 0


class TestExtractPartialAnswer:
    def test_extract_order_number(self, service: ProactiveGatheringService) -> None:
        fields = [
            MissingField(
                field_name="order_number",
                display_name="order number",
                priority=1,
                mode="ecommerce",
                example_values=["#1234"],
            )
        ]
        result = service.extract_partial_answer("my order is #1234", fields, "ecommerce")
        assert "order_number" in result
        assert "#1234" in result["order_number"]

    def test_extract_budget(self, service: ProactiveGatheringService) -> None:
        fields = [
            MissingField(
                field_name="budget",
                display_name="budget",
                priority=1,
                mode="ecommerce",
                example_values=["$50"],
            )
        ]
        result = service.extract_partial_answer("under $100", fields, "ecommerce")
        assert "budget" in result
        assert result["budget"] == 100.0

    def test_extract_color(self, service: ProactiveGatheringService) -> None:
        fields = [
            MissingField(
                field_name="color",
                display_name="color",
                priority=2,
                mode="ecommerce",
                example_values=["red"],
            ),
        ]
        result = service.extract_partial_answer("I want a blue one", fields, "ecommerce")
        assert "color" in result
        assert result["color"] == "blue"

    def test_extract_brand(self, service: ProactiveGatheringService) -> None:
        fields = [
            MissingField(
                field_name="brand",
                display_name="brand",
                priority=3,
                mode="ecommerce",
                example_values=["Nike"],
            ),
        ]
        result = service.extract_partial_answer("I want Nike shoes", fields, "ecommerce")
        assert "brand" in result

    def test_extract_size(self, service: ProactiveGatheringService) -> None:
        fields = [
            MissingField(
                field_name="size",
                display_name="size",
                priority=2,
                mode="ecommerce",
                example_values=["M"],
            ),
        ]
        result = service.extract_partial_answer("I need size L", fields, "ecommerce")
        assert "size" in result

    def test_fallback_assigns_highest_priority_field(
        self, service: ProactiveGatheringService
    ) -> None:
        fields = [
            MissingField(
                field_name="budget",
                display_name="budget",
                priority=1,
                mode="ecommerce",
                example_values=["$50"],
            ),
            MissingField(
                field_name="color",
                display_name="color",
                priority=2,
                mode="ecommerce",
                example_values=["red"],
            ),
        ]
        result = service.extract_partial_answer("something random", fields, "ecommerce")
        assert "budget" in result
        assert result["budget"] == "something random"

    def test_no_fields_returns_empty(self, service: ProactiveGatheringService) -> None:
        result = service.extract_partial_answer("hello", [], "ecommerce")
        assert result == {}


class TestRegexPatterns:
    def test_budget_pattern_dollar_sign(self) -> None:
        assert _BUDGET_PATTERN.search("$50") is not None

    def test_budget_pattern_under(self) -> None:
        assert _BUDGET_PATTERN.search("under 100 dollars") is not None

    def test_color_pattern_common(self) -> None:
        for color in ("red", "blue", "green", "black", "white", "navy"):
            assert _COLOR_PATTERN.search(f"I want {color}") is not None

    def test_size_pattern_letter(self) -> None:
        for size in ("XS", "S", "M", "L", "XL", "XXL"):
            assert _SIZE_PATTERN.search(f"size {size}") is not None

    def test_order_number_pattern(self) -> None:
        assert _ORDER_NUMBER_PATTERN.search("#1234") is not None
        assert _ORDER_NUMBER_PATTERN.search("ORD-567") is not None
        assert _ORDER_NUMBER_PATTERN.search("12345") is not None

    def test_brand_known_set(self) -> None:
        assert "nike" in _BRAND_KNOWN
        assert "adidas" in _BRAND_KNOWN
        assert "apple" in _BRAND_KNOWN
