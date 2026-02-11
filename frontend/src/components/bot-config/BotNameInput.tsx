/**
 * BotNameInput Component
 *
 * Story 1.12: Bot Naming
 *
 * Displays a text input for entering and editing the bot name with:
 * - Bot Name input (max 50 characters)
 * - Character count display
 * - Validation and help text
 * - Live preview of bot name in context
 *
 * WCAG 2.1 AA accessible.
 */

import * as React from 'react';
import { Bot, Sparkles } from 'lucide-react';
import { useBotConfigStore } from '../../stores/botConfigStore';

export interface BotNameInputProps {
  /** Optional CSS class name */
  className?: string;
  /** Whether the input is disabled (during save operations) */
  disabled?: boolean;
}

/**
 * BotNameInput Component
 *
 * A form component for managing the bot name with:
 * - Text input for bot name (max 50 chars)
 * - Character count display
 * - Live preview showing how the bot name appears
 * - Validation and error display
 */
export const BotNameInput = React.forwardRef<HTMLInputElement, BotNameInputProps>(
  ({ className = '', disabled = false }, ref) => {
    const { botName, setBotName, error, personality } = useBotConfigStore();

    // Handle bot name change
    const handleBotNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      const value = e.target.value.slice(0, 50); // Enforce max length
      setBotName(value);
    };

    // Character count color based on remaining characters
    const getCharacterCountColor = () => {
      const length = botName?.length || 0;
      const remaining = 50 - length;
      if (remaining < 10) return 'text-red-600';
      if (remaining < 20) return 'text-amber-600';
      return 'text-gray-500';
    };

    // Generate preview message based on personality and bot name
    const getPreviewMessage = () => {
      const name = botName?.trim() || 'your shopping assistant';
      const business = 'the store';

      switch (personality) {
        case 'professional':
          return `Good day. I'm ${name}, here to assist you with inquiries about ${business}.`;
        case 'enthusiastic':
          return `Hey there!!! I'm ${name}, super excited to help you with ${business}!!!`;
        case 'friendly':
        default:
          return `Hi! I'm ${name}, here to help you with questions about ${business}.`;
      }
    };

    return (
      <div className={`space-y-6 ${className}`}>
        {/* Error Display */}
        {error && (
          <div
            role="alert"
            className="p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3"
          >
            <svg
              className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                clipRule="evenodd"
              />
            </svg>
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        {/* Bot Name Field */}
        <div className="space-y-2">
          <label
            htmlFor="bot-name"
            className="flex items-center gap-2 text-sm font-medium text-gray-700"
          >
            <Bot size={16} className="text-gray-500" />
            Bot Name
          </label>
          <input
            ref={ref}
            id="bot-name"
            type="text"
            value={botName || ''}
            onChange={handleBotNameChange}
            disabled={disabled}
            maxLength={50}
            placeholder="e.g., GearBot, ShopAssistant, Helper"
            className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-colors disabled:bg-gray-100 disabled:cursor-not-allowed"
            aria-describedby="bot-name-description bot-name-count"
          />
          <p id="bot-name-description" className="text-xs text-gray-500">
            Give your bot a name that customers will see in their conversations. Leave empty to
            use a generic greeting.
          </p>
          <p
            id="bot-name-count"
            className={`text-xs font-medium text-right ${getCharacterCountColor()}`}
          >
            {(botName?.length || 0)} / 50
          </p>
        </div>

        {/* Live Preview */}
        <div className="p-4 bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg">
          <div className="flex items-center gap-2 text-sm font-medium text-blue-900 mb-2">
            <Sparkles size={16} className="text-blue-600" />
            Preview: How customers see your bot
          </div>
          <div className="p-3 bg-white rounded-lg border border-blue-100">
            <p className="text-sm text-gray-700 italic">
              "{getPreviewMessage()}"
            </p>
          </div>
          <p className="text-xs text-blue-700 mt-2">
            The bot name appears in greetings and responses throughout the conversation.
          </p>
        </div>
      </div>
    );
  }
);

BotNameInput.displayName = 'BotNameInput';
