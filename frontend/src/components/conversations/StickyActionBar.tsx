/**
 * StickyActionBar Component - Story 4-9: Open in Messenger Reply
 *
 * Fixed bottom action bar with prominent "Open in Messenger" / "Return to Bot" button.
 * Party Mode: Sally - sticky positioning for easy merchant access.
 */

import React from 'react';
import OpenInMessengerButton from './OpenInMessengerButton';
import type { HybridModeState, FacebookPageInfo } from '../../types/conversation';

interface StickyActionBarProps {
  conversationId: number;
  platformSenderId: string;
  hybridMode: HybridModeState | null;
  facebookPage: FacebookPageInfo | null;
  isLoading?: boolean;
  onHybridModeChange?: (enabled: boolean) => Promise<void>;
}

export default function StickyActionBar({
  conversationId,
  platformSenderId,
  hybridMode,
  facebookPage,
  isLoading = false,
  onHybridModeChange,
}: StickyActionBarProps) {
  const isHybridModeActive = hybridMode?.enabled === true;
  const remainingSeconds = hybridMode?.remainingSeconds;

  const formatRemainingTime = (seconds: number): string => {
    if (seconds < 60) {
      return `${seconds}s`;
    }
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) {
      return `${minutes}m`;
    }
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;
    if (remainingMinutes === 0) {
      return `${hours}h`;
    }
    return `${hours}h ${remainingMinutes}m`;
  };

  return (
    <div
      data-testid="sticky-action-bar"
      className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 
                 shadow-lg p-4 z-40 md:ml-64"
    >
      <div className="max-w-4xl mx-auto flex items-center justify-between">
        <div className="flex-1">
          {isHybridModeActive && remainingSeconds !== undefined && (
            <div className="flex items-center gap-2 text-sm text-green-600">
              <span className="inline-block w-2 h-2 rounded-full bg-green-500 animate-pulse" />
              <span>
                You're in control! Bot will resume in {formatRemainingTime(remainingSeconds)}
              </span>
            </div>
          )}
          {!isHybridModeActive && (
            <p className="text-sm text-gray-500">
              Click to respond to this customer directly in Messenger
            </p>
          )}
        </div>
        
        <OpenInMessengerButton
          conversationId={conversationId}
          platformSenderId={platformSenderId}
          hybridMode={hybridMode}
          facebookPage={facebookPage}
          isLoading={isLoading}
          onHybridModeChange={onHybridModeChange}
        />
      </div>
    </div>
  );
}
