/**
 * OpenInMessengerButton Component - Story 4-9: Open in Messenger Reply
 *
 * Button that opens Facebook Messenger at a specific conversation.
 * Supports smart state: shows "Open in Messenger" or "Return to Bot"
 * depending on hybrid mode status.
 */

import React, { useState } from 'react';
import { MessageCircle, Bot, Loader2 } from 'lucide-react';
import type { HybridModeState, FacebookPageInfo } from '../../types/conversation';

interface OpenInMessengerButtonProps {
  conversationId: number;
  platformSenderId: string;
  hybridMode: HybridModeState | null;
  facebookPage: FacebookPageInfo | null;
  isLoading?: boolean;
  onHybridModeChange?: (enabled: boolean) => Promise<void>;
}

export default function OpenInMessengerButton({
  conversationId,
  platformSenderId,
  hybridMode,
  facebookPage,
  isLoading = false,
  onHybridModeChange,
}: OpenInMessengerButtonProps) {
  const [isToggling, setIsToggling] = useState(false);
  const [showTooltip, setShowTooltip] = useState(false);

  const isHybridModeActive = hybridMode?.enabled === true;
  const hasFacebookConnection = facebookPage?.isConnected === true && facebookPage.pageId;
  const isDisabled = !hasFacebookConnection || isLoading || isToggling;

  const handleClick = async () => {
    if (isDisabled) return;

    if (isHybridModeActive) {
      setIsToggling(true);
      try {
        await onHybridModeChange?.(false);
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
        className={`
          inline-flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm
          transition-colors duration-200
          ${
            isHybridModeActive
              ? 'bg-green-600 hover:bg-green-700 text-white'
              : 'bg-blue-600 hover:bg-blue-700 text-white'
          }
          ${isDisabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
        `}
        aria-label={isHybridModeActive ? 'Return control to bot' : 'Open conversation in Messenger'}
      >
        {(isLoading || isToggling) ? (
          <Loader2 size={16} className="animate-spin" />
        ) : isHybridModeActive ? (
          <Bot size={16} />
        ) : (
          <MessageCircle size={16} />
        )}
        <span>
          {isHybridModeActive ? 'Return to Bot' : 'Open in Messenger'}
        </span>
      </button>

      {showTooltip && (
        <div
          data-testid="no-facebook-tooltip"
          className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 
                     bg-gray-900 text-white text-xs rounded-lg shadow-lg whitespace-nowrap z-10"
        >
          Connect a Facebook page to enable Messenger replies
          <div className="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-gray-900" />
        </div>
      )}
    </div>
  );
}
