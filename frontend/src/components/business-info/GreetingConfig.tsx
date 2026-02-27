/**
 * Greeting Configuration Component
 *
 * Story 1.14: Smart Greeting Templates
 *
 * Provides:
 * - Display of current personality-based default greeting
 * - Custom greeting textarea with placeholder variable hints
 * - "Use custom greeting" checkbox/toggle
 * - Live preview of how greeting will appear to customers
 * - "Reset to Default" button
 * - Help text for placeholder variables
 * - Suggestion panel with personality-appropriate greeting
 * - Tone mismatch warning for Professional personality
 *
 * WCAG 2.1 AA accessible.
 */

import React from 'react';
import { MessageSquare, Info, RotateCcw, AlertTriangle, Loader2 } from 'lucide-react';

/**
 * Greeting configuration state interface
 */
interface GreetingConfigProps {
  personality: string | null;
  greetingTemplate: string | null;
  useCustomGreeting: boolean;
  defaultTemplate: string | null;
  availableVariables: string[];
  onUpdate: (data: {
    greeting_template?: string;
    use_custom_greeting?: boolean;
  }) => void;
  onReset: () => void;
  disabled?: boolean;
  botName?: string | null;
  businessName?: string | null;
  businessHours?: string | null;
  showSuggestion?: boolean;
  suggestedGreeting?: string;
  suggestionLoading?: boolean;
  onApplySuggestion?: () => void;
  toneMismatchWarning?: string | null;
  onDismissWarning?: () => void;
  onSaveAnyway?: () => void;
}

/**
 * Variable badges for available placeholders
 */
const VariableBadges: React.FC<{ variables: string[] }> = ({ variables }) => {
  if (variables.length === 0) return null;

  return (
    <span className="flex flex-wrap gap-2 mt-2">
      {variables.map((v) => (
        <span
          key={v}
          className="inline-flex items-center px-2 py-1 bg-blue-50 text-blue-700 text-xs font-mono rounded-md"
          dangerouslySetInnerHTML={{ __html: '&quot;' + v + '&quot;' }}
        />
      ))}
    </span>
  );
};

/**
 * GreetingPreview Component
 *
 * Shows live preview of how the greeting will appear
 */
const GreetingPreview: React.FC<{ message: string }> = ({ message }) => {
  return (
    <div className="mt-4 p-4 bg-gray-50 border border-gray-200 rounded-lg">
      <div className="flex items-center gap-2 mb-2">
        <MessageSquare size={16} className="text-gray-500" />
        <span className="text-sm font-medium text-gray-700">Preview</span>
      </div>
      <p className="text-gray-800 italic">&quot;{message || 'Your greeting will appear here...'}&quot;</p>
    </div>
  );
};

/**
 * GreetingConfig Component
 *
 * Main component for greeting configuration with live preview.
 */
