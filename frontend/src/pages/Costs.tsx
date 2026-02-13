/**
 * Costs Page - Real-time cost tracking and budget management
 *
 * Displays:
 * - Cost summary cards with period-over-period trends
 * - Daily spend chart with budget cap
 * - Date range filters
 * - Top conversations by cost
 * - Provider cost breakdown
 *
 * Story 3-5: Real-Time Cost Tracking
 */

import { useEffect, useState, useMemo } from 'react';
import { AlertCircle, Calendar, RefreshCw, BarChart3, Infinity } from 'lucide-react';
import { CostSummaryCards } from '../components/costs/CostSummaryCards';
import { BudgetConfiguration } from '../components/costs/BudgetConfiguration';
import { BudgetRecommendationDisplay } from '../components/costs/BudgetRecommendationDisplay';
import { BudgetWarningBanner } from '../components/costs/BudgetWarningBanner';
import { BotPausedBanner } from '../components/costs/BotPausedBanner';
import { BudgetHardStopModal } from '../components/costs/BudgetHardStopModal';
import { BudgetAlertConfig } from '../components/costs/BudgetAlertConfig';
import { useCostTrackingStore } from '../stores/costTrackingStore';
import { useToast } from '../context/ToastContext';
import { formatCost } from '../types/cost';

/**
 * Date range preset option
 */
interface DateRangePreset {
  label: string;
  dateFrom: string;
  dateTo?: string;
}

// Generate today's date in YYYY-MM-DD format
const getTodayDate = (): string => {
  const today = new Date();
  return today.toISOString().split('T')[0];
};

// Get date X days ago
const getDateDaysAgo = (days: number): string => {
  const date = new Date();
  date.setDate(date.getDate() - days);
  return date.toISOString().split('T')[0];
};

// Get first day of current month
const getFirstDayOfMonth = (): string => {
  const date = new Date();
  return new Date(date.getFullYear(), date.getMonth(), 1).toISOString().split('T')[0];
};

// Date range presets
const DATE_RANGE_PRESETS: DateRangePreset[] = [
  { label: 'Today', dateFrom: getTodayDate() },
  { label: 'Last 7 Days', dateFrom: getDateDaysAgo(7) },
  { label: 'Last 30 Days', dateFrom: getDateDaysAgo(30) },
  { label: 'This Month', dateFrom: getFirstDayOfMonth() },
];

// Default budget cap
const DEFAULT_BUDGET_CAP = 50;

