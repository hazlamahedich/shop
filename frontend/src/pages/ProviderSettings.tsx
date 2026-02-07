/** LLM Provider Settings Page.
 *
 * Story 3.4: LLM Provider Switching
 *
 * Main page for viewing and switching LLM providers.
 * Displays current provider, available providers, and configuration modal.
 */

import React, { useEffect } from 'react';
import { useLLMProviderStore } from '../stores/llmProviderStore';
import { ProviderCard } from '../components/providers/ProviderCard';
import { ProviderConfigModal } from '../components/providers/ProviderConfigModal';
import { ProviderComparison } from '../components/providers/ProviderComparison';
import { ProviderSwitchSuccess } from '../components/providers/ProviderSwitchSuccess';

export const ProviderSettings: React.FC = () => {
  const {
    currentProvider,
    availableProviders,
    isLoading,
    switchError,
    loadProviders,
    selectedProvider,
  } = useLLMProviderStore();

  useEffect(() => {
    loadProviders();
  }, [loadProviders]);

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  if (switchError) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div
          className="bg-red-50 border border-red-200 rounded-lg p-4"
          role="alert"
        >
          <p className="text-red-700">Error: {switchError}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-6">LLM Provider Settings</h1>

      {/* Current Provider Status */}
      <div className="mb-8">
        <h2 className="text-lg font-semibold mb-4">Current Provider</h2>
        {currentProvider && (
          <div className="flex items-center gap-3 p-4 bg-blue-50 rounded-lg border border-blue-200">
            <div
              className="w-3 h-3 bg-green-500 rounded-full"
              aria-label="Provider active"
            ></div>
            <span className="font-medium">{currentProvider.name}</span>
            <span className="text-sm text-gray-600">
              (Model: {currentProvider.model})
            </span>
            <span className="text-sm text-gray-600 ml-auto">
              Configured: {new Date(currentProvider.configuredAt).toLocaleDateString()}
            </span>
          </div>
        )}
      </div>

      {/* Provider Cards */}
      <div className="mb-8">
        <h2 className="text-lg font-semibold mb-4">Available Providers</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {availableProviders.map((provider) => (
            <ProviderCard
              key={provider.id}
              provider={provider}
              isActive={provider.id === currentProvider?.id}
            />
          ))}
        </div>
      </div>

      {/* Configuration Modal */}
      {selectedProvider && <ProviderConfigModal />}

      {/* Provider Comparison Table */}
      <ProviderComparison providers={availableProviders} />

      {/* Success Notification */}
      <ProviderSwitchSuccess />
    </div>
  );
};
