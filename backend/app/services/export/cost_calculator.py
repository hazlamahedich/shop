"""LLM Cost Calculator service.

Provides per-provider cost calculation for LLM usage across different
providers (Ollama, OpenAI, Anthropic, Gemini, GLM-4.7).
"""

from __future__ import annotations

from typing import Final


# LLM Provider pricing models (USD per million tokens)
# Source: Provider pricing pages as of 2026
LLM_PRICING: Final[dict[str, dict[str, float]]] = {
    "ollama": {
        "per_million": 0.0,  # Free (self-hosted)
    },
    "openai": {
        "per_million": 0.0015,  # gpt-3.5-turbo (approximate)
    },
    "anthropic": {
        "per_million": 0.00025,  # claude-instant (approximate)
    },
    "gemini": {
        "per_million": 0.00007,  # gemini-pro (approximate)
    },
    "glm-4.7": {
        "per_million": 0.0001,  # Approximate
    },
}


class CostCalculator:
    """Service for calculating LLM costs per provider.

    Provides cost estimation based on token usage and provider pricing.
    Costs are rounded to 4 decimal places for consistency in exports.
    """

    def calculate_llm_cost(self, provider: str, total_tokens: int) -> float:
        """Calculate estimated cost for LLM usage.

        Args:
            provider: LLM provider name (e.g., "openai", "ollama")
            total_tokens: Total tokens used (prompt + completion)

        Returns:
            Estimated cost in USD, rounded to 4 decimal places

        Examples:
            >>> calculator = CostCalculator()
            >>> calculator.calculate_llm_cost("ollama", 1000)
            0.0
            >>> calculator.calculate_llm_cost("openai", 1000000)
            0.0015
        """
        # Get pricing for provider, default to Ollama (free) if unknown
        pricing = LLM_PRICING.get(provider.lower(), LLM_PRICING["ollama"])
        per_million = pricing["per_million"]

        # Calculate cost: (tokens / 1M) * rate_per_million
        cost = (total_tokens / 1_000_000) * per_million

        # Round to 4 decimal places for consistency
        return round(cost, 4)

    def get_provider_pricing(self, provider: str) -> dict[str, float]:
        """Get pricing information for a provider.

        Args:
            provider: LLM provider name

        Returns:
            Dictionary with pricing information (per_million rate)

        Examples:
            >>> calculator = CostCalculator()
            >>> calculator.get_provider_pricing("openai")
            {'per_million': 0.0015}
        """
        return LLM_PRICING.get(provider.lower(), LLM_PRICING["ollama"])

    def list_supported_providers(self) -> list[str]:
        """Get list of supported LLM providers.

        Returns:
            List of provider names

        Examples:
            >>> calculator = CostCalculator()
            >>> "openai" in calculator.list_supported_providers()
            True
        """
        return list(LLM_PRICING.keys())
