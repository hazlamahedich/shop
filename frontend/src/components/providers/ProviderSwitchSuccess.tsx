/** Provider Switch Success Component.
 *
 * Story 3.4: LLM Provider Switching
 *
 * Displays success notification after provider switch.
 * Shows new provider name, activation time, and auto-dismisses.
 * WCAG AA compliant with screen reader announcement.
 */

import React, { useEffect, useState } from 'react';
import { CheckCircle, X } from 'lucide-react';
import { useLLMProviderStore } from '../../stores/llmProviderStore';

export const ProviderSwitchSuccess: React.FC = () => {
  const { currentProvider, switchError, previousProviderId } = useLLMProviderStore();
  const [showSuccess, setShowSuccess] = useState(false);
  const [lastSwitchedProvider, setLastSwitchedProvider] = useState<string | null>(null);

  // Show success notification when provider changes
  useEffect(() => {
    if (currentProvider && previousProviderId && lastSwitchedProvider !== currentProvider.id) {
      // Provider was switched (previousProviderId indicates a switch occurred)
      setShowSuccess(true);
      setLastSwitchedProvider(currentProvider.id);
      // Auto-dismiss after 5 seconds
      const timer = setTimeout(() => {
        setShowSuccess(false);
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [currentProvider, previousProviderId, lastSwitchedProvider]);

  // Hide notification on error
  useEffect(() => {
    if (switchError) {
      setShowSuccess(false);
    }
  }, [switchError]);

  if (!showSuccess || !currentProvider) {
    return null;
  }

  const handleDismiss = () => {
    setShowSuccess(false);
  };

  return (
    <div
      className="fixed bottom-4 right-4 z-50"
      role="alert"
      aria-live="polite"
      aria-atomic="true"
    >
      <div className="bg-green-50 border border-green-200 rounded-lg shadow-lg p-4 min-w-[320px]">
        {/* Header with dismiss button */}
        <div className="flex items-start justify-between mb-2">
          <div className="flex items-center gap-2">
            <CheckCircle
              size={20}
              className="text-green-600"
              aria-hidden="true"
            />
            <h3 className="font-semibold text-green-900">Provider Switched Successfully</h3>
          </div>
          <button
            onClick={handleDismiss}
            className="text-green-600 hover:text-green-800 focus:outline-none focus:ring-2 focus:ring-green-500 rounded p-0.5"
            aria-label="Dismiss notification"
          >
            <X size={16} />
          </button>
        </div>

        {/* Success message details */}
        <div className="text-sm text-green-800">
          <p>
            Your LLM provider has been switched to <strong>{currentProvider.name}</strong>.
          </p>
          <p className="text-xs text-green-600 mt-1">
            Activated: {new Date().toLocaleString()}
          </p>
        </div>

        {/* Optional action link */}
        <div className="mt-3 pt-2 border-t border-green-200">
          <a
            href="/settings"
            className="text-sm text-green-700 hover:text-green-900 underline font-medium"
          >
            View Settings
          </a>
        </div>
      </div>
    </div>
  );
};
