/**
 * OpenInMessengerButton Component
 *
 * Industrial Technical Dashboard design with terminal aesthetics.
 * Button for hybrid mode control and Messenger integration.
 */

import React, { useState, useEffect } from 'react';
import { MessageCircle, Bot, Loader2, Check } from 'lucide-react';
import type { HybridModeState, FacebookPageInfo } from '../../types/conversation';

interface OpenInMessengerButtonProps {
  conversationId: number;
  platformSenderId: string;
  hybridMode: HybridModeState | null;
  facebookPage: FacebookPageInfo | null;
  isLoading?: boolean;
  onHybridModeChange?: (enabled: boolean) => Promise<void>;
  onConversationRefresh?: () => Promise<void>;
}

export default function OpenInMessengerButton({
  conversationId: _conversationId,
  platformSenderId,
  hybridMode,
  facebookPage,
  isLoading = false,
  onHybridModeChange,
  onConversationRefresh,
}: OpenInMessengerButtonProps) {
  const [isToggling, setIsToggling] = useState(false);
  const [showTooltip, setShowTooltip] = useState(false);
  const [showToast, setShowToast] = useState(false);

  const isHybridModeActive = hybridMode?.enabled === true;
  const hasFacebookConnection = facebookPage?.isConnected === true && facebookPage.pageId;
  const isDisabled = !hasFacebookConnection || isLoading || isToggling;

  useEffect(() => {
    if (showToast) {
      const timer = setTimeout(() => setShowToast(false), 3000);
      return () => clearTimeout(timer);
    }
  }, [showToast]);

  const handleClick = async () => {
    if (isDisabled) return;

    if (isHybridModeActive) {
      setIsToggling(true);
      try {
        await onHybridModeChange?.(false);
        setShowToast(true);
        await onConversationRefresh?.();
      } finally {
        setIsToggling(false);
      }
    } else {
      const messengerUrl = `https://m.me/${facebookPage?.pageId}?thread_id=${platformSenderId}`;
      window.open(messengerUrl, '_blank');
      
      setIsToggling(true);
      try {
        await onHybridModeChange?.(true);
      } finally {
        setIsToggling(false);
      }
    }
  };

  const handleMouseEnter = () => {
    if (!hasFacebookConnection) {
      setShowTooltip(true);
    }
  };

  const handleMouseLeave = () => {
    setShowTooltip(false);
  };

  return (
    <div 
      className="relative inline-block"
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      <button
        data-testid={isHybridModeActive ? 'return-to-bot-btn' : 'open-in-messenger-btn'}
        onClick={handleClick}
        disabled={isDisabled}
        className="inline-flex items-center gap-3 px-5 py-3 transition-all duration-300 disabled:opacity-30 disabled:cursor-not-allowed"
        style={{
          fontFamily: 'JetBrains Mono, monospace',
          backgroundColor: isHybridModeActive ? '#00FF8810' : '#0A0A0A',
          border: `1px solid ${isHybridModeActive ? '#00FF8840' : '#2f2f2f'}`,
          color: isHybridModeActive ? '#00FF88' : '#FFFFFF',
          fontSize: '10px',
          fontWeight: 700,
          letterSpacing: '0.15em',
        }}
        aria-label={isHybridModeActive ? 'Return control to bot' : 'Open conversation in Messenger'}
      >
        {(isLoading || isToggling) ? (
          <Loader2 size={14} className="animate-spin" />
        ) : isHybridModeActive ? (
          <Bot size={14} />
        ) : (
          <MessageCircle size={14} />
        )}
        <span className="uppercase">
          {isHybridModeActive ? 'Return to Bot' : 'Open in Messenger'}
        </span>
      </button>

      {showTooltip && (
        <div
          data-testid="no-facebook-tooltip"
          className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-3 px-4 py-3 whitespace-nowrap z-10"
          style={{
            backgroundColor: '#0A0A0A',
            border: '1px solid #2f2f2f',
          }}
        >
          <span 
            className="text-[10px] font-medium"
            style={{ fontFamily: 'JetBrains Mono, monospace', color: '#8a8a8a' }}
          >
            Connect Facebook page to enable Messenger
          </span>
          <div 
            className="absolute top-full left-1/2 transform -translate-x-1/2"
            style={{
              border: '4px solid transparent',
              borderTopColor: '#2f2f2f',
            }}
          />
        </div>
      )}

      {showToast && (
        <div
          data-testid="return-to-bot-toast"
          role="status"
          aria-live="polite"
          className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-3 px-4 py-3 whitespace-nowrap z-20 animate-in fade-in slide-in-from-bottom-2 duration-300"
          style={{
            backgroundColor: '#00FF88',
          }}
        >
          <div className="flex items-center gap-3">
            <Check size={14} style={{ color: '#0C0C0C' }} />
            <span 
              className="text-[10px] font-bold uppercase tracking-widest"
              style={{ fontFamily: 'JetBrains Mono, monospace', color: '#0C0C0C' }}
            >
              Bot resumed control
            </span>
          </div>
          <div 
            className="absolute top-full left-1/2 transform -translate-x-1/2"
            style={{
              border: '4px solid transparent',
              borderTopColor: '#00FF88',
            }}
          />
        </div>
      )}
    </div>
  );
}
