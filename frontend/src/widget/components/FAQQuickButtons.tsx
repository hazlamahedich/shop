import * as React from 'react';
import type { FAQQuickButton, WidgetTheme, ThemeMode } from '../types/widget';
import { useReducedMotion } from '../hooks/useReducedMotion';
import { useRipple } from '../hooks/useRipple';

export interface FAQQuickButtonsProps {
  buttons: FAQQuickButton[];
  onButtonClick: (button: FAQQuickButton) => void;
  theme: WidgetTheme;
  themeMode?: ThemeMode;
  disabled?: boolean;
}

interface FAQQuickButtonItemProps {
  button: FAQQuickButton;
  index: number;
  onClick: (button: FAQQuickButton, index: number) => void;
  theme: WidgetTheme;
  isDark: boolean;
  disabled: boolean;
  reducedMotion: boolean;
}

function FAQQuickButtonItem({
  button,
  index,
  onClick,
  theme,
  isDark,
  disabled,
  reducedMotion,
}: FAQQuickButtonItemProps) {
  const { ripples, createRipple } = useRipple();

  const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    if (disabled) return;
    createRipple(e);
    onClick(button, index);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLButtonElement>) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onClick(button, index);
    }
  };

  const textColor = isDark ? '#c7d2fe' : theme.primaryColor;
  const bgColor = isDark ? 'rgba(199, 210, 254, 0.1)' : `${theme.primaryColor}1a`;
  const borderColor = isDark ? 'rgba(199, 210, 254, 0.2)' : `${theme.primaryColor}33`;
  const hoverBg = isDark ? 'rgba(199, 210, 254, 0.15)' : `${theme.primaryColor}26`;
  const hoverBorder = isDark ? 'rgba(199, 210, 254, 0.35)' : `${theme.primaryColor}66`;

  return (
    <button
      data-testid={`faq-quick-button-${button.id}`}
      type="button"
      role="button"
      aria-label={button.question}
      tabIndex={0}
      disabled={disabled}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      className="faq-quick-button"
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
        cursor: disabled ? 'not-allowed' : 'pointer',
        opacity: disabled ? 0.5 : 1,
        transition: reducedMotion ? 'none' : 'all 150ms ease',
        whiteSpace: 'nowrap',
        position: 'relative',
        overflow: 'hidden',
        boxShadow: isDark ? '0 1px 2px rgba(0, 0, 0, 0.2)' : '0 1px 2px rgba(0, 0, 0, 0.05)',
      }}
      onMouseEnter={(e) => {
        if (!disabled) {
          e.currentTarget.style.backgroundColor = hoverBg;
          e.currentTarget.style.borderColor = hoverBorder;
          e.currentTarget.style.transform = 'translateY(-1px)';
        }
      }}
      onMouseLeave={(e) => {
        if (!disabled) {
          e.currentTarget.style.backgroundColor = bgColor;
          e.currentTarget.style.borderColor = borderColor;
          e.currentTarget.style.transform = 'translateY(0)';
        }
      }}
    >
      {button.icon && (
        <span className="faq-quick-button-icon" style={{ fontSize: '16px' }} aria-hidden="true">
          {button.icon}
        </span>
      )}
      <span className="faq-quick-button-text">{button.question}</span>
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

export const FAQQuickButtons: React.FC<FAQQuickButtonsProps> = ({
  buttons,
  onButtonClick,
  theme,
  themeMode,
  disabled = false,
}) => {
  const reducedMotion = useReducedMotion();
  const isDark = themeMode === 'dark';

  const handleClick = (button: FAQQuickButton, _index: number) => {
    onButtonClick(button);
  };

  if (!buttons || buttons.length === 0) {
    return null;
  }

  return (
    <div
      data-testid="faq-quick-buttons"
      role="group"
      aria-label="FAQ quick buttons"
      className="faq-quick-buttons"
      style={{
        display: 'flex',
        flexWrap: 'wrap',
        gap: '8px',
        padding: '8px 0',
      }}
    >
      {buttons.map((button, index) => (
        <FAQQuickButtonItem
          key={button.id}
          button={button}
          index={index}
          onClick={handleClick}
          theme={theme}
          isDark={isDark}
          disabled={disabled}
          reducedMotion={reducedMotion}
        />
      ))}
    </div>
  );
};
