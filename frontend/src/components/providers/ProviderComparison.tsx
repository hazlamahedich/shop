/** Provider Comparison Component.
 *
 * Story 3.4: LLM Provider Switching
 *
 * Displays pricing comparison table and cost estimates for all providers.
 * Helps merchants make informed decisions about provider selection.
 */

import React from 'react';
import type { Provider } from '../../stores/llmProviderStore';

interface ProviderComparisonProps {
  providers: Provider[];
}

export const ProviderComparison: React.FC<ProviderComparisonProps> = ({
  providers,
}) => {
  if (providers.length === 0) {
    return null;
  }

  return (
    <div className="mt-8">
      <h2 className="text-lg font-semibold mb-4">Provider Comparison</h2>

      <div className="overflow-x-auto">
        <table
          data-testid="provider-comparison-table"
          className="w-full border-collapse border border-gray-200"
          role="table"
          aria-label="LLM Provider Pricing Comparison"
        >
          <thead>
            <tr className="bg-gray-50">
              <th className="border border-gray-200 px-4 py-2 text-left font-semibold">
                Provider
              </th>
              <th className="border border-gray-200 px-4 py-2 text-right font-semibold">
                Input Cost (per 1M)
              </th>
              <th className="border border-gray-200 px-4 py-2 text-right font-semibold">
                Output Cost (per 1M)
              </th>
              <th className="border border-gray-200 px-4 py-2 text-right font-semibold">
                Est. Monthly Cost
              </th>
              <th className="border border-gray-200 px-4 py-2 text-left font-semibold">
                Key Features
              </th>
            </tr>
          </thead>
          <tbody>
            {providers.map((provider) => (
              <tr
                key={provider.id}
                className={provider.isActive ? 'bg-blue-50' : ''}
              >
                <td className="border border-gray-200 px-4 py-2">
                  <div className="font-medium">{provider.name}</div>
                  {provider.isActive && (
                    <span className="text-xs text-green-600 font-medium">
                      (Current)
                    </span>
                  )}
                </td>
                <td className="border border-gray-200 px-4 py-2 text-right">
                  ${provider.pricing.inputCost.toFixed(2)}
                </td>
                <td className="border border-gray-200 px-4 py-2 text-right">
                  ${provider.pricing.outputCost.toFixed(2)}
                </td>
                <td className="border border-gray-200 px-4 py-2 text-right">
                  ${provider.estimatedMonthlyCost?.toFixed(2) || '0.00'}
                </td>
                <td className="border border-gray-200 px-4 py-2">
                  <div className="flex flex-wrap gap-1">
                    {provider.features.slice(0, 3).map((feature) => (
                      <span
                        key={feature}
                        className="text-xs bg-gray-100 px-2 py-0.5 rounded capitalize"
                      >
                        {feature}
                      </span>
                    ))}
                    {provider.features.length > 3 && (
                      <span className="text-xs text-gray-500">
                        +{provider.features.length - 3} more
                      </span>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Savings Calculator Note */}
      <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
        <p className="text-sm text-yellow-800">
          <strong>Note:</strong> Estimated monthly costs are based on typical usage
          (100K input + 50K output tokens). Your actual costs will vary based on usage.
        </p>
      </div>
    </div>
  );
};
