import type { WidgetTheme } from '../types/widget';

export interface TypingIndicatorProps {
  isVisible: boolean;
  botName: string;
  theme: WidgetTheme;
}

export function TypingIndicator({ isVisible, botName, theme }: TypingIndicatorProps) {
  if (!isVisible) return null;

  return (
    <>
      <style>{`
        @keyframes shopbot-skeleton-shimmer {
          0% { background-position: -200% 0; }
          100% { background-position: 200% 0; }
        }
        @keyframes shopbot-skeleton-pulse {
          0%, 100% { opacity: 0.5; }
          50% { opacity: 1; }
        }
        .shopbot-skeleton-bar {
          background: linear-gradient(90deg, #9ca3af 0%, #d1d5db 50%, #9ca3af 100%);
          background-size: 200% 100%;
          animation: shopbot-skeleton-shimmer 1.5s ease-in-out infinite, shopbot-skeleton-pulse 1.5s ease-in-out infinite;
        }
      `}</style>
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
            backgroundColor: theme.botBubbleColor,
            display: 'flex',
            flexDirection: 'column',
            gap: 6,
            minWidth: 80,
          }}
        >
          <span style={{ fontSize: 11, color: theme.textColor, marginBottom: 2, opacity: 0.8 }}>
            {botName}
          </span>
          <div className="shopbot-skeleton-bar" style={{ width: '100%', height: 10, borderRadius: 4 }} />
          <div className="shopbot-skeleton-bar" style={{ width: '75%', height: 10, borderRadius: 4, animationDelay: '0.2s' }} />
          <div className="shopbot-skeleton-bar" style={{ width: '50%', height: 10, borderRadius: 4, animationDelay: '0.4s' }} />
        </div>
      </div>
    </>
  );
}
