/**
 * Budget Progress Bar Component
 *
 * Displays visual progress of monthly budget usage with color coding:
 * - Green: < 50% of budget used
 * - Yellow: 50-80% of budget used
 * - Red: >= 80% of budget used
 *
 * Story 3-7: Visual Budget Progress
 * AC: 1 - Visual progress bar showing current spend vs budget cap
 */

import { useMemo } from 'react';
import type { BudgetProgress } from '../../types/cost';
import { formatCost } from '../../types/cost';

interface BudgetProgressBarProps {
  /**
   * Budget progress data from API
   */
  budgetProgress: BudgetProgress | null;
  /**
   * Loading state
   */
  loading?: boolean;
  /**
   * Optional CSS class name
   */
  className?: string;
}

/**
 * Get color classes based on budget status
 */
const getStatusColors = (status: BudgetProgress['budgetStatus']) => {
  switch (status) {
    case 'green':
      return {
        bg: 'bg-green-500',
        bgLight: 'bg-green-500/10',
        text: 'text-green-400',
        border: 'border-green-500/20',
        bgHover: 'hover:bg-green-600',
      };
    case 'yellow':
      return {
        bg: 'bg-yellow-500',
        bgLight: 'bg-yellow-500/10',
        text: 'text-yellow-400',
        border: 'border-yellow-500/20',
        bgHover: 'hover:bg-yellow-600',
      };
    case 'red':
      return {
        bg: 'bg-red-500',
        bgLight: 'bg-red-500/10',
        text: 'text-red-400',
        border: 'border-red-500/20',
        bgHover: 'hover:bg-red-600',
      };
    case 'no_limit':
      return {
        bg: 'bg-white/20',
        bgLight: 'bg-white/[0.03]',
        text: 'text-white/60',
        border: 'border-white/10',
        bgHover: 'hover:bg-white/30',
      };
    default:
      return {
        bg: 'bg-white/20',
        bgLight: 'bg-white/[0.03]',
        text: 'text-white/60',
        border: 'border-white/10',
        bgHover: 'hover:bg-white/30',
      };
  }
};

/**
 * Get status text description
 */
const getStatusText = (
  status: BudgetProgress['budgetStatus'],
  percentage: number | null
): string => {
  if (status === 'no_limit') {
    return 'No budget limit set';
  }
  if (percentage === null) {
    return 'Budget status unavailable';
  }

  switch (status) {
    case 'green':
      return 'On track - well within budget';
    case 'yellow':
      return 'Caution - more than half budget used';
    case 'red':
      return 'Warning - approaching budget limit';
    default:
      return '';
  }
};

