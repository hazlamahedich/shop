import * as React from 'react';
import FocusTrap from 'focus-trap-react';
import type { ProactiveTrigger, ProactiveTriggerAction } from '../types/widget';

export interface ProactiveModalProps {
  trigger: ProactiveTrigger;
  isOpen: boolean;
  onAction: (action: ProactiveTriggerAction) => void;
  onDismiss: () => void;
  theme?: {
    primaryColor?: string;
    backgroundColor?: string;
    textColor?: string;
  };
}

function CloseIcon() {
  return (
    <svg
      width="20"
      height="20"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <line x1="18" x2="6" y1="6" y2="18" />
      <line x1="6" x2="18" y1="6" y2="18" />
    </svg>
  );
}

function ChatIcon() {
  return (
    <svg
      width="20"
      height="20"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
    </svg>
  );
}

export function ProactiveModal({
  trigger,
  isOpen,
  onAction,
  onDismiss,
  theme,
}: ProactiveModalProps) {
  const modalRef = React.useRef<HTMLDivElement>(null);
  const previousActiveElement = React.useRef<HTMLElement | null>(null);

  React.useEffect(() => {
    if (isOpen) {
      previousActiveElement.current = document.activeElement as HTMLElement;
    }
  }, [isOpen]);

  React.useEffect(() => {
    if (!isOpen && previousActiveElement.current) {
      previousActiveElement.current.focus();
    }
  }, [isOpen]);

  React.useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onDismiss();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, onDismiss]);

  if (!isOpen || !trigger) {
    return null;
  }

  return (
    <FocusTrap active={isOpen} focusTrapOptions={{ initialFocus: false }}>
      <div
        ref={modalRef}
        data-testid="proactive-modal"
        role="dialog"
        aria-modal="true"
        aria-live="assertive"
        className="proactive-modal-overlay"
        onClick={(e) => {
          if (e.target === e.currentTarget) onDismiss();
        }}
      >
        <div className="proactive-modal-container">
          <button
            data-testid="proactive-dismiss-button"
            type="button"
            className="proactive-modal-close"
            onClick={onDismiss}
            aria-label="Close proactive message"
          >
            <CloseIcon />
          </button>

          <div className="proactive-modal-icon">
            <ChatIcon />
          </div>

          <h2
            id="proactive-title"
            data-testid="proactive-title"
            className="proactive-modal-title"
          >
            Need Help?
          </h2>

          <p
            id="proactive-message"
            data-testid="proactive-message"
            className="proactive-modal-message"
          >
            {trigger.message}
          </p>

          <div className="proactive-modal-actions">
            {trigger.actions.map((action, index) => (
              <button
                key={index}
                data-testid={`proactive-action-button-${index}`}
                type="button"
                className={`proactive-action-button ${index === 0 ? '' : 'proactive-action-secondary'}`}
                onClick={() => onAction(action)}
                style={
                  index === 0 && theme?.primaryColor
                    ? { backgroundColor: theme.primaryColor }
                    : undefined
                }
              >
                {action.text}
              </button>
            ))}
          </div>
        </div>
      </div>
    </FocusTrap>
  );
}