const Costs = () => {
  const {
    costSummary,
    costSummaryLoading,
    costSummaryError,
    previousPeriodSummary,
    isPolling,
    pollingInterval,
    lastUpdate,
    fetchCostSummary,
    setCostSummaryParams,
    startPolling,
    stopPolling,
    getMerchantSettings,
    merchantSettings,
    merchantSettingsError,
    fetchBotStatus,
    botStatus,
    resumeBot,
  } = useCostTrackingStore();

  const [showHardStopModal, setShowHardStopModal] = useState(false);

  useEffect(() => {
    if (botStatus?.isPaused) {
      setShowHardStopModal(true);
    }
  }, [botStatus?.isPaused]);

  // Local state for date range inputs and budget cap
  const [dateFrom, setDateFrom] = useState<string>(getDateDaysAgo(30));
  const [dateTo, setDateTo] = useState<string>(getTodayDate());

  // Toast notification
  const { toast } = useToast();

  // Show merchant settings error
  useEffect(() => {
    if (merchantSettingsError) {
      toast(merchantSettingsError, 'error');
    }
  }, [merchantSettingsError, toast]);
  // Load merchant settings (budget cap) on mount
  useEffect(() => {
    getMerchantSettings();
    fetchBotStatus();
  }, [getMerchantSettings, fetchBotStatus]);

  // Start real-time polling on mount
  useEffect(() => {
    startPolling(undefined, pollingInterval);

    return () => {
      stopPolling();
    };
  }, [startPolling, stopPolling, pollingInterval]);

  // Handle date range preset click
  const handlePresetClick = (preset: DateRangePreset) => {
    setDateFrom(preset.dateFrom);
    setDateTo(preset.dateTo || getTodayDate());
  };

  // Handle custom date range change
  const handleDateRangeChange = () => {
    setCostSummaryParams({ dateFrom, dateTo });
    fetchCostSummary({ dateFrom, dateTo });
  };

  // Show error toasts from store state
  useEffect(() => {
    if (costSummaryError) {
      toast(costSummaryError, 'error');
    }
  }, [costSummaryError, toast]);

  // Clean up lint error about unused setPollingInterval
  // It was fixed earlier but let's double check imports if needed

  // Handle refresh
  const handleRefresh = () => {
    fetchCostSummary({ dateFrom, dateTo });
  };

  // Handle polling toggle
  const handleTogglePolling = () => {
    if (isPolling) {
      stopPolling();
    } else {
      startPolling(undefined, pollingInterval);
    }
  };

  // Calculate daily costs for chart
  const dailyData = useMemo(() => {
    if (!costSummary?.dailyBreakdown) return [];

    return costSummary.dailyBreakdown.map((day) => ({
      date: new Date(day.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      cost: day.totalCostUsd,
      requests: day.requestCount,
    }));
  }, [costSummary]);

  // Get max daily cost for chart scaling
  const maxDailyCost = useMemo(() => {
    const budgetCap = merchantSettings?.budgetCap ?? DEFAULT_BUDGET_CAP;
    if (dailyData.length === 0) return 1;
    return Math.max(...dailyData.map((d) => d.cost), budgetCap / 10);
  }, [dailyData, merchantSettings?.budgetCap]);

  // Get top conversations
  const topConversations = useMemo(() => {
    return costSummary?.topConversations?.slice(0, 5) || [];
  }, [costSummary]);

  // provider breakdown sorted by cost
  const providersByCost = useMemo(() => {
    if (!costSummary?.costsByProvider) return [];

    return Object.entries(costSummary.costsByProvider)
      .map(([name, data]) => ({ name, ...data }))
      .sort((a, b) => b.costUsd - a.costUsd);
  }, [costSummary]);

  // Daily spend data calculation

  // Comparison with ManyChat (estimated)
  const manyChatEstimated = useMemo(() => {
    if (!costSummary) return null;
    // ManyChat is estimated to be ~3.5x more expensive based on industry benchmarks
    return costSummary.totalCostUsd * 3.5;
  }, [costSummary]);

  const savings = useMemo(() => {
    if (!manyChatEstimated || !costSummary) return null;
    return manyChatEstimated - costSummary.totalCostUsd;
  }, [manyChatEstimated, costSummary]);

  // Check if budget cap is null/undefined (no limit set)
  const hasNoBudgetLimit = merchantSettings !== null && 
    merchantSettings !== undefined && 
    (merchantSettings?.budgetCap === null || merchantSettings?.budgetCap === undefined);

  return (
    <div className="space-y-6">
      {/* Hard Stop Modal (Story 3-8) - Shows when bot is paused at 100% */}
      <BudgetHardStopModal
        onIncreaseBudget={() => {
          const budgetSection = document.getElementById('budget-input');
          if (budgetSection) {
            budgetSection.focus();
            budgetSection.scrollIntoView({ behavior: 'smooth' });
          }
        }}
        onResumeBot={async () => {
          await resumeBot();
        }}
        onClose={() => setShowHardStopModal(false)}
      />

      {/* Bot Paused Banner (Story 3-8) - Show first if bot is paused */}
      <BotPausedBanner
        onIncreaseBudget={() => {
          const budgetSection = document.getElementById('budget-input');
          if (budgetSection) {
            budgetSection.focus();
            budgetSection.scrollIntoView({ behavior: 'smooth' });
          }
        }}
        onViewSpending={() => {
          window.scrollTo({ top: 0, behavior: 'smooth' });
        }}
      />

      {/* Budget Warning Banner (Story 3-8) - Show at 80%+ */}
      <BudgetWarningBanner
        onIncreaseBudget={() => {
          const budgetSection = document.getElementById('budget-input');
          if (budgetSection) {
            budgetSection.focus();
            budgetSection.scrollIntoView({ behavior: 'smooth' });
          }
        }}
        onViewDetails={() => {
          window.scrollTo({ top: 0, behavior: 'smooth' });
        }}
      />

      {/* No Budget Limit Banner - Show when budget cap is null */}
      {hasNoBudgetLimit && (
        <div className="bg-gradient-to-r from-amber-50 to-orange-50 border-2 border-amber-300 rounded-xl p-5 shadow-sm">
          <div className="flex items-center gap-4">
            <div className="flex-shrink-0 w-14 h-14 bg-amber-100 rounded-full flex items-center justify-center border-2 border-amber-200">
              <Infinity size={28} className="text-amber-600" strokeWidth={2.5} />
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-bold text-amber-900">Unlimited Spending Active</h3>
                <span className="px-2 py-0.5 bg-amber-200 text-amber-800 text-xs font-semibold rounded-full uppercase tracking-wide">
                  No Cap
                </span>
              </div>
              <p className="text-sm text-amber-700 mt-1">
                Your bot has no spending limit. Set a budget cap to receive alerts and prevent overspending.
              </p>
            </div>
            <button
              onClick={() => {
                const budgetSection = document.getElementById('budget-input');
                if (budgetSection) {
                  budgetSection.focus();
                  budgetSection.scrollIntoView({ behavior: 'smooth' });
                }
              }}
              className="px-5 py-2.5 bg-amber-600 text-white font-semibold rounded-lg hover:bg-amber-700 transition-colors shadow-sm"
            >
              Set Budget Cap
            </button>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-2xl sm:text-3xl font-bold text-gray-900">Costs & Budget</h2>
            {hasNoBudgetLimit && (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-amber-100 text-amber-800 text-sm font-bold rounded-full border border-amber-300 shadow-sm">
                <Infinity size={16} className="text-amber-600" />
                Unlimited
              </span>
            )}
          </div>
          {lastUpdate && (
            <p className="text-xs sm:text-sm text-gray-500 mt-1">
              Last updated: {new Date(lastUpdate).toLocaleTimeString()}
            </p>
          )}
        </div>
        <div className="flex items-center space-x-2 w-full sm:w-auto">
          <button
            onClick={handleRefresh}
            disabled={costSummaryLoading}
            className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50"
            title="Refresh data"
          >
            <RefreshCw size={18} className={costSummaryLoading ? 'animate-spin' : ''} />
          </button>
          <button
            onClick={handleTogglePolling}
            className={`px-2 sm:px-3 py-2 text-xs sm:text-sm font-medium rounded-lg transition-colors whitespace-nowrap ${
              isPolling
                ? 'bg-green-100 text-green-700 hover:bg-green-200'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {isPolling ? 'Polling Active' : 'Polling Paused'}
          </button>
        </div>
      </div>

      {/* Budget Recommendation (Story 3-6) */}
      <BudgetRecommendationDisplay />

      {/* Date Range Filter */}
      <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
        <div className="flex flex-col sm:flex-row flex-wrap items-start sm:items-center gap-3 sm:gap-4">
          <div className="flex items-center space-x-2 text-gray-700">
            <Calendar size={18} />
            <span className="text-sm font-medium">Date Range:</span>
          </div>

          {/* Presets */}
          <div className="flex flex-wrap gap-2 w-full sm:w-auto">
            {DATE_RANGE_PRESETS.map((preset) => (
              <button
                key={preset.label}
                onClick={() => handlePresetClick(preset)}
                className={`px-3 py-1.5 text-sm font-medium rounded-lg transition-colors ${
                  dateFrom === preset.dateFrom && (!preset.dateTo || dateTo === preset.dateTo)
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {preset.label}
              </button>
            ))}
          </div>

          {/* Custom Date Range */}
          <div className="flex flex-wrap items-center gap-2 w-full sm:w-auto sm:ml-auto">
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              className="px-2 sm:px-3 py-1.5 text-xs sm:text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
            />
            <span className="text-gray-500 text-xs sm:text-sm">to</span>
            <input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              className="px-2 sm:px-3 py-1.5 text-xs sm:text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
            />
            <button
              onClick={handleDateRangeChange}
              disabled={costSummaryLoading}
              className="px-2 sm:px-3 py-1.5 text-xs sm:text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 whitespace-nowrap"
            >
              Apply
            </button>
          </div>
        </div>
      </div>

      {/* Error State */}
      {costSummaryError && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center">
            <AlertCircle size={20} className="text-red-500 mr-2" />
            <p className="text-sm text-red-700">{costSummaryError}</p>
            <button
              onClick={() => fetchCostSummary({ dateFrom, dateTo })}
              className="ml-auto text-sm text-red-700 font-medium hover:underline"
            >
              Retry
            </button>
          </div>
        </div>
      )}

      {/* Summary Cards with Trends */}
      <CostSummaryCards previousPeriodSummary={previousPeriodSummary ?? undefined} />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Chart Section */}
        <div className="lg:col-span-2 bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h3 className="font-bold text-gray-900 flex items-center">
                <BarChart3 size={18} className="mr-2" />
                Daily Spend
              </h3>
              <p className="text-xs text-gray-500 mt-1">
                Cost breakdown by day for selected period
              </p>
            </div>
          </div>

          {/* Chart Area */}
          {dailyData.length > 0 ? (
            <div className="h-64 bg-gray-50 rounded-lg p-4 relative">
              {/* Budget Cap Line */}
              <div
                className="absolute left-0 w-full border-t-2 border-dashed border-red-300 pointer-events-none z-10"
                style={{
                  top: `${100 - Math.min(((merchantSettings?.budgetCap ?? DEFAULT_BUDGET_CAP) / (maxDailyCost * dailyData.length || 1)) * 100, 100)}%`,
                }}
              />
              <span
                className="absolute right-2 text-xs text-red-500"
                style={{
                  top: `${100 - Math.min(((merchantSettings?.budgetCap ?? DEFAULT_BUDGET_CAP) / (maxDailyCost * dailyData.length || 1)) * 100, 100) - 3}%`,
                }}
              >
                Cap ${merchantSettings?.budgetCap ?? DEFAULT_BUDGET_CAP}
              </span>

              {/* Bar Chart */}
              <div className="flex items-end justify-between h-full pt-6 px-2">
                {dailyData.map((day, i) => (
                  <div
                    key={i}
                    className="flex-1 mx-1 bg-blue-100 rounded-t relative group"
                    style={{ height: `${(day.cost / maxDailyCost) * 100}%` }}
                  >
                    <div
                      className="absolute bottom-0 w-full bg-blue-600 rounded-t"
                      style={{ height: '100%' }}
                    />
                    {/* Tooltip */}
                    <div className="hidden group-hover:block absolute bottom-full left-1/2 -translate-x-1/2 mb-2 bg-gray-900 text-white text-xs py-1 px-2 rounded whitespace-nowrap z-20">
                      <div className="font-medium">{day.date}</div>
                      <div>{formatCost(day.cost)}</div>
                      <div className="text-gray-400">{day.requests} requests</div>
                    </div>
                    {/* Date label */}
                    <div className="absolute -bottom-6 left-1/2 -translate-x-1/2 text-xs text-gray-500 whitespace-nowrap">
                      {day.date}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="h-64 flex items-center justify-center text-gray-500">
              <p>No daily data available for selected period</p>
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Budget Configuration (Story 3-6) */}
          <BudgetConfiguration currentSpend={costSummary?.totalCostUsd} />

          {/* Alert Configuration (Story 3-8) */}
          <BudgetAlertConfig />

          {/* Cost Comparison */}
          {manyChatEstimated !== null && savings !== null && (
            <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-bold text-gray-900">Cost Comparison</h3>
                <div className="group relative">
                  <button className="text-gray-400 hover:text-gray-600">
                    <AlertCircle size={16} />
                  </button>
                  <div className="absolute right-0 top-full mt-2 w-48 bg-gray-900 text-white text-xs rounded-lg p-2 opacity-0 group-hover:opacity-100 transition-opacity z-20">
                    Estimated based on industry benchmarks. Actual costs may vary.
                  </div>
                </div>
              </div>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="font-medium text-gray-700">Shop (You)</span>
                    <span className="font-bold text-green-600">
                      {formatCost(costSummary?.totalCostUsd || 0, 2)}
                    </span>
                  </div>
                  <div className="w-full bg-gray-100 rounded-full h-4">
                    <div
                      className="bg-green-500 h-4 rounded-full"
                      style={{
                        width: `${Math.min(((costSummary?.totalCostUsd || 0) / manyChatEstimated) * 100, 100)}%`,
                      }}
                    />
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="font-medium text-gray-700">ManyChat (Est.)</span>
                    <span className="font-bold text-red-600">
                      {formatCost(manyChatEstimated, 2)}
                    </span>
                  </div>
                  <div className="w-full bg-gray-100 rounded-full h-4">
                    <div className="bg-red-500 h-4 rounded-full" style={{ width: '100%' }} />
                  </div>
                </div>
              </div>
              {savings > 0 && (
                <div className="mt-6 p-3 bg-green-50 rounded-lg border border-green-100">
                  <p className="text-sm text-green-800 font-medium text-center">
                    You saved {formatCost(savings, 2)} this period!
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Top Conversations & Provider Breakdown */}
      {topConversations.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Top Conversations */}
          <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
            <h3 className="font-bold text-gray-900 mb-4">Top Conversations by Cost</h3>
            <div className="space-y-3">
              {topConversations.map((conv, i) => (
                <div
                  key={conv.conversationId}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                >
                  <div className="flex items-center space-x-3">
                    <span className="w-6 h-6 flex items-center justify-center bg-blue-100 text-blue-700 rounded-full text-xs font-bold">
                      {i + 1}
                    </span>
                    <span className="text-sm font-mono text-gray-700">
                      {conv.conversationId.slice(0, 8)}...
                    </span>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-bold text-gray-900">
                      {formatCost(conv.totalCostUsd || 0, 4)}
                    </p>
                    <p className="text-xs text-gray-500">{conv.requestCount} requests</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Provider Breakdown */}
          {providersByCost.length > 0 && (
            <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
              <h3 className="font-bold text-gray-900 mb-4">Cost by Provider</h3>
              <div className="space-y-3">
                {providersByCost.map((provider) => {
                  const providerTotal = costSummary?.totalCostUsd || 1;
                  const percentage = (provider.costUsd / providerTotal) * 100;

                  return (
                    <div key={provider.name}>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="font-medium text-gray-700 capitalize">
                          {provider.name}
                        </span>
                        <span className="font-bold text-gray-900">
                          {formatCost(provider.costUsd || 0, 2)}
                        </span>
                      </div>
                      <div className="w-full bg-gray-100 rounded-full h-2">
                        <div
                          className="bg-blue-500 h-2 rounded-full"
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                      <p className="text-xs text-gray-500 mt-1">
                        {percentage.toFixed(1)}% of total · {provider.requests} requests
                      </p>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default Costs;
