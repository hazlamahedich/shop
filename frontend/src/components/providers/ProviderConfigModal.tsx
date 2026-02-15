/** Provider Configuration Modal Component.
 *
 * Story 3.4: LLM Provider Switching
 *
 * Modal for configuring provider-specific settings (API key for cloud providers,
 * server URL for Ollama). Includes validation before switching.
 *
 * Follows WCAG AA accessibility with focus trap and proper ARIA attributes.
 */

import React, { useEffect, useRef, useState } from 'react';
import { X, Loader2, RefreshCw } from 'lucide-react';
import { useLLMProviderStore } from '../../stores/llmProviderStore';
import { getProviderModels, refreshModelsCache, DiscoveredModel } from '../../services/llmProvider';

export const ProviderConfigModal: React.FC = () => {
  const {
    selectedProvider,
    isSwitching,
    switchError,
    switchProvider,
    closeConfigModal,
    validationInProgress,
  } = useLLMProviderStore();

  const [apiKey, setApiKey] = React.useState('');
  const [serverUrl, setServerUrl] = React.useState('http://localhost:11434');
  const [selectedModel, setSelectedModel] = useState<string>('');
  const [models, setModels] = useState<DiscoveredModel[]>([]);
  const [loadingModels, setLoadingModels] = useState(false);
  const [modelsError, setModelsError] = useState<string | null>(null);
  const modalRef = useRef<HTMLDivElement>(null);
  const cancelButtonRef = useRef<HTMLButtonElement>(null);

  const loadModels = async (providerId: string) => {
    setLoadingModels(true);
    setModelsError(null);
    try {
      const response = await getProviderModels(providerId);
      setModels(response.data.models);
      const downloadableModels = response.data.models.filter(m => !m.isLocal || m.isDownloaded);
      if (downloadableModels.length > 0) {
        setSelectedModel(downloadableModels[0].id);
      } else if (response.data.models.length > 0) {
        setSelectedModel(response.data.models[0].id);
      }
    } catch (err) {
      setModelsError('Failed to load models');
      console.error('Failed to load models:', err);
    } finally {
      setLoadingModels(false);
    }
  };

  const handleRefreshModels = async () => {
    if (!selectedProvider) return;
    setLoadingModels(true);
    try {
      await refreshModelsCache();
      await loadModels(selectedProvider.id);
    } catch (err) {
      setModelsError('Failed to refresh models');
    } finally {
      setLoadingModels(false);
    }
  };

  // Load models when provider changes
  useEffect(() => {
    if (selectedProvider) {
      loadModels(selectedProvider.id);
    }
  }, [selectedProvider?.id]);

  // Focus trap for accessibility
  useEffect(() => {
    if (selectedProvider && modalRef.current) {
      const focusableElements = modalRef.current.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );
      const firstElement = focusableElements[0] as HTMLElement;
      if (firstElement) {
        firstElement.focus();
      }
    }
  }, [selectedProvider]);

  // Close on escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && selectedProvider) {
        closeConfigModal();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [selectedProvider, closeConfigModal]);

  if (!selectedProvider) return null;

  const isCloudProvider = ['openai', 'anthropic', 'gemini', 'glm'].includes(
    selectedProvider.id
  );
  const isOllama = selectedProvider.id === 'ollama';

  const handleSwitch = async () => {
    try {
      await switchProvider({
        providerId: selectedProvider.id,
        apiKey: isCloudProvider ? apiKey : undefined,
        serverUrl: isOllama ? serverUrl : undefined,
        model: selectedModel || undefined,
      });
      // Reset form on success
      setApiKey('');
      setServerUrl('');
      setSelectedModel('');
    } catch (error) {
      // Error is handled by store
    }
  };

  const handleCancel = () => {
    setApiKey('');
    setServerUrl('');
    setSelectedModel('');
    closeConfigModal();
  };

  const isDisabled = isSwitching || validationInProgress;
  const canSubmit =
    ((isCloudProvider && apiKey.length > 0) ||
    (isOllama && serverUrl.length > 0)) &&
    selectedModel.length > 0;

  // Group models for display
  const downloadedModels = models.filter(m => m.isDownloaded);
  const libraryModels = models.filter(m => m.isLocal && !m.isDownloaded);
  const cloudModels = models.filter(m => !m.isLocal);

  return (
    <div
      data-testid="provider-config-modal"
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
      onClick={(e) => {
        if (e.target === e.currentTarget) handleCancel();
      }}
    >
      <div
        ref={modalRef}
        className="bg-white rounded-lg p-6 w-full max-w-md shadow-xl"
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <h2 id="modal-title" className="text-lg font-semibold">
            Configure {selectedProvider.name}
          </h2>
          <button
            ref={cancelButtonRef}
            onClick={handleCancel}
            className="text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded"
            aria-label="Close modal"
            disabled={isDisabled}
          >
            <X size={20} />
          </button>
        </div>

        {/* Provider Info */}
        <div className="mb-4 p-3 bg-gray-50 rounded-lg">
          <p className="text-sm text-gray-600">{selectedProvider.description}</p>
          <p className="text-sm font-medium mt-2">
            Pricing: ${selectedProvider.pricing.inputCost.toFixed(2)} / ${selectedProvider.pricing.outputCost.toFixed(2)} per 1M tokens
          </p>
          {/* Cost Estimate */}
          <div className="mt-3 p-2 bg-blue-50 rounded border border-blue-200">
            <p className="text-xs text-blue-800 font-medium">Estimated Monthly Cost</p>
            <p className="text-sm text-blue-900 font-bold">
              ${selectedProvider.estimatedMonthlyCost?.toFixed(2) || '0.00'}
            </p>
            <p className="text-xs text-blue-600 mt-1">
              Based on typical usage (100K input + 50K output tokens/month)
            </p>
          </div>
        </div>

        {/* Form */}
        <div className="space-y-4">
          {isCloudProvider && (
            <div>
              <label htmlFor="api-key" className="block text-sm font-medium mb-1">
                API Key
              </label>
              <input
                id="api-key"
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="Enter your API key"
                className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                disabled={isDisabled}
                autoComplete="off"
              />
              <p className="text-xs text-gray-500 mt-1">
                Your API key is encrypted and stored securely
              </p>
            </div>
          )}

          {isOllama && (
            <div>
              <label htmlFor="server-url" className="block text-sm font-medium mb-1">
                Ollama Server URL
              </label>
              <input
                id="server-url"
                type="url"
                value={serverUrl}
                onChange={(e) => setServerUrl(e.target.value)}
                placeholder="http://localhost:11434"
                className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                disabled={isDisabled}
              />
              <p className="text-xs text-gray-500 mt-1">
                URL of your Ollama server (must be accessible from this server)
              </p>
            </div>
          )}

          {/* Model Selection */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <label htmlFor="model" className="block text-sm font-medium">
                Model
              </label>
              <button
                type="button"
                onClick={handleRefreshModels}
                disabled={loadingModels || isDisabled}
                className="text-xs text-blue-600 hover:text-blue-700 flex items-center gap-1 disabled:opacity-50"
              >
                <RefreshCw size={12} className={loadingModels ? 'animate-spin' : ''} />
                Refresh
              </button>
            </div>
            {loadingModels ? (
              <div className="flex items-center gap-2 text-sm text-gray-500 py-2">
                <Loader2 size={14} className="animate-spin" />
                Loading models...
              </div>
            ) : modelsError ? (
              <p className="text-sm text-red-600">{modelsError}</p>
            ) : (
              <select
                id="model"
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                disabled={isDisabled}
              >
                {models.length === 0 && (
                  <option value="">No models available</option>
                )}
                {downloadedModels.length > 0 && (
                  <optgroup label="Downloaded (Ready)">
                    {downloadedModels.map((m) => (
                      <option key={m.id} value={m.id}>
                        {m.name}
                      </option>
                    ))}
                  </optgroup>
                )}
                {libraryModels.length > 0 && (
                  <optgroup label="Available to Pull">
                    {libraryModels.map((m) => (
                      <option key={m.id} value={m.id}>
                        {m.name}
                      </option>
                    ))}
                  </optgroup>
                )}
                {cloudModels.length > 0 && (
                  <optgroup label="Cloud Models">
                    {cloudModels.map((m) => (
                      <option key={m.id} value={m.id}>
                        {m.name} {m.pricing.inputCostPerMillion > 0 && `($${m.pricing.inputCostPerMillion.toFixed(2)}/1M in)`}
                      </option>
                    ))}
                  </optgroup>
                )}
              </select>
            )}
            {selectedModel && (
              <p className="text-xs text-gray-500 mt-1">
                {models.find(m => m.id === selectedModel)?.description || ''}
              </p>
            )}
          </div>

          {/* Error Display */}
          {switchError && (
            <div
              className="p-3 bg-red-50 border border-red-200 rounded-lg"
              role="alert"
              aria-live="polite"
            >
              <p className="text-sm text-red-700">{switchError}</p>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex gap-2 mt-6">
          <button
            onClick={handleCancel}
            disabled={isDisabled}
            className="flex-1 px-4 py-2 border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            Cancel
          </button>
          <button
            onClick={handleSwitch}
            disabled={isDisabled || !canSubmit}
            className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center gap-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            {(isSwitching || validationInProgress) && (
              <Loader2 size={16} className="animate-spin" aria-hidden="true" />
            )}
            {isSwitching
              ? 'Switching...'
              : validationInProgress
              ? 'Validating...'
              : 'Switch Provider'}
          </button>
        </div>
      </div>
    </div>
  );
};
