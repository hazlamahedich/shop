/** MessageBubble component.
 *
 * Story 1.13: Bot Preview Mode
 *
 * Displays a single message in the preview chat.
 * Different styles for user and bot messages.
 */

import * as React from 'react';
import { ConfidenceIndicator } from './ConfidenceIndicator';
import type { PreviewMessage } from '../../stores/previewStore';

export interface MessageBubbleProps {
  /** The message to display */
  message: PreviewMessage;
  /** Bot name to display for bot messages */
  botName: string;
  /** Optional className for styling */
  className?: string;
}

/**
 * Format timestamp for display
 */
function formatTimestamp(date: Date): string {
  return new Intl.DateTimeFormat('en-US', {
    hour: 'numeric',
    minute: '2-digit',
  }).format(date);
}

export function MessageBubble({
  message,
  botName,
  className = '',
}: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const isBot = message.role === 'bot';

  return (
    <div
      className={`message-bubble flex ${isUser ? 'justify-end' : 'justify-start'} mb-4 ${className}`}
      role="listitem"
      data-testid={isBot ? "bot-response" : "user-message"}
    >
      <div
        className={`max-w-[75%] rounded-lg px-4 py-2 ${
          isUser
            ? 'bg-blue-500 text-white rounded-br-sm'
            : 'bg-gray-100 text-gray-800 rounded-bl-sm'
        }`}
      >
        {/* Bot name for bot messages */}
        {isBot && (
          <div className="text-xs font-semibold text-gray-600 mb-1">
            {botName}
          </div>
        )}

        {/* Message content */}
        <p className="text-sm whitespace-pre-wrap break-words">
          {message.content}
        </p>

        {/* Timestamp */}
        <div className={`text-xs mt-1 ${isUser ? 'text-blue-100' : 'text-gray-500'}`}>
          {formatTimestamp(message.timestamp)}
        </div>

        {/* Confidence indicator for bot messages */}
        {isBot && message.confidence !== undefined && (
          <div className="mt-2">
            <ConfidenceIndicator
              confidence={message.confidence}
              confidenceLevel={message.confidenceLevel || 'medium'}
              metadata={message.metadata}
            />
          </div>
        )}
      </div>
    </div>
  );
}
