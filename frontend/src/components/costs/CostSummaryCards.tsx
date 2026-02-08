/**
 * CostSummaryCards Component
 *
 * Displays dashboard summary cards for LLM cost tracking:
 * - Total cost with trend indicator (vs previous period)
 * - Total tokens processed
 * - Total request count
 * - Average cost per request
 * - Top provider by usage
 *
 * Story 3-5: Real-Time Cost Tracking
 */

import React, { useMemo } from 'react';
import { DollarSign, Hash, Zap, Cpu, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { useCostTrackingStore } from '../../stores/costTrackingStore';
import { formatCost, formatTokens } from '../../types/cost';
import type { CostSummary } from '../../types/cost';

interface CardData {
  label: string;
  value: string;
  icon: React.ReactNode;
  colorClass: string;
  bgColorClass: string;
  trend?: {
    value: number;
    label: string;
  };
}

interface TrendIndicatorProps {
  value: number;
  label: string;
}

const TrendIndicator: React.FC<TrendIndicatorProps> = ({ value, label }) => {
  if (value === 0) {
    return (
      <span className="flex items-center text-xs text-gray-500">
        <Minus size={14} className="mr-1" />
        No change from {label}
      </span>
    );
  }

  const isPositive = value > 0;
  const colorClass = isPositive ? 'text-red-600' : 'text-green-600';
  const Icon = isPositive ? TrendingUp : TrendingDown;

  return (
    <span className={`flex items-center text-xs ${colorClass}`}>
      <Icon size={14} className="mr-1" />
      {Math.abs(value).toFixed(1)}% vs {label}
    </span>
  );
};

// Reusable stat card component
const StatCard: React.FC<{
  label: string;
  value: string;
  icon: React.ReactNode;
  colorClass: string;
  bgColorClass: string;
  trend?: React.ReactNode;
}> = ({ label, value, icon, colorClass, bgColorClass, trend }) => (
  <div className="bg-white border border-gray-200 rounded-lg p-5 shadow-sm">
    <div className="flex items-start justify-between">
      <div className="flex-1">
        <p className="text-sm font-medium text-gray-600 mb-1">{label}</p>
        <p className={`text-2xl font-bold ${colorClass}`}>{value}</p>
        {trend && <div className="mt-2">{trend}</div>}
      </div>
      <div className={`p-3 rounded-lg ${bgColorClass}`}>
        {icon}
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

  // Determine top provider
  const topProvider = useMemo(() => {
    if (!costSummary?.costsByProvider) return null;

    const providers = Object.entries(costSummary.costsByProvider);
    if (providers.length === 0) return null;

    // Sort by request count (primary) and cost (secondary)
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

  // Calculate trends if previous period data available
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

  // Loading state
  if (costSummaryLoading && !costSummary) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-white border border-gray-200 rounded-lg p-5 shadow-sm animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-24 mb-2"></div>
            <div className="h-8 bg-gray-200 rounded w-32 mb-2"></div>
            <div className="h-3 bg-gray-200 rounded w-28"></div>
          </div>
        ))}
      </div>
    );
  }

  // No data state
  if (!costSummary) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-8 shadow-sm">
        <div className="text-center">
          <DollarSign size={32} className="text-gray-300 mx-auto mb-3" />
          <p className="text-sm text-gray-500">No cost data available</p>
          <p className="text-xs text-gray-400 mt-1">Data will appear once LLM requests are made</p>
        </div>
      </div>
    );
  }

  // Prepare card data
  const cards: CardData[] = [
    {
      label: 'Total Cost',
      value: formatCost(costSummary.totalCostUsd, 2),
      icon: <DollarSign size={20} className="text-blue-600" />,
      colorClass: 'text-blue-600',
      bgColorClass: 'bg-blue-50',
      trend: costTrend ? { value: costTrend.value, label: costTrend.label } : undefined,
    },
    {
      label: 'Total Tokens',
      value: formatTokens(costSummary.totalTokens),
      icon: <Hash size={20} className="text-purple-600" />,
      colorClass: 'text-purple-600',
      bgColorClass: 'bg-purple-50',
      trend: tokensTrend ? { value: tokensTrend.value, label: tokensTrend.label } : undefined,
    },
    {
      label: 'Total Requests',
      value: costSummary.requestCount.toLocaleString(),
      icon: <Zap size={20} className="text-green-600" />,
      colorClass: 'text-green-600',
      bgColorClass: 'bg-green-50',
      trend: requestsTrend ? { value: requestsTrend.value, label: requestsTrend.label } : undefined,
    },
    {
      label: 'Avg Cost/Request',
      value: formatCost(costSummary.avgCostPerRequest),
      icon: <Cpu size={20} className="text-orange-600" />,
      colorClass: 'text-orange-600',
      bgColorClass: 'bg-orange-50',
    },
  ];

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Cost Overview</h3>
        {lastUpdate && (
          <span className="text-xs text-gray-500">
            Last updated: {new Date(lastUpdate).toLocaleTimeString()}
          </span>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
        {cards.map((card) => (
          <StatCard
            key={card.label}
            label={card.label}
            value={card.value}
            icon={card.icon}
            colorClass={card.colorClass}
            bgColorClass={card.bgColorClass}
            trend={
              card.trend ? (
                <TrendIndicator value={card.trend.value} label={card.trend.label} />
              ) : undefined
            }
          />
        ))}
      </div>

      {/* Top Provider Card */}
      {topProvider && (
        <div className="bg-white border border-gray-200 rounded-lg p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="p-3 rounded-lg bg-gray-50">
                <Cpu size={20} className="text-gray-600" />
              </div>
              <div>
                <p className="text-sm font-medium text-gray-600">Top Provider</p>
                <p className="text-lg font-semibold text-gray-900 capitalize">{topProvider.name}</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-sm text-gray-500">{topProvider.requests} requests</p>
              <p className="text-sm font-medium text-gray-900">{formatCost(topProvider.costUsd, 2)}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CostSummaryCards;
