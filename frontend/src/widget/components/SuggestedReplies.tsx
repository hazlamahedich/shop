import * as React from 'react';
import type { WidgetTheme } from '../types/widget';
import { useReducedMotion } from '../hooks/useReducedMotion';

export interface SuggestedRepliesProps {
  suggestions: string[];
  onSelect: (suggestion: string) => void;
  theme: WidgetTheme;
  disabled?: boolean;
}

export function SuggestedReplies({
  suggestions,
  onSelect,
  theme,
  disabled = false,
}: SuggestedRepliesProps) {
  const [selectedIndex, setSelectedIndex] = React.useState<number | null>(null);
  const reducedMotion = useReducedMotion();

  const handleClick = (suggestion: string, index: number) => {
    if (disabled) return;
    setSelectedIndex(index);
    onSelect(suggestion);
  };

  const handleKeyDown = (e: React.KeyboardEvent, suggestion: string, index: number) => {
    if (disabled) return;

    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleClick(suggestion, index);
    }
  };

  if (!suggestions || suggestions.length === 0) {
    return null;
  }

  const limitedSuggestions = suggestions.slice(0, 4);

  return (
    <>
      <style>{`
        .suggested-reply-chip:focus {
          outline: 2px solid ${theme.primaryColor};
          outline-offset: 2px;
        }
        .suggested-reply-chip:focus-visible {
          outline: 2px solid ${theme.primaryColor};
          outline-offset: 2px;
        }
        .suggested-reply-chip:hover:not(:disabled) {
          transform: scale(1.02);
        }
        .suggested-reply-chip:active:not(:disabled) {
          transform: scale(0.95);
        }
      `}</style>
      <div
        data-testid="suggested-replies"
        role="group"
        aria-label="Suggested replies"
        className="suggested-replies"
        style={{
          display: 'flex',
          flexWrap: 'nowrap',
          gap: '8px',
          padding: '8px 12px',
          flexShrink: 0,
          overflowX: 'auto',
          WebkitOverflowScrolling: 'touch',
        }}
      >
        {limitedSuggestions.map((suggestion, index) => (
          <button
            key={suggestion}
            data-testid={`suggested-reply-${index}`}
            type="button"
            role="button"
            aria-label={suggestion}
            disabled={disabled || selectedIndex !== null}
            onClick={() => handleClick(suggestion, index)}
            onKeyDown={(e) => handleKeyDown(e, suggestion, index)}
            className={`suggested-reply-chip${reducedMotion ? ' suggested-reply-chip--reduced-motion' : ''}`}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              minHeight: '44px',
              minWidth: '44px',
              padding: '10px 16px',
              border: `1px solid ${theme.primaryColor}`,
              borderRadius: '22px',
              backgroundColor: 'transparent',
              color: theme.primaryColor,
              fontFamily: theme.fontFamily,
              fontSize: '14px',
              fontWeight: 500,
              cursor: disabled || selectedIndex !== null ? 'not-allowed' : 'pointer',
              opacity: disabled || selectedIndex !== null ? 0.5 : 1,
              transition: reducedMotion
                ? 'none'
                : 'transform 100ms ease, background-color 150ms ease, opacity 150ms ease',
              whiteSpace: 'nowrap',
              flexShrink: 0,
            }}
          >
            {suggestion}
          </button>
        ))}
      </div>
    </>
  );
}
