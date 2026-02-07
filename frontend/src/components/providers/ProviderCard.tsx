/** Provider Card Component.
 *
 * Story 3.4: LLM Provider Switching
 *
 * Displays a single LLM provider with pricing, features, and selection button.
 * Follows WCAG AA accessibility requirements.
 */

import React from 'react';
import { Check, Zap, DollarSign, Server } from 'lucide-react';
import { useLLMProviderStore } from '../../stores/llmProviderStore';
import type { Provider } from '../../stores/llmProviderStore';

interface ProviderCardProps {
  provider: Provider;
  isActive: boolean;
}

export const ProviderCard: React.FC<ProviderCardProps> = ({ provider, isActive }) => {
  const { selectProvider } = useLLMProviderStore();

  const handleSelect = () => {
    selectProvider(provider.id);
  };

  const getFeatureIcon = (feature: string): React.ReactNode => {
    switch (feature) {
      case 'local':
        return <Server size={14} aria-hidden="true" />;
      case 'free':
        return <DollarSign size={14} aria-hidden="true" />;
      case 'fast':
        return <Zap size={14} aria-hidden="true" />;
      default:
        return null;
    }
  };

  return (
    <div
      data-testid={`provider-card-${provider.id}`}
      className={`border rounded-lg p-4 transition-all ${
        isActive
          ? 'border-blue-500 bg-blue-50'
          : 'border-gray-200 hover:border-gray-300'
      }`}
      role="option"
      aria-selected={isActive}
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          handleSelect();
        }
      }}
    >
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="font-semibold text-lg">{provider.name}</h3>
          <p className="text-sm text-gray-600">{provider.description}</p>
        </div>
        {isActive && (
          <span className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full flex items-center gap-1">
            <Check size={12} aria-hidden="true" />
            <span>Active</span>
          </span>
        )}
      </div>

      {/* Pricing */}
      <div className="mb-3">
        <p className="text-sm font-medium">Pricing (per 1M tokens):</p>
        <p className="text-lg font-bold">
          ${provider.pricing.inputCost.toFixed(2)} / ${provider.pricing.outputCost.toFixed(2)}
        </p>
        <p className="text-xs text-gray-500">
          Input: ${provider.pricing.inputCost} | Output: ${provider.pricing.outputCost}
        </p>
      </div>

      {/* Features */}
      <div className="mb-4 flex flex-wrap gap-2" role="list" aria-label="Provider features">
        {provider.features.map((feature) => (
          <span
            key={feature}
            className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded-full flex items-center gap-1"
            role="listitem"
          >
            {getFeatureIcon(feature)}
            <span className="capitalize">{feature}</span>
          </span>
        ))}
      </div>

      {/* Estimated Monthly Cost */}
      {provider.estimatedMonthlyCost !== undefined && (
        <div className="mb-4">
          <p className="text-xs text-gray-500">
            Est. Monthly Cost: ${provider.estimatedMonthlyCost.toFixed(2)}
          </p>
        </div>
      )}

      {/* Select Button */}
      <button
        onClick={handleSelect}
        disabled={isActive}
        className={`w-full py-2 px-4 rounded-lg font-medium transition-colors ${
          isActive
            ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
            : 'bg-blue-600 text-white hover:bg-blue-700 focus:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2'
        }`}
        aria-label={`Select ${provider.name} provider`}
      >
        {isActive ? 'Current Provider' : 'Select Provider'}
      </button>
    </div>
  );
};
