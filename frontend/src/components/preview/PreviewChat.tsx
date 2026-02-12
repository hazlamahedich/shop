/** PreviewChat component.
 *
 * Story 1.13: Bot Preview Mode
 *
 * Main chat interface for preview mode testing.
 * Integrates message list, input, quick-try buttons, and reset functionality.
 */

import * as React from 'react';
import { MessageList } from './MessageList';
import { QuickTryButtons } from './QuickTryButtons';
import { usePreviewStore } from '../../stores/previewStore';
import { Button } from '../ui/Button';
import { Alert } from '../ui/Alert';

export interface PreviewChatProps {
  /** Optional className for styling */
  className?: string;
  /** Optional bot name override */
  botName?: string;
}

export function PreviewChat({ className = '', botName }: PreviewChatProps) {
  const {
    messages,
    isLoading,
    error,
    starterPrompts,
    sendMessage,
    resetConversation,
    setBotName,
  } = usePreviewStore();

  const [inputValue, setInputValue] = React.useState('');
  const messagesEndRef = React.useRef<HTMLDivElement>(null);
  const inputRef = React.useRef<HTMLInputElement>(null);

  // Update bot name if provided
  React.useEffect(() => {
    if (botName) {
      setBotName(botName);
    }
  }, [botName, setBotName]);

  // Auto-scroll to bottom when new messages arrive
  React.useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  const handleSendMessage = async () => {
    const message = inputValue.trim();
    if (!message || isLoading) return;

    setInputValue('');
    await sendMessage(message);

    // Focus input after sending
    if (inputRef.current) {
      inputRef.current.focus();
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleQuickTry = async (prompt: string) => {
    if (isLoading) return;
    setInputValue(prompt);
    await sendMessage(prompt);

    // Focus input after sending
    if (inputRef.current) {
      inputRef.current.focus();
    }
  };

  const handleReset = async () => {
    if (isLoading) return;
    await resetConversation();

    // Focus input after reset
    if (inputRef.current) {
      inputRef.current.focus();
    }
  };

  const { botName: currentBotName } = usePreviewStore();

  return (
    <div className={`preview-chat flex flex-col h-full ${className}`} data-testid="preview-chat">
      {/* Preview mode badge */}
      <div className="flex items-center justify-between px-4 py-2 bg-blue-50 border-b border-blue-200">
        <div className="flex items-center gap-2">
          <span className="px-2 py-1 text-xs font-semibold text-blue-700 bg-blue-200 rounded">
            PREVIEW MODE
          </span>
          <span className="text-sm text-blue-600">
            Sandbox environment - No real customers will see these messages
          </span>
        </div>
        <Button
          type="button"
          variant="secondary"
          size="sm"
          onClick={handleReset}
          disabled={isLoading || messages.length === 0}
          aria-label="Reset conversation"
          data-testid="reset-button"
        >
          Reset Conversation
        </Button>
      </div>

      {/* Error alert */}
      {error && (
        <div className="px-4 pt-2">
          <Alert type="error" dismissible onDismiss={() => usePreviewStore.getState().setError(null)}>
            {error}
          </Alert>
        </div>
      )}

      {/* Message list */}
      <MessageList
        messages={messages}
        botName={currentBotName}
        messagesEndRef={messagesEndRef}
        className="flex-1"
        data-testid="preview-messages"
      />

      {/* Quick-try buttons */}
      {starterPrompts.length > 0 && messages.length === 0 && (
        <div className="px-4 py-3 border-t border-gray-200 bg-gray-50">
          <QuickTryButtons
            starterPrompts={starterPrompts}
            onPromptClick={handleQuickTry}
            disabled={isLoading}
          />
        </div>
      )}

      {/* Message input */}
      <div className="px-4 py-3 border-t border-gray-200 bg-white">
        <div className="flex gap-2">
          <input
            ref={inputRef}
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type a message to test your bot..."
            disabled={isLoading}
            maxLength={1000}
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
            aria-label="Message input"
            data-testid="message-input"
          />
          <Button
            type="button"
            variant="primary"
            onClick={handleSendMessage}
            disabled={!inputValue.trim() || isLoading}
            aria-label="Send message"
            data-testid="send-button"
          >
            {isLoading ? (
              <svg
                className="animate-spin h-5 w-5"
                fill="none"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
            ) : (
              <svg
                className="w-5 h-5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                />
              </svg>
            )}
          </Button>
        </div>
        <p className="mt-1 text-xs text-gray-500">
          Messages are limited to 1000 characters. This is a sandbox environment.
        </p>
      </div>
    </div>
  );
}
