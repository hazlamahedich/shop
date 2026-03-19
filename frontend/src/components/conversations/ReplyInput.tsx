/**
 * ReplyInput Component
 *
 * Industrial Technical Dashboard design with terminal aesthetics.
 * Platform-aware input for merchant replies.
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
    label: 'MESSENGER TRANSMISSION',
    placeholder: 'Compose transmission via Facebook Messenger protocol...',
    color: '#00FF88',
  },
  facebook: {
    icon: MessageCircle,
    label: 'MESSENGER TRANSMISSION',
    placeholder: 'Compose transmission via Facebook Messenger protocol...',
    color: '#00FF88',
  },
  widget: {
    icon: Globe,
    label: 'WIDGET TRANSMISSION',
    placeholder: 'Compose transmission via website widget interface...',
    color: '#00FF88',
  },
  preview: {
    icon: AlertCircle,
    label: 'READ-ONLY MODE',
    placeholder: 'Preview sessions cannot transmit to external clients',
    color: '#6a6a6a',
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
      <div className="flex items-center gap-4 px-5 py-4">
        <AlertCircle size={16} style={{ color: '#6a6a6a' }} />
        <span 
          className="text-[11px] font-medium"
          style={{ fontFamily: 'JetBrains Mono, monospace', color: '#6a6a6a' }}
        >
          Preview sessions are read-only. No external transmission possible.
        </span>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && (
        <div 
          className="flex items-center gap-3 px-4 py-3"
          style={{ backgroundColor: '#FF444420', border: '1px solid #FF444440' }}
        >
          <AlertCircle size={14} style={{ color: '#FF4444' }} />
          <span 
            className="text-[10px] font-bold uppercase tracking-widest"
            style={{ fontFamily: 'JetBrains Mono, monospace', color: '#FF4444' }}
          >
            {error}
          </span>
        </div>
      )}

      <div className="flex items-end gap-4">
        <div className="flex-1 space-y-3">
          <div className="flex items-center gap-3">
            <PlatformIcon size={14} style={{ color: config.color }} />
            <span 
              className="text-[9px] font-bold uppercase tracking-[0.3em]"
              style={{ fontFamily: 'JetBrains Mono, monospace', color: config.color }}
            >
              {config.label}
            </span>
          </div>

          <div 
            className="relative"
            style={{ backgroundColor: '#080808', border: '1px solid #2f2f2f' }}
          >
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={config.placeholder}
              disabled={isDisabled}
              rows={2}
              className="w-full px-5 py-4 bg-transparent resize-none focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed"
              style={{
                fontFamily: 'JetBrains Mono, monospace',
                fontSize: '12px',
                fontWeight: 500,
                color: '#FFFFFF',
                lineHeight: 1.5,
              }}
              maxLength={5000}
            />

            <div className="absolute bottom-3 right-3 flex items-center gap-4">
              <span 
                className="text-[10px] font-semibold"
                style={{ 
                  fontFamily: 'JetBrains Mono, monospace', 
                  color: message.length > 4500 ? '#FF8800' : '#6a6a6a' 
                }}
              >
                {message.length.toLocaleString()}/5000
              </span>
            </div>
          </div>
        </div>

        <button
          type="submit"
          disabled={!message.trim() || isDisabled}
          className="flex items-center gap-3 px-6 py-4 transition-all disabled:opacity-30 disabled:cursor-not-allowed"
          style={{
            backgroundColor: message.trim() && !isDisabled ? '#00FF88' : '#0A0A0A',
            border: '1px solid #2f2f2f',
            color: message.trim() && !isDisabled ? '#0C0C0C' : '#6a6a6a',
          }}
        >
          {isLoading ? (
            <Loader2 size={16} className="animate-spin" />
          ) : (
            <Send size={16} />
          )}
          <span 
            className="text-[10px] font-bold uppercase tracking-[0.2em]"
            style={{ fontFamily: 'JetBrains Mono, monospace' }}
          >
            TRANSMIT
          </span>
        </button>
      </div>
    </form>
  );
};

export default ReplyInput;