export const GreetingConfig: React.FC<GreetingConfigProps> = ({
  personality,
  greetingTemplate,
  useCustomGreeting,
  defaultTemplate,
  availableVariables,
  onUpdate,
  onReset,
  disabled = false,
  botName,
  businessName,
  businessHours,
  showSuggestion = false,
  suggestedGreeting,
  suggestionLoading = false,
  onApplySuggestion,
  toneMismatchWarning,
  onDismissWarning,
  onSaveAnyway,
}) => {
  // Local state for custom greeting input
  const [customText, setCustomText] = React.useState(greetingTemplate || '');
  const [useCustom, setUseCustom] = React.useState(useCustomGreeting);

  // Get personality display name
  const getPersonalityName = (p: string | null): string => {
    switch (p) {
      case 'professional':
        return 'Professional';
      case 'enthusiastic':
        return 'Enthusiastic';
      case 'friendly':
      default:
        return 'Friendly';
    }
  };

  // Get personality color for display
  const getPersonalityColor = (p: string | null): string => {
    switch (p) {
      case 'professional':
        return 'text-indigo-700 bg-indigo-50';
      case 'enthusiastic':
        return 'text-amber-700 bg-amber-50';
      case 'friendly':
      default:
        return 'text-green-700 bg-green-50';
    }
  };

  // Build preview message with variable substitution (client-side)
  const buildPreviewMessage = (): string => {
    let message: string;

    if (useCustom && customText.trim().length > 0) {
      message = customText;
    } else if (defaultTemplate) {
      message = defaultTemplate;
    } else {
      message = "Hi! I'm your shopping assistant from the store.";
    }

    // Simple variable substitution for preview
    // Note: Real substitution happens on backend with actual merchant data
    return message
      .replace(/{bot_name}/g, botName || 'Your Bot')
      .replace(/{business_name}/g, businessName || 'Your Business')
      .replace(/{business_hours}/g, businessHours || '9 AM - 6 PM');
  };

  const previewMessage = buildPreviewMessage();

  // Handle custom text change
  const handleTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value;
    setCustomText(value);

    // Auto-enable custom greeting when user starts typing
    if (value.trim().length > 0 && !useCustom) {
      setUseCustom(true);
    }

    // Update parent
    onUpdate({
      greeting_template: value || undefined,
      use_custom_greeting: useCustom || value.trim().length > 0 ? true : false,
    });
  };

  // Handle toggle change
  const handleToggleChange = (checked: boolean) => {
    setUseCustom(checked);
    onUpdate({
      greeting_template: customText || undefined,
      use_custom_greeting: checked,
    });
  };

  // Handle reset to default
  const handleReset = () => {
    setCustomText('');
    setUseCustom(false);
    onReset();
  };

  const personalityColor = getPersonalityColor(personality);
  const personalityName = getPersonalityName(personality);

  return (
    <div className="space-y-6">
      {/* Personality Info */}
      {personality && (
        <div className="flex items-center justify-between p-4 bg-white rounded-lg border border-gray-200">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-1">
              Default Greeting Template
            </h3>
            <p className="text-sm text-gray-600">
              Based on your <span className={`font-medium px-2 py-0.5 rounded ${personalityColor}`}>
                {personalityName}
              </span>{' '}personality
            </p>
          </div>
        </div>
      )}

      {/* Default Template Display (read-only) */}
      {defaultTemplate && (
        <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-sm font-medium text-gray-700">Default Template:</span>
            <span className={`inline-flex items-center px-2 py-1 text-xs font-medium rounded-md ${personalityColor}`}>
              {personalityName}
            </span>
          </div>
          <p className="text-sm text-gray-600 font-mono bg-white p-3 rounded border border-gray-300">
            {defaultTemplate}
          </p>
        </div>
      )}

      {/* Custom Greeting Section */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">
            Customize Your Greeting
          </h3>
          <div className="flex items-center gap-3">
            {/* Use Custom Greeting Toggle */}
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={useCustom}
                onChange={(e) => handleToggleChange(e.target.checked)}
                disabled={disabled}
                className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
                aria-describedby="use-custom-greeting-desc"
              />
              <span className="text-sm font-medium text-gray-700">
                Use custom greeting
              </span>
            </label>

            {/* Reset Button */}
            <button
              type="button"
              onClick={handleReset}
              disabled={disabled}
              className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              aria-label="Reset to default greeting template"
            >
              <RotateCcw size={16} />
              Reset to Default
            </button>
          </div>
          <p id="use-custom-greeting-desc" className="text-sm text-gray-500">
            Enable to use your custom greeting instead of the personality default.
          </p>
        </div>

        {/* Custom Greeting Textarea */}
        <div className="mt-4">
          <label htmlFor="custom-greeting" className="block text-sm font-medium text-gray-700 mb-2">
            Custom Greeting Message
          </label>
          <textarea
            id="custom-greeting"
            value={customText}
            onChange={handleTextChange}
            disabled={disabled}
            rows={4}
            maxLength={500}
            placeholder={`Enter your custom greeting. Use variables like {bot_name}, {business_name}, or {business_hours}.`}
            className="w-full px-3 py-2 text-sm text-gray-900 placeholder:text-gray-400 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50 disabled:cursor-not-allowed resize-none"
            aria-describedby="greeting-help greeting-counter"
          />
          <div className="flex items-center justify-between mt-2">
            <p id="greeting-help" className="text-xs text-gray-500">
              <Info size={12} className="inline mr-1" />
              Available variables:{' '}
              <VariableBadges variables={availableVariables} />
            </p>
            <span id="greeting-counter" className="text-xs text-gray-500">
              {customText.length}/500
            </span>
          </div>
        </div>

        {/* Suggestion Panel - NOW BELOW CUSTOM GREETING */}
        {showSuggestion && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mt-4">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <p className="text-sm font-medium text-blue-800 mb-1">
                  💡 Suggested greeting for {personalityName} personality:
                </p>
                {suggestionLoading ? (
                  <div className="flex items-center gap-2 text-sm text-blue-600">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Transforming your greeting...</span>
                  </div>
                ) : suggestedGreeting ? (
                  <p className="text-sm text-blue-700 italic">
                    &quot;{suggestedGreeting}&quot;
                  </p>
                ) : (
                  <p className="text-sm text-blue-600 italic">
                    Enter a custom greeting above to see a personality-matched suggestion.
                  </p>
                )}
              </div>
              {onApplySuggestion && suggestedGreeting && !suggestionLoading && (
                <button
                  type="button"
                  onClick={onApplySuggestion}
                  disabled={disabled}
                  className="px-3 py-1.5 text-sm font-medium text-blue-700 bg-white border border-blue-300 rounded-md hover:bg-blue-50 flex-shrink-0 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Apply
                </button>
              )}
            </div>
          </div>
        )}

        {/* Tone Mismatch Warning */}
        {toneMismatchWarning && (
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm text-amber-800">{toneMismatchWarning}</p>
                <div className="flex gap-2 mt-3">
                  {onSaveAnyway && (
                    <button
                      type="button"
                      onClick={onSaveAnyway}
                      disabled={disabled}
                      className="px-3 py-1.5 text-sm font-medium text-amber-700 bg-white border border-amber-300 rounded-md hover:bg-amber-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                      Save Anyway
                    </button>
                  )}
                  {onDismissWarning && (
                    <button
                      type="button"
                      onClick={onDismissWarning}
                      disabled={disabled}
                      className="px-3 py-1.5 text-sm font-medium text-gray-600 hover:text-gray-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                      Dismiss
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Live Preview */}
      <GreetingPreview message={previewMessage} />

      {/* Help Section */}
      <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <h4 className="text-sm font-semibold text-blue-900 mb-2 flex items-center gap-2">
          <Info size={16} />
          About Greeting Variables
        </h4>
        <div className="space-y-2 text-sm text-blue-800">
          <p>
            <strong dangerouslySetInnerHTML={{ __html: '&quot;{bot_name}&quot;' }} />
            <span> — The name you&apos;ve given your bot (from Bot Configuration).</span>
          </p>
          <p>
            <strong dangerouslySetInnerHTML={{ __html: '&quot;{business_name}&quot;' }} />
            <span> — Your business name (from Business Info).</span>
          </p>
          <p>
            <strong dangerouslySetInnerHTML={{ __html: '&quot;{business_hours}&quot;' }} />
            <span> — Your business hours (from Business Info).</span>
          </p>
          <p className="text-blue-700 text-xs mt-2">
            These variables are automatically replaced with your actual information when the bot sends its greeting.
          </p>
        </div>
      </div>
    </div>
  );
};

export default GreetingConfig;
