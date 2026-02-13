/**
 * BudgetWarningBanner Component
 *
 * Displays warning banner when budget usage reaches 80%+
 * Story 3-8: Budget Alert Notifications
 *
 * Color coding:
 * - Yellow (#FEF3C7) for 80-94%
 * - Red (#FEE2E2) for 95%+
 */

import { useState, useEffect } from 'react';
import { useCostTrackingStore } from '../../stores/costTrackingStore';

const DISMISS_KEY = 'budget_warning_dismissed';
const DISMISS_DURATION_MS = 24 * 60 * 60 * 1000; // 24 hours

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

  const budgetCap = merchantSettings?.budgetCap ?? merchantSettings?.budget_cap;
  const totalCost = costSummary?.totalCostUsd ?? 0;

  // No warning if no budget cap set (unlimited)
  if (budgetCap === null || budgetCap === undefined) {
    return null;
  }

  const budgetPercentage = budgetCap && budgetCap > 0 ? (totalCost / budgetCap) * 100 : 0;

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

  if (budgetPercentage < 80 || isDismissed) {
    return null;
  }

  const isCritical = budgetPercentage >= 95;
  const bgColor = isCritical ? 'bg-red-100' : 'bg-yellow-100';
  const borderColor = isCritical ? 'border-red-400' : 'border-yellow-400';
  const textColor = isCritical ? 'text-red-800' : 'text-yellow-800';

  const handleDismiss = () => {
    localStorage.setItem(DISMISS_KEY, Date.now().toString());
    setIsDismissed(true);
  };

  return (
    <div
      className={`${bgColor} ${borderColor} border-l-4 p-4 mb-4`}
      role="alert"
      aria-live="polite"
      data-testid="budget-warning-banner"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <span className="text-2xl mr-3" role="img" aria-label="Warning">
            ⚠️
          </span>
          <div>
            <p className={`font-bold ${textColor}`}>
              Budget Alert: {Math.round(budgetPercentage)}% of your ${budgetCap?.toFixed(2)} budget
              used
            </p>
            {costSummary?.dailyBreakdown && costSummary.dailyBreakdown.length > 0 && (
              <p className={`${textColor} text-sm opacity-80`}>
                At current rate, you may exceed your budget this month.
              </p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={onViewDetails}
            className="text-sm text-gray-600 hover:text-gray-800 underline"
            aria-label="View spending details"
          >
            View Details
          </button>
          <button
            onClick={onIncreaseBudget}
            className={`px-4 py-2 rounded font-medium ${
              isCritical
                ? 'bg-red-600 text-white hover:bg-red-700'
                : 'bg-yellow-600 text-white hover:bg-yellow-700'
            }`}
            aria-label="Increase budget"
          >
            Increase Budget
          </button>
          {!isCritical && (
            <button
              onClick={handleDismiss}
              className="ml-2 text-gray-500 hover:text-gray-700"
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
