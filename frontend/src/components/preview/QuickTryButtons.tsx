/** QuickTryButtons component.
 *
 * Story 1.13: Bot Preview Mode
 *
 * Displays quick-try starter prompt buttons.
 * Allows merchants to quickly test common scenarios.
 */

import * as React from 'react';

export interface QuickTryButtonsProps {
  /** Array of starter prompt strings */
  starterPrompts: string[];
  /** Callback when a prompt is clicked */
  onPromptClick: (prompt: string) => void;
  /** Optional className for styling */
  className?: string;
  /** Whether buttons are disabled */
  disabled?: boolean;
}

export function QuickTryButtons({
  starterPrompts,
  onPromptClick,
  className = '',
  disabled = false,
}: QuickTryButtonsProps) {
  if (starterPrompts.length === 0) {
    return null;
  }

  return (
    <div className={`quick-try-buttons ${className}`} data-testid="quick-try-buttons">
      <p className="text-sm text-gray-600 mb-2">Quick try:</p>
      <div className="flex flex-wrap gap-2">
        {starterPrompts.map((prompt, index) => (
          <button
            key={index}
            type="button"
            onClick={() => onPromptClick(prompt)}
            disabled={disabled}
            className="quick-try-button px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-full transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label={`Try prompt: ${prompt}`}
            data-testid={`quick-try-button-${index}`}
            data-prompt={prompt}
          >
            {prompt}
          </button>
        ))}
      </div>
    </div>
  );
}
