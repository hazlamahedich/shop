/**
 * GreetingEditor Component
 *
 * Story 1.10: Bot Personality Configuration
 *
 * Textarea component for editing custom greeting messages with:
 * - Character count display (max 500)
 * - Reset to default button
 * - Live greeting preview
 * - Validation feedback
 */

import * as React from 'react';
import { RotateCcw } from 'lucide-react';

export interface GreetingEditorProps {
  /** Current greeting value */
  value: string;
  /** Callback when greeting changes */
  onChange: (value: string) => void;
  /** Default greeting for the current personality */
  defaultGreeting: string;
  /** Callback to reset to default greeting */
  onReset: () => void;
  /** Maximum character limit */
  maxLength?: number;
  /** Optional CSS class name */
  className?: string;
  /** Whether to show the character count */
  showCharacterCount?: boolean;
  /** Disabled state */
  disabled?: boolean;
}

const DEFAULT_MAX_LENGTH = 500;

/**
 * GreetingEditor Component
 *
 * A textarea component for editing custom greeting messages with:
 * - Live character count with visual warning when approaching limit
 * - Reset to default button
 * - Optional preview of the greeting
 * - Accessibility support
 */
export const GreetingEditor = React.forwardRef<HTMLTextAreaElement, GreetingEditorProps>(
  (
    {
      value,
      onChange,
      defaultGreeting,
      onReset,
      maxLength = DEFAULT_MAX_LENGTH,
      className = '',
      showCharacterCount = true,
      disabled = false,
    },
    ref
  ) => {
    const [localValue, setLocalValue] = React.useState(value || '');
    const characterCount = localValue.length;
    const isNearLimit = characterCount > maxLength * 0.9;
    const isAtLimit = characterCount >= maxLength;
    const hasCustomGreeting = localValue.trim().length > 0;

    // Sync with prop value
    React.useEffect(() => {
      setLocalValue(value || '');
    }, [value]);

    const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      const newValue = e.target.value;
      if (newValue.length <= maxLength) {
        setLocalValue(newValue);
        onChange(newValue);
      }
    };

    const handleReset = () => {
      setLocalValue('');
      onChange('');
      onReset();
    };

    return (
      <div className={`space-y-3 ${className}`}>
        {/* Header with label and reset button */}
        <div className="flex items-center justify-between relative">
          <label
            htmlFor="greeting-input"
            className="block text-sm font-medium text-gray-700"
          >
            Custom Greeting
            <span className="text-gray-400 font-normal ml-1">(optional)</span>
          </label>
          {hasCustomGreeting && (
            <button
              type="button"
              onClick={handleReset}
              disabled={disabled}
              className="inline-flex items-center gap-1.5 text-sm text-gray-600 hover:text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed transition-colors relative z-10"
              style={{ zIndex: 10 }}
              aria-label="Reset to default greeting"
            >
              <RotateCcw size={14} />
              Reset to Default
            </button>
          )}
        </div>

        {/* Textarea input */}
        <div className="relative">
          <textarea
            ref={ref}
            id="greeting-input"
            value={localValue}
            onChange={handleChange}
            disabled={disabled}
            maxLength={maxLength}
            placeholder={`Enter a custom greeting or use the default: "${defaultGreeting}"`}
            rows={3}
            className={`
              w-full px-4 py-3 rounded-lg border resize-none
              focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary
              disabled:bg-gray-50 disabled:text-gray-500 disabled:cursor-not-allowed
              transition-colors
              ${isAtLimit
                ? 'border-red-300 bg-red-50/30'
                : isNearLimit
                  ? 'border-amber-300 bg-amber-50/30'
                  : 'border-gray-300 bg-white'
              }
            `}
            aria-describedby="greeting-description greeting-character-count"
          />
        </div>

        {/* Helper text and character count */}
        <div className="flex items-center justify-between">
          <p
            id="greeting-description"
            className="text-xs text-gray-500"
          >
            Leave empty to use the personality's default greeting
          </p>
          {showCharacterCount && (
            <div
              id="greeting-character-count"
              className={`
                text-sm font-medium
                ${isAtLimit
                  ? 'text-red-600'
                  : isNearLimit
                    ? 'text-amber-600'
                    : 'text-gray-500'
                }
              `}
              aria-live="polite"
            >
              {characterCount} / {maxLength}
              {isAtLimit && ' (limit reached)'}
            </div>
          )}
        </div>

        {/* Greeting preview */}
        {localValue && (
          <div className="p-3 bg-gray-50 rounded-lg border border-gray-200">
            <p className="text-xs text-gray-500 mb-1">Preview:</p>
            <p className="text-sm text-gray-800">{localValue || <em className="text-gray-400">No greeting set</em>}</p>
          </div>
        )}
      </div>
    );
  }
);

GreetingEditor.displayName = 'GreetingEditor';
