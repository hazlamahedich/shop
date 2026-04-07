import * as React from 'react';
import type { WidgetTheme, ThemeMode } from '../types/widget';
import { useReducedMotion } from '../hooks/useReducedMotion';

export interface SuggestedRepliesProps {
  suggestions: string[];
  onSelect: (suggestion: string) => void;
  theme: WidgetTheme;
  themeMode?: ThemeMode;
  disabled?: boolean;
}

export function SuggestedReplies({
  suggestions,
  onSelect,
  theme,
  themeMode,
  disabled = false,
}: SuggestedRepliesProps) {
  const [selectedIndex, setSelectedIndex] = React.useState<number | null>(null);
  const reducedMotion = useReducedMotion();
  const isDark = themeMode === 'dark';

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
            minHeight: '40px',
            padding: '8px 16px',
            border: `1px solid ${isDark ? 'rgba(199, 210, 254, 0.2)' : `${theme.primaryColor}33`}`,
            borderRadius: '20px',
            backgroundColor: isDark ? 'rgba(199, 210, 254, 0.1)' : `${theme.primaryColor}1a`,
            color: isDark ? '#c7d2fe' : theme.primaryColor,
            fontFamily: theme.fontFamily,
            fontSize: '13px',
            fontWeight: 500,
            cursor: disabled || selectedIndex !== null ? 'not-allowed' : 'pointer',
            opacity: disabled || selectedIndex !== null ? 0.5 : 1,
            transition: reducedMotion ? 'none' : 'all 150ms ease',
            whiteSpace: 'nowrap',
            flexShrink: 0,
            boxShadow: isDark ? '0 1px 2px rgba(0, 0, 0, 0.2)' : '0 1px 2px rgba(0, 0, 0, 0.05)',
            position: 'relative',
          }}
          onMouseEnter={(e) => {
            if (!disabled && selectedIndex === null) {
              e.currentTarget.style.backgroundColor = isDark ? 'rgba(199, 210, 254, 0.15)' : `${theme.primaryColor}26`;
              e.currentTarget.style.borderColor = isDark ? 'rgba(199, 210, 254, 0.35)' : `${theme.primaryColor}66`;
              e.currentTarget.style.transform = 'translateY(-1px)';
            }
          }}
          onMouseLeave={(e) => {
            if (!disabled && selectedIndex === null) {
              e.currentTarget.style.backgroundColor = isDark ? 'rgba(199, 210, 254, 0.1)' : `${theme.primaryColor}1a`;
              e.currentTarget.style.borderColor = isDark ? 'rgba(199, 210, 254, 0.2)' : `${theme.primaryColor}33`;
              e.currentTarget.style.transform = 'translateY(0)';
            }
          }}
        >
          {suggestion}
        </button>
      ))}
    </div>
  );
}
