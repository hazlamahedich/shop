/**
 * BotConfig Page Component
 *
 * Story 1.12: Bot Naming
 * Story 1.15: Product Highlight Pins
 *
 * Main page for configuring bot settings including:
 * - Bot name input with live preview
 * - Display of current personality
 * - Product highlight pins management (Story 1.15)
 * - Save functionality for bot name changes
 * - Loading states and error handling
 * - Navigation breadcrumbs
 *
 * WCAG 2.1 AA accessible.
 */

import React from 'react';
import { useEffect } from 'react';
import { Info, CheckCircle2, AlertCircle, Palette } from 'lucide-react';
import { useToast } from '../context/ToastContext';
import { useBotConfigStore } from '../stores/botConfigStore';
import { useOnboardingPhaseStore } from '../stores/onboardingPhaseStore';
import { BotNameInput } from '../components/bot-config/BotNameInput';
import { ProductPinList } from '../components/business-info/ProductPinList';
import { TutorialPrompt } from '../components/onboarding/TutorialPrompt';

/**
 * Get personality display name and color
 */
function getPersonalityInfo(personality: string | null) {
  switch (personality) {
    case 'professional':
      return { name: 'Professional', color: 'text-indigo-700', bgColor: 'bg-indigo-50' };
    case 'enthusiastic':
      return { name: 'Enthusiastic', color: 'text-amber-700', bgColor: 'bg-amber-50' };
    case 'friendly':
    default:
      return { name: 'Friendly', color: 'text-green-700', bgColor: 'bg-green-50' };
  }
}

/**
 * BotConfig Component
 *
 * Main configuration page for bot naming and personality display.
 *
 * Features:
 * - Bot name input with live preview
 * - Display of current personality
 * - Save functionality for bot name
 * - Automatic loading of existing configuration
 * - Success and error notifications
 */
