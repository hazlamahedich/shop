import type { WidgetTheme } from '../types/widget';

export interface TypingIndicatorProps {
  isVisible: boolean;
  botName: string;
  theme: WidgetTheme;
}

export function TypingIndicator({ isVisible, botName, theme }: TypingIndicatorProps) {
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
          padding: '8px 12px',
          borderRadius: 16,
          backgroundColor: theme.botBubbleColor,
          display: 'flex',
          alignItems: 'center',
          gap: 4,
        }}
      >
        <span style={{ fontSize: 11, color: theme.textColor, marginRight: 8, opacity: 0.8 }}>
          {botName}
        </span>
        <TypingDot />
        <TypingDot />
        <TypingDot />
      </div>
    </div>
  );
}

function TypingDot() {
  return <span className="typing-dot" />;
}
