import * as React from 'react';
import FocusTrap from 'focus-trap-react';
import type { WidgetTheme, WidgetConfig, WidgetMessage } from '../types/widget';
import { MessageList } from './MessageList';
import { MessageInput } from './MessageInput';
import { TypingIndicator } from './TypingIndicator';

export interface ChatWindowProps {
  isOpen: boolean;
  onClose: () => void;
  theme: WidgetTheme;
  config: WidgetConfig | null;
  messages: WidgetMessage[];
  isTyping: boolean;
  onSendMessage: (content: string) => Promise<void>;
  error: string | null;
}

function ChatWindow({
  isOpen,
  onClose,
  theme,
  config,
  messages,
  isTyping,
  onSendMessage,
  error,
}: ChatWindowProps) {
  const [inputValue, setInputValue] = React.useState('');
  const inputRef = React.useRef<HTMLInputElement>(null);

  const positionStyle = theme.position === 'bottom-left'
    ? { left: 20 }
    : { right: 20 };

  React.useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  React.useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, onClose]);

  const handleSend = async () => {
    if (!inputValue.trim()) return;
    const message = inputValue.trim();
    setInputValue('');
    await onSendMessage(message);
  };

  if (!isOpen) return null;

  return (
    <FocusTrap active={isOpen}>
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Chat window"
        className="chat-window"
        style={{
          position: 'fixed',
          bottom: 90,
          ...positionStyle,
          width: theme.width,
          height: theme.height,
          maxWidth: 'calc(100vw - 40px)',
          maxHeight: 'calc(100vh - 120px)',
          backgroundColor: theme.backgroundColor,
          borderRadius: theme.borderRadius,
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.15)',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          zIndex: 9998,
          fontFamily: theme.fontFamily,
          fontSize: theme.fontSize,
          color: theme.textColor,
        }}
      >
        <div
          className="chat-header"
          style={{
            padding: '16px',
            backgroundColor: theme.primaryColor,
            color: 'white',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            borderRadius: `${theme.borderRadius}px ${theme.borderRadius}px 0 0`,
          }}
        >
          <span className="chat-header-title" style={{ fontWeight: 600 }}>
            {config?.botName ?? 'Assistant'}
          </span>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close chat window"
            style={{
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              padding: 4,
              color: 'white',
            }}
          >
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        <MessageList
          messages={messages}
          botName={config?.botName ?? 'Assistant'}
          welcomeMessage={config?.welcomeMessage}
          theme={theme}
          isLoading={isTyping}
        />

        {isTyping && (
          <TypingIndicator
            isVisible={isTyping}
            botName={config?.botName ?? 'Assistant'}
            theme={theme}
          />
        )}

        {error && (
          <div
            className="chat-error"
            role="alert"
            style={{
              padding: '8px 16px',
              backgroundColor: '#fee2e2',
              color: '#dc2626',
              fontSize: 12,
            }}
          >
            {error}
          </div>
        )}

        <MessageInput
          value={inputValue}
          onChange={setInputValue}
          onSend={handleSend}
          disabled={isTyping}
          placeholder="Type a message..."
          inputRef={inputRef as React.Ref<HTMLInputElement>}
          theme={theme}
        />
      </div>
    </FocusTrap>
  );
}

export default ChatWindow;
