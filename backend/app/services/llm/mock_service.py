"""Mock LLM Service for testing and verification.

Provides deterministic responses compliant with BaseLLMService interface.
Based on tests/fixtures/mock_llm.py but adapted for application use.

Context-aware: returns intent classification JSON when called by the
IntentClassifier, and natural language responses for general chat / FAQ
rephrasing / any other conversational use.
"""

from __future__ import annotations

import structlog

from app.services.llm.base_llm_service import (
    BaseLLMService,
    LLMMessage,
    LLMResponse,
)

logger = structlog.get_logger(__name__)

_CLASSIFICATION_KEYWORDS = frozenset(
    {
        "intent",
        "classification",
        "classify",
        "categorize",
        "ecommerce intent",
        "shopping intent",
    }
)

_GREETING_PATTERNS = ["hi", "hello", "hey", "good morning", "good afternoon"]
_HANDOFF_PATTERNS = ["human", "person", "agent", "speak to", "talk to", "representative"]
_PRODUCT_PATTERNS = ["product", "item", "search", "find", "look for", "show me"]
_ORDER_PATTERNS = ["order", "where is", "track", "shipping", "delivery"]
_CART_PATTERNS = ["cart", "bag", "basket"]
_CHECKOUT_PATTERNS = ["checkout", "buy", "purchase", "pay"]
_FAQ_PATTERNS = [
    "faq",
    "question",
    "help",
    "how do",
    "what is",
    "who",
    "when",
    "where",
    "why",
    "how",
]


class MockLLMService(BaseLLMService):
    """Mock LLM provider for testing and verification.

    Context-aware: detects whether the caller needs intent classification
    (JSON) or conversational responses (natural language) by inspecting
    the system prompt for classification-related keywords.
    """

    CLASSIFICATION_RESPONSES = {
        "checkout_request": {
            "content": '{"intent": "checkout", "confidence": 0.98, "entities": {}}',
            "intent": "checkout",
        },
        "order_status": {
            "content": '{"intent": "order_tracking", "confidence": 0.92, "entities": {"order_id": "12345"}}',
            "intent": "order_tracking",
        },
        "view_cart": {
            "content": '{"intent": "view_cart", "confidence": 0.99, "entities": {}}',
            "intent": "view_cart",
        },
        "add_to_cart": {
            "content": '{"intent": "add_to_cart", "confidence": 0.97, "entities": {"product_id": "123", "quantity": 1}}',
            "intent": "add_to_cart",
        },
        "product_search_simple": {
            "content": '{"intent": "product_search", "confidence": 0.95, "entities": {"category": "shoes", "budget": 100, "size": "8"}}',
            "intent": "product_search",
        },
        "product_search_vague": {
            "content": '{"intent": "product_search", "confidence": 0.65, "entities": {"category": "shoes"}}',
            "intent": "product_search",
        },
        "human_handoff": {
            "content": '{"intent": "human_handoff", "confidence": 0.99, "entities": {"reason": "explicit_request"}}',
            "intent": "human_handoff",
        },
        "greeting": {
            "content": '{"intent": "unknown", "confidence": 0.8, "entities": {}}',
            "intent": "unknown",
        },
    }

    CHAT_RESPONSES = {
        "greeting": "Hi there! How can I help you today?",
        "handoff": "I'd be happy to connect you with a human agent. Let me transfer you now.",
        "product": "I'd be happy to help you find what you're looking for! Could you tell me more about what you need?",
        "order": "I can help you with your order. Could you provide your order number?",
        "cart": "Let me check your cart for you.",
        "checkout": "Great choice! Let me help you with the checkout process.",
        "faq": "That's a great question! Let me help you with that.",
        "default": "I'm here to help! Could you tell me more about what you're looking for?",
    }

    @property
    def provider_name(self) -> str:
        return "mock"

    async def test_connection(self) -> bool:
        return True

    def _is_classification_call(self, messages: list[LLMMessage]) -> bool:
        """Detect intent classification calls by inspecting the system prompt."""
        for msg in messages:
            if msg.role == "system":
                lower = msg.content.lower()
                if any(kw in lower for kw in _CLASSIFICATION_KEYWORDS):
                    return True
        return False

    async def chat(
        self,
        messages: list[LLMMessage],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> LLMResponse:
        """Return deterministic response based on context and keywords.

        Returns intent classification JSON for classification calls,
        natural language for conversational calls (chat, FAQ rephrase, etc).
        """
        last_user_msg = next(
            (m.content for m in reversed(messages) if m.role == "user"), ""
        ).lower()

        logger.info(
            "mock_llm_chat",
            message=last_user_msg,
            is_classification=self._is_classification_call(messages),
        )

        if self._is_classification_call(messages):
            return self._classification_response(last_user_msg)

        return self._chat_response(last_user_msg)

    def _classification_response(self, last_user_msg: str) -> LLMResponse:
        """Return intent classification JSON (for IntentClassifier calls)."""
        response_data = self.CLASSIFICATION_RESPONSES["product_search_vague"]

        if any(w in last_user_msg for w in _CHECKOUT_PATTERNS):
            response_data = self.CLASSIFICATION_RESPONSES["checkout_request"]
        elif any(w in last_user_msg for w in _ORDER_PATTERNS):
            response_data = self.CLASSIFICATION_RESPONSES["order_status"]
        elif any(w in last_user_msg for w in _HANDOFF_PATTERNS):
            response_data = self.CLASSIFICATION_RESPONSES["human_handoff"]
        elif any(w in last_user_msg for w in _CART_PATTERNS):
            response_data = self.CLASSIFICATION_RESPONSES["view_cart"]
        elif any(w in last_user_msg for w in ["add", "put"]):
            response_data = self.CLASSIFICATION_RESPONSES["add_to_cart"]
        elif any(w in last_user_msg for w in ["budget", "size", "under", "less than"]):
            response_data = self.CLASSIFICATION_RESPONSES["product_search_simple"]
        elif any(w in last_user_msg for w in _GREETING_PATTERNS):
            response_data = self.CLASSIFICATION_RESPONSES["greeting"]

        return LLMResponse(
            content=response_data["content"],
            tokens_used=10,
            model="mock-model",
            provider="mock",
            metadata={"mock": True, "intent": response_data["intent"]},
        )

    def _chat_response(self, last_user_msg: str) -> LLMResponse:
        """Return natural language response (for LLMHandler / FAQ rephrase calls)."""
        response = self.CHAT_RESPONSES["default"]

        if any(p in last_user_msg for p in _GREETING_PATTERNS):
            response = self.CHAT_RESPONSES["greeting"]
        elif any(p in last_user_msg for p in _HANDOFF_PATTERNS):
            response = self.CHAT_RESPONSES["handoff"]
        elif any(p in last_user_msg for p in _CHECKOUT_PATTERNS):
            response = self.CHAT_RESPONSES["checkout"]
        elif any(p in last_user_msg for p in _ORDER_PATTERNS):
            response = self.CHAT_RESPONSES["order"]
        elif any(p in last_user_msg for p in _CART_PATTERNS):
            response = self.CHAT_RESPONSES["cart"]
        elif any(p in last_user_msg for p in _PRODUCT_PATTERNS):
            response = self.CHAT_RESPONSES["product"]
        elif any(p in last_user_msg for p in _FAQ_PATTERNS):
            response = self.CHAT_RESPONSES["faq"]

        return LLMResponse(
            content=response,
            tokens_used=10,
            model="mock-model",
            provider="mock",
            metadata={"mock": True},
        )

    def count_tokens(self, text: str) -> int:
        return len(text) // 4

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        return 0.0
