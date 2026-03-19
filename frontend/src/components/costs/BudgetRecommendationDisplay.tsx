/**
 * Budget Recommendation Display Component - Industrial Technical Dashboard
 *
 * Displays budget recommendation based on cost history:
 * - Shows recommended budget with rationale
 * - Apply recommendation button
 * - "No limit" option for removing budget cap
 *
 * Story 3-6: Budget Cap Configuration
 */

import { useState, useEffect } from 'react';
import { Lightbulb, CheckCircle, AlertCircle } from 'lucide-react';
import { useCostTrackingStore } from '../../stores/costTrackingStore';
import { formatCost } from '../../types/cost';
import { useToast } from '../../context/ToastContext';

interface BudgetRecommendationData {
  recommendedBudget: number;
  rationale: string;
  currentAvgDailyCost: number;
  projectedMonthlySpend: number;
}

interface BudgetRecommendationDisplayProps {
  onApplyRecommendation?: (budget: number) => void;
}

export const BudgetRecommendationDisplay = ({
  onApplyRecommendation,
}: BudgetRecommendationDisplayProps) => {
  const { toast } = useToast();
  const { getBudgetRecommendation, updateMerchantSettings } = useCostTrackingStore();
  const [recommendation, setRecommendation] = useState<BudgetRecommendationData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isApplying, setIsApplying] = useState(false);

  useEffect(() => {
    fetchRecommendation();
  }, []);

  const fetchRecommendation = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await getBudgetRecommendation();
      console.log('Budget recommendation response from store:', response);

      const data = response as any;

      if (!data) {
        throw new Error('No recommendation data received');
      }

      setRecommendation({
        recommendedBudget: data.recommendedBudget ?? data.recommended_budget,
        rationale: data.rationale,
        currentAvgDailyCost: data.currentAvgDailyCost ?? data.current_avg_daily_cost,
        projectedMonthlySpend: data.projectedMonthlySpend ?? data.projected_monthly_spend,
      });
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load recommendation';
      setError(errorMessage);
      console.error('Failed to fetch budget recommendation:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleApplyRecommendation = async () => {
    if (!recommendation) return;

    setIsApplying(true);

    try {
      if (onApplyRecommendation) {
        onApplyRecommendation(recommendation.recommendedBudget);
      } else {
        await updateMerchantSettings(recommendation.recommendedBudget);
        toast('Budget recommendation applied successfully', 'success');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to apply recommendation';
      toast(errorMessage, 'error');
    } finally {
      setIsApplying(false);
    }
  };

  if (isLoading) {
    return (
      <div className="px-10">
        <div className="bg-blue-500/5 border border-blue-500/15 p-4">
          <div className="animate-pulse flex items-start space-x-3">
            <div className="w-6 h-6 bg-blue-500/30"></div>
            <div className="flex-1 space-y-2">
              <div className="h-4 bg-blue-500/20 w-3/4"></div>
              <div className="h-3 bg-blue-500/10 w-full"></div>
              <div className="h-3 bg-blue-500/10 w-1/2"></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="px-10">
        <div className="bg-white/5 border border-white/10 p-4">
          <div className="flex items-start space-x-3">
            <AlertCircle className="text-white/40 mt-0.5" size={20} />
            <div className="flex-1">
              <p className="text-sm text-white/40 font-mono">Unable to load budget recommendation.</p>
              <button
                onClick={fetchRecommendation}
                className="text-sm text-blue-400 hover:text-blue-300 font-mono mt-1 underline underline-offset-2"
              >
                Retry
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!recommendation) {
    return null;
  }

  return (
    <div className="px-10">
      <div className="bg-gradient-to-r from-blue-500/5 to-indigo-500/5 border border-blue-500/15 p-5">
        <div className="flex items-start space-x-3">
          <div className="flex-shrink-0">
            <div className="w-10 h-10 bg-blue-500/15 border border-blue-500/30 flex items-center justify-center">
              <Lightbulb className="text-blue-400" size={20} />
            </div>
          </div>

          <div className="flex-1 min-w-0">
            <h4 className="text-sm font-bold text-white font-['Space_Grotesk'] uppercase tracking-wide mb-1">
              Budget Recommendation
            </h4>

            <div className="mt-3 space-y-2">
              <div className="flex items-baseline justify-between p-3 bg-blue-500/5 border border-blue-500/10">
                <span className="text-[10px] text-white/60 font-mono uppercase tracking-[2px]">Recommended Monthly Budget:</span>
                <span className="text-xl font-bold text-blue-400 font-mono">
                  {formatCost(recommendation.recommendedBudget, 2)}
                </span>
              </div>

              <div className="flex items-baseline justify-between text-xs px-3">
                <span className="text-white/40 font-mono">Current daily avg:</span>
                <span className="text-white/60 font-mono font-medium">
                  {formatCost(recommendation.currentAvgDailyCost, 4)}
                </span>
              </div>

              <div className="flex items-baseline justify-between text-xs px-3">
                <span className="text-white/40 font-mono">Projected monthly:</span>
                <span className="text-white/60 font-mono font-medium">
                  {formatCost(recommendation.projectedMonthlySpend, 2)}
                </span>
              </div>
            </div>

            <p className="text-xs text-white/50 font-mono mt-3 leading-relaxed">{recommendation.rationale}</p>

            <div className="mt-4 flex items-center space-x-2">
              <button
                onClick={handleApplyRecommendation}
                disabled={isApplying}
                className="inline-flex items-center px-4 py-2 text-[10px] font-bold text-white bg-blue-500 font-mono uppercase tracking-[2px] hover:bg-blue-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isApplying ? (
                  <>
                    <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full mr-2" />
                    Applying...
                  </>
                ) : (
                  <>
                    <CheckCircle size={14} className="mr-1.5" />
                    Apply Recommendation
                  </>
                )}
              </button>

              <button
                onClick={async () => {
                  if (onApplyRecommendation) {
                    onApplyRecommendation(0);
                  } else {
                    try {
                      await updateMerchantSettings(null as any);
                      toast('Budget cap removed. No limit set.', 'success');
                    } catch {
                      toast('Failed to remove budget cap', 'error');
                    }
                  }
                }}
                className="px-4 py-2 text-[10px] font-bold text-white/60 bg-white/5 border border-white/10 font-mono uppercase tracking-[2px] hover:bg-white/10 hover:text-white/80 transition-colors"
              >
                No Limit
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BudgetRecommendationDisplay;
