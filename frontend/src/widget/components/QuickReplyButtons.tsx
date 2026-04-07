import * as React from 'react';
import type { QuickReply, WidgetTheme, ThemeMode } from '../types/widget';
import { useReducedMotion } from '../hooks/useReducedMotion';
import { useRipple } from '../hooks/useRipple';
import { trackQuickReplyClick } from '../utils/analytics';

export interface QuickReplyButtonsProps {
  quickReplies: QuickReply[];
  onReply: (reply: QuickReply) => void;
  theme: WidgetTheme;
  themeMode?: ThemeMode;
  dismissOnSelect?: boolean;
  disabled?: boolean;
}

interface QuickReplyButtonProps {
  reply: QuickReply;
  index: number;
  onClick: (reply: QuickReply, index: number) => void;
  onKeyDown: (e: React.KeyboardEvent, reply: QuickReply, index: number) => void;
  theme: WidgetTheme;
  isDark: boolean;
  disabled: boolean;
  isSelected: boolean;
  reducedMotion: boolean;
}

function QuickReplyButton({
  reply,
  index,
  onClick,
  onKeyDown,
  theme,
  isDark,
  disabled,
  isSelected,
  reducedMotion,
}: QuickReplyButtonProps) {
  const { ripples, createRipple } = useRipple();

  const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    if (disabled) return;
    createRipple(e);
    onClick(reply, index);
  };

  const textColor = isDark ? '#c7d2fe' : theme.primaryColor;
  const bgColor = isDark ? 'rgba(199, 210, 254, 0.1)' : `${theme.primaryColor}1a`;
  const borderColor = isDark ? 'rgba(199, 210, 254, 0.2)' : `${theme.primaryColor}33`;
  const hoverBg = isDark ? 'rgba(199, 210, 254, 0.15)' : `${theme.primaryColor}26`;
  const hoverBorder = isDark ? 'rgba(199, 210, 254, 0.35)' : `${theme.primaryColor}66`;

  return (
    <button
      key={reply.id}
      data-testid={`quick-reply-button-${reply.id}`}
      type="button"
      role="button"
      aria-label={reply.text}
      disabled={disabled || isSelected}
      onClick={handleClick}
      onKeyDown={(e) => onKeyDown(e, reply, index)}
      className={`quick-reply-button${reducedMotion ? ' quick-reply-button--reduced-motion' : ''}`}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '6px',
        minHeight: '40px',
        padding: '8px 14px',
        border: `1px solid ${borderColor}`,
        borderRadius: '16px',
        backgroundColor: bgColor,
        color: textColor,
        fontFamily: theme.fontFamily,
        fontSize: '13px',
        fontWeight: 500,
        cursor: disabled || isSelected ? 'not-allowed' : 'pointer',
        opacity: disabled || isSelected ? 0.5 : 1,
        transition: reducedMotion ? 'none' : 'all 150ms ease',
        whiteSpace: 'nowrap',
        position: 'relative',
        overflow: 'hidden',
        boxShadow: isDark ? '0 1px 2px rgba(0, 0, 0, 0.2)' : '0 1px 2px rgba(0, 0, 0, 0.05)',
      }}
      onMouseEnter={(e) => {
        if (!disabled && !isSelected) {
          e.currentTarget.style.backgroundColor = hoverBg;
          e.currentTarget.style.borderColor = hoverBorder;
          e.currentTarget.style.transform = 'translateY(-1px)';
        }
      }}
      onMouseLeave={(e) => {
        if (!disabled && !isSelected) {
          e.currentTarget.style.backgroundColor = bgColor;
          e.currentTarget.style.borderColor = borderColor;
          e.currentTarget.style.transform = 'translateY(0)';
        }
      }}
    >
      {reply.icon && (
        <span style={{ fontSize: '16px' }} aria-hidden="true">
          {reply.icon}
        </span>
      )}
      <span>{reply.text}</span>
      {/* Ripple effects */}
      {ripples.map((ripple) => (
        <span
          key={ripple.id}
          data-testid="ripple-effect"
          style={{
            position: 'absolute',
            left: ripple.x,
            top: ripple.y,
            width: 10,
            height: 10,
            borderRadius: '50%',
            backgroundColor: 'rgba(255, 255, 255, 0.3)',
            transform: 'translate(-50%, -50%)',
            pointerEvents: 'none',
            animationName: reducedMotion ? 'none' : 'ripple',
            animationDuration: reducedMotion ? '0ms' : '600ms',
            animationTimingFunction: 'ease-out',
            animationFillMode: 'forwards',
          }}
        />
      ))}
    </button>
  );
}

export function QuickReplyButtons({
  quickReplies,
  onReply,
  theme,
  themeMode,
  dismissOnSelect = true,
  disabled = false,
}: QuickReplyButtonsProps) {
  const [selectedIndex, setSelectedIndex] = React.useState<number | null>(null);
  const reducedMotion = useReducedMotion();
  const isDark = themeMode === 'dark';

  const handleClick = (reply: QuickReply, index: number) => {
    if (disabled) return;
    setSelectedIndex(index);
    trackQuickReplyClick(reply.text);
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
        <QuickReplyButton
          key={reply.id}
          reply={reply}
          index={index}
          onClick={handleClick}
          onKeyDown={handleKeyDown}
          theme={theme}
          isDark={isDark}
          disabled={disabled}
          isSelected={dismissOnSelect && selectedIndex !== null}
          reducedMotion={reducedMotion}
        />
      ))}
    </div>
  );
}
