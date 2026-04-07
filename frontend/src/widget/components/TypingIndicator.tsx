import * as React from 'react';
import type { WidgetTheme, ThemeMode } from '../types/widget';
import { useReducedMotion } from '../hooks/useReducedMotion';

export interface TypingIndicatorProps {
  isVisible: boolean;
  botName: string;
  theme: WidgetTheme;
  themeMode?: ThemeMode;
}

export function TypingIndicator({ isVisible, botName, theme, themeMode }: TypingIndicatorProps) {
  const reducedMotion = useReducedMotion();
  const isDark = themeMode === 'dark';

  if (!isVisible) return null;

  return (
    <div
      className="typing-indicator"
      role="status"
      aria-live="polite"
      aria-label={`${botName} is typing`}
      style={{
        display: 'flex',
        alignItems: 'center',
        padding: '8px 16px',
      }}
    >
      <div
        style={{
          padding: '10px 14px',
          borderRadius: 16,
          backgroundColor: isDark ? 'rgba(255, 255, 255, 0.08)' : theme.botBubbleColor,
          display: 'flex',
          flexDirection: 'column',
          gap: 8,
        }}
      >
        <span
          style={{
            fontSize: 11,
            color: isDark ? '#94a3b8' : theme.textColor,
            marginBottom: 2,
            opacity: 0.8,
          }}
        >
          {botName}
        </span>
        <div
          data-testid="typing-dots"
          style={{
            display: 'flex',
            gap: 4,
            alignItems: 'center',
            padding: '4px 0',
          }}
        >
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              data-testid="typing-dot"
              style={{
                width: 8,
                height: 8,
                borderRadius: '50%',
                backgroundColor: isDark ? 'rgba(255, 255, 255, 0.4)' : theme.primaryColor,
                animationName: reducedMotion ? 'none' : 'typing-dot-bounce',
                animationDuration: reducedMotion ? '0ms' : '1.4s',
                animationTimingFunction: 'ease-in-out',
                animationIterationCount: 'infinite',
                animationDelay: reducedMotion ? '0ms' : `${i * 150}ms`,
              }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
