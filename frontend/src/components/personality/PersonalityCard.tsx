/**
 * PersonalityCard Component
 *
 * Story 1.10: Bot Personality Configuration
 *
 * Displays a personality type option as a selectable card.
 * Shows personality name, description, and a preview of the greeting style.
 * Provides visual feedback for selection state.
 */

import * as React from 'react';
import { Smile, Briefcase, Zap } from 'lucide-react';
import type { PersonalityType } from '../../types/enums';
import {
  PersonalityDisplay,
  PersonalityDescriptions,
  PersonalityDefaultGreetings,
} from '../../types/enums';

export interface PersonalityCardProps {
  /** The personality type this card represents */
  personality: PersonalityType;
  /** Whether this personality is currently selected */
  isSelected: boolean;
  /** Callback when the card is clicked */
  onSelect: (personality: PersonalityType) => void;
  /** Optional CSS class name */
  className?: string;
}

/**
 * Map personality types to their icons
 */
const PERSONALITY_ICONS: Record<PersonalityType, React.ElementType> = {
  friendly: Smile,
  professional: Briefcase,
  enthusiastic: Zap,
};

/**
 * Map personality types to their accent colors
 */
const PERSONALITY_COLORS: Record<PersonalityType, { bg: string; text: string; border: string }> = {
  friendly: {
    bg: 'bg-amber-50',
    text: 'text-amber-700',
    border: 'border-amber-200',
  },
  professional: {
    bg: 'bg-slate-50',
    text: 'text-slate-700',
    border: 'border-slate-200',
  },
  enthusiastic: {
    bg: 'bg-purple-50',
    text: 'text-purple-700',
    border: 'border-purple-200',
  },
};

/**
 * PersonalityCard Component
 *
 * A selectable card displaying a personality option with:
 * - Icon and name
 * - Description of the tone and style
 * - Preview of the default greeting
 * - Visual selection state
 */
export const PersonalityCard = React.forwardRef<HTMLButtonElement, PersonalityCardProps>(
  ({ personality, isSelected, onSelect, className = '' }, ref) => {
    const Icon = PERSONALITY_ICONS[personality];
    const colors = PERSONALITY_COLORS[personality];
    const displayName = PersonalityDisplay[personality];
    const description = PersonalityDescriptions[personality];
    const defaultGreeting = PersonalityDefaultGreetings[personality];

    return (
      <button
        ref={ref}
        type="button"
        onClick={() => onSelect(personality)}
        className={`
          relative text-left p-5 rounded-xl border-2 transition-all duration-200
          ${isSelected
            ? `border-primary bg-primary/5 shadow-md ring-2 ring-primary/20`
            : `border-gray-200 bg-white hover:border-gray-300 hover:shadow-sm`
          }
          focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2
          disabled:opacity-50 disabled:cursor-not-allowed
          ${className}
        `}
        aria-pressed={isSelected}
        aria-describedby={`${personality}-description ${personality}-preview`}
      >
        {/* Header with icon and name */}
        <div className="flex items-center gap-3 mb-3">
          <div className={`p-2 rounded-lg ${colors.bg} ${colors.text}`}>
            <Icon size={20} strokeWidth={2} />
          </div>
          <h3 className="text-lg font-semibold text-gray-900">
            {displayName}
          </h3>
          {isSelected && (
            <span className="ml-auto">
              <svg
                className="w-5 h-5 text-primary"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                  clipRule="evenodd"
                />
              </svg>
            </span>
          )}
        </div>

        {/* Description */}
        <p
          id={`${personality}-description`}
          className="text-sm text-gray-600 mb-3"
        >
          {description}
        </p>

        {/* Greeting preview */}
        <div className={`p-3 rounded-lg ${colors.bg} ${colors.border} border`}>
          <p
            id={`${personality}-preview`}
            className="text-sm font-medium text-gray-800"
          >
            "{defaultGreeting}"
          </p>
        </div>

        {/* Screen reader announcement for selection */}
        {isSelected && (
          <span className="sr-only">
            {displayName} personality selected
          </span>
        )}
      </button>
    );
  }
);

PersonalityCard.displayName = 'PersonalityCard';
