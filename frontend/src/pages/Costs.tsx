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
 * Re-imagined with Mantis aesthetic.
 */

import { useEffect, useState, useMemo } from 'react';
import { AlertCircle, Calendar, RefreshCw, BarChart3, Infinity, TrendingUp, Activity, DollarSign } from 'lucide-react';
import { CostSummaryCards } from '../components/costs/CostSummaryCards';
import { BudgetConfiguration } from '../components/costs/BudgetConfiguration';
import { BudgetRecommendationDisplay } from '../components/costs/BudgetRecommendationDisplay';
import { BudgetWarningBanner } from '../components/costs/BudgetWarningBanner';
import { BotPausedBanner } from '../components/costs/BotPausedBanner';
import { BudgetHardStopModal } from '../components/costs/BudgetHardStopModal';
import { BudgetAlertConfig } from '../components/costs/BudgetAlertConfig';
import { CostComparisonCard } from '../components/costs/CostComparisonCard';
import { useCostTrackingStore } from '../stores/costTrackingStore';
import { useToast } from '../context/ToastContext';
import { formatCost } from '../types/cost';
import { GlassCard } from '../components/ui/GlassCard';

/**
 * Date range preset option
 */
interface DateRangePreset {
  label: string;
  dateFrom: string;
  dateTo?: string;
}

const getTodayDate = (): string => {
  const today = new Date();
  return today.toISOString().split('T')[0];
};

const getDateDaysAgo = (days: number): string => {
  const date = new Date();
  date.setDate(date.getDate() - days);
  return date.toISOString().split('T')[0];
};

const getFirstDayOfMonth = (): string => {
  const date = new Date();
  return new Date(date.getFullYear(), date.getMonth(), 1).toISOString().split('T')[0];
};

