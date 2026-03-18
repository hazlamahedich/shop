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
    color: 'text-emerald-400',
    borderColor: 'border-emerald-500/20',
  },
  facebook: {
    icon: MessageCircle,
    label: 'Send via Messenger',
    placeholder: 'Type your reply to send via Facebook Messenger...',
    color: 'text-emerald-400',
    borderColor: 'border-emerald-500/20',
  },
  widget: {
    icon: Globe,
    label: 'Send to Widget',
    placeholder: 'Type your reply to send to the customer on your website...',
    color: 'text-emerald-400',
    borderColor: 'border-emerald-500/20',
  },
  preview: {
    icon: AlertCircle,
    label: 'Preview is Read-Only',
    placeholder: 'Cannot reply to preview conversations',
    color: 'text-zinc-500',
    borderColor: 'border-zinc-500/20',
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
      <div className="bg-[#0a0a0a]/60 backdrop-blur-2xl border-t border-emerald-500/10 p-4">
        <div className="flex items-center gap-2 text-zinc-500 text-sm">
          <AlertCircle size={16} />
          <span>Preview conversations are read-only. They are not sent to real customers.</span>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-[#0a0a0a]/60 backdrop-blur-2xl border-t border-emerald-500/10 p-4 relative z-10">
      <form onSubmit={handleSubmit} className="max-w-4xl mx-auto space-y-4">
        {/* Platform indicator & Errors */}
        <div className="flex items-center justify-between gap-4">
          <div className={`flex items-center gap-2 text-xs font-medium uppercase tracking-wider ${config.color}`}>
            <PlatformIcon size={14} />
            <span>{config.label}</span>
          </div>

          {error && (
            <div className="flex items-center gap-2 text-red-400 text-xs bg-red-500/10 px-3 py-1 rounded-full border border-red-500/20 animate-in fade-in slide-in-from-top-1">
              <AlertCircle size={14} />
              <span>{error}</span>
            </div>
          )}
        </div>

        {/* Input area */}
        <div className="relative group">
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={config.placeholder}
            disabled={isDisabled}
            rows={2}
            className="w-full bg-black/40 border border-emerald-500/10 rounded-xl px-4 py-3 text-emerald-50/90 placeholder:text-emerald-900/40 resize-none focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500/40 transition-all disabled:opacity-50 disabled:cursor-not-allowed custom-scrollbar"
            maxLength={5000}
          />
          
          <div className="absolute bottom-3 right-3 flex items-center gap-3">
            {/* Character count */}
            <span className={`text-[10px] font-medium transition-colors ${
              message.length > 4500 ? 'text-amber-500' : 'text-emerald-900/40'
            }`}>
              {message.length.toLocaleString()} / 5,000
            </span>

            <button
              type="submit"
              disabled={!message.trim() || isDisabled}
              className="flex items-center justify-center w-10 h-10 bg-emerald-500 text-black rounded-lg hover:bg-emerald-400 disabled:bg-emerald-500/10 disabled:text-emerald-500/20 shadow-[0_0_20px_rgba(16,185,129,0.2)] hover:shadow-[0_0_25px_rgba(16,185,129,0.4)] transition-all duration-300 group-hover:scale-105 active:scale-95 disabled:scale-100 disabled:shadow-none"
            >
              {isLoading ? (
                <Loader2 size={18} className="animate-spin" />
              ) : (
                <Send size={18} />
              )}
            </button>
          </div>
        </div>
      </form>
    </div>
  );
};

export default ReplyInput;
