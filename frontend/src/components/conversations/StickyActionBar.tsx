/**
 * StickyActionBar Component
 *
 * Industrial Technical Dashboard design with terminal aesthetics.
 * Fixed bottom action bar for hybrid mode control.
 */

import OpenInMessengerButton from './OpenInMessengerButton';
import { MessageCircle } from 'lucide-react';
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
      className="fixed bottom-0 left-0 right-0 z-40 md:ml-64"
      style={{ 
        backgroundColor: '#0A0A0A', 
        borderTop: '1px solid #2f2f2f',
      }}
    >
      <div className="max-w-5xl mx-auto flex items-center justify-between gap-6 px-8 py-4">
        <div className="flex-1">
          {isHybridModeActive && remainingSeconds !== undefined && (
            <div 
              className="flex items-center gap-4 px-4 py-3"
              style={{ backgroundColor: '#00FF8810', border: '1px solid #00FF8840' }}
            >
              <span className="relative flex h-2 w-2">
                <span 
                  className="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75"
                  style={{ backgroundColor: '#00FF88' }}
                />
                <span 
                  className="relative inline-flex rounded-full h-2 w-2"
                  style={{ backgroundColor: '#00FF88' }}
                />
              </span>
              <span 
                className="text-[10px] font-bold uppercase tracking-widest"
                style={{ fontFamily: 'JetBrains Mono, monospace', color: '#00FF88' }}
              >
                OVERRIDE ACTIVE
              </span>
              <span 
                className="text-[10px] font-medium"
                style={{ fontFamily: 'JetBrains Mono, monospace', color: '#6a6a6a' }}
              >
                Bot resumes in {formatRemainingTime(remainingSeconds)}
              </span>
            </div>
          )}
          {!isHybridModeActive && (
            <div className="flex items-center gap-4">
              <div 
                className="w-9 h-9 flex items-center justify-center"
                style={{ backgroundColor: '#080808', border: '1px solid #2f2f2f' }}
              >
                <MessageCircle size={14} style={{ color: '#6a6a6a' }} />
              </div>
              <p 
                className="text-[10px] font-medium uppercase tracking-widest"
                style={{ fontFamily: 'JetBrains Mono, monospace', color: '#6a6a6a' }}
              >
                Click to initiate manual override in Messenger
              </p>
            </div>
          )}
        </div>
        
        <div className="flex items-center gap-4">
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
    </div>
  );
}
