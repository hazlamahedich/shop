/**
 * Budget Recommendation Display Component
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

  // Fetch budget recommendation on mount using the store/service layer
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
        // Use the existing store method instead of direct fetch
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
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
        <div className="animate-pulse flex items-start space-x-3">
          <div className="w-6 h-6 bg-blue-300 rounded-full"></div>
          <div className="flex-1 space-y-2">
            <div className="h-4 bg-blue-300 rounded w-3/4"></div>
            <div className="h-3 bg-blue-200 rounded w-full"></div>
            <div className="h-3 bg-blue-200 rounded w-1/2"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-xl p-4">
        <div className="flex items-start space-x-3">
          <AlertCircle className="text-gray-400 mt-0.5" size={20} />
          <div className="flex-1">
            <p className="text-sm text-gray-600">Unable to load budget recommendation.</p>
            <button
              onClick={fetchRecommendation}
              className="text-sm text-blue-600 hover:text-blue-700 mt-1"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!recommendation) {
    return null;
  }

  return (
    <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-xl p-5">
      <div className="flex items-start space-x-3">
        <div className="flex-shrink-0">
          <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
            <Lightbulb className="text-blue-600" size={20} />
          </div>
        </div>

        <div className="flex-1 min-w-0">
          <h4 className="text-sm font-semibold text-gray-900 mb-1">Budget Recommendation</h4>

          <div className="mt-3 space-y-2">
            <div className="flex items-baseline justify-between">
              <span className="text-sm text-gray-600">Recommended Monthly Budget:</span>
              <span className="text-xl font-bold text-blue-700">
                {formatCost(recommendation.recommendedBudget, 2)}
              </span>
            </div>

            <div className="flex items-baseline justify-between text-xs">
              <span className="text-gray-500">Current daily avg:</span>
              <span className="text-gray-700 font-medium">
                {formatCost(recommendation.currentAvgDailyCost, 4)}
              </span>
            </div>

            <div className="flex items-baseline justify-between text-xs">
              <span className="text-gray-500">Projected monthly:</span>
              <span className="text-gray-700 font-medium">
                {formatCost(recommendation.projectedMonthlySpend, 2)}
              </span>
            </div>
          </div>

          <p className="text-xs text-gray-600 mt-3 leading-relaxed">{recommendation.rationale}</p>

          <div className="mt-4 flex items-center space-x-2">
            <button
              onClick={handleApplyRecommendation}
              disabled={isApplying}
              className="inline-flex items-center px-3 py-1.5 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isApplying ? (
                <>
                  <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full mr-2" />
                  Applying...
                </>
              ) : (
                <>
                  <CheckCircle size={16} className="mr-1.5" />
                  Apply Recommendation
                </>
              )}
            </button>

            <button
              onClick={() => {
                // Handle "No limit" option
                if (onApplyRecommendation) {
                  onApplyRecommendation(0); // 0 signals no limit, handled by parent
                } else {
                  // Use the existing store method instead of direct fetch
                  updateMerchantSettings(null)
                    .then(() => {
                      toast('Budget cap removed. No limit set.', 'success');
                    })
                    .catch(() => {
                      toast('Failed to remove budget cap', 'error');
                    });
                }
              }}
              className="px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              No Limit
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BudgetRecommendationDisplay;
