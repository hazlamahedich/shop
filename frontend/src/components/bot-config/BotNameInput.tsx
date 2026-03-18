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
import { Bot, Sparkles, AlertCircle } from 'lucide-react';
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
            className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl flex items-start gap-4 animate-shake"
          >
            <AlertCircle size={20} className="text-red-400 flex-shrink-0 mt-0.5" />
            <p className="text-sm text-red-200 font-medium">{error}</p>
          </div>
        )}

        {/* Bot Name Field */}
        <div className="space-y-3">
          <label
            htmlFor="bot-name"
            className="flex items-center gap-2 text-sm font-semibold text-white/70 uppercase tracking-widest"
          >
            <Bot size={16} className="text-[var(--mantis-glow)]" />
            Bot Designation
          </label>
          <div className="relative group">
            <input
              ref={ref}
              id="bot-name"
              type="text"
              value={botName || ''}
              onChange={handleBotNameChange}
              disabled={disabled}
              maxLength={50}
              placeholder="e.g., GEAR_CORE, ASSISTANT_VX, MANTIS_UNIT"
              className="w-full px-5 py-4 bg-black/20 border border-white/10 rounded-xl focus:ring-2 focus:ring-[var(--mantis-glow)]/50 focus:border-[var(--mantis-glow)]/50 focus:bg-black/40 transition-all duration-300 disabled:opacity-20 disabled:cursor-not-allowed text-white placeholder:text-white/20"
              aria-describedby="bot-name-description bot-name-count"
            />
            <div className="absolute inset-0 rounded-xl bg-[var(--mantis-glow)]/5 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />
          </div>
          <div className="flex justify-between items-start pt-1 px-1">
            <p id="bot-name-description" className="text-xs text-white/40 leading-relaxed max-w-[70%]">
              Assign a unique designation for customer-facing interfaces. Defaults to &quot;Neural Assistant&quot; if null.
            </p>
            <p
              id="bot-name-count"
              className={`text-xs font-mono font-bold ${
                (botName?.length || 0) >= 45 ? 'text-red-400' : 
                (botName?.length || 0) >= 35 ? 'text-amber-400' : 
                'text-[var(--mantis-glow)]'
              }`}
            >
              {(botName?.length || 0)} <span className="text-white/20">/</span> 50
            </p>
          </div>
        </div>

        {/* Live Preview */}
        <div className="relative overflow-hidden p-6 bg-white/5 border border-white/10 rounded-2xl group">
          <div className="absolute top-0 right-0 p-8 bg-[var(--mantis-glow)]/5 blur-3xl rounded-full translate-x-1/2 -translate-y-1/2" />
          
          <div className="relative flex items-center gap-3 text-xs font-bold text-[var(--mantis-glow)] uppercase tracking-widest mb-4">
            <Sparkles size={14} />
            Output Simulation
          </div>
          
          <div className="relative p-5 bg-black/40 rounded-xl border border-white/5 backdrop-blur-sm shadow-xl">
            <p className="text-sm text-white/80 font-medium leading-relaxed italic">
              &quot;{getPreviewMessage()}&quot;
            </p>
          </div>
          
          <p className="relative text-[10px] text-white/30 mt-4 leading-tight uppercase font-bold tracking-tighter">
            * Identity module propagates to all customer-facing touchpoints
          </p>
        </div>
      </div>
    );
  }
);

BotNameInput.displayName = 'BotNameInput';
