/**
 * BudgetWarningBanner Component - Industrial Technical Dashboard
 *
 * Displays warning banner when budget usage reaches 80%+
 * Story 3-8: Budget Alert Notifications
 *
 * Color coding:
 * - Orange for 80-94%
 * - Red for 95%+
 */

import { useState, useEffect } from 'react';
import { useCostTrackingStore } from '../../stores/costTrackingStore';

const DISMISS_KEY = 'budget_warning_dismissed';
const DISMISS_DURATION_MS = 24 * 60 * 60 * 1000;

interface BudgetWarningBannerProps {
  onIncreaseBudget?: () => void;
  onViewDetails?: () => void;
}

export function BudgetWarningBanner({
  onIncreaseBudget,
  onViewDetails,
}: BudgetWarningBannerProps) {
  const [isDismissed, setIsDismissed] = useState(false);
  const costSummary = useCostTrackingStore((state) => state.costSummary);
  const merchantSettings = useCostTrackingStore((state) => state.merchantSettings);

  useEffect(() => {
    const dismissedAt = localStorage.getItem(DISMISS_KEY);
    if (dismissedAt) {
      const dismissedTime = parseInt(dismissedAt, 10);
      if (Date.now() - dismissedTime < DISMISS_DURATION_MS) {
        setIsDismissed(true);
      } else {
        localStorage.removeItem(DISMISS_KEY);
      }
    }
  }, []);

  const budgetCap = merchantSettings?.budgetCap ?? merchantSettings?.budget_cap;
  const totalCost = costSummary?.totalCostUsd ?? 0;

  if (budgetCap === null || budgetCap === undefined) {
    return null;
  }

  const budgetPercentage = budgetCap && budgetCap > 0 ? (totalCost / budgetCap) * 100 : 0;

  if (budgetPercentage < 80 || isDismissed) {
    return null;
  }

  const isCritical = budgetPercentage >= 95;
  const bgColor = isCritical ? 'bg-red-500/10' : 'bg-orange-500/10';
  const borderColor = isCritical ? 'border-red-500/30' : 'border-orange-500/30';
  const textColor = isCritical ? 'text-red-300' : 'text-orange-300';
  const iconColor = isCritical ? 'text-red-400' : 'text-orange-400';
  const btnBg = isCritical ? 'bg-red-500' : 'bg-orange-500';
  const btnHover = isCritical ? 'hover:bg-red-600' : 'hover:bg-orange-600';

  const handleDismiss = () => {
    localStorage.setItem(DISMISS_KEY, Date.now().toString());
    setIsDismissed(true);
  };

  return (
    <div
      className={`${bgColor} ${borderColor} border-l-2 p-4 mb-4`}
      role="alert"
      aria-live="polite"
      data-testid="budget-warning-banner"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <div className={`w-10 h-10 flex items-center justify-center ${bgColor} border ${borderColor} mr-4`}>
            <span className={`text-lg font-bold font-mono ${iconColor}`}>
              {isCritical ? '!' : '⚠'}
            </span>
          </div>
          <div>
            <p className={`font-bold ${textColor} font-['Space_Grotesk'] uppercase tracking-wide text-sm`}>
              Budget Alert: {Math.round(budgetPercentage)}% of ${budgetCap?.toFixed(2)} budget used
            </p>
            {costSummary?.dailyBreakdown && costSummary.dailyBreakdown.length > 0 && (
              <p className={`${textColor}/60 text-xs font-mono mt-1`}>
                At current rate, you may exceed your budget this month.
              </p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={onViewDetails}
            className="text-xs text-white/40 hover:text-white/60 font-mono underline underline-offset-2"
            aria-label="View spending details"
          >
            View Details
          </button>
          <button
            onClick={onIncreaseBudget}
            className={`px-4 py-2 text-[10px] font-bold ${btnBg} text-white font-mono uppercase tracking-[2px] ${btnHover} transition-colors`}
            aria-label="Increase budget"
          >
            Increase Budget
          </button>
          {!isCritical && (
            <button
              onClick={handleDismiss}
              className="w-8 h-8 flex items-center justify-center text-white/40 hover:text-white/60 hover:bg-white/10 transition-colors"
              aria-label="Dismiss warning for 24 hours"
            >
              ✕
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
