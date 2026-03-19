/**
 * CostSummaryCards Component - Industrial Technical Dashboard
 *
 * Displays dashboard summary cards for LLM cost tracking:
 * - Total cost with trend indicator (vs previous period)
 * - Total tokens processed
 * - Total request count
 * - Average cost per request
 *
 * Story 3-5: Real-Time Cost Tracking
 */

import React, { useMemo } from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { useCostTrackingStore } from '../../stores/costTrackingStore';
import { formatCost, formatTokens } from '../../types/cost';
import type { CostSummary } from '../../types/cost';

interface TrendIndicatorProps {
  value: number;
  label: string;
}

const TrendIndicator: React.FC<TrendIndicatorProps> = ({ value, label }) => {
  if (value === 0) {
    return (
      <span className="flex items-center text-xs text-white/40 font-mono">
        <Minus size={14} className="mr-1" />
        No change from {label}
      </span>
    );
  }

  const isPositive = value > 0;
  const colorClass = isPositive ? 'text-red-400' : 'text-emerald-400';
  const Icon = isPositive ? TrendingUp : TrendingDown;

  return (
    <span className={`flex items-center text-xs font-mono ${colorClass}`}>
      <Icon size={14} className="mr-1" />
      {Math.abs(value).toFixed(1)}% vs {label}
    </span>
  );
};

const StatCard: React.FC<{
  label: string;
  value: string;
  iconBg: string;
  iconBorder: string;
  iconColor: string;
  iconSymbol: string;
  valueColor: string;
  trend?: React.ReactNode;
}> = ({ label, value, iconBg, iconBorder, iconColor, iconSymbol, valueColor, trend }) => (
  <div className="bg-[#0A0A0A] border border-emerald-500/15 p-5">
    <div className="flex items-start justify-between">
      <div className="flex-1">
        <p className="text-[11px] font-semibold text-white/60 font-mono tracking-[2px] uppercase mb-1">{label}</p>
        <p className={`text-[28px] font-bold font-mono tracking-tight ${valueColor}`}>{value}</p>
        {trend && <div className="mt-2">{trend}</div>}
      </div>
      <div className={`w-10 h-10 flex items-center justify-center ${iconBg} border ${iconBorder}`}>
        <span className={`text-lg font-bold font-mono ${iconColor}`}>{iconSymbol}</span>
      </div>
    </div>
  </div>
);

export const CostSummaryCards: React.FC<{
  previousPeriodSummary?: CostSummary;
}> = ({ previousPeriodSummary }) => {
  const {
    costSummary,
    costSummaryLoading,
    lastUpdate,
  } = useCostTrackingStore();

  const topProvider = useMemo(() => {
    if (!costSummary?.costsByProvider) return null;

    const providers = Object.entries(costSummary.costsByProvider);
    if (providers.length === 0) return null;

    const sorted = providers.sort(([, a], [, b]) => {
      if (a.requests !== b.requests) {
        return b.requests - a.requests;
      }
      return b.costUsd - a.costUsd;
    });

    return {
      name: sorted[0][0],
      requests: sorted[0][1].requests,
      costUsd: sorted[0][1].costUsd,
    };
  }, [costSummary]);

  const costTrend = useMemo(() => {
    if (!costSummary || !previousPeriodSummary) return null;
    const current = costSummary.totalCostUsd;
    const previous = previousPeriodSummary.totalCostUsd;
    if (previous === 0) return null;
    return {
      value: ((current - previous) / previous) * 100,
      label: 'previous period',
    };
  }, [costSummary, previousPeriodSummary]);

  const tokensTrend = useMemo(() => {
    if (!costSummary || !previousPeriodSummary) return null;
    const current = costSummary.totalTokens;
    const previous = previousPeriodSummary.totalTokens;
    if (previous === 0) return null;
    return {
      value: ((current - previous) / previous) * 100,
      label: 'previous period',
    };
  }, [costSummary, previousPeriodSummary]);

  const requestsTrend = useMemo(() => {
    if (!costSummary || !previousPeriodSummary) return null;
    const current = costSummary.requestCount;
    const previous = previousPeriodSummary.requestCount;
    if (previous === 0) return null;
    return {
      value: ((current - previous) / previous) * 100,
      label: 'previous period',
    };
  }, [costSummary, previousPeriodSummary]);

  if (costSummaryLoading && !costSummary) {
    return (
      <div className="px-10 pt-8 pb-4">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="bg-[#0A0A0A] border border-emerald-500/15 p-5 animate-pulse">
              <div className="h-4 bg-white/10 w-24 mb-2"></div>
              <div className="h-8 bg-white/10 w-32 mb-2"></div>
              <div className="h-3 bg-white/10 w-28"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (!costSummary) {
    return (
      <div className="px-10 pt-8 pb-4">
        <div className="bg-[#0A0A0A] border border-emerald-500/15 p-8">
          <div className="text-center">
            <span className="text-4xl font-mono text-white/40">$</span>
            <p className="text-sm text-white/60 font-mono mt-3">No cost data available</p>
            <p className="text-xs text-white/40 font-mono mt-1">Data will appear once LLM requests are made</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="px-10 pt-8 pb-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-bold text-white font-['Space_Grotesk'] uppercase tracking-wide">Cost Overview</h3>
        {lastUpdate && (
          <span className="text-xs text-white/60 font-mono">
            Last updated: {new Date(lastUpdate).toLocaleTimeString()}
          </span>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
        <StatCard
          label="Total Cost"
          value={formatCost(costSummary.totalCostUsd, 4)}
          iconBg="bg-blue-500/15"
          iconBorder="border-blue-500/30"
          iconColor="text-blue-400"
          iconSymbol="$"
          valueColor="text-blue-400"
          trend={costTrend ? <TrendIndicator value={costTrend.value} label={costTrend.label} /> : undefined}
        />
        <StatCard
          label="Total Tokens"
          value={formatTokens(costSummary.totalTokens)}
          iconBg="bg-purple-500/15"
          iconBorder="border-purple-500/30"
          iconColor="text-purple-400"
          iconSymbol="#"
          valueColor="text-purple-400"
          trend={tokensTrend ? <TrendIndicator value={tokensTrend.value} label={tokensTrend.label} /> : undefined}
        />
        <StatCard
          label="Total Requests"
          value={costSummary.requestCount.toLocaleString()}
          iconBg="bg-emerald-500/15"
          iconBorder="border-emerald-500/30"
          iconColor="text-emerald-400"
          iconSymbol="⚡"
          valueColor="text-emerald-400"
          trend={requestsTrend ? <TrendIndicator value={requestsTrend.value} label={requestsTrend.label} /> : undefined}
        />
        <StatCard
          label="Avg Cost/Request"
          value={formatCost(costSummary.avgCostPerRequest)}
          iconBg="bg-orange-500/15"
          iconBorder="border-orange-500/30"
          iconColor="text-orange-400"
          iconSymbol="◎"
          valueColor="text-orange-400"
        />
      </div>

      {topProvider && (
        <div className="bg-[#0A0A0A] border border-emerald-500/15 p-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 flex items-center justify-center bg-white/5 border border-white/10">
                <span className="text-lg font-mono text-white/60">◈</span>
              </div>
              <div>
                <p className="text-[11px] font-semibold text-white/60 font-mono tracking-[2px] uppercase">Top Provider</p>
                <p className="text-base font-bold text-white font-['Space_Grotesk'] capitalize">{topProvider.name}</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-xs text-white/60 font-mono">{topProvider.requests} requests</p>
              <p className="text-sm font-bold text-emerald-400 font-mono">{formatCost(topProvider.costUsd, 4)}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CostSummaryCards;
