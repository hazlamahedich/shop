"""Context Summarization Service using LLM.

Story 11-1: Conversation Context Memory
Task 4: Implement context summarization to avoid token bloat.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings as get_settings
from app.services.llm.base_llm_service import BaseLLMService, LLMMessage
from app.services.llm.llm_factory import LLMProviderFactory

logger = structlog.get_logger(__name__)

_PRODUCT_PATTERN = re.compile(
    r"\b(shoes?|shirt|dress|jacket|pants?|hat|bag|phone|laptop|watch|headphones?)\b",
    re.IGNORECASE,
)
_PRICE_PATTERN = re.compile(r"\$\d+[\d,.]*|\d+\s?(?:dollars?|bucks?)", re.IGNORECASE)
_SIZE_PATTERN = re.compile(r"\bsize\s+([\w]+)\b", re.IGNORECASE)
_COLOR_PATTERN = re.compile(
    r"\b(red|blue|green|black|white|yellow|orange|pink|purple|brown|gray|grey|navy)\b",
    re.IGNORECASE,
)

MAX_CONTEXT_CHARS_FOR_PROMPT = 12000


class ContextSummarizerService:
    """Summarizes conversation context using LLM for token efficiency.

    Trigger Conditions:
    - Every 5 conversation turns
    - Context size exceeds 1KB
    - Before LLM prompt generation

    Summary Structure:
    {
        "original_turns": 10,
        "summarized_at": "2026-03-31T12:00:00Z",
        "key_points": [
            "Customer looking for running shoes under $100",
            "Prefers Nike brand",
            "Size 10, red color preference"
        ],
        "active_constraints": {
            "budget_max": 100,
            "brand": "Nike"
        }
    }
    """

    def __init__(
        self,
        db: AsyncSession,
        llm_service: BaseLLMService | None = None,
    ):
        """Initialize context summarizer service.

        Args:
            db: Database session (for loading merchant config if needed)
            llm_service: LLM service instance (optional, will create if not provided)
        """
        self.db = db
        self.llm = llm_service
        self.logger = structlog.get_logger(__name__)

    async def summarize_context(
        self,
        context: dict[str, Any],
        conversation_id: int | None = None,
    ) -> dict[str, Any]:
        """Summarize conversation context using LLM.

        Args:
            context: Current context dictionary
            conversation_id: Optional conversation ID for logging

        Returns:
            Summary dictionary with key_points and active_constraints
        """
        mode = context.get("mode", "ecommerce")

        try:
            # Build summarization prompt based on mode
            system_prompt = self._get_system_prompt(mode)
            user_prompt = self._build_user_prompt(context, mode)

            # Call LLM for summarization
            if not self.llm:
                self.llm = self._create_llm_service()

            messages = [
                LLMMessage(role="system", content=system_prompt),
                LLMMessage(role="user", content=user_prompt),
            ]

            response = await self.llm.chat(
                messages=messages,
                temperature=0.3,  # Low temperature for consistent summaries
                max_tokens=500,
            )

            # Parse LLM response
            summary = self._parse_summary_response(response.content, context, mode)

            self.logger.info(
                "Context summarized successfully",
                conversation_id=conversation_id,
                original_turns=context.get("turn_count", 0),
                summary_points=len(summary.get("key_points", [])),
            )

            return summary

        except Exception as e:
            self.logger.error(
                "Summarization failed, using fallback",
                error=str(e),
                conversation_id=conversation_id,
            )
            # Fallback to simple extraction
            return self._fallback_summary(context)

    def _get_system_prompt(self, mode: str) -> str:
        """Get system prompt for summarization based on mode.

        Args:
            mode: Merchant mode (ecommerce or general)

        Returns:
            System prompt for LLM
        """
        if mode == "ecommerce":
            return """You are a conversation summarization assistant for e-commerce chatbots.
Your task is to analyze the conversation context and extract key information.

Focus on:
1. Products viewed/mentioned (with IDs if available)
2. Budget/price constraints
3. Size, color, brand preferences
4. Cart status
5. Search history themes

Output a JSON object with this exact structure:
{
    "key_points": [
        "Customer is looking for red running shoes under $100",
        "Prefers Nike brand, size 10"
    ],
    "active_constraints": {
        "budget_max": 100,
        "brand": "Nike",
        "size": "10",
        "color": "red"
    }
}

Keep key_points concise (3-5 bullet points max).
Include all active constraints in active_constraints."""
        else:  # general mode
            return """You are a conversation summarization assistant for customer support chatbots.
Your task is to analyze the conversation context and extract key information.

Focus on:
1. Topics discussed
2. Documents/articles referenced
3. Support issues raised (with types)
4. Escalation status
5. Customer sentiment indicators

Output a JSON object with this exact structure:
{
    "key_points": [
        "Customer has login issues",
        "Referenced KB article 123",
        "Low frustration detected"
    ],
    "active_constraints": {
        "escalation_status": "low",
        "active_issues": ["login"]
    }
}

