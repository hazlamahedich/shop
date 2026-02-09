/**
 * Budget Projection Display Component
 *
 * Displays monthly spend projection based on current daily average:
 * - Shows days so far and days in month
 * - Displays daily average spend
 * - Shows projected monthly spend
 * - Warns if projection exceeds budget cap
 *
 * Story 3-7: Visual Budget Progress
 * AC: 2 - Monthly spend projection display
 */

import { useMemo } from 'react';
import { TrendingUp, Calendar, Activity } from 'lucide-react';
import type { BudgetProgress } from '../../types/cost';
import { formatCost } from '../../types/cost';

interface BudgetProjectionProps {
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
 * Get projection warning level
 */
const getProjectionLevel = (
  projectedExceedsBudget: boolean,
  projectionAvailable: boolean
): 'warning' | 'info' | 'unavailable' => {
  if (!projectionAvailable) return 'unavailable';
  if (projectedExceedsBudget) return 'warning';
  return 'info';
};

export const BudgetProjection: React.FC<BudgetProjectionProps> = ({
  budgetProgress,
  loading = false,
  className = '',
}) => {
  // Calculate display values
  const displayValues = useMemo(() => {
    if (!budgetProgress) {
      return {
        level: 'unavailable' as const,
        dailyAverage: null,
        projectedSpend: null,
        projectionText: 'Insufficient data for projection',
        projectionSubtext: 'Need at least 3 days of cost data',
      };
    }

    const {
      dailyAverage,
      projectedSpend,
      projectionAvailable,
      projectedExceedsBudget,
      daysSoFar,
      daysInMonth,
    } = budgetProgress;

    const level = getProjectionLevel(projectedExceedsBudget, projectionAvailable);

    if (!projectionAvailable) {
      return {
        level,
        dailyAverage,
        projectedSpend,
        projectionText: 'Insufficient data for projection',
        projectionSubtext: `Need at least 3 days of data (currently ${daysSoFar} day${
          daysSoFar !== 1 ? 's' : ''
        })`,
      };
    }

    if (projectedExceedsBudget) {
      return {
        level: 'warning',
        dailyAverage,
        projectedSpend,
        projectionText: `Projected to exceed budget by ${formatCost(
          (projectedSpend ?? 0) - (budgetProgress.budgetCap ?? 0),
          2
        )}`,
        projectionSubtext: `Based on current daily average of ${formatCost(
          dailyAverage ?? 0,
          2
        )}`,
      };
    }

    return {
      level: 'info',
      dailyAverage,
      projectedSpend,
      projectionText: `On track to spend ${formatCost(projectedSpend ?? 0, 2)} this month`,
      projectionSubtext: `Based on daily average of ${formatCost(dailyAverage ?? 0, 2)}`,
    };
  }, [budgetProgress]);

  // Loading skeleton
  if (loading) {
    return (
      <div className={`bg-white p-6 rounded-xl border border-gray-200 shadow-sm ${className}`}>
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="space-y-3">
            <div className="h-16 bg-gray-200 rounded"></div>
            <div className="h-16 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  // No data state
  if (!budgetProgress) {
    return (
      <div className={`bg-white p-6 rounded-xl border border-gray-200 shadow-sm ${className}`}>
        <h3 className="font-bold text-gray-900 mb-2">Budget Projection</h3>
        <p className="text-sm text-gray-500">Unable to load projection data</p>
      </div>
    );
  }

  const { daysSoFar, daysInMonth, budgetCap, projectionAvailable } = budgetProgress;
  const { level, dailyAverage, projectedSpend, projectionText, projectionSubtext } =
    displayValues;

  // Determine styling based on level
  const levelStyles = {
    warning: {
      bg: 'bg-amber-50',
      border: 'border-amber-200',
      text: 'text-amber-800',
      iconColor: 'text-amber-600',
      iconBg: 'bg-amber-100',
    },
    info: {
      bg: 'bg-blue-50',
      border: 'border-blue-200',
      text: 'text-blue-800',
      iconColor: 'text-blue-600',
      iconBg: 'bg-blue-100',
    },
    unavailable: {
      bg: 'bg-gray-50',
      border: 'border-gray-200',
      text: 'text-gray-600',
      iconColor: 'text-gray-500',
      iconBg: 'bg-gray-100',
    },
  };

  const styles = levelStyles[level];

  return (
    <div
      className={`bg-white p-6 rounded-xl border ${styles.border} shadow-sm ${className}`}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-bold text-gray-900">Monthly Projection</h3>
        {level === 'warning' && (
          <span className="flex items-center text-xs font-medium text-amber-600">
            <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse mr-1" />
            Action needed
          </span>
        )}
      </div>

      {/* Calendar Days */}
      <div className={`${styles.bg} rounded-lg p-4 mb-4 border ${styles.border}`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <div className={`p-2 rounded-lg ${styles.iconBg} mr-3`}>
              <Calendar size={18} className={styles.iconColor} />
            </div>
            <div>
              <p className="text-xs text-gray-600">Days in month</p>
              <p className="text-lg font-bold text-gray-900">
                {daysSoFar} / {daysInMonth}
              </p>
            </div>
          </div>
          <div className="text-right">
            <p className="text-xs text-gray-600">Progress</p>
            <p className="text-lg font-bold text-gray-900">
              {((daysSoFar / daysInMonth) * 100).toFixed(0)}%
            </p>
          </div>
        </div>
      </div>

      {/* Daily Average */}
      {projectionAvailable && dailyAverage !== null && (
        <div className="mb-4">
          <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <div className="flex items-center">
              <Activity size={16} className="text-gray-500 mr-2" />
              <span className="text-sm text-gray-600">Daily average</span>
            </div>
            <span className="text-lg font-bold text-gray-900">
              {formatCost(dailyAverage, 2)}
            </span>
          </div>
        </div>
      )}

      {/* Projection Display */}
      <div
        className={`${styles.bg} rounded-lg p-4 border ${styles.border} ${
          level === 'warning' ? 'border-l-4 border-l-amber-500' : ''
        }`}
      >
        <div className="flex items-start">
          <div className={`p-2 rounded-lg ${styles.iconBg} mr-3 flex-shrink-0`}>
            <TrendingUp size={18} className={styles.iconColor} />
          </div>
          <div className="flex-1">
            <p className={`text-sm font-medium ${styles.text}`}>
              {projectionText}
            </p>
            <p className="text-xs text-gray-600 mt-1">{projectionSubtext}</p>

            {/* Projected vs Budget comparison */}
            {level !== 'unavailable' && projectedSpend !== null && budgetCap !== null && (
              <div className="mt-3 pt-3 border-t border-gray-200">
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-gray-600">Projected spend</span>
                  <span className="font-medium text-gray-900">
                    {formatCost(projectedSpend, 2)}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full transition-all duration-500 ${
                      level === 'warning' ? 'bg-amber-500' : 'bg-blue-500'
                    }`}
                    style={{
                      width: `${Math.min((projectedSpend / budgetCap) * 100, 100)}%`,
                    }}
                  />
                </div>
                {level === 'warning' && (
                  <p className="text-xs text-amber-700 mt-2 font-medium">
                    This is{' '}
                    {(((projectedSpend - budgetCap) / budgetCap) * 100).toFixed(0)}
                    % over your budget
                  </p>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Recommendations */}
      {level === 'warning' && (
        <div className="mt-4 p-3 bg-amber-50 rounded-lg border border-amber-200">
          <p className="text-xs text-amber-800">
            <strong>Recommendation:</strong> Consider increasing your budget cap or
            optimizing your AI prompts to reduce token usage.
          </p>
        </div>
      )}
    </div>
  );
};

export default BudgetProjection;
