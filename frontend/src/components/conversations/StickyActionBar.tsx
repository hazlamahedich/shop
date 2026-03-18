/**
 * StickyActionBar Component - Story 4-9: Open in Messenger Reply
 *
 * Fixed bottom action bar with prominent "Open in Messenger" / "Return to Bot" button.
 * Party Mode: Sally - sticky positioning for easy merchant access.
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
      className="fixed bottom-0 left-0 right-0 bg-[#0a0a0a]/80 backdrop-blur-xl border-t border-emerald-500/10 
                 shadow-[0_-10px_40px_rgba(0,0,0,0.5)] p-4 z-40 md:ml-64 animate-in fade-in slide-in-from-bottom-4 duration-500"
    >
      <div className="max-w-4xl mx-auto flex items-center justify-between gap-6">
        <div className="flex-1">
          {isHybridModeActive && remainingSeconds !== undefined && (
            <div className="flex items-center gap-3 bg-emerald-500/5 border border-emerald-500/10 px-4 py-2 rounded-full w-fit">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
              <span className="text-sm font-medium text-emerald-400">
                Merchant in Control • <span className="text-emerald-500/60 font-normal">Bot resumes in</span> {formatRemainingTime(remainingSeconds)}
              </span>
            </div>
          )}
          {!isHybridModeActive && (
            <div className="flex items-center gap-3 text-zinc-400 group cursor-default">
              <div className="w-8 h-8 rounded-full bg-emerald-500/5 border border-emerald-500/10 flex items-center justify-center group-hover:border-emerald-500/20 transition-colors">
                <MessageCircle size={14} className="text-emerald-500/40" />
              </div>
              <p className="text-sm">
                Click to respond to this customer directly in Messenger
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