Keep key_points concise (3-5 bullet points max).
Include all active issues and constraints in active_constraints."""

    def _build_user_prompt(self, context: dict[str, Any], mode: str) -> str:
        """Build user prompt with context data.

        Truncates conversation history if context exceeds MAX_CONTEXT_CHARS_FOR_PROMPT
        to avoid hitting LLM token limits on long conversations.

        Args:
            context: Current context dictionary
            mode: Merchant mode

        Returns:
            User prompt for LLM
        """
        context_json = json.dumps(context, indent=2, default=str)

        if len(context_json) > MAX_CONTEXT_CHARS_FOR_PROMPT:
            context_json = self._truncate_context(context, MAX_CONTEXT_CHARS_FOR_PROMPT)

        if mode == "ecommerce":
            prompt = f"""Analyze this e-commerce conversation context and provide a summary:

```json
{context_json}
```

Extract key points and active constraints."""
        else:  # general mode
            prompt = f"""Analyze this customer support conversation context and provide a summary:

```json
{context_json}
```

Extract key points and active constraints."""

        return prompt

    def _truncate_context(self, context: dict[str, Any], max_chars: int) -> str:
        """Truncate context to fit within token budget by trimming conversation history.

        Keeps recent messages and discards older ones when context is too large.

        Args:
            context: Current context dictionary
            max_chars: Maximum character budget

        Returns:
            JSON string of truncated context
        """
        context_copy = dict(context)
        history = list(context_copy.get("conversation_history", []))

        if not history:
            return json.dumps(context_copy, indent=2, default=str)

        summary_line = f"[... {len(history)} earlier messages truncated for length ...]"

        while history:
            context_copy["conversation_history"] = [summary_line] + history
            serialized = json.dumps(context_copy, indent=2, default=str)
            if len(serialized) <= max_chars:
                return serialized
            history.pop(0)

        context_copy["conversation_history"] = [summary_line]
        return json.dumps(context_copy, indent=2, default=str)

    def _parse_summary_response(
        self,
        llm_response: str,
        context: dict[str, Any],
        mode: str,
    ) -> dict[str, Any]:
        """Parse LLM response into summary structure.

        Args:
            llm_response: Raw LLM response text
            context: Original context (for fallback)
            mode: Merchant mode

        Returns:
            Parsed summary dictionary
        """
        try:
            # Try to parse JSON response
            # Handle markdown code blocks if present
            if "```json" in llm_response:
                # Extract JSON from code block
                start = llm_response.find("```json") + 7
                end = llm_response.find("```", start)
                json_str = llm_response[start:end].strip()
            elif "```" in llm_response:
                # Extract from plain code block
                start = llm_response.find("```") + 3
                end = llm_response.find("```", start)
                json_str = llm_response[start:end].strip()
            else:
                json_str = llm_response.strip()

            parsed = json.loads(json_str)

            # Build summary structure
            summary = {
                "original_turns": context.get("turn_count", 0),
                "summarized_at": datetime.now(timezone.utc).isoformat(),
                "key_points": parsed.get("key_points", []),
                "active_constraints": parsed.get("active_constraints", {}),
            }

            return summary

        except json.JSONDecodeError as e:
            self.logger.warning(
                "Failed to parse LLM response as JSON",
                error=str(e),
                response=llm_response[:200],
            )
            # Fallback to simple extraction
            return self._fallback_summary(context)

    def _fallback_summary(self, context: dict[str, Any]) -> dict[str, Any]:
        """Fallback summarization without LLM.

        Args:
            context: Current context dictionary

        Returns:
            Simple summary dictionary
        """
        key_points = []
        active_constraints = context.get("constraints", {})
        mode = context.get("mode", "ecommerce")

        if mode == "ecommerce":
            # Extract key points from e-commerce context
            if context.get("viewed_products"):
                key_points.append(
                    f"Viewed {len(context['viewed_products'])} products: {context['viewed_products'][:3]}"
                )
            if active_constraints.get("budget_max"):
                key_points.append(f"Budget max: ${active_constraints['budget_max']}")
            if active_constraints.get("brand"):
                key_points.append(f"Brand preference: {active_constraints['brand']}")
            if active_constraints.get("size") or active_constraints.get("color"):
                preferences = []
                if active_constraints.get("size"):
                    preferences.append(f"size {active_constraints['size']}")
                if active_constraints.get("color"):
                    preferences.append(f"{active_constraints['color']} color")
                key_points.append(f"Preferences: {', '.join(preferences)}")

        else:  # general mode
            # Extract key points from general mode context
            if context.get("topics_discussed"):
                key_points.append(f"Topics: {', '.join(context['topics_discussed'][:3])}")
            if context.get("documents_referenced"):
                key_points.append(f"Referenced {len(context['documents_referenced'])} documents")
            if context.get("support_issues"):
                issue_types = [issue.get("type", "unknown") for issue in context["support_issues"]]
                key_points.append(f"Issues: {', '.join(issue_types)}")
            if context.get("escalation_status"):
                key_points.append(f"Escalation: {context['escalation_status']}")

        return {
            "original_turns": context.get("turn_count", 0),
            "summarized_at": datetime.now(timezone.utc).isoformat(),
            "key_points": key_points,
            "active_constraints": active_constraints,
        }

    async def summarize_for_customer(
        self,
        context_dict: dict[str, Any],
        mode: str,
        conversation_id: int | None = None,
    ) -> str:
        """Generate a customer-facing conversation summary in markdown format.

        Uses a separate prompt and parser from the internal summarize_context().
        Returns formatted markdown string, NOT a dict.

        Args:
            context_dict: Conversation context as dict
            mode: Merchant mode (ecommerce or general)
            conversation_id: Conversation ID for logging

        Returns:
            Markdown-formatted summary string
        """
        try:
            system_prompt = self._get_customer_system_prompt(mode)

            user_prompt = self._build_user_prompt(context_dict, mode)

            if not self.llm:
                self.llm = self._create_llm_service()

            messages = [
                LLMMessage(role="system", content=system_prompt),
                LLMMessage(role="user", content=user_prompt),
            ]

            response = await self.llm.chat(
                messages=messages,
                temperature=0.3,
                max_tokens=800,
            )

            return response.content.strip()

        except Exception as e:
            self.logger.error(
                "Customer summarization failed, using fallback",
                error=str(e),
                conversation_id=conversation_id,
            )
            return self._fallback_customer_summary(context_dict, mode)

    def _get_customer_system_prompt(self, mode: str) -> str:
        """Get system prompt for customer-facing summarization.

        Args:
            mode: Merchant mode (ecommerce or general)

        Returns:
            System prompt instructing LLM to output formatted markdown
        """
        if mode == "ecommerce":
            return (
                "Summarize this shopping conversation for the customer in markdown. "
                "Include sections:\n"
                "- 🛍️ Products Discussed\n"
                "- 🎯 Preferences & Constraints\n"
                "- 🛒 Cart Status\n"
                "- 📋 Suggested Next Steps\n"
                "Use bullet points. Be concise and friendly."
            )
        return (
            "Summarize this support conversation for the customer in markdown. "
            "Include sections:\n"
            "- 📝 Topics Covered\n"
            "- 📄 Documents Referenced\n"
            "- ✅ Issues & Resolutions\n"
            "- ❓ Open Items\n"
            "Use bullet points. Be concise and friendly."
        )

    def _fallback_customer_summary(
        self,
        context_dict: dict[str, Any],
        mode: str,
    ) -> str:
        """Rule-based fallback for customer-facing summary without LLM.

        Args:
            context_dict: Conversation context as dict
            mode: Merchant mode

        Returns:
            Plain markdown summary string
        """
        history = context_dict.get("conversation_history", [])
        if not history:
            return "No conversation history to summarize."

        customer_messages = [
            msg.get("content", "")
            for msg in history
            if isinstance(msg, dict)
            and msg.get("role") in ("customer", "user")
            and msg.get("content")
        ]
        all_text = " ".join(customer_messages)

        if mode == "ecommerce":
            products = set(m.group(1).lower() for m in _PRODUCT_PATTERN.finditer(all_text))
            prices = _PRICE_PATTERN.findall(all_text)
            sizes = _SIZE_PATTERN.findall(all_text)
            colors = _COLOR_PATTERN.findall(all_text)

            lines = ["🛍️ **Discussion Summary:**"]
            if products:
                lines.append(f"- Products mentioned: {', '.join(sorted(products))}")
            if prices:
                lines.append(f"- Budget/price mentions: {', '.join(prices)}")
            if sizes:
                lines.append(f"- Size preferences: {', '.join(sizes)}")
            if colors:
                lines.append(f"- Color preferences: {', '.join(colors)}")
            if not any([products, prices, sizes, colors]):
                lines.append(
                    f"- {customer_messages[-1][:120]}"
                    if customer_messages
                    else "- No details extracted"
                )
            return "\n".join(lines)

        topics = [msg[:80] for msg in customer_messages] if customer_messages else []
        lines = ["📝 **Topics Covered:**"]
        for t in topics[:5]:
            lines.append(f"- {t}")
        if not topics:
            lines.append("- No topics extracted")
        return "\n".join(lines)

    def _create_llm_service(self) -> BaseLLMService:
        """Create LLM service instance using factory.

        Returns:
            LLM service instance
        """
        settings = get_settings()

        provider_name = settings.get("LLM_PROVIDER", "ollama")
        config = {
            "api_key": settings.get("LLM_API_KEY", ""),
            "model": settings.get("LLM_MODEL", "llama3"),
            "api_base": settings.get("LLM_API_BASE", ""),
        }

        llm_service = LLMProviderFactory.create_provider(provider_name, config)

        self.logger.info(
            "Created LLM service for summarization",
            provider=provider_name,
            model=config["model"],
        )

        return llm_service
