/**
 * BudgetHardStopModal Component - Industrial Technical Dashboard
 *
 * Displays modal when bot is paused due to budget limit
 * Implements focus trap for accessibility (AC3)
 * Story 3-8: Budget Alert Notifications
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import { useCostTrackingStore } from '../../stores/costTrackingStore';

interface BudgetHardStopModalProps {
  onIncreaseBudget?: () => void;
  onResumeBot?: () => void;
  onClose?: () => void;
}

export function BudgetHardStopModal({
  onIncreaseBudget,
  onResumeBot,
  onClose,
}: BudgetHardStopModalProps) {
  const botStatus = useCostTrackingStore((state) => state.botStatus);
  const merchantSettings = useCostTrackingStore((state) => state.merchantSettings);
  const resumeBot = useCostTrackingStore((state) => state.resumeBot);
  const [isResuming, setIsResuming] = useState(false);
  const [isClosing, setIsClosing] = useState(false);

  const handleIncreaseBudget = () => {
    setIsClosing(true);
    if (onIncreaseBudget) {
      onIncreaseBudget();
    }
  };

  const handleClose = useCallback(() => {
    setIsClosing(true);
    if (onClose) {
      onClose();
    }
  }, [onClose]);

  const modalRef = useRef<HTMLDivElement>(null);
  const firstFocusableRef = useRef<HTMLButtonElement>(null);
  const lastFocusableRef = useRef<HTMLButtonElement>(null);

  const isPaused = botStatus?.isPaused ?? false;
  const pauseReason = botStatus?.pauseReason ?? 'Budget limit reached';
  const budgetCap = merchantSettings?.budgetCap ?? botStatus?.budgetCap;
  const monthlySpend = botStatus?.monthlySpend ?? 0;
  const canResume = budgetCap === null || budgetCap === undefined || budgetCap > monthlySpend;

  useEffect(() => {
    if (isPaused && firstFocusableRef.current) {
      firstFocusableRef.current.focus();
    }
  }, [isPaused]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isPaused) return;

      if (e.key === 'Escape' && onClose) {
        handleClose();
        return;
      }

      if (e.key === 'Tab' && modalRef.current) {
        const focusableElements = modalRef.current.querySelectorAll(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        const firstElement = focusableElements[0] as HTMLElement;
        const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;

        if (e.shiftKey && document.activeElement === firstElement) {
          e.preventDefault();
          lastElement.focus();
        } else if (!e.shiftKey && document.activeElement === lastElement) {
          e.preventDefault();
          firstElement.focus();
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isPaused, onClose, handleClose]);

  useEffect(() => {
    const shouldLockScroll = isPaused && !isClosing;
    if (shouldLockScroll) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isPaused, isClosing]);

  if (!isPaused || isClosing) {
    return null;
  }

  const handleResumeBot = async () => {
    setIsResuming(true);
    try {
      await resumeBot();
      if (onResumeBot) {
        onResumeBot();
      }
    } finally {
      setIsResuming(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      role="dialog"
      aria-modal="true"
      aria-labelledby="hard-stop-title"
      aria-describedby="hard-stop-description"
    >
      <div
        className="absolute inset-0 bg-black/80 backdrop-blur-sm"
        onClick={handleClose}
        aria-hidden="true"
      />

      <div
        ref={modalRef}
        className="relative bg-[#0A0A0A] border border-red-500/30 shadow-2xl max-w-md w-full mx-4 p-6"
        data-testid="budget-hard-stop-modal"
      >
        <div className="text-center mb-6">
          <div className="w-16 h-16 mx-auto mb-4 flex items-center justify-center bg-red-500/20 border border-red-500/30">
            <span className="text-3xl">⛔</span>
          </div>
          <h2
            id="hard-stop-title"
            className="text-xl font-bold text-red-400 font-['Space_Grotesk'] uppercase tracking-wide mb-2"
          >
            Bot Paused
          </h2>
          <p id="hard-stop-description" className="text-white/60 font-mono text-sm">
            {pauseReason}
          </p>
        </div>

        <div className="bg-red-500/10 border border-red-500/20 p-4 mb-6">
          {budgetCap !== null && budgetCap !== undefined ? (
            <>
              <div className="flex justify-between mb-2">
                <span className="text-white/60 font-mono text-xs">Current Budget:</span>
                <span className="font-bold text-white font-mono">${budgetCap.toFixed(2)}</span>
              </div>
              <div className="flex justify-between mb-2">
                <span className="text-white/60 font-mono text-xs">Spent:</span>
                <span className="font-bold text-red-400 font-mono">${monthlySpend.toFixed(2)}</span>
              </div>
              <div className="flex justify-between pt-2 border-t border-red-500/20">
                <span className="text-white/60 font-mono text-xs">Status:</span>
                <span className="font-bold text-red-400 font-mono uppercase tracking-wide">Budget Exceeded</span>
              </div>
            </>
          ) : (
            <>
              <div className="flex justify-between mb-2">
                <span className="text-white/60 font-mono text-xs">Spent:</span>
                <span className="font-bold text-red-400 font-mono">${monthlySpend.toFixed(2)}</span>
              </div>
              <div className="flex justify-between pt-2 border-t border-red-500/20">
                <span className="text-white/60 font-mono text-xs">Status:</span>
                <span className="font-bold text-emerald-400 font-mono uppercase tracking-wide">No Budget Limit - Ready to Resume</span>
              </div>
            </>
          )}
        </div>

        <p className="text-xs text-white/40 font-mono mb-6 text-center leading-relaxed">
          {budgetCap !== null && budgetCap !== undefined
            ? 'Your bot is not responding to customer messages. Increase your budget above your current spend to resume operations.'
            : 'Your bot was paused but now has no budget limit. You can resume operations immediately.'}
        </p>

        <div className="flex flex-col gap-3">
          <button
            ref={firstFocusableRef}
            onClick={handleIncreaseBudget}
            className="w-full px-4 py-3 bg-emerald-500 text-black text-[10px] font-bold font-mono uppercase tracking-[2px]
                       hover:bg-emerald-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/50
                       focus:ring-offset-2 focus:ring-offset-[#0A0A0A] transition-colors"
            aria-label="Increase budget to resume bot"
          >
            Increase Budget
          </button>

          <button
            ref={lastFocusableRef}
            onClick={handleResumeBot}
            disabled={!canResume || isResuming}
            className={`w-full px-4 py-3 text-[10px] font-bold font-mono uppercase tracking-[2px] transition-colors
                        focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-[#0A0A0A]
                        ${
                          canResume
                            ? 'bg-blue-500 text-white hover:bg-blue-600 focus:ring-blue-500/50'
                            : 'bg-white/10 text-white/40 cursor-not-allowed border border-white/10'
                        }`}
            aria-label="Resume bot operations"
            aria-disabled={!canResume}
          >
            {isResuming ? 'Resuming...' : canResume ? 'Resume Bot' : 'Resume Bot (requires budget increase)'}
          </button>
        </div>

        {onClose && (
          <button
            onClick={handleClose}
            className="absolute top-4 right-4 text-white/40 hover:text-white/60
                       focus:outline-none focus:ring-2 focus:ring-white/30 rounded"
            aria-label="Close modal"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        )}
      </div>
    </div>
  );
}
