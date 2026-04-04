from __future__ import annotations

import pytest

from app.services.intent.classification_schema import IntentType
from app.services.proactive_gathering.intent_requirements import (
    INTENT_REQUIREMENTS,
    IntentRequirement,
    get_requirements_for_intent,
    is_skip_intent,
)


class TestSkipIntents:
    def test_greeting(self) -> None:
        assert is_skip_intent(IntentType.GREETING) is True

    def test_checkout(self) -> None:
        assert is_skip_intent(IntentType.CHECKOUT) is True

    def test_unknown(self) -> None:
        assert is_skip_intent(IntentType.UNKNOWN) is True

    def test_clarification(self) -> None:
        assert is_skip_intent(IntentType.CLARIFICATION) is True

    def test_cart_view(self) -> None:
        assert is_skip_intent(IntentType.CART_VIEW) is True

    def test_cart_remove(self) -> None:
        assert is_skip_intent(IntentType.CART_REMOVE) is True

    def test_cart_clear(self) -> None:
        assert is_skip_intent(IntentType.CART_CLEAR) is True

    def test_product_recommendation(self) -> None:
        assert is_skip_intent(IntentType.PRODUCT_RECOMMENDATION) is True

    def test_add_last_viewed(self) -> None:
        assert is_skip_intent(IntentType.ADD_LAST_VIEWED) is True

    def test_forget_preferences(self) -> None:
        assert is_skip_intent(IntentType.FORGET_PREFERENCES) is True

    def test_check_consent_status(self) -> None:
        assert is_skip_intent(IntentType.CHECK_CONSENT_STATUS) is True

    def test_cart_add_not_skip(self) -> None:
        assert is_skip_intent(IntentType.CART_ADD) is False

    def test_product_search_not_skip(self) -> None:
        assert is_skip_intent(IntentType.PRODUCT_SEARCH) is False

    def test_order_tracking_not_skip(self) -> None:
        assert is_skip_intent(IntentType.ORDER_TRACKING) is False


class TestIntentRequirements:
    def test_product_search_has_requirements(self) -> None:
        reqs = INTENT_REQUIREMENTS[IntentType.PRODUCT_SEARCH]
        assert len(reqs) >= 1

    def test_product_inquiry_has_product_identifier(self) -> None:
        reqs = INTENT_REQUIREMENTS[IntentType.PRODUCT_INQUIRY]
        field_names = [r.field_name for r in reqs]
        assert "product_identifier" in field_names

    def test_product_comparison_has_product_identifiers(self) -> None:
        reqs = INTENT_REQUIREMENTS[IntentType.PRODUCT_COMPARISON]
        field_names = [r.field_name for r in reqs]
        assert "product_identifiers" in field_names

    def test_cart_add_has_product_identifier(self) -> None:
        reqs = INTENT_REQUIREMENTS[IntentType.CART_ADD]
        field_names = [r.field_name for r in reqs]
        assert "product_identifier" in field_names

    def test_order_tracking_has_order_number(self) -> None:
        reqs = INTENT_REQUIREMENTS[IntentType.ORDER_TRACKING]
        assert len(reqs) == 1
        assert reqs[0].field_name == "order_number"
        assert len(reqs[0].example_values) == 3

    def test_human_handoff_has_issue_type_and_urgency(self) -> None:
        reqs = INTENT_REQUIREMENTS[IntentType.HUMAN_HANDOFF]
        field_names = [r.field_name for r in reqs]
        assert "issue_type" in field_names
        assert "urgency" in field_names

    def test_general_has_topic_category(self) -> None:
        reqs = INTENT_REQUIREMENTS[IntentType.GENERAL]
        assert len(reqs) == 1
        assert reqs[0].field_name == "topic_category"
        assert reqs[0].mode == "general"
        assert reqs[0].required is True

    def test_all_requirements_have_consistent_fields(self) -> None:
        for intent, reqs in INTENT_REQUIREMENTS.items():
            for req in reqs:
                assert req.field_name, f"Empty field_name for {intent}"
                assert req.display_name, f"Empty display_name for {intent}"
                assert 1 <= req.priority <= 3, f"Invalid priority for {intent}.{req.field_name}"
                assert req.mode in ("ecommerce", "general", "both")


class TestHelperFunctions:
    def test_get_requirements_for_intent_known(self) -> None:
        reqs = get_requirements_for_intent(IntentType.PRODUCT_SEARCH)
        assert len(reqs) == len(INTENT_REQUIREMENTS[IntentType.PRODUCT_SEARCH])

    def test_get_requirements_for_intent_unknown(self) -> None:
        reqs = get_requirements_for_intent(IntentType.FORGET_PREFERENCES)
        assert reqs == []

    def test_is_skip_intent_true_cases(self) -> None:
        assert is_skip_intent(IntentType.GREETING) is True
        assert is_skip_intent(IntentType.CART_ADD) is False

    def test_intent_requirement_fields(self) -> None:
        req = IntentRequirement(
            field_name="test",
            display_name="Test Field",
            required=True,
            priority=1,
            mode="both",
            example_values=["a", "b"],
        )
        assert req.field_name == "test"
        assert req.display_name == "Test Field"
        assert req.required is True
        assert req.priority == 1
        assert req.mode == "both"
        assert req.example_values == ["a", "b"]