const DATE_RANGE_PRESETS: DateRangePreset[] = [
  { label: 'Today', dateFrom: getTodayDate() },
  { label: 'Last 7 Days', dateFrom: getDateDaysAgo(7) },
  { label: 'Last 30 Days', dateFrom: getDateDaysAgo(30) },
  { label: 'This Month', dateFrom: getFirstDayOfMonth() },
];

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

  const [dateFrom, setDateFrom] = useState<string>(getDateDaysAgo(30));
  const [dateTo, setDateTo] = useState<string>(getTodayDate());

  const { toast } = useToast();

  useEffect(() => {
    if (merchantSettingsError) {
      toast(merchantSettingsError, 'error');
    }
  }, [merchantSettingsError, toast]);

  useEffect(() => {
    getMerchantSettings();
    fetchBotStatus();
  }, [getMerchantSettings, fetchBotStatus]);

  useEffect(() => {
    const initialParams = { dateFrom, dateTo };
    setCostSummaryParams(initialParams);
    fetchCostSummary(initialParams);
    startPolling(undefined, pollingInterval);

    return () => {
      stopPolling();
    };
  }, [startPolling, stopPolling, pollingInterval]);

  const handlePresetClick = (preset: DateRangePreset) => {
    const newDateFrom = preset.dateFrom;
    const newDateTo = preset.dateTo || getTodayDate();
    setDateFrom(newDateFrom);
    setDateTo(newDateTo);
    setCostSummaryParams({ dateFrom: newDateFrom, dateTo: newDateTo });
    fetchCostSummary({ dateFrom: newDateFrom, dateTo: newDateTo });
  };

  const handleDateRangeChange = () => {
    setCostSummaryParams({ dateFrom, dateTo });
    fetchCostSummary({ dateFrom, dateTo });
  };

  useEffect(() => {
    if (costSummaryError) {
      toast(costSummaryError, 'error');
    }
  }, [costSummaryError, toast]);

  const handleRefresh = () => {
    fetchCostSummary({ dateFrom, dateTo });
  };

  const handleTogglePolling = () => {
    if (isPolling) {
      stopPolling();
    } else {
      startPolling(undefined, pollingInterval);
    }
  };

  const dailyData = useMemo(() => {
    if (!costSummary?.dailyBreakdown) return [];

    return costSummary.dailyBreakdown.map((day) => ({
      date: new Date(day.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      cost: day.totalCostUsd,
      requests: day.requestCount,
    }));
  }, [costSummary]);

  const maxDailyCost = useMemo(() => {
    const budgetCap = merchantSettings?.budgetCap ?? DEFAULT_BUDGET_CAP;
    if (dailyData.length === 0) return 1;
    return Math.max(...dailyData.map((d) => d.cost), budgetCap / 10);
  }, [dailyData, merchantSettings?.budgetCap]);

  const topConversations = useMemo(() => {
    return costSummary?.topConversations?.slice(0, 5) || [];
  }, [costSummary]);

  const providersByCost = useMemo(() => {
    if (!costSummary?.costsByProvider) return [];

    return Object.entries(costSummary.costsByProvider)
      .map(([name, data]) => ({ name, ...data }))
      .sort((a, b) => b.costUsd - a.costUsd);
  }, [costSummary]);

  const hasNoBudgetLimit = merchantSettings !== null && 
    merchantSettings !== undefined && 
    (merchantSettings?.budgetCap === null || merchantSettings?.budgetCap === undefined);

  return (
    <div className="space-y-12 animate-in fade-in slide-in-from-bottom-4 duration-700 pb-20">
      {/* Modals & Banners */}
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

      {hasNoBudgetLimit && (
        <GlassCard accent="mantis" className="p-8 border-amber-500/20 bg-amber-500/[0.03]">
          <div className="flex items-center gap-8">
            <div className="flex-shrink-0 w-16 h-16 bg-amber-500/10 rounded-2xl flex items-center justify-center border border-amber-500/20 text-amber-500">
              <Infinity size={32} strokeWidth={2.5} />
            </div>
            <div className="flex-1 space-y-2">
              <div className="flex items-center gap-3">
                <h3 className="text-xl font-black text-amber-100 uppercase tracking-tight">Unlimited Spending Active</h3>
                <span className="px-3 py-1 bg-amber-500 text-black text-[10px] font-black rounded-full uppercase tracking-widest">
                  No Cap
                </span>
              </div>
              <p className="text-sm text-amber-500/60 font-medium">
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
              className="px-8 h-14 bg-amber-500 text-black font-black text-[10px] uppercase tracking-[0.3em] rounded-2xl hover:bg-amber-400 transition-all shadow-[0_0_20px_rgba(245,158,11,0.2)]"
            >
              Set Budget Cap
            </button>
          </div>
        </GlassCard>
      )}

      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div className="space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-emerald-500/5 border border-emerald-500/10 rounded-full text-[10px] font-black uppercase tracking-[0.2em] text-emerald-400">
            <DollarSign size={12} />
            Neural Resource Consumption
          </div>
          <h1 className="text-5xl font-black tracking-tight text-white leading-none mantis-glow-text">
            Costs & Budget
          </h1>
          {lastUpdate && (
            <p className="text-sm text-emerald-500/60 font-medium">
              Last Analysis: <span className="text-white/60 font-mono tracking-tighter">{new Date(lastUpdate).toLocaleTimeString()}</span>
            </p>
          )}
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleRefresh}
            disabled={costSummaryLoading}
            className="w-14 h-14 flex items-center justify-center bg-white/5 border border-white/10 rounded-2xl text-white/40 hover:text-emerald-400 hover:border-emerald-500/20 hover:bg-emerald-500/5 transition-all duration-300 disabled:opacity-50"
          >
            <RefreshCw size={20} className={costSummaryLoading ? 'animate-spin' : ''} />
          </button>
          <button
            onClick={handleTogglePolling}
            className={`h-14 px-8 font-black text-[10px] uppercase tracking-[0.3em] rounded-2xl border transition-all duration-300 ${
              isPolling
                ? 'bg-emerald-500 text-black border-emerald-500 shadow-[0_0_20px_rgba(16,185,129,0.3)]'
                : 'bg-white/5 border-white/10 text-white hover:bg-white/10 hover:border-white/20'
            }`}
          >
            {isPolling ? 'Neural Sync Active' : 'Neural Sync Paused'}
          </button>
        </div>
      </div>

      <BudgetRecommendationDisplay />

      {/* Range Control */}
      <GlassCard className="p-4 bg-emerald-500/[0.01] border-white/[0.03]">
        <div className="flex flex-col lg:flex-row items-center justify-between gap-6">
          <div className="flex flex-wrap items-center gap-3">
            <div className="w-10 h-10 flex items-center justify-center bg-white/5 border border-white/10 rounded-xl text-emerald-500/60">
              <Calendar size={18} />
            </div>
            {DATE_RANGE_PRESETS.map((preset) => (
              <button
                key={preset.label}
                onClick={() => handlePresetClick(preset)}
                className={`px-5 py-2.5 text-[10px] font-black uppercase tracking-widest rounded-xl border transition-all duration-300 ${
                  dateFrom === preset.dateFrom && (!preset.dateTo || dateTo === preset.dateTo)
                    ? 'bg-emerald-500 text-black border-emerald-500 shadow-[0_0_15px_rgba(16,185,129,0.2)]'
                    : 'bg-white/5 border-white/10 text-white/40 hover:text-white hover:bg-white/10'
                }`}
              >
                {preset.label}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-4 w-full lg:w-auto">
            <div className="flex items-center gap-3 bg-white/5 border border-white/10 rounded-xl px-4 py-2 flex-1">
              <input
                type="date"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
                className="bg-transparent text-xs text-white uppercase tracking-widest font-black focus:outline-none w-full"
              />
              <span className="text-emerald-900/20 font-black">/</span>
              <input
                type="date"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
                className="bg-transparent text-xs text-white uppercase tracking-widest font-black focus:outline-none w-full"
              />
            </div>
            <button
              onClick={handleDateRangeChange}
              disabled={costSummaryLoading}
              className="h-12 px-6 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 font-black text-[10px] uppercase tracking-[0.2em] rounded-xl hover:bg-emerald-500 hover:text-black transition-all duration-300"
            >
              Apply Interval
            </button>
          </div>
        </div>
      </GlassCard>

      <CostSummaryCards previousPeriodSummary={previousPeriodSummary ?? undefined} />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Expenditure Graph */}
        <div className="lg:col-span-2">
          <GlassCard accent="mantis" className="h-[500px] flex flex-col p-0 overflow-hidden border-emerald-500/5 bg-emerald-500/[0.01]">
            <div className="p-8 border-b border-white/[0.03] flex items-center justify-between bg-white/[0.01]">
              <div className="space-y-1">
                <h3 className="text-xl font-black text-white uppercase tracking-tight flex items-center gap-3">
                  <BarChart3 className="text-emerald-500" size={20} />
                  Expenditure Index
                </h3>
                <p className="text-[10px] font-black text-emerald-500/60 uppercase tracking-[0.2em]">Neural request cost distribution</p>
              </div>
              <div className="flex items-center gap-3 px-4 py-2 bg-emerald-500/5 rounded-xl border border-emerald-500/10">
                <TrendingUp size={14} className="text-emerald-400" />
                <span className="text-[10px] font-black text-emerald-400 uppercase tracking-widest">Active Scale</span>
              </div>
            </div>

            <div className="flex-1 p-10 flex flex-col justify-end">
              {dailyData.length > 0 ? (
                <div className="relative h-full flex items-end justify-between gap-4">
                  {/* Neural Grid Lines */}
                  <div className="absolute inset-0 flex flex-col justify-between pointer-events-none opacity-20">
                    {[0, 1, 2, 3, 4].map((i) => (
                      <div key={i} className="border-t border-emerald-500/10 w-full h-0"></div>
                    ))}
                  </div>

                  {/* Budget Hard Stop Indicator */}
                  <div
                    className="absolute left-0 w-full border-t border-dashed border-red-500/50 pointer-events-none z-10 before:content-[''] before:absolute before:left-0 before:w-full before:h-8 before:bg-red-500/[0.03] before:-top-4"
                    style={{
                      bottom: `${Math.min(((merchantSettings?.budgetCap ?? DEFAULT_BUDGET_CAP) / (maxDailyCost || 1)) * 100, 100)}%`,
                    }}
                  >
                    <div className="absolute -top-6 right-0 bg-red-500/10 backdrop-blur-md px-3 py-1 rounded-full border border-red-500/20">
                       <span className="text-[9px] font-black text-red-500 uppercase tracking-widest">Hard Stop Limit: ${merchantSettings?.budgetCap ?? DEFAULT_BUDGET_CAP}</span>
                    </div>
                  </div>

                  {/* Bars */}
                  {dailyData.map((day, i) => (
                    <div
                      key={i}
                      className="group relative flex-1"
                      style={{ height: `${(day.cost / maxDailyCost) * 100}%` }}
                    >
                      <div className="absolute inset-0 bg-emerald-500/10 border-x border-t border-emerald-500/20 rounded-t-xl transition-all duration-500 group-hover:bg-emerald-500 group-hover:shadow-[0_0_30px_rgba(16,185,129,0.3)]"></div>
                      
                      {/* Neural Tooltip */}
                      <div className="opacity-0 group-hover:opacity-100 absolute -top-16 left-1/2 -translate-x-1/2 z-20 pointer-events-none transition-all duration-300 transform scale-90 group-hover:scale-100">
                        <div className="px-5 py-3 bg-[#0a0a0a] border border-emerald-500/30 rounded-2xl shadow-2xl space-y-1">
                          <p className="text-[9px] font-black text-emerald-500 uppercase tracking-widest">{day.date}</p>
                          <p className="text-sm font-black text-white">{formatCost(day.cost)}</p>
                        </div>
                        <div className="w-2 h-2 bg-emerald-500/30 rotate-45 mx-auto -mt-1 border-r border-b border-emerald-500/30"></div>
                      </div>

                      <div className="absolute -bottom-10 left-1/2 -translate-x-1/2 -rotate-45 whitespace-nowrap opacity-20 group-hover:opacity-60 transition-opacity">
                         <span className="text-[9px] font-black text-white uppercase tracking-widest">{day.date}</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="h-full flex flex-col items-center justify-center text-center space-y-4">
                  <div className="w-16 h-16 bg-white/5 border border-white/10 rounded-full flex items-center justify-center text-emerald-900/10">
                    <Activity size={32} />
                  </div>
                  <p className="text-xs font-black text-emerald-500/60 uppercase tracking-widest">No spectral data detected in specified range</p>
                </div>
              )}
            </div>
          </GlassCard>
        </div>

        {/* Configurations Sidebar */}
        <div className="space-y-8">
          <BudgetConfiguration currentSpend={costSummary?.totalCostUsd} />
          <BudgetAlertConfig />
          <CostComparisonCard />
        </div>
      </div>

      {/* Analytics Breakdown */}
      {topConversations.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <GlassCard accent="mantis" className="p-8 space-y-10 border-emerald-500/5 bg-emerald-500/[0.01]">
            <div className="space-y-1">
              <h3 className="text-xl font-black text-white uppercase tracking-tight">Heavy Transmissions</h3>
              <p className="text-[10px] font-black text-emerald-900/40 uppercase tracking-[0.2em]">Top resource-intensive conversations</p>
            </div>
            <div className="space-y-4">
              {topConversations.map((conv, i) => (
                <div
                  key={conv.conversationId}
                  className="group flex items-center justify-between p-6 bg-white/[0.02] border border-white/5 rounded-2xl hover:bg-emerald-500/[0.03] hover:border-emerald-500/20 transition-all duration-300"
                >
                  <div className="flex items-center gap-6">
                    <span className="w-10 h-10 flex items-center justify-center bg-white/5 border border-white/10 text-emerald-900/40 rounded-xl text-xs font-black group-hover:bg-emerald-500 group-hover:text-black group-hover:border-emerald-500 transition-colors">
                      {i + 1}
                    </span>
                    <div>
                      <span className="text-xs font-mono font-black text-white block">
                        {conv.conversationId.slice(0, 16).toUpperCase()}
                      </span>
                      <span className="text-[9px] font-black text-emerald-900/40 uppercase tracking-widest">{conv.requestCount} Neural Requests</span>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-lg font-black text-emerald-500 group-hover:mantis-glow-text transition-all tracking-tight">
                      {formatCost(conv.totalCostUsd || 0, 4)}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </GlassCard>

          {providersByCost.length > 0 && (
            <GlassCard accent="mantis" className="p-8 space-y-10 border-emerald-500/5 bg-emerald-500/[0.01]">
              <div className="space-y-1">
                <h3 className="text-xl font-black text-white uppercase tracking-tight">Node Distribution</h3>
                <p className="text-[10px] font-black text-emerald-900/40 uppercase tracking-[0.2em]">Usage across LLM providers</p>
              </div>
              <div className="space-y-10">
                {providersByCost.map((provider) => {
                  const providerTotal = costSummary?.totalCostUsd || 1;
                  const percentage = (provider.costUsd / providerTotal) * 100;

                  return (
                    <div key={provider.name} className="space-y-4">
                      <div className="flex justify-between items-end">
                        <div className="space-y-1">
                          <span className="text-xs font-black text-white uppercase tracking-widest block">
                            {provider.name}
                          </span>
                          <span className="text-[9px] font-black text-emerald-900/40 uppercase tracking-[0.2em]">
                             {provider.requests} total requests
                          </span>
                        </div>
                        <span className="text-xl font-black text-emerald-500 tracking-tight">
                          {formatCost(provider.costUsd || 0, 4)}
                        </span>
                      </div>
                      <div className="relative w-full h-3 bg-white/5 rounded-full overflow-hidden border border-white/5">
                        <div
                          className="absolute h-full bg-emerald-500 rounded-full shadow-[0_0_15px_rgba(16,185,129,0.3)] transition-all duration-1000"
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                      <div className="flex justify-between">
                         <span className="text-[9px] font-black text-emerald-900/20 uppercase tracking-[0.4em]">Contribution Load</span>
                         <span className="text-[10px] font-black text-emerald-500/60 uppercase tracking-widest">{percentage.toFixed(1)}%</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </GlassCard>
          )}
        </div>
      )}
    </div>
  );
};

export default Costs;
