import type { WidgetTheme } from '../types/widget';

export interface StreamingIndicatorProps {
  isVisible: boolean;
  theme: WidgetTheme;
}

export function StreamingIndicator({ isVisible, theme }: StreamingIndicatorProps) {
  if (!isVisible) return null;

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
          color: theme.textColor,
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
}

export function StreamErrorIndicator({ error }: StreamErrorIndicatorProps) {
  if (!error) return null;

  return (
    <div
      data-testid="stream-error-indicator"
      role="alert"
      style={{
        padding: '8px 12px',
        margin: '4px 12px',
        borderRadius: 8,
        backgroundColor: '#fef2f2',
        border: '1px solid #fecaca',
        color: '#991b1b',
        fontSize: 13,
      }}
    >
      Something went wrong with the streaming response. Please try again.
    </div>
  );
}
