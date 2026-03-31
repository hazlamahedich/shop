"""LLM-based Context Extractor (Proof of Concept).

This module demonstrates how to use LLM for context extraction
instead of regex patterns, addressing technical debt item #1.

Usage:
    extractor = LLMContextExtractor(llm_service)
    context = await extractor.extract(
        message="Show me red shoes under $50",
        mode="ecommerce",
        existing_context={}
    )
    # Returns: {
    #     "product_ids": [],
    #     "price_constraints": {"max": 50},
    #     "color_preferences": ["red"],
    #     "categories": ["shoes"]
    # }
"""

from __future__ import annotations

import json
import logging
from typing import Any

from app.services.llm.base_llm_service import BaseLLMService

logger = logging.getLogger(__name__)


class LLMContextExtractor:
    """Extract conversation context using LLM with mode-aware prompts.

    This is a proof-of-concept for replacing regex-based extraction
    with LLM-based extraction for better accuracy and flexibility.

    Technical Debt: Story 11-1, Item #1
    """

    def __init__(self, llm_service: BaseLLMService):
        """Initialize LLM context extractor.

        Args:
            llm_service: LLM service for context extraction
        """
        self.llm = llm_service

    async def extract(
        self,
        message: str,
        mode: str,
        existing_context: dict[str, Any],
    ) -> dict[str, Any]:
        """Extract context from user message using LLM.

        Args:
            message: User message to extract context from
            mode: Merchant mode (ecommerce or general)
            existing_context: Previous context in conversation

        Returns:
            Extracted context as dictionary
        """
        system_prompt = self._get_system_prompt(mode)

        user_prompt = self._build_user_prompt(message, existing_context)

        try:
            response = await self.llm.generate(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,  # Low temperature for consistent extraction
                max_tokens=500,
            )

            extracted_context = self._parse_response(response)

            logger.info(
                "llm_context_extraction_success",
                mode=mode,
                message_length=len(message),
                extracted_fields=list(extracted_context.keys()),
            )

            return extracted_context

        except Exception as e:
            logger.error(
                "llm_context_extraction_failed",
                mode=mode,
                error=str(e),
            )
            # Fallback to empty context on error
            return {}

    def _get_system_prompt(self, mode: str) -> str:
        """Get mode-specific system prompt for LLM.

        Args:
            mode: Merchant mode (ecommerce or general)

        Returns:
            System prompt string
        """
        if mode == "ecommerce":
            return """You are a context extraction expert for e-commerce conversations.

Extract the following information from the user message:
- product_ids: List of product IDs mentioned (integers, e.g., [123, 456])
- price_constraints: Budget/price limits with min/max (e.g., {"min": 20, "max": 100})
- size_preferences: Size requirements (e.g., ["M", "10"])
- color_preferences: Color requirements (e.g., ["red", "blue"])
- categories: Product categories of interest (e.g., ["shoes", "running"])
- urgency: How urgent (immediate/soon/eventual/none)

Rules:
- Return ONLY valid JSON, no explanations
- Use empty arrays [] if nothing found
- Use null for optional fields not mentioned
- Infer implicit references from conversation history
- Extract numbers from price mentions ($50, "50 dollars", etc.)

Example output format:
{
  "product_ids": [123, 456],
  "price_constraints": {"max": 100},
  "size_preferences": ["M"],
  "color_preferences": ["red"],
  "categories": ["shoes"],
  "urgency": "soon"
}"""

        else:  # general mode
            return """You are a context extraction expert for customer support conversations.

Extract the following information from the user message:
- topics: Main topics discussed (e.g., ["login", "password", "order"])
- issues: Problems or complaints mentioned (e.g., ["cannot access", "late delivery"])
- escalation_needed: Whether this requires human intervention (true/false)
- sentiment: Customer sentiment (positive/neutral/negative)
- urgency: How urgent (immediate/soon/eventual/none)

Rules:
- Return ONLY valid JSON, no explanations
- Use empty arrays [] if nothing found
- Detect sentiment from language and tone
- Escalation needed if: angry, repeated issues, complex problem, urgent request
- Infer urgency from words like "asap", "emergency", "when", etc.

Example output format:
{
  "topics": ["login", "account"],
  "issues": ["cannot access account"],
  "escalation_needed": false,
  "sentiment": "neutral",
  "urgency": "soon"
}"""

    def _build_user_prompt(
        self,
        message: str,
        existing_context: dict[str, Any],
    ) -> str:
        """Build user prompt with message and context.

        Args:
            message: User message
            existing_context: Previous conversation context

        Returns:
            User prompt string
        """
        prompt = f"User message: {message}\n"

        if existing_context:
            prompt += f"\nPrevious context:\n{json.dumps(existing_context, indent=2)}\n"
            prompt += "\nNote: Consider the previous context when extracting. "
            prompt += "For example, if user says 'in blue' and previous context "
            prompt += "shows they were discussing shoes, extract color_preferences as ['blue']."

        return prompt

    def _parse_response(self, response: str) -> dict[str, Any]:
        """Parse LLM response and validate JSON.

        Args:
            response: LLM response string

        Returns:
            Parsed context dictionary
        """
        try:
            # Try to extract JSON from response
            # Handle markdown code blocks
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            elif "```" in response:
                json_start = response.find("```") + 3
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            else:
                json_str = response.strip()

            context = json.loads(json_str)

            # Validate structure
            if not isinstance(context, dict):
                logger.warning("llm_response_not_dict", response=response)
                return {}

            return context

        except json.JSONDecodeError as e:
            logger.error(
                "llm_json_parse_error",
                error=str(e),
                response=response[:200],  # Log first 200 chars
            )
            return {}

    def _merge_context(
        self,
        existing_context: dict[str, Any],
        new_context: dict[str, Any],
    ) -> dict[str, Any]:
        """Merge new context with existing context.

        Args:
            existing_context: Previous context
            new_context: Newly extracted context

        Returns:
            Merged context dictionary
        """
        merged = existing_context.copy()

        for key, value in new_context.items():
            if value is None or value == [] or value == "":
                # Skip empty values
                continue

            if isinstance(value, list):
                # Merge lists, avoiding duplicates
                existing_list = merged.get(key, [])
                merged[key] = list(set(existing_list + value))
            elif isinstance(value, dict):
                # Merge dicts, with new values taking precedence
                existing_dict = merged.get(key, {})
                merged[key] = {**existing_dict, **value}
            else:
                # Replace non-list, non-dict values
                merged[key] = value

        return merged


# Example usage (for testing):
async def example_usage():
    """Example of how to use LLMContextExtractor."""
    from app.services.llm.anthropic_llm import AnthropicLLMService

    # Initialize
    llm_service = AnthropicLLMService()
    extractor = LLMContextExtractor(llm_service)

    # Example 1: E-commerce mode
    context1 = await extractor.extract(
        message="Show me red running shoes under $100",
        mode="ecommerce",
        existing_context={},
    )
    print(f"E-commerce context: {json.dumps(context1, indent=2)}")

    # Example 2: With previous context
    context2 = await extractor.extract(
        message="What about in blue?",
        mode="ecommerce",
        existing_context=context1,  # User is referring back to shoes
    )
    print(f"E-commerce context (with history): {json.dumps(context2, indent=2)}")

    # Example 3: General mode
    context3 = await extractor.extract(
        message="I haven't received my order yet and it's been 2 weeks!",
        mode="general",
        existing_context={},
    )
    print(f"General context: {json.dumps(context3, indent=2)}")
