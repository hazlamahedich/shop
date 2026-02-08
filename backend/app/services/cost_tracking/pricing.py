"""LLM Pricing Configuration.

Centralized pricing data for all LLM providers.
Prices are per 1M tokens (input, output) in USD.

Based on pricing from LLM providers as of 2026-02.
Update these values when provider pricing changes.
"""

from __future__ import annotations

from typing import Final

# Provider pricing per 1M tokens (input, output) in USD
LLM_PRICING: Final[dict[str, dict | float]] = {
    "ollama": {"input": 0.0, "output": 0.0},
    "openai": {
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "gpt-4o": {"input": 2.50, "output": 10.0},
        "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
    },
    "anthropic": {
        "claude-3-haiku": {"input": 0.25, "output": 1.25},
        "claude-3-sonnet": {"input": 3.0, "output": 15.0},
    },
    "gemini": {
        "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
        "gemini-pro": {"input": 0.50, "output": 1.50},
    },
    "glm": {
        "glm-4-flash": {"input": 0.10, "output": 0.10},
        "glm-4-plus": {"input": 0.50, "output": 0.50},
    },
}
