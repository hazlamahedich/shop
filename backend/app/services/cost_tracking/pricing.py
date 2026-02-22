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
        "gemini-2.5-flash-lite": {"input": 0.10, "output": 0.40},
        "gemini-2.5-flash": {"input": 0.30, "output": 2.50},
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
        model_id = model.get("id", "")

        # Handle OpenRouter format (e.g., "google/gemini-2.5-flash-lite")
        if "/" in model_id:
            provider_prefix, model_name = model_id.split("/", 1)
        else:
            provider_prefix = model.get("provider", "")
            model_name = model_id

        # Map OpenRouter provider prefixes to our provider IDs
        provider_mapping = {
            "google": "gemini",
            "openai": "openai",
            "anthropic": "anthropic",
            "meta-llama": "meta",
        }
        provider = provider_mapping.get(provider_prefix, provider_prefix)

        # Get pricing - handle both formats
        input_price = (
            model.get("input_price_per_million")
            or model.get("inputCostPerMillion")
            or model.get("input_cost_per_million", 0.0)
        )

        output_price = (
            model.get("output_price_per_million")
            or model.get("outputCostPerMillion")
            or model.get("output_cost_per_million", 0.0)
        )

        # Also check nested pricing object
        pricing = model.get("pricing", {})
        if not input_price:
            input_price = pricing.get("inputCostPerMillion") or pricing.get(
                "input_cost_per_million", 0.0
            )
        if not output_price:
            output_price = pricing.get("outputCostPerMillion") or pricing.get(
                "output_cost_per_million", 0.0
            )

        if provider and model_name:
            set_dynamic_pricing(
                provider, model_name, float(input_price or 0), float(output_price or 0)
            )
            updated += 1

    if updated > 0:
        logger.info("dynamic_pricing_updated", models_updated=updated)

    return updated


OPENROUTER_API_URL = "https://openrouter.ai/api/v1/models"


async def initialize_pricing_from_openrouter() -> int:
    """Fetch pricing from OpenRouter API and populate dynamic pricing cache.

    Should be called on application startup to ensure all models have
    correct pricing before any LLM requests are made.

    Returns:
        Number of models with pricing updated
    """
    import httpx

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(OPENROUTER_API_URL)
            response.raise_for_status()
            data = response.json()

        models = data.get("data", [])
        updated = 0

        for model_data in models:
            model_id = model_data.get("id", "")

            # Handle OpenRouter format (e.g., "google/gemini-2.5-flash-lite")
            if "/" not in model_id:
                continue

            provider_prefix, model_name = model_id.split("/", 1)

            # Map OpenRouter provider prefixes to our provider IDs
            provider_mapping = {
                "google": "gemini",
                "openai": "openai",
                "anthropic": "anthropic",
                "meta-llama": "meta",
            }
            provider = provider_mapping.get(provider_prefix, provider_prefix)

            # Get pricing from OpenRouter (per-token, convert to per-1M)
            pricing = model_data.get("pricing", {})
            prompt_price = float(pricing.get("prompt", 0) or 0)
            completion_price = float(pricing.get("completion", 0) or 0)

            input_per_million = prompt_price * 1_000_000
            output_per_million = completion_price * 1_000_000

            if provider and model_name:
                set_dynamic_pricing(provider, model_name, input_per_million, output_per_million)
                updated += 1

        logger.info("pricing_initialized_from_openrouter", models_updated=updated)
        return updated

    except Exception as e:
        logger.warning("openrouter_pricing_init_failed", error=str(e))
        return 0


LLM_PRICING = STATIC_PRICING
