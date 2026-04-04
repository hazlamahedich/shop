from __future__ import annotations

from dataclasses import dataclass, field

from app.services.intent.classification_schema import IntentType


@dataclass(frozen=True)
class IntentRequirement:
    field_name: str
    display_name: str
    required: bool
    priority: int
    mode: str
    example_values: list[str] = field(default_factory=list)


_SKIP_INTENTS: set[IntentType] = {
    IntentType.GREETING,
    IntentType.CHECKOUT,
    IntentType.UNKNOWN,
    IntentType.CLARIFICATION,
    IntentType.CART_VIEW,
    IntentType.CART_REMOVE,
    IntentType.CART_CLEAR,
    IntentType.ADD_LAST_VIEWED,
    IntentType.FORGET_PREFERENCES,
    IntentType.CHECK_CONSENT_STATUS,
    IntentType.PRODUCT_RECOMMENDATION,
    IntentType.SUMMARIZE,
}

INTENT_REQUIREMENTS: dict[IntentType, list[IntentRequirement]] = {
    IntentType.PRODUCT_SEARCH: [
        IntentRequirement(
            "budget", "budget", True, 1, "ecommerce", ["$50", "under $100", "around $200"]
        ),
        IntentRequirement("size", "size", False, 2, "ecommerce", ["S", "M", "L", "10", "42"]),
        IntentRequirement("color", "color", False, 2, "ecommerce", ["red", "blue", "black"]),
        IntentRequirement("brand", "brand", False, 3, "ecommerce", ["Nike", "Adidas", "Samsung"]),
        IntentRequirement(
            "category", "category", False, 2, "ecommerce", ["shoes", "electronics", "clothing"]
        ),
    ],
    IntentType.PRODUCT_INQUIRY: [
        IntentRequirement(
            "product_identifier",
            "product name or selection",
            True,
            1,
            "ecommerce",
            ["the red shirt", "the first one", "Nike shoes"],
        ),
    ],
    IntentType.PRODUCT_COMPARISON: [
        IntentRequirement(
            "product_identifiers",
            "products to compare (at least 2)",
            True,
            1,
            "ecommerce",
            ["Nike vs Adidas", "the red and blue ones"],
        ),
    ],
    IntentType.CART_ADD: [
        IntentRequirement(
            "product_identifier",
            "product to add",
            True,
            1,
            "ecommerce",
            ["the red shirt", "that one", "the Nike shoes"],
        ),
    ],
    IntentType.ORDER_TRACKING: [
        IntentRequirement(
            "order_number",
            "order number",
            True,
            1,
            "ecommerce",
            ["#1001", "ORD-123", "1001"],
        ),
    ],
    IntentType.HUMAN_HANDOFF: [
        IntentRequirement(
            "issue_type",
            "type of issue",
            True,
            1,
            "both",
            ["return", "billing", "shipping problem", "product defect"],
        ),
        IntentRequirement(
            "urgency",
            "urgency level",
            False,
            2,
            "both",
            ["urgent", "not urgent", "whenever"],
        ),
    ],
    IntentType.GENERAL: [
        IntentRequirement(
            "topic_category",
            "topic or question",
            True,
            1,
            "general",
            ["shipping policy", "return policy", "business hours"],
        ),
    ],
}


def get_requirements_for_intent(intent: IntentType) -> list[IntentRequirement]:
    return list(INTENT_REQUIREMENTS.get(intent, []))


def is_skip_intent(intent: IntentType) -> bool:
    return intent in _SKIP_INTENTS
