import type { WidgetTheme, ThemeMode } from '../types/widget';

export interface StreamingIndicatorProps {
  isVisible: boolean;
  theme: WidgetTheme;
  themeMode?: ThemeMode;
}

export function StreamingIndicator({ isVisible, theme, themeMode }: StreamingIndicatorProps) {
  if (!isVisible) return null;

  const isDark = themeMode === 'dark';

  return (
    <div
      data-testid="streaming-indicator"
      role="status"
      aria-live="polite"
      aria-label="Streaming response"
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 4,
        padding: '4px 8px',
        marginLeft: 12,
        marginBottom: 4,
      }}
    >
      <div
        style={{
          width: 6,
          height: 6,
          borderRadius: '50%',
          backgroundColor: theme.primaryColor,
          animationName: 'streaming-pulse',
          animationDuration: '1s',
          animationTimingFunction: 'ease-in-out',
          animationIterationCount: 'infinite',
        }}
      />
      <span
        style={{
          fontSize: 11,
          color: isDark ? '#94a3b8' : theme.textColor,
          opacity: 0.7,
        }}
      >
        streaming...
      </span>
    </div>
  );
}

export interface StreamErrorIndicatorProps {
  error: string | null;
  themeMode?: ThemeMode;
}

export function StreamErrorIndicator({ error, themeMode }: StreamErrorIndicatorProps) {
  if (!error) return null;

  const isDark = themeMode === 'dark';

  return (
    <div
      data-testid="stream-error-indicator"
      role="alert"
      style={{
        padding: '8px 12px',
        margin: '4px 12px',
        borderRadius: 8,
        backgroundColor: isDark ? 'rgba(239, 68, 68, 0.15)' : '#fef2f2',
        border: isDark ? '1px solid rgba(239, 68, 68, 0.3)' : '1px solid #fecaca',
        color: isDark ? '#fca5a5' : '#991b1b',
        fontSize: 13,
      }}
    >
      Something went wrong with the streaming response. Please try again.
    </div>
  );
}
