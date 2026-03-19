/**
 * Budget Projection Display Component - Industrial Technical Dashboard
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
  budgetProgress: BudgetProgress | null;
  loading?: boolean;
  className?: string;
}

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

  if (loading) {
    return (
      <div className={`bg-[#0A0A0A] border border-emerald-500/15 p-6 ${className}`}>
        <div className="animate-pulse">
          <div className="h-6 bg-white/10 w-1/3 mb-4"></div>
          <div className="space-y-3">
            <div className="h-16 bg-white/10"></div>
            <div className="h-16 bg-white/10"></div>
          </div>
        </div>
      </div>
    );
  }

  if (!budgetProgress) {
    return (
      <div className={`bg-[#0A0A0A] border border-emerald-500/15 p-6 ${className}`}>
        <h3 className="text-sm font-bold text-white font-['Space_Grotesk'] uppercase tracking-wide mb-2">Budget Projection</h3>
        <p className="text-sm text-white/40 font-mono">Unable to load projection data</p>
      </div>
    );
  }

  const { daysSoFar, daysInMonth, budgetCap, projectionAvailable } = budgetProgress;
  const { level, dailyAverage, projectedSpend, projectionText, projectionSubtext } =
    displayValues;

  const levelStyles = {
    warning: {
      border: 'border-orange-500/30',
      text: 'text-orange-300',
      iconColor: 'text-orange-400',
      iconBg: 'bg-orange-500/15',
    },
    info: {
      border: 'border-blue-500/30',
      text: 'text-blue-300',
      iconColor: 'text-blue-400',
      iconBg: 'bg-blue-500/15',
    },
    unavailable: {
      border: 'border-white/10',
      text: 'text-white/40',
      iconColor: 'text-white/40',
      iconBg: 'bg-white/5',
    },
  };

  const styles = levelStyles[level];

  return (
    <div
      className={`bg-[#0A0A0A] border ${styles.border} p-6 ${className}`}
    >
      <div className="flex justify-between items-start mb-4">
        <h3 className="text-sm font-bold text-white font-['Space_Grotesk'] uppercase tracking-wide">Budget Projection</h3>
        <div className="flex items-center gap-2 text-[10px] text-white/40 font-mono">
          <Calendar size={14} className="text-emerald-500/60" />
          <span>Day {daysSoFar} of {daysInMonth}</span>
        </div>
      </div>

      <div className="space-y-4">
        <div className={`p-4 ${styles.iconBg} border-l-2 ${styles.border}`}>
          <div className="flex items-center gap-3 mb-2">
            <TrendingUp size={18} className={styles.iconColor} />
            <p className={`text-sm font-bold ${styles.text} font-mono`}>
              {projectionText}
            </p>
          </div>
          <p className="text-xs text-white/40 font-mono ml-7">
            {projectionSubtext}
          </p>
        </div>

        {projectionAvailable && dailyAverage !== null && projectedSpend !== null && (
          <div className="grid grid-cols-2 gap-4">
            <div className="p-3 bg-white/5 border border-white/10">
              <p className="text-[10px] text-white/40 font-mono uppercase tracking-[2px] mb-1">Daily Average</p>
              <p className="text-lg font-bold text-white font-mono">{formatCost(dailyAverage, 2)}</p>
            </div>
            <div className="p-3 bg-white/5 border border-white/10">
              <p className="text-[10px] text-white/40 font-mono uppercase tracking-[2px] mb-1">Projected Total</p>
              <p className={`text-lg font-bold font-mono ${level === 'warning' ? 'text-orange-400' : 'text-emerald-400'}`}>
                {formatCost(projectedSpend, 2)}
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default BudgetProjection;
