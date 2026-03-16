import * as React from 'react';
import type { QuickReply, WidgetTheme } from '../types/widget';

export interface QuickReplyButtonsProps {
  quickReplies: QuickReply[];
  onReply: (reply: QuickReply) => void;
  theme: WidgetTheme;
  dismissOnSelect?: boolean;
  disabled?: boolean;
}

function useReducedMotion(): boolean {
  if (typeof window === 'undefined') return false;
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

export function QuickReplyButtons({
  quickReplies,
  onReply,
  theme,
  dismissOnSelect = true,
  disabled = false,
}: QuickReplyButtonsProps) {
  const [selectedIndex, setSelectedIndex] = React.useState<number | null>(null);
  const reducedMotion = useReducedMotion();

  const handleClick = (reply: QuickReply, index: number) => {
    if (disabled) return;
    setSelectedIndex(index);
    onReply(reply);
  };

  const handleKeyDown = (e: React.KeyboardEvent, reply: QuickReply, index: number) => {
    if (disabled) return;
    
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleClick(reply, index);
    }
  };

  if (!quickReplies || quickReplies.length === 0) {
    return null;
  }

  return (
    <div
      data-testid="quick-reply-buttons"
      role="group"
      aria-label="Quick reply options"
      className="quick-reply-buttons"
      style={{
        display: 'flex',
        flexWrap: 'wrap',
        gap: '8px',
        padding: '8px 16px',
        flexShrink: 0,
      }}
    >
      {quickReplies.map((reply, index) => (
        <button
          key={reply.id}
          data-testid={`quick-reply-button-${reply.id}`}
          type="button"
          role="button"
          aria-label={reply.text}
          disabled={disabled || (dismissOnSelect && selectedIndex !== null)}
          onClick={() => handleClick(reply, index)}
          onKeyDown={(e) => handleKeyDown(e, reply, index)}
          className={`quick-reply-button${reducedMotion ? ' quick-reply-button--reduced-motion' : ''}`}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '6px',
            minHeight: '44px',
            minWidth: '44px',
            padding: '10px 16px',
            border: `1px solid ${theme.primaryColor}`,
            borderRadius: '20px',
            backgroundColor: 'transparent',
            color: theme.primaryColor,
            fontFamily: theme.fontFamily,
            fontSize: '14px',
            fontWeight: 500,
            cursor: disabled || (dismissOnSelect && selectedIndex !== null) ? 'not-allowed' : 'pointer',
            opacity: disabled || (dismissOnSelect && selectedIndex !== null) ? 0.5 : 1,
            transition: reducedMotion ? 'none' : 'transform 100ms ease, background-color 150ms ease, opacity 150ms ease',
            whiteSpace: 'nowrap',
          }}
        >
          {reply.icon && (
            <span style={{ fontSize: '16px' }} aria-hidden="true">
              {reply.icon}
            </span>
          )}
          <span>{reply.text}</span>
        </button>
      ))}
    </div>
  );
}
