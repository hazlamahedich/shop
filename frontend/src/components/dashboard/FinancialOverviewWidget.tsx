import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { TrendingUp, TrendingDown, Zap, DollarSign } from 'lucide-react';
import { analyticsService } from '../../services/analyticsService';
import { costTrackingService } from '../../services/costTracking';
import type { CostSummary } from '../../types/cost';
import { useAuthStore } from '../../stores/authStore';

function formatCurrency(value: number): string {
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `$${(value / 1_000).toFixed(1)}K`;
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(value);
}

function formatUSD(value: number): string {
  if (value < 0.001) return '$0.00';
  if (value < 1) return `$${value.toFixed(4)}`;
  return `$${value.toFixed(2)}`;
}

export function FinancialOverviewWidget() {
  const navigate = useNavigate();
  const onboardingMode = useAuthStore((state) => state.merchant?.onboardingMode);
  const isEcommerce = onboardingMode !== 'general';

  const { data: summaryData, isLoading: revLoading } = useQuery({
    queryKey: ['analytics', 'summary'],
    queryFn: () => analyticsService.getSummary(),
    refetchInterval: 60_000,
    staleTime: 30_000,
  });

  const now = new Date();
  const monthStart = new Date(now.getFullYear(), now.getMonth(), 1)
    .toISOString()
    .split('T')[0];

  const { data: costEnvelope, isLoading: costLoading } = useQuery({
    queryKey: ['costs', 'summary', 'monthly'],
    queryFn: () => costTrackingService.getCostSummary({ dateFrom: monthStart }),
    refetchInterval: 60_000,
    staleTime: 30_000,
  });

  const isLoading = revLoading || costLoading;
  const orderStats = summaryData?.orderStats;
  const costData = costEnvelope?.data as CostSummary | undefined;

  const totalRevenue = typeof orderStats?.totalRevenue === 'number' ? orderStats.totalRevenue : 0;
  const totalOrders = typeof orderStats?.total === 'number' ? orderStats.total : 0;
  const totalCost = typeof costData?.totalCostUsd === 'number' ? costData.totalCostUsd : 0;
  const tokenCount = typeof costData?.totalTokens === 'number' ? costData.totalTokens : 0;
  const requestCount = typeof costData?.requestCount === 'number' ? costData.requestCount : 0;

  const hasRevenue = isEcommerce && totalRevenue > 0;
  const roi = totalCost > 0 && hasRevenue ? totalRevenue / totalCost : 0;

  const revenueTrend = orderStats?.momComparison?.revenueChangePercent;

  const previousCost = costData?.previousPeriodSummary?.totalCostUsd;
  const costTrend = previousCost && previousCost > 0
    ? ((totalCost - previousCost) / previousCost) * 100
    : null;

  const weekData = [12, 18, 15, 25, 22, 30, 35];
  const maxWeek = Math.max(...weekData);

  if (!isEcommerce) {
    return (
      <div
        className="relative overflow-hidden glass-card transition-all duration-300 h-full"
        data-testid="financial-overview-widget"
      >
        <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-blue-400 to-indigo-400 opacity-60" />

        <div className="p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-white">AI Cost</h3>
            {costTrend !== null && (
              <div className="flex items-center gap-1">
                {costTrend >= 0 ? (
                  <TrendingUp size={12} className="text-amber-400" />
                ) : (
                  <TrendingDown size={12} className="text-green-400" />
                )}
                <span className={`text-xs font-semibold ${costTrend >= 0 ? 'text-amber-400' : 'text-green-400'}`}>
                  {costTrend >= 0 ? '+' : ''}{costTrend.toFixed(0)}%
                </span>
              </div>
            )}
          </div>

          <div className="flex gap-6 mb-4">
            <div className="flex-1">
              <p className="text-[10px] text-white/50 uppercase tracking-wide mb-1">Cost (30d)</p>
              {isLoading ? (
                <div className="h-6 w-20 bg-white/5 rounded animate-pulse" />
              ) : (
                <>
                  <p className="text-xl font-bold text-white">{formatUSD(totalCost)}</p>
                  <p className="text-[10px] text-white/40">{requestCount} requests</p>
                </>
              )}
            </div>

            <div className="flex-1">
              <p className="text-[10px] text-white/50 uppercase tracking-wide mb-1">Tokens Used</p>
              {isLoading ? (
                <div className="h-6 w-16 bg-white/5 rounded animate-pulse" />
              ) : (
                <>
                  <p className="text-xl font-bold text-blue-400">{(tokenCount / 1000000).toFixed(2)}M</p>
                  <p className="text-[10px] text-white/40">total tokens</p>
                </>
              )}
            </div>

            <div className="flex-1">
              <p className="text-[10px] text-white/50 uppercase tracking-wide mb-1">Avg / Request</p>
              {isLoading ? (
                <div className="h-6 w-16 bg-white/5 rounded animate-pulse" />
              ) : (
                <>
                  <p className="text-xl font-bold text-white">
                    {requestCount > 0 ? formatUSD(totalCost / requestCount) : '$0'}
                  </p>
                  <p className="text-[10px] text-white/40">per request</p>
                </>
              )}
            </div>
          </div>

          <div className="h-10 flex items-end gap-1">
            {weekData.map((val, i) => (
              <div
                key={i}
                className="flex-1 rounded-t transition-all duration-300"
                style={{
                  height: `${(val / maxWeek) * 100}%`,
                  backgroundColor: i === weekData.length - 1 ? '#3b82f6' : `rgba(59, 130, 246, ${0.3 + (i / weekData.length) * 0.5})`,
                }}
              />
            ))}
          </div>

          <button
            onClick={() => navigate('/costs')}
            className="flex items-center gap-1.5 text-xs font-bold text-blue-400 hover:text-blue-300 transition-all mt-3 hover:translate-x-1"
          >
            <DollarSign size={11} />
            VIEW COST DETAILS
          </button>
        </div>
      </div>
    );
  }

  return (
    <div
      className="relative overflow-hidden glass-card transition-all duration-300 h-full"
      data-testid="financial-overview-widget"
    >
      <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-purple-400 to-indigo-400 opacity-60" />

      <div className="p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-white">Financial Overview</h3>
          {revenueTrend !== undefined && revenueTrend !== null && (
            <div className="flex items-center gap-1">
              {revenueTrend >= 0 ? (
                <TrendingUp size={12} className="text-green-400" />
              ) : (
                <TrendingDown size={12} className="text-red-400" />
              )}
              <span className={`text-xs font-semibold ${revenueTrend >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {revenueTrend >= 0 ? '+' : ''}{revenueTrend.toFixed(0)}%
              </span>
            </div>
          )}
        </div>

        <div className="flex gap-6 mb-4">
          <div className="flex-1">
            <p className="text-[10px] text-white/50 uppercase tracking-wide mb-1">Revenue (30d)</p>
            {isLoading ? (
              <div className="h-6 w-20 bg-white/5 rounded animate-pulse" />
            ) : (
              <>
                <p className="text-xl font-bold text-white">{formatCurrency(totalRevenue)}</p>
                <p className="text-[10px] text-white/40">{totalOrders} orders</p>
              </>
            )}
          </div>

          <div className="flex-1">
            <p className="text-[10px] text-white/50 uppercase tracking-wide mb-1">AI Cost (30d)</p>
            {isLoading ? (
              <div className="h-6 w-20 bg-white/5 rounded animate-pulse" />
            ) : (
              <>
                <p className="text-xl font-bold text-white">{formatUSD(totalCost)}</p>
                <p className="text-[10px] text-white/40">{(tokenCount / 1000000).toFixed(1)}M tokens</p>
              </>
            )}
          </div>

          <div className="flex-1">
            <p className="text-[10px] text-white/50 uppercase tracking-wide mb-1">ROI</p>
            {isLoading ? (
              <div className="h-6 w-16 bg-white/5 rounded animate-pulse" />
            ) : (
              <>
                <p className="text-xl font-bold text-green-400">{roi > 0 ? `${roi.toFixed(0)}x` : '—'}</p>
                <p className="text-[10px] text-white/40">Rev / Cost</p>
              </>
            )}
          </div>
        </div>

        <div className="h-10 flex items-end gap-1">
          {weekData.map((val, i) => (
            <div
              key={i}
              className="flex-1 rounded-t transition-all duration-300"
              style={{
                height: `${(val / maxWeek) * 100}%`,
                backgroundColor: i === weekData.length - 1 ? '#8B5CF6' : `rgba(139, 92, 246, ${0.3 + (i / weekData.length) * 0.5})`,
              }}
            />
          ))}
        </div>

        <button
          onClick={() => navigate('/costs')}
          className="flex items-center gap-1.5 text-xs font-bold text-purple-400 hover:text-purple-300 transition-all mt-3 hover:translate-x-1"
        >
          <Zap size={11} className="fill-current" />
          VIEW COST DETAILS
        </button>
      </div>
    </div>
  );
}

export default FinancialOverviewWidget;
