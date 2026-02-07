"""Tests for LLM Cost Calculator service.

Tests cost calculation accuracy for different providers and token amounts.
Per NFR-L3, cost calculations must be accurate within 5%.
"""

from __future__ import annotations

import pytest

from app.services.export.cost_calculator import CostCalculator, LLM_PRICING


class TestCostCalculator:
    """Test suite for CostCalculator service."""

    @pytest.fixture
    def calculator(self) -> CostCalculator:
        """Create a CostCalculator instance for testing."""
        return CostCalculator()

    def test_ollama_free_provider(self, calculator: CostCalculator) -> None:
        """Test that Ollama provider returns zero cost (self-hosted)."""
        cost = calculator.calculate_llm_cost("ollama", 1_000_000)
        assert cost == 0.0

    def test_ollama_free_with_any_tokens(self, calculator: CostCalculator) -> None:
        """Test that Ollama is free regardless of token count."""
        assert calculator.calculate_llm_cost("ollama", 0) == 0.0
        assert calculator.calculate_llm_cost("ollama", 100) == 0.0
        assert calculator.calculate_llm_cost("ollama", 10_000_000) == 0.0

    def test_openai_cost_calculation(self, calculator: CostCalculator) -> None:
        """Test OpenAI cost calculation with exact million tokens."""
        # 1M tokens * 0.0015 per M = 0.0015
        cost = calculator.calculate_llm_cost("openai", 1_000_000)
        assert cost == 0.0015

    def test_openai_partial_million(self, calculator: CostCalculator) -> None:
        """Test OpenAI cost with partial million tokens."""
        # 500K tokens * 0.0015 per M = 0.00075
        cost = calculator.calculate_llm_cost("openai", 500_000)
        assert cost == 0.0008  # Rounded to 4 decimal places

    def test_openai_small_token_count(self, calculator: CostCalculator) -> None:
        """Test OpenAI cost with small token count."""
        # 1000 tokens * 0.0015 per M = 0.0000015
        cost = calculator.calculate_llm_cost("openai", 1_000)
        assert cost == 0.0  # Rounds to 0.0000 at 4 decimals

    def test_anthropic_cost_calculation(self, calculator: CostCalculator) -> None:
        """Test Anthropic cost calculation."""
        # 1M tokens * 0.00025 per M = 0.00025
        cost = calculator.calculate_llm_cost("anthropic", 1_000_000)
        assert cost == 0.0003  # Rounded to 4 decimal places

    def test_gemini_cost_calculation(self, calculator: CostCalculator) -> None:
        """Test Gemini cost calculation."""
        # 1M tokens * 0.00007 per M = 0.00007
        cost = calculator.calculate_llm_cost("gemini", 1_000_000)
        assert cost == 0.0001  # Rounded to 4 decimal places

    def test_glm_cost_calculation(self, calculator: CostCalculator) -> None:
        """Test GLM-4.7 cost calculation."""
        # 1M tokens * 0.0001 per M = 0.0001
        cost = calculator.calculate_llm_cost("glm-4.7", 1_000_000)
        assert cost == 0.0001

    def test_unknown_provider_defaults_to_free(self, calculator: CostCalculator) -> None:
        """Test that unknown providers default to Ollama (free)."""
        cost = calculator.calculate_llm_cost("unknown_provider", 1_000_000)
        assert cost == 0.0

    def test_case_insensitive_provider(self, calculator: CostCalculator) -> None:
        """Test that provider names are case-insensitive."""
        cost_upper = calculator.calculate_llm_cost("OPENAI", 1_000_000)
        cost_lower = calculator.calculate_llm_cost("openai", 1_000_000)
        cost_mixed = calculator.calculate_llm_cost("OpenAI", 1_000_000)

        assert cost_upper == cost_lower == cost_mixed == 0.0015

    def test_zero_tokens(self, calculator: CostCalculator) -> None:
        """Test cost calculation with zero tokens."""
        cost = calculator.calculate_llm_cost("openai", 0)
        assert cost == 0.0

    def test_large_token_count(self, calculator: CostCalculator) -> None:
        """Test cost calculation with very large token count."""
        # 10M tokens * 0.0015 per M = 0.015
        cost = calculator.calculate_llm_cost("openai", 10_000_000)
        assert cost == 0.015

    def test_get_provider_pricing_openai(self, calculator: CostCalculator) -> None:
        """Test getting pricing for OpenAI."""
        pricing = calculator.get_provider_pricing("openai")
        assert pricing == {"per_million": 0.0015}

    def test_get_provider_pricing_ollama(self, calculator: CostCalculator) -> None:
        """Test getting pricing for Ollama."""
        pricing = calculator.get_provider_pricing("ollama")
        assert pricing == {"per_million": 0.0}

    def test_get_provider_pricing_unknown(self, calculator: CostCalculator) -> None:
        """Test getting pricing for unknown provider defaults to Ollama."""
        pricing = calculator.get_provider_pricing("unknown")
        assert pricing == {"per_million": 0.0}

    def test_list_supported_providers(self, calculator: CostCalculator) -> None:
        """Test listing all supported providers."""
        providers = calculator.list_supported_providers()
        assert isinstance(providers, list)
        assert "openai" in providers
        assert "ollama" in providers
        assert "anthropic" in providers
        assert "gemini" in providers
        assert "glm-4.7" in providers

    def test_cost_accuracy_within_5_percent(self, calculator: CostCalculator) -> None:
        """Test cost calculation accuracy within 5% per NFR-L3."""
        # For OpenAI: 1M tokens should be $0.0015
        expected_cost = 0.0015
        actual_cost = calculator.calculate_llm_cost("openai", 1_000_000)

        # Calculate percentage difference
        percentage_diff = abs(actual_cost - expected_cost) / expected_cost * 100
        assert percentage_diff < 5.0, f"Cost accuracy {percentage_diff}% exceeds 5% threshold"

    def test_realistic_conversation_tokens(self, calculator: CostCalculator) -> None:
        """Test cost for realistic conversation token counts."""
        # Typical conversation might use 500-2000 tokens
        cost_500 = calculator.calculate_llm_cost("openai", 500)
        cost_1000 = calculator.calculate_llm_cost("openai", 1_000)
        cost_2000 = calculator.calculate_llm_cost("openai", 2_000)

        # All should round appropriately
        assert cost_500 == 0.0  # 0.00000075 rounds to 0.0000
        assert cost_1000 == 0.0  # 0.0000015 rounds to 0.0000
        assert cost_2000 == 0.0  # 0.000003 rounds to 0.0000

    def test_rounding_behavior(self, calculator: CostCalculator) -> None:
        """Test that costs are consistently rounded to 4 decimal places."""
        # Test values that should round up
        cost = calculator.calculate_llm_cost("openai", 340_000)
        # 340K * 0.0015 / 1M = 0.00051 -> rounds to 0.0005
        assert cost == 0.0005

        # Test values at rounding boundary
        cost_boundary = calculator.calculate_llm_cost("openai", 333_334)
        # 333.334K * 0.0015 / 1M = 0.000500001 -> rounds to 0.0005
        assert cost_boundary == 0.0005
