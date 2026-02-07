/** Savings Calculator Component.
 *
 * Story 3.4: LLM Provider Switching
 *
 * Calculates and displays potential cost savings when switching providers.
 * Shows comparison between current provider and selected alternative.
 */

import React, { useMemo } from 'react';
import type { Provider, CurrentProvider } from '../../stores/llmProviderStore';

interface SavingsCalculatorProps {
  providers: Provider[];
  currentProvider: CurrentProvider | null;
}

interface SavingsCalculation {
  providerId: string;
  providerName: string;
  monthlyCost: number;
  savingsAmount: number;
  savingsPercentage: number;
}

export const SavingsCalculator: React.FC<SavingsCalculatorProps> = ({
  providers,
  currentProvider,
}) => {
  // Typical usage assumptions for calculations
  const MONTHLY_INPUT_TOKENS = 100000; // 100K input tokens
  const MONTHLY_OUTPUT_TOKENS = 50000; // 50K output tokens

  const savings = useMemo(() => {
    if (!currentProvider) return [];

    // Find current provider's pricing
    const currentProviderData = providers.find(p => p.id === currentProvider.id);
    if (!currentProviderData) return [];

    const currentCost = calculateMonthlyCost(currentProviderData, MONTHLY_INPUT_TOKENS, MONTHLY_OUTPUT_TOKENS);

    return providers
      .map((provider) => {
        const providerCost = calculateMonthlyCost(provider, MONTHLY_INPUT_TOKENS, MONTHLY_OUTPUT_TOKENS);
        const savingsAmount = currentCost - providerCost;
        const savingsPercentage = currentCost > 0 ? (savingsAmount / currentCost) * 100 : 0;

        return {
          providerId: provider.id,
          providerName: provider.name,
          monthlyCost: providerCost,
          savingsAmount,
          savingsPercentage,
        };
      })
      .filter((calc) => calc.savingsAmount > 0) // Only show providers with savings
      .sort((a, b) => b.savingsAmount - a.savingsAmount); // Sort by highest savings
  }, [providers, currentProvider, MONTHLY_INPUT_TOKENS, MONTHLY_OUTPUT_TOKENS]);

  if (!currentProvider || savings.length === 0) {
    return null;
  }

  const topSavings = savings.slice(0, 3); // Show top 3 savings options

  return (
    <div className="bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-lg p-6">
      <div className="flex items-center gap-2 mb-4">
        <svg
          className="w-6 h-6 text-green-600"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
        <h3 className="text-lg font-semibold text-green-900">Potential Monthly Savings</h3>
      </div>

      <p className="text-sm text-green-700 mb-4">
        Based on your typical usage ({(MONTHLY_INPUT_TOKENS / 1000).toFixed(0)}K input + {(MONTHLY_OUTPUT_TOKENS / 1000).toFixed(0)}K output tokens/month)
      </p>

      <div className="space-y-3">
        {topSavings.map((saving, index) => (
          <div
            key={saving.providerId}
            className="flex items-center justify-between bg-white rounded-lg p-4 border border-green-100"
          >
            <div className="flex items-center gap-3">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-white font-bold ${
                  index === 0 ? 'bg-green-500' : index === 1 ? 'bg-emerald-500' : 'bg-teal-500'
                }`}
              >
                {index + 1}
              </div>
              <div>
                <p className="font-medium text-gray-900">{saving.providerName}</p>
                <p className="text-sm text-gray-500">
                  ${saving.monthlyCost.toFixed(2)}/mo vs ${currentProvider.totalCostUsd.toFixed(2)}/mo
                </p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-lg font-bold text-green-600">
                -${saving.savingsAmount.toFixed(2)}
              </p>
              <p className="text-sm text-green-700">
                {saving.savingsPercentage.toFixed(0)}% savings
              </p>
            </div>
          </div>
        ))}
      </div>

      {/* Annual savings projection */}
      {topSavings.length > 0 && (
        <div className="mt-4 pt-4 border-t border-green-200">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-green-800">
              Estimated Annual Savings (top option):
            </span>
            <span className="text-xl font-bold text-green-900">
              ${(topSavings[0].savingsAmount * 12).toFixed(2)}
            </span>
          </div>
        </div>
      )}

      <p className="text-xs text-green-600 mt-4">
        * Savings are estimates based on typical usage. Your actual costs may vary based on your actual token consumption.
      </p>
    </div>
  );
};

/** Helper function to calculate monthly cost for a provider */
function calculateMonthlyCost(
  provider: Provider,
  inputTokens: number,
  outputTokens: number
): number {
  const inputCost = (inputTokens / 1000000) * provider.pricing.inputCost;
  const outputCost = (outputTokens / 1000000) * provider.pricing.outputCost;
  return inputCost + outputCost;
}
