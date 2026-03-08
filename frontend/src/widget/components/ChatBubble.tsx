import * as React from 'react';
import type { WidgetTheme } from '../types/widget';

export interface ChatBubbleProps {
  isOpen: boolean;
  onClick: () => void;
  theme: WidgetTheme;
  onPrefetch?: () => void;
  unreadCount?: number;
}

export function ChatBubble({ isOpen, onClick, theme, onPrefetch, unreadCount = 0 }: ChatBubbleProps) {
  const positionStyle = theme.position === 'bottom-left'
    ? { left: 20 }
    : { right: 20 };

  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      onClick();
    }
  };

  const handleMouseEnter = () => {
    if (onPrefetch) {
      onPrefetch();
    }
  };

  const showBadge = !isOpen && unreadCount > 0;

  return (
    <button
      type="button"
      className={`shopbot-chat-bubble ${showBadge ? 'has-unread' : ''}`}
      data-testid="chat-bubble"
      onClick={onClick}
      onKeyDown={handleKeyDown}
      onMouseEnter={handleMouseEnter}
      aria-label={isOpen ? 'Close chat' : 'Open chat'}
      aria-expanded={isOpen}
      style={{
        position: 'fixed',
        bottom: 20,
        ...positionStyle,
        backgroundColor: theme.primaryColor,
        borderRadius: '50%',
        width: 60,
        height: 60,
        border: 'none',
        cursor: 'pointer',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
        transition: 'transform 0.2s ease, box-shadow 0.2s ease',
        zIndex: 2147483647,
      }}
    >
      {isOpen ? (
        <svg
          width="24"
          height="24"
          viewBox="0 0 24 24"
          fill="none"
          stroke="white"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <line x1="18" y1="6" x2="6" y2="18" />
          <line x1="6" y1="6" x2="18" y2="18" />
        </svg>
      ) : (
        <svg
          width="24"
          height="24"
          viewBox="0 0 24 24"
          fill="none"
          stroke="white"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
        </svg>
      )}
      {showBadge && (
        <span
          className="bubble-badge"
          style={{
            position: 'absolute',
            top: -5,
            right: -5,
            backgroundColor: '#ef4444',
            color: 'white',
            borderRadius: '50%',
            minWidth: 20,
            height: 20,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 11,
            fontWeight: 600,
            padding: '0 4px',
          }}
        >
          {unreadCount > 99 ? '99+' : unreadCount}
        </span>
      )}
    </button>
  );
}
