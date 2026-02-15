"""LLM Pricing Configuration.

Centralized pricing data for all LLM providers.
Prices are per 1M tokens (input, output) in USD.

Dynamic pricing is fetched from OpenRouter API and cached.
Fallback static pricing is used when API is unavailable.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
import structlog

logger = structlog.get_logger(__name__)

STATIC_PRICING: Dict[str, Dict | float] = {
    "ollama": {"input": 0.0, "output": 0.0},
    "openai": {
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "gpt-4o": {"input": 2.50, "output": 10.0},
        "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
        "gpt-4": {"input": 30.0, "output": 60.0},
        "gpt-4-turbo": {"input": 10.0, "output": 30.0},
    },
    "anthropic": {
        "claude-3-haiku": {"input": 0.25, "output": 1.25},
        "claude-3-sonnet": {"input": 3.0, "output": 15.0},
        "claude-3-opus": {"input": 15.0, "output": 75.0},
        "claude-3-5-haiku": {"input": 1.0, "output": 5.0},
        "claude-3-5-sonnet": {"input": 3.0, "output": 15.0},
    },
    "gemini": {
        "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
        "gemini-pro": {"input": 0.50, "output": 1.50},
        "gemini-1.5-pro": {"input": 3.50, "output": 10.50},
    },
    "glm": {
        "glm-4-flash": {"input": 0.10, "output": 0.10},
        "glm-4-plus": {"input": 0.50, "output": 0.50},
    },
}

_dynamic_pricing: Dict[str, Dict[str, Dict[str, float]]] = {}


def set_dynamic_pricing(provider: str, model: str, input_price: float, output_price: float) -> None:
    """Set dynamic pricing for a provider/model."""
    if provider not in _dynamic_pricing:
        _dynamic_pricing[provider] = {}
    _dynamic_pricing[provider][model] = {
        "input": input_price,
        "output": output_price,
    }


def get_pricing(provider: str, model: Optional[str] = None) -> Dict[str, float]:
    """Get pricing for a provider/model.

    Checks dynamic pricing first, then falls back to static pricing.

    Args:
        provider: Provider ID (openai, anthropic, etc.)
        model: Model ID (gpt-4o-mini, claude-3-haiku, etc.)

    Returns:
        Dict with 'input' and 'output' prices per 1M tokens
    """
    if provider in _dynamic_pricing and model in _dynamic_pricing[provider]:
        return _dynamic_pricing[provider][model]

    if provider not in STATIC_PRICING:
        return {"input": 0.0, "output": 0.0}

    provider_pricing = STATIC_PRICING[provider]

    if isinstance(provider_pricing, dict) and "input" in provider_pricing:
        return provider_pricing

    if isinstance(provider_pricing, dict) and model and model in provider_pricing:
        return provider_pricing[model]

    if isinstance(provider_pricing, dict) and model:
        for model_key in provider_pricing:
            if model_key in model or model in model_key:
                return provider_pricing[model_key]

    return {"input": 0.0, "output": 0.0}


def calculate_cost(
    provider: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
) -> float:
    """Calculate cost for token usage.

    Args:
        provider: Provider ID
        model: Model ID
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens

    Returns:
        Total cost in USD
    """
    pricing = get_pricing(provider, model)
    input_cost = (input_tokens / 1_000_000) * pricing.get("input", 0.0)
    output_cost = (output_tokens / 1_000_000) * pricing.get("output", 0.0)
    return input_cost + output_cost


def update_pricing_from_discovery(models_data: list[Dict[str, Any]]) -> int:
    """Update dynamic pricing from model discovery data.

    Args:
        models_data: List of model data from ModelDiscoveryService

    Returns:
        Number of models updated
    """
    updated = 0
    for model in models_data:
        provider = model.get("provider", "")
        model_id = model.get("id", "")
        pricing = model.get("pricing", {})

        input_price = pricing.get("inputCostPerMillion", pricing.get("input_cost_per_million", 0.0))
        output_price = pricing.get(
            "outputCostPerMillion", pricing.get("output_cost_per_million", 0.0)
        )

        if provider and model_id:
            set_dynamic_pricing(provider, model_id, input_price, output_price)
            updated += 1

    if updated > 0:
        logger.info("dynamic_pricing_updated", models_updated=updated)

    return updated


LLM_PRICING = STATIC_PRICING
