/**
 * CostSummaryCards Component - Hyper-Luminous Observer Aesthetic
 *
 * Displays tactical summary metrics for LLM cost tracking:
 * - Total cost (Neural Investment)
 * - Budget Reservoir (Remaining)
 * - Total tokens processed
 * - Average cost per request
 *
 * Story 3-5: Real-Time Cost Tracking
 */

import React, { useMemo } from 'react';
import { TrendingUp, TrendingDown, Minus, Activity, Zap, Cpu, Target } from 'lucide-react';
import { useCostTrackingStore } from '../../stores/costTrackingStore';
import { formatCost, formatTokens } from '../../types/cost';
import { GlassCard } from '../ui/GlassCard';
import type { CostSummary } from '../../types/cost';

interface TrendIndicatorProps {
  value: number;
}

const TrendIndicator: React.FC<TrendIndicatorProps> = ({ value }) => {
  if (value === 0) {
    return (
      <span className="flex items-center text-[10px] text-white/20 font-black uppercase tracking-widest">
        <Minus size={12} className="mr-1" />
        Stable
      </span>
    );
  }

  const isPositive = value > 0;
  const colorClass = isPositive ? 'text-rose-500' : 'text-emerald-400';
  const Icon = isPositive ? TrendingUp : TrendingDown;

  return (
    <span className={`flex items-center text-[10px] font-black uppercase tracking-widest ${colorClass}`}>
      <Icon size={12} className="mr-1" />
      {Math.abs(value).toFixed(1)}% Flux
    </span>
  );
};

const StatCard: React.FC<{
  label: string;
  value: string;
  subLabel?: string;
  icon: React.ReactNode;
  accentColor: string;
  trend?: React.ReactNode;
}> = ({ label, value, subLabel, icon, accentColor, trend }) => (
  <GlassCard accent="mantis" className="p-6 relative overflow-hidden group border-white/[0.03] bg-white/[0.01]">
    {/* Subtle Background Glow */}
    <div className={`absolute -right-4 -top-4 w-24 h-24 rounded-full blur-3xl opacity-5 transition-opacity group-hover:opacity-10 bg-${accentColor}`} />
    
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className={`w-10 h-10 rounded-xl flex items-center justify-center bg-white/5 border border-white/10 text-${accentColor}`}>
          {icon}
        </div>
        {trend}
      </div>
      
      <div className="space-y-1">
        <p className="text-[10px] font-black text-white/40 uppercase tracking-[0.2em] leading-none">{label}</p>
        <div className="flex items-baseline gap-2">
           <p className="text-3xl font-black text-white tracking-tighter leading-none">{value}</p>
        </div>
        {subLabel && (
          <p className="text-[9px] font-black text-white/20 uppercase tracking-widest pt-1">{subLabel}</p>
        )}
      </div>
    </div>
  </GlassCard>
);

export const CostSummaryCards: React.FC<{
  previousPeriodSummary?: CostSummary;
}> = ({ previousPeriodSummary }) => {
  const {
    costSummary,
    costSummaryLoading,
    merchantSettings,
  } = useCostTrackingStore();

  const budgetCap = merchantSettings?.budgetCap || 50;
  const remainingBudget = Math.max(0, budgetCap - (costSummary?.totalCostUsd || 0));
  const budgetPercentage = budgetCap > 0 ? (remainingBudget / budgetCap) * 100 : 0;

  const costTrend = useMemo(() => {
    if (!costSummary || !previousPeriodSummary) return null;
    const current = costSummary.totalCostUsd;
    const previous = previousPeriodSummary.totalCostUsd;
    if (previous === 0) return null;
    return {
      value: ((current - previous) / previous) * 100,
    };
  }, [costSummary, previousPeriodSummary]);

  const tokensTrend = useMemo(() => {
    if (!costSummary || !previousPeriodSummary) return null;
    const current = costSummary.totalTokens;
    const previous = previousPeriodSummary.totalTokens;
    if (previous === 0) return null;
    return {
      value: ((current - previous) / previous) * 100,
    };
  }, [costSummary, previousPeriodSummary]);

  if (costSummaryLoading && !costSummary) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-40 bg-white/[0.02] border border-white/[0.05] rounded-3xl animate-pulse" />
        ))}
      </div>
    );
  }

  if (!costSummary) return null;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          label="Neural Investment"
          value={formatCost(costSummary.totalCostUsd, 2)}
          subLabel={`${costSummary.requestCount.toLocaleString()} TOTAL TRANSMISSIONS`}
          icon={<Activity size={20} />}
          accentColor="emerald-400"
          trend={costTrend ? <TrendIndicator value={costTrend.value} /> : undefined}
        />
        
        <StatCard
          label="Budget Reservoir"
          value={budgetCap === null ? 'UNLIMITED' : formatCost(remainingBudget, 2)}
          subLabel={`${budgetPercentage.toFixed(1)}% CAPACITY REMAINING`}
          icon={<Target size={20} />}
          accentColor="blue-400"
        />

        <StatCard
          label="Token Throughput"
          value={formatTokens(costSummary.totalTokens)}
          subLabel="CUMULATIVE SPECTRAL DEPTH"
          icon={<Cpu size={20} />}
          accentColor="purple-400"
          trend={tokensTrend ? <TrendIndicator value={tokensTrend.value} /> : undefined}
        />

        <StatCard
          label="Intelligence ROI"
          value={formatCost(costSummary.avgCostPerRequest, 4)}
          subLabel="EFFICIENCY INDEX PER NODE"
          icon={<Zap size={20} />}
          accentColor="amber-400"
        />
      </div>
    </div>
  );
};

export default CostSummaryCards;
