/**
 * CostComparisonCard - Displays cost comparison vs ManyChat
 *
 * Shows:
 * - Merchant's actual spend vs ManyChat estimate
 * - Savings amount and percentage
 * - Methodology tooltip on hover
 *
 * Story 3.9: Cost Comparison Display
 */

import { useState } from 'react';
import { CheckCircle, AlertTriangle, Info } from 'lucide-react';
import { useCostTrackingStore } from '../../stores/costTrackingStore';
import { formatCost } from '../../types/cost';

export function CostComparisonCard() {
  const { costSummary } = useCostTrackingStore();
  const [showTooltip, setShowTooltip] = useState(false);

  const comparison = costSummary?.costComparison;

  if (!comparison) {
    return null;
  }

  const {
    manyChatEstimate,
    savingsAmount,
    savingsPercentage,
    merchantSpend,
    methodology,
  } = comparison;

  const hasSavings = savingsAmount > 0;
  const hasNeutralOrNegativeSavings = savingsAmount <= 0;
  const safeManyChatEstimate = manyChatEstimate > 0 ? manyChatEstimate : 1;

  return (
    <div className="bg-white/[0.03] p-6 rounded-xl border border-white/10 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-bold text-gray-900">Cost Comparison</h3>
        <button
          onClick={() => setShowTooltip(!showTooltip)}
          className="text-white/40 hover:text-white/60 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 rounded"
          aria-label="View comparison methodology"
          aria-expanded={showTooltip}
        >
          <Info size={16} />
        </button>
      </div>

      {showTooltip && (
        <div className="mb-4 p-3 bg-white/[0.03] rounded-lg text-sm text-white/60 border border-white/10">
          {methodology}
        </div>
      )}

      <p className="text-white/60 mb-4">
        You spent{' '}
        <span className="font-bold text-white/80">
          {formatCost(merchantSpend, 4)}
        </span>{' '}
        this month vs.{' '}
        <span className="font-bold text-white/80">
          ~${manyChatEstimate.toFixed(0)}-{(manyChatEstimate * 1.5).toFixed(0)}
        </span>{' '}
        with ManyChat
      </p>

      {hasSavings ? (
        <div className="flex items-center gap-2 p-3 bg-green-500/10 rounded-lg border border-green-500/20">
          <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0" />
          <span className="font-semibold text-green-400">
            You saved {formatCost(savingsAmount, 4)} ({savingsPercentage.toFixed(0)}
            %)
          </span>
        </div>
      ) : hasNeutralOrNegativeSavings ? (
        <div className="flex items-center gap-2 p-3 bg-amber-500/10 rounded-lg border border-amber-500/20">
          <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0" />
          <span className="text-sm text-amber-300">
            Consider reviewing your LLM provider configuration for cost optimization
          </span>
        </div>
      ) : null}

      <div className="mt-4 space-y-3">
        <div>
          <div className="flex justify-between text-xs mb-1">
            <span className="font-medium text-white/60">Shop (You)</span>
            <span className="font-bold text-green-400">
              {formatCost(merchantSpend, 4)}
            </span>
          </div>
          <div className="w-full bg-white/[0.05] rounded-full h-3">
            <div
              className="bg-green-500 h-3 rounded-full transition-all duration-300"
              style={{
                width: `${Math.min((merchantSpend / (safeManyChatEstimate * 1.5)) * 100, 100)}%`,
              }}
            />
          </div>
        </div>

        <div>
          <div className="flex justify-between text-xs mb-1">
            <span className="font-medium text-white/60">ManyChat (Est.)</span>
            <span className="font-bold text-white/50">
              {formatCost(manyChatEstimate, 2)}
            </span>
          </div>
          <div className="w-full bg-white/[0.05] rounded-full h-3">
            <div
              className="bg-white/20 h-3 rounded-full transition-all duration-300"
              style={{ width: '100%' }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
