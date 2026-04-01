"""Unit tests for natural language variation handling in pattern classifier.

Story 11-3: Tests that _classify_by_patterns handles colloquialisms, typos,
synonyms, indirect requests, and diverse phrasings for all major intents.
"""

import pytest

from app.services.conversation.unified_conversation_service import UnifiedConversationService
from app.services.intent.classification_schema import IntentType


@pytest.fixture
def svc():
    return UnifiedConversationService(db=None)


class TestGreetingVariations:
    @pytest.mark.parametrize(
        "msg",
        [
            "hi",
            "hello",
            "hey",
            "howdy",
            "yo",
            "sup",
            "what's up",
            "heya",
            "hi there",
            "hello there",
            "hey anyone there",
            "good morning",
            "good evening",
        ],
    )
    def test_greeting_variations(self, svc, msg):
        result = svc._classify_by_patterns(msg)
        assert result is not None, f"No match for: {msg!r}"
        assert result.intent == IntentType.GREETING


class TestCartAddVariations:
    @pytest.mark.parametrize(
        "msg",
        [
            "add this to my cart",
            "put that in my cart",
            "throw it in my bag",
            "toss it in the basket",
            "I'll take that",
            "hook me up with this",
            "get me that",
            "I want to add to my cart",
        ],
    )
    def test_cart_add_variations(self, svc, msg):
        result = svc._classify_by_patterns(msg)
        assert result is not None, f"No match for: {msg!r}"
        assert result.intent == IntentType.CART_ADD


class TestCartViewVariations:
    @pytest.mark.parametrize(
        "msg",
        [
            "show my cart",
            "what's in my basket",
            "view my bag",
            "cart contents",
        ],
    )
    def test_cart_view_variations(self, svc, msg):
        result = svc._classify_by_patterns(msg)
        assert result is not None, f"No match for: {msg!r}"
        assert result.intent == IntentType.CART_VIEW


class TestCheckoutVariations:
    @pytest.mark.parametrize(
        "msg",
        [
            "checkout",
            "let's do this",
            "ring me up",
            "take my money",
            "I'm ready to buy",
            "ready to pay",
            "time to pay",
        ],
    )
    def test_checkout_variations(self, svc, msg):
        result = svc._classify_by_patterns(msg)
        assert result is not None, f"No match for: {msg!r}"
        assert result.intent == IntentType.CHECKOUT


class TestOrderTrackingVariations:
    @pytest.mark.parametrize(
        "msg",
        [
            "where is my order",
            "where's my stuff",
            "where's my package",
            "has my order shipped",
            "delivery status",
            "when will my order arrive",
            "wher is my ordr",
            "order status",
            "track my order",
        ],
    )
    def test_order_tracking_variations(self, svc, msg):
        result = svc._classify_by_patterns(msg)
        assert result is not None, f"No match for: {msg!r}"
        assert result.intent == IntentType.ORDER_TRACKING

    def test_extracts_order_number(self, svc):
        result = svc._classify_by_patterns("where is order #1234")
        assert result is not None
        assert result.intent == IntentType.ORDER_TRACKING
        assert result.entities.order_number == "1234"

    def test_extracts_order_number_with_text(self, svc):
        result = svc._classify_by_patterns("track my order ORD-5678")
        assert result is not None
        assert result.entities.order_number.lower() == "ord-5678"


class TestHumanHandoffVariations:
    @pytest.mark.parametrize(
        "msg",
        [
            "talk to a person",
            "speak to a human",
            "this bot isn't helping",
            "get me someone who knows",
            "connect me to support",
            "let me talk to your manager",
            "I need real help",
            "no more bot",
        ],
    )
    def test_handoff_variations(self, svc, msg):
        result = svc._classify_by_patterns(msg)
        assert result is not None, f"No match for: {msg!r}"
        assert result.intent == IntentType.HUMAN_HANDOFF


class TestProductSearchVariations:
    @pytest.mark.parametrize(
        "msg",
        [
            "wondering if you carry hiking boots",
            "do you stock yoga mats",
            "I'm in the market for a laptop",
            "got any sneakers",
            "browsing for jackets",
            "find me headphones",
            "I need a dress",
        ],
    )
    def test_indirect_product_search(self, svc, msg):
        result = svc._classify_by_patterns(msg)
        assert result is not None, f"No match for: {msg!r}"
        assert result.intent == IntentType.PRODUCT_SEARCH


class TestPriceSearchVariations:
    @pytest.mark.parametrize(
        "msg,expected_budget",
        [
            ("products under $100", 100.0),
            ("under $50", 50.0),
            ("what can I get for around 50 bucks", 50.0),
            ("looking for something under 75", 75.0),
        ],
    )
    def test_price_constraint_search(self, svc, msg, expected_budget):
        result = svc._classify_by_patterns(msg)
        assert result is not None, f"No match for: {msg!r}"
        assert result.intent == IntentType.PRODUCT_SEARCH
        assert result.entities.budget == expected_budget

    def test_cheapest_search(self, svc):
        result = svc._classify_by_patterns("show me the cheapest")
        assert result is not None
        assert result.intent == IntentType.PRODUCT_SEARCH
        assert result.entities.constraints.get("sort_order") == "asc"

    def test_most_expensive_search(self, svc):
        result = svc._classify_by_patterns("what's the most expensive")
        assert result is not None
        assert result.intent == IntentType.PRODUCT_SEARCH
        assert result.entities.constraints.get("sort_order") == "desc"

    def test_fancy_stuff_search(self, svc):
        result = svc._classify_by_patterns("show me the fancy stuff")
        assert result is not None
        assert result.intent == IntentType.PRODUCT_SEARCH


class TestForgetPreferencesVariations:
    @pytest.mark.parametrize(
        "msg",
        [
            "forget my preferences",
            "clear my data",
            "wipe my history",
            "clean slate please",
            "start over",
            "erase everything",
        ],
    )
    def test_forget_variations(self, svc, msg):
        result = svc._classify_by_patterns(msg)
        assert result is not None, f"No match for: {msg!r}"
        assert result.intent == IntentType.FORGET_PREFERENCES


class TestCheckConsentVariations:
    @pytest.mark.parametrize(
        "msg",
        [
            "are my preferences saved",
            "do you remember my preferences",
            "you still know my settings",
            "what's my consent status",
            "confirm if my preferences are saved",
        ],
    )
    def test_consent_check_variations(self, svc, msg):
        result = svc._classify_by_patterns(msg)
        assert result is not None, f"No match for: {msg!r}"
        assert result.intent == IntentType.CHECK_CONSENT_STATUS


class TestTypoTolerance:
    @pytest.mark.parametrize(
        "msg",
        [
            "sho me chep shoos",
            "wher is my ordr",
            "serch for laptob",
        ],
    )
    def test_typo_tolerance(self, svc, msg):
        result = svc._classify_by_patterns(msg)
        assert result is not None, f"No match for typo input: {msg!r}"


class TestNormalizationDoesNotCorrupt:
    @pytest.mark.parametrize(
        "msg",
        [
            "this bot isn't helping",
            "helping me with shipping",
            "login issues need support",
        ],
    )
    def test_no_substring_corruption(self, svc, msg):
        from app.services.intent.variation_maps import normalize_message

        result = normalize_message(msg)
        assert "assword" not in result
        assert "helpassword" not in result