export const BudgetProgressBar: React.FC<BudgetProgressBarProps> = ({
  budgetProgress,
  loading = false,
  className = '',
}) => {
  // Calculate display values
  const displayValues = useMemo(() => {
    if (!budgetProgress) {
      return {
        percentage: 0,
        clampedPercentage: 0,
        remaining: 0,
        statusText: 'Loading budget data...',
        colors: getStatusColors('no_limit'),
      };
    }

    const { monthlySpend, budgetCap, budgetPercentage, budgetStatus } = budgetProgress;

    // Handle no limit case
    if (budgetCap === null) {
      return {
        percentage: 0,
        clampedPercentage: 0,
        remaining: 0,
        statusText: getStatusText(budgetStatus, budgetPercentage),
        colors: getStatusColors(budgetStatus),
      };
    }

    const percentage = budgetPercentage ?? 0;
    const remaining = Math.max(0, budgetCap - monthlySpend);

    return {
      percentage,
      clampedPercentage: Math.min(Math.max(percentage, 0), 100),
      remaining,
      statusText: getStatusText(budgetStatus, budgetPercentage),
      colors: getStatusColors(budgetStatus),
    };
  }, [budgetProgress]);

  // Loading skeleton
  if (loading) {
    return (
      <div className={`bg-white/[0.03] p-6 rounded-xl border border-white/10 shadow-sm ${className}`}>
        <div className="animate-pulse">
          <div className="h-6 bg-white/10 rounded w-1/3 mb-4"></div>
          <div className="h-4 bg-white/10 rounded w-full mb-2"></div>
          <div className="h-8 bg-white/10 rounded w-full"></div>
        </div>
      </div>
    );
  }

  // No data state
  if (!budgetProgress) {
    return (
      <div className={`bg-white/[0.03] p-6 rounded-xl border border-white/10 shadow-sm ${className}`}>
        <h3 className="font-bold text-white/80 mb-2">Budget Progress</h3>
        <p className="text-sm text-white/50">Unable to load budget data</p>
      </div>
    );
  }

  const { monthlySpend, budgetCap } = budgetProgress;
  const { clampedPercentage, remaining, statusText, colors } = displayValues;

  return (
    <div
      className={`bg-white p-6 rounded-xl border ${colors.border} shadow-sm ${className}`}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-bold text-white/80">Budget Progress</h3>
        <div className="flex items-center space-x-2">
          {/* Status indicator dot */}
          <span
            className={`w-3 h-3 rounded-full ${colors.bg} ${budgetProgress.budgetStatus === 'red' ? 'animate-pulse' : ''}`}
            aria-hidden="true"
          />
          <span className={`text-xs font-medium ${colors.text}`}>
            {statusText}
          </span>
        </div>
      </div>

      {/* Spend Display */}
      <div className="mb-4">
        {budgetCap === null ? (
          <div className="text-center py-4 bg-white/[0.03] rounded-lg border border-white/10">
            <p className="text-lg font-bold text-white/80">
              {formatCost(monthlySpend, 2)} spent this month
            </p>
            <div className="flex items-center justify-center mt-2 text-white/50">
              <span className="text-sm">No budget limit</span>
              <span className="mx-2 text-white/20">|</span>
              <span className="text-sm text-white/50">Unlimited spending</span>
            </div>
          </div>
        ) : (
          <div className="flex justify-between items-end">
            <div>
              <p className="text-sm text-white/50">Monthly spend</p>
              <p className="text-2xl font-bold text-white/80">
                {formatCost(monthlySpend, 2)}
              </p>
            </div>
            <div className="text-right">
              <p className="text-sm text-white/50">Budget cap</p>
              <p className="text-lg font-bold text-white/70">
                {formatCost(budgetCap, 2)}
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Progress Bar */}
      {budgetCap !== null && (
        <div className="mb-4">
          {/* ARIA: Progress meter with proper accessibility */}
          <div
            role="progressbar"
            aria-valuenow={Math.round(clampedPercentage)}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label={`Budget progress: ${Math.round(clampedPercentage)}% of ${formatCost(budgetCap, 2)} used`}
            className="relative"
          >
            {/* Background track */}
            <div className="w-full bg-white/[0.05] rounded-full h-4 overflow-hidden">
              {/* Animated progress fill */}
              <div
                className={`h-full ${colors.bg} ${colors.bgHover} transition-all duration-500 ease-out rounded-full`}
                style={{ width: `${clampedPercentage}%` }}
              />
            </div>
          </div>

          {/* Percentage text */}
          <div className="flex justify-between mt-2">
            <span className={`text-sm font-medium ${colors.text}`}>
              {clampedPercentage.toFixed(1)}% of budget used
            </span>
            {remaining > 0 && (
              <span className="text-sm text-white/50">
                {formatCost(remaining, 2)} remaining
              </span>
            )}
          </div>
        </div>
      )}

      {/* Alert for high usage */}
      {budgetProgress.budgetStatus === 'red' && budgetCap !== null && (
        <div
          className={`mt-4 p-3 ${colors.bgLight} rounded-lg border ${colors.border}`}
          role="alert"
        >
          <p className={`text-sm ${colors.text} font-medium`}>
            ⚠️ You've used {clampedPercentage.toFixed(1)}% of your monthly budget.
            Consider reducing usage or increasing your budget cap.
          </p>
        </div>
      )}
    </div>
  );
};

export default BudgetProgressBar;
