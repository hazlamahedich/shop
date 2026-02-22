/**
 * ReplyInput Component
 *
 * Input component for merchant to reply to conversations.
 * Platform-aware: shows appropriate UI for Messenger/Widget.
 * Hidden for Preview conversations (read-only).
 */

import React, { useState } from 'react';
import { Send, Loader2, MessageCircle, Globe, AlertCircle } from 'lucide-react';

interface ReplyInputProps {
  conversationId: number;
  platform: 'messenger' | 'widget' | 'preview' | 'facebook';
  onSend: (content: string) => Promise<void>;
  isLoading?: boolean;
  disabled?: boolean;
}

const platformConfig = {
  messenger: {
    icon: MessageCircle,
    label: 'Send via Messenger',
    placeholder: 'Type your reply to send via Facebook Messenger...',
    color: 'text-indigo-600',
  },
  facebook: {
    icon: MessageCircle,
    label: 'Send via Messenger',
    placeholder: 'Type your reply to send via Facebook Messenger...',
    color: 'text-indigo-600',
  },
  widget: {
    icon: Globe,
    label: 'Send to Widget',
    placeholder: 'Type your reply to send to the customer on your website...',
    color: 'text-blue-600',
  },
  preview: {
    icon: AlertCircle,
    label: 'Preview is Read-Only',
    placeholder: 'Cannot reply to preview conversations',
    color: 'text-gray-400',
  },
};

export const ReplyInput: React.FC<ReplyInputProps> = ({
  conversationId: _conversationId,
  platform,
  onSend,
  isLoading = false,
  disabled = false,
}) => {
  const [message, setMessage] = useState('');
  const [error, setError] = useState<string | null>(null);

  const config = platformConfig[platform as keyof typeof platformConfig] || platformConfig.preview;
  const PlatformIcon = config.icon;
  const isPreview = platform === 'preview';
  const isDisabled = disabled || isLoading || isPreview;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!message.trim() || isDisabled) return;

    setError(null);

    try {
      await onSend(message.trim());
      setMessage('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send message');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  if (isPreview) {
    return (
      <div className="bg-gray-50 border-t border-gray-200 p-4">
        <div className="flex items-center gap-2 text-gray-500 text-sm">
          <AlertCircle size={16} />
          <span>Preview conversations are read-only. They are not sent to real customers.</span>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white border-t border-gray-200 p-4">
      <form onSubmit={handleSubmit} className="space-y-3">
        {/* Platform indicator */}
        <div className={`flex items-center gap-2 text-sm ${config.color}`}>
          <PlatformIcon size={16} />
          <span>{config.label}</span>
        </div>

        {/* Error message */}
        {error && (
          <div className="flex items-center gap-2 text-red-600 text-sm bg-red-50 p-2 rounded">
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
        )}

        {/* Input area */}
        <div className="flex gap-2">
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={config.placeholder}
            disabled={isDisabled}
            rows={2}
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
            maxLength={5000}
          />
          <button
            type="submit"
            disabled={!message.trim() || isDisabled}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center gap-2 self-end"
          >
            {isLoading ? (
              <Loader2 size={18} className="animate-spin" />
            ) : (
              <Send size={18} />
            )}
          </button>
        </div>

        {/* Character count */}
        <div className="text-xs text-gray-400 text-right">
          {message.length} / 5000
        </div>
      </form>
    </div>
  );
};

export default ReplyInput;