export const BotConfig: React.FC = () => {
  const {
    botName,
    personality,
    loadingState,
    error,
    isDirty,
    fetchBotConfig,
    updateBotName,
    clearError,
  } = useBotConfigStore();

  const markBotConfigComplete = useOnboardingPhaseStore((state) => state.markBotConfigComplete);

  const { toast } = useToast();

  // Load configuration on mount
  useEffect(() => {
    const loadConfig = async () => {
      try {
        await fetchBotConfig();
      } catch (err) {
        console.error('Failed to load configuration:', err);
        toast('Failed to load configuration', 'error');
      }
    };

    loadConfig();
  }, [fetchBotConfig, toast]);

  // Handle save bot name
  const handleSaveBotName = async () => {
    clearError();

    try {
      await updateBotName({
        bot_name: botName,
      });

      markBotConfigComplete('botName');
      toast('Bot name saved successfully!', 'success');
    } catch (err) {
      console.error('Failed to save bot name:', err);
      toast('Failed to save bot name', 'error');
    }
  };

  // Is any operation in progress?
  const isLoading = loadingState === 'loading';
  const hasConfig = botName || personality;
  const personalityInfo = getPersonalityInfo(personality);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Breadcrumb Navigation */}
      <nav className="bg-white border-b border-gray-200" aria-label="Breadcrumb">
        <div className="max-w-6xl mx-auto px-6 py-3">
          <ol className="flex items-center gap-2 text-sm">
            <li>
              <a href="/dashboard" className="text-gray-500 hover:text-gray-700 transition-colors">
                Dashboard
              </a>
            </li>
            <li className="text-gray-400">/</li>
            <li>
              <span className="font-medium text-gray-900">Bot Configuration</span>
            </li>
          </ol>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-6 py-8">
        {/* Page Header */}
        <div className="mb-8">
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                Bot Configuration
              </h1>
              <p className="text-lg text-gray-600 max-w-3xl">
                Customize how your bot introduces itself. Set a memorable bot name 
                and configure product highlights. For greeting customization, visit 
                the <a href="/personality" className="text-blue-600 hover:underline">Bot Personality</a> page.
              </p>
            </div>
            <div className="flex items-center gap-2 px-3 py-1.5 bg-blue-50 text-blue-700 rounded-lg text-sm">
              <Info size={16} />
              <span>Stories 1.12 & 1.15</span>
            </div>
          </div>
        </div>

        {/* Tutorial Prompt Banner - Post-configuration */}
      <TutorialPrompt />

      {/* Error Display (page-level) */}
        {error && (
          <div
            role="alert"
            className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3"
          >
            <AlertCircle size={20} className="text-red-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm font-medium text-red-800">Error</p>
              <p className="text-sm text-red-700 mt-1">{error}</p>
            </div>
            <button
              type="button"
              onClick={clearError}
              className="text-red-600 hover:text-red-800"
              aria-label="Dismiss error"
            >
              ×
            </button>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Bot Name Input */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-semibold text-gray-900">Bot Name</h2>
                {botName && (
                  <span className="inline-flex items-center gap-1 px-2 py-1 bg-green-50 text-green-700 text-xs font-medium rounded-md">
                    <CheckCircle2 size={12} />
                    Configured
                  </span>
                )}
              </div>

              <div className="space-y-6">
                <BotNameInput disabled={isLoading} />

                {/* Save Button */}
                <div className="pt-4 border-t border-gray-200">
                  <button
                    type="button"
                    onClick={handleSaveBotName}
                    disabled={isLoading || !isDirty}
                    className="w-full px-4 py-2.5 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    {isLoading ? (
                      <span className="flex items-center justify-center gap-2">
                        <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                          <circle
                            className="opacity-25"
                            cx="12"
                            cy="12"
                            r="10"
                            stroke="currentColor"
                            strokeWidth="4"
                            fill="none"
                          />
                          <path
                            className="opacity-75"
                            fill="currentColor"
                            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                          />
                        </svg>
                        Saving...
                      </span>
                    ) : (
                      'Save Bot Name'
                    )}
                  </button>
                  {!isDirty && hasConfig && (
                    <p className="text-xs text-center text-gray-500 mt-2">All changes saved</p>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Current Settings Display */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-6">Current Settings</h2>

              <div className="space-y-4">
                {/* Personality Display */}
                {personality && (
                  <div className="p-4 rounded-lg border border-gray-200">
                    <div className="flex items-center gap-2 mb-2">
                      <Palette size={16} className="text-gray-500" />
                      <span className="text-sm font-medium text-gray-700">Personality</span>
                    </div>
                    <span
                      className={`inline-block px-2 py-1 text-sm font-medium rounded-md ${personalityInfo.bgColor} ${personalityInfo.color}`}
                    >
                      {personalityInfo.name}
                    </span>
                  </div>
                )}

                {/* No Settings Message */}
                {!personality && (
                  <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                    <p className="text-sm text-gray-600">
                      No personality configured yet. Visit the Bot Personality page to set up your bot's tone and greeting.
                    </p>
                  </div>
                )}

                {/* Configure Personality Link */}
                <div className="pt-4 border-t border-gray-200">
                  <a
                    href="/personality"
                    className="text-sm text-blue-600 hover:text-blue-700 font-medium"
                  >
                    Configure personality & greeting →
                  </a>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Story 1.15: Product Highlight Pins Section */}
        <div className="max-w-6xl mx-auto px-6">
          <ProductPinList />
        </div>

        {/* Help Section */}
        <div className="mt-8 p-6 bg-blue-50 border border-blue-200 rounded-xl">
          <h3 className="text-lg font-semibold text-blue-900 mb-3">How Bot Configuration Works</h3>
          <div className="grid md:grid-cols-2 gap-6 text-sm text-blue-800">
            {/* Story 1.12: Bot Names */}
            <div>
              <h4 className="font-medium mb-2">Bot Names</h4>
              <p className="text-blue-700">
                A custom bot name creates a branded experience for your customers. Choose a name
                that reflects your business identity.
              </p>
              <p className="text-blue-700 text-xs mt-2">
                Example: &quot;Hi! I'm GearBot, here to help you...&quot;
              </p>
            </div>

            {/* Story 1.15: Product Highlight Pins */}
            <div>
              <h4 className="font-medium mb-2">Product Highlight Pins</h4>
              <p className="text-blue-700">
                Pin important products to boost their recommendations. Pinned products
                appear first with a 2x relevance boost.
              </p>
              <p className="text-blue-700 text-xs mt-2">
                <strong>Limit:</strong> Up to 10 products can be pinned.
                Pinned earlier in list = higher priority.
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default BotConfig;
