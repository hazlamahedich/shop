/** MessageList component.
 *
 * Story 1.13: Bot Preview Mode
 *
 * Displays the list of messages in the preview conversation.
 * Auto-scrolls to show the latest message.
 */

import * as React from 'react';
import { MessageBubble } from './MessageBubble';
import type { PreviewMessage } from '../../stores/previewStore';

export interface MessageListProps {
  /** Array of messages to display */
  messages: PreviewMessage[];
  /** Bot name to display */
  botName: string;
  /** Optional className for styling */
  className?: string;
  /** Reference to the messages container for auto-scrolling */
  messagesEndRef?: React.RefObject<HTMLDivElement>;
  /** Optional data-testid for E2E testing */
  'data-testid'?: string;
}

export function MessageList({
  messages,
  botName,
  className = '',
  messagesEndRef,
  'data-testid': dataTestId = 'message-list',
}: MessageListProps) {
  if (messages.length === 0) {
    return (
      <div className={`message-list flex items-center justify-center h-full ${className}`} data-testid={dataTestId}>
        <div className="text-center text-gray-500">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
            />
          </svg>
          <p className="mt-2">Start a conversation to test your bot.</p>
          <p className="text-sm">Use the quick-try buttons or type a message below.</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`message-list overflow-y-auto flex-1 ${className}`} data-testid={dataTestId}>
      <div role="list" className="py-4 px-4">
        {messages.map((message) => (
          <MessageBubble
            key={message.id}
            message={message}
            botName={botName}
          />
        ))}
      </div>

      {/* Auto-scroll anchor */}
      {messagesEndRef && <div ref={messagesEndRef} />}
    </div>
  );
}
