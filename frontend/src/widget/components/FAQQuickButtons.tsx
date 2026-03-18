import * as React from 'react';
import type { FAQQuickButton, WidgetTheme } from '../types/widget';
import { useReducedMotion } from '../hooks/useReducedMotion';
import { useRipple } from '../hooks/useRipple';

export interface FAQQuickButtonsProps {
  buttons: FAQQuickButton[];
  onButtonClick: (button: FAQQuickButton) => void;
  theme: WidgetTheme;
  disabled?: boolean;
}

interface FAQQuickButtonItemProps {
  button: FAQQuickButton;
  index: number;
  onClick: (button: FAQQuickButton, index: number) => void;
  theme: WidgetTheme;
  disabled: boolean;
  reducedMotion: boolean;
}

function FAQQuickButtonItem({
  button,
  index,
  onClick,
  theme,
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
        minHeight: '44px',
        minWidth: '44px',
        padding: '10px 16px',
        border: `1px solid ${theme.primaryColor}`,
        borderRadius: '20px',
        backgroundColor: 'transparent',
        color: theme.textColor,
        fontFamily: theme.fontFamily,
        fontSize: '14px',
        fontWeight: 500,
        cursor: disabled ? 'not-allowed' : 'pointer',
        opacity: disabled ? 0.5 : 1,
        transition: reducedMotion ? 'none' : 'transform 100ms ease, background-color 150ms ease, opacity 150ms ease',
        whiteSpace: 'nowrap',
        position: 'relative',
        overflow: 'hidden',
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
  disabled = false,
}) => {
  const reducedMotion = useReducedMotion();

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
          disabled={disabled}
          reducedMotion={reducedMotion}
        />
      ))}
    </div>
  );
};
