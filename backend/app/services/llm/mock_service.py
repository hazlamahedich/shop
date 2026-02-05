"""Mock LLM Service for testing and verification.

Provides deterministic responses compliant with BaseLLMService interface.
Based on tests/fixtures/mock_llm.py but adapted for application use.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import structlog

from app.services.llm.base_llm_service import (
    BaseLLMService,
    LLMMessage,
    LLMResponse,
)

logger = structlog.get_logger(__name__)


class MockLLMService(BaseLLMService):
    """Mock LLM provider for testing and verification.

    Returns predefined deterministic responses based on prompt keywords.
    Useful for manual verification, contract testing, and offline development.
    """

    PREDEFINED_RESPONSES = {
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
        # Catch-all for basic "hi" or unknown
        "greeting": {
            "content": '{"intent": "unknown", "confidence": 0.8, "entities": {}}',
            "intent": "unknown",
        },
    }

    @property
    def provider_name(self) -> str:
        return "mock"

    async def test_connection(self) -> bool:
        """Mock connection check."""
        return True

    async def chat(
        self,
        messages: List[LLMMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> LLMResponse:
        """Return deterministic response based on keywords in the *last* user message."""

        # Extract last user message
        last_user_msg = next(
            (m.content for m in reversed(messages) if m.role == "user"), ""
        ).lower()

        logger.info("mock_llm_chat", message=last_user_msg)

        # Determine response logic (mirrors tests/fixtures/mock_llm.py)
        response_data = self.PREDEFINED_RESPONSES["product_search_vague"]  # Default

        if any(w in last_user_msg for w in ["checkout", "buy", "purchase"]):
            response_data = self.PREDEFINED_RESPONSES["checkout_request"]
        elif any(w in last_user_msg for w in ["order", "where is", "track"]):
            response_data = self.PREDEFINED_RESPONSES["order_status"]
        elif any(w in last_user_msg for w in ["human", "person", "agent", "speak to"]):
            response_data = self.PREDEFINED_RESPONSES["human_handoff"]
        elif any(w in last_user_msg for w in ["cart", "bag"]):
            response_data = self.PREDEFINED_RESPONSES["view_cart"]
        elif any(w in last_user_msg for w in ["add", "put"]):
            response_data = self.PREDEFINED_RESPONSES["add_to_cart"]
        elif any(w in last_user_msg for w in ["budget", "size", "under", "less than"]):
            response_data = self.PREDEFINED_RESPONSES["product_search_simple"]
        elif "hi" == last_user_msg or "hello" in last_user_msg:
            response_data = self.PREDEFINED_RESPONSES["greeting"]

        # Note: The IntentClassifier expects JSON in the content
        return LLMResponse(
            content=response_data["content"],
            tokens_used=10,
            model="mock-model",
            provider="mock",
            metadata={"mock": True, "intent": response_data["intent"]},
        )

    def count_tokens(self, text: str) -> int:
        return len(text) // 4

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        return 0.0
