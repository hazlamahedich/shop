/**
 * BotPausedBanner Component - Industrial Technical Dashboard
 *
 * Displays critical banner when bot is paused due to budget limit
 * NO dismiss option - requires action
 * Story 3-8: Budget Alert Notifications
 */

import { useCostTrackingStore } from '../../stores/costTrackingStore';

interface BotPausedBannerProps {
  onIncreaseBudget?: () => void;
  onViewSpending?: () => void;
  onResumeBot?: () => void;
}

export function BotPausedBanner({ onIncreaseBudget, onViewSpending, onResumeBot }: BotPausedBannerProps) {
  const botStatus = useCostTrackingStore((state) => state.botStatus);
  const merchantSettings = useCostTrackingStore((state) => state.merchantSettings);
  const resumeBot = useCostTrackingStore((state) => state.resumeBot);

  if (!botStatus?.isPaused) {
    return null;
  }

  const budgetCap = merchantSettings?.budgetCap ?? botStatus?.budgetCap;
  const canResumeWithNoLimit = budgetCap === null || budgetCap === undefined;

  const getPausedDuration = () => {
    return 'Bot is currently paused';
  };

  const handleResumeBot = async () => {
    await resumeBot();
    if (onResumeBot) {
      onResumeBot();
    }
  };

  const handleIncreaseBudget = async () => {
    if (onIncreaseBudget) {
      onIncreaseBudget();
    }
  };

  return (
    <div
      className="bg-red-500/10 border-l-2 border-red-500/50 p-4 mb-4"
      role="alert"
      aria-live="assertive"
      data-testid="bot-paused-banner"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <div className="w-10 h-10 flex items-center justify-center bg-red-500/20 border border-red-500/30 mr-4">
            <span className="text-lg font-bold font-mono text-red-400">⛔</span>
          </div>
          <div>
            <p className="font-bold text-red-300 font-['Space_Grotesk'] uppercase tracking-wide text-sm">
              Bot Paused: {botStatus.pauseReason || 'Budget limit reached'}
            </p>
            <p className="text-red-400/80 text-xs font-mono mt-1">
              {getPausedDuration()} • Your bot is not responding to customer messages
            </p>
            {budgetCap !== null && budgetCap !== undefined && (
              <p className="text-red-400/60 text-xs font-mono mt-1">
                Current budget: ${budgetCap.toFixed(2)} | Spent: $
                {botStatus.monthlySpend?.toFixed(2) ?? '0.00'}
              </p>
            )}
            {canResumeWithNoLimit && (
              <p className="text-emerald-400 text-xs font-mono font-bold mt-1">
                ✓ No budget limit set - you can resume your bot
              </p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={onViewSpending}
            className="text-xs text-white/40 hover:text-white/60 font-mono underline underline-offset-2"
            aria-label="View spending details"
          >
            View Spending
          </button>
          {canResumeWithNoLimit ? (
            <button
              onClick={handleResumeBot}
              className="px-4 py-2 bg-emerald-500 text-black text-[10px] font-bold font-mono uppercase tracking-[2px] hover:bg-emerald-400 transition-colors"
              aria-label="Resume bot"
            >
              Resume Bot
            </button>
          ) : (
            <button
              onClick={handleIncreaseBudget}
              className="px-4 py-2 bg-red-500 text-white text-[10px] font-bold font-mono uppercase tracking-[2px] hover:bg-red-600 transition-colors"
              aria-label="Increase budget to resume bot"
            >
              Increase Budget
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
