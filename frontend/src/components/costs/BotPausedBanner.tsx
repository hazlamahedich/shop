/**
 * BotPausedBanner Component
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

  // Check if budget cap is null (no limit) - bot can resume
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
      className="bg-red-100 border-l-4 border-red-500 p-4 mb-4"
      role="alert"
      aria-live="assertive"
      data-testid="bot-paused-banner"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <span className="text-2xl mr-3" role="img" aria-label="Bot Paused">
            🛑
          </span>
          <div>
            <p className="font-bold text-red-800">
              Bot Paused: {botStatus.pauseReason || 'Budget limit reached'}
            </p>
            <p className="text-red-700 text-sm">
              {getPausedDuration()} • Your bot is not responding to customer messages
            </p>
            {budgetCap !== null && budgetCap !== undefined && (
              <p className="text-red-700 text-sm">
                Current budget: ${budgetCap.toFixed(2)} | Spent: $
                {botStatus.monthlySpend?.toFixed(2) ?? '0.00'}
              </p>
            )}
            {canResumeWithNoLimit && (
              <p className="text-green-700 text-sm font-medium mt-1">
                ✓ No budget limit set - you can resume your bot
              </p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={onViewSpending}
            className="text-sm text-red-700 hover:text-red-900 underline"
            aria-label="View spending details"
          >
            View Spending
          </button>
          {canResumeWithNoLimit ? (
            <button
              onClick={handleResumeBot}
              className="px-4 py-2 bg-green-600 text-white rounded font-medium hover:bg-green-700 focus:ring-2 focus:ring-green-500 focus:ring-offset-2"
              aria-label="Resume bot"
            >
              Resume Bot
            </button>
          ) : (
            <button
              onClick={handleIncreaseBudget}
              className="px-4 py-2 bg-red-600 text-white rounded font-medium hover:bg-red-700 focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
              aria-label="Increase budget to resume bot"
            >
              Increase Budget to Resume
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
