import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { DollarSign, AlertTriangle, Zap, ChevronRight, TrendingUp, TrendingDown } from 'lucide-react';
import { costTrackingService } from '../../services/costTracking';
import type { CostSummary } from '../../types/cost';

function formatUSD(value: number): string {
  if (value < 0.001) return '$0.00';
  if (value < 1) return `$${value.toFixed(4)}`;
  return `$${value.toFixed(2)}`;
}

interface ProviderRow {
  provider: string;
  cost: number;
  percentage: number;
}

function getProviderBreakdown(data: CostSummary | undefined): ProviderRow[] {
  if (!data?.costsByProvider) return [];
  const total = Object.values(data.costsByProvider).reduce((s, v) => s + v.costUsd, 0);
  if (total === 0) return [];
  return Object.entries(data.costsByProvider)
    .map(([provider, summary]) => ({
      provider,
      cost: summary.costUsd,
      percentage: Math.round((summary.costUsd / total) * 100),
    }))
    .sort((a, b) => b.cost - a.cost)
    .slice(0, 3);
}

const PROVIDER_COLORS = [
  'bg-blue-500',
  'bg-purple-500',
  'bg-teal-500',
  'bg-orange-500',
];

export function AICostWidget() {
  const navigate = useNavigate();

  const now = new Date();
  const monthStart = new Date(now.getFullYear(), now.getMonth(), 1)
    .toISOString()
    .split('T')[0];

  const { data: envelope, isLoading, isError } = useQuery({
    queryKey: ['costs', 'summary', 'monthly'],
    queryFn: () => costTrackingService.getCostSummary({ dateFrom: monthStart }),
    refetchInterval: 60_000,
    staleTime: 30_000,
  });

  const summaryData = envelope?.data as CostSummary | undefined;

  const totalCost: number =
    typeof summaryData?.totalCostUsd === 'number' ? summaryData.totalCostUsd : 0;
  const requestCount: number =
    typeof summaryData?.requestCount === 'number' ? summaryData.requestCount : 0;

  const previousCost = summaryData?.previousPeriodSummary?.totalCostUsd;
  const momChangePercent = previousCost && previousCost > 0
    ? ((totalCost - previousCost) / previousCost) * 100
    : null;

  const budgetCap: number | null = null;
  const budgetPct = budgetCap && budgetCap > 0 ? (totalCost / budgetCap) * 100 : null;

  const isNearBudget = budgetPct !== null && budgetPct >= 80;
  const progressColor =
    budgetPct === null
      ? 'bg-blue-500'
      : budgetPct >= 80
      ? 'bg-red-500'
      : budgetPct >= 60
      ? 'bg-yellow-400'
      : 'bg-green-500';

  const providers = getProviderBreakdown(summaryData);

  return (
    <div
      className="relative overflow-hidden rounded-2xl bg-white border border-gray-100 shadow-sm"
      data-testid="ai-cost-widget"
    >
      <div
        className={`absolute inset-x-0 top-0 h-1 bg-gradient-to-r ${
          isNearBudget ? 'from-red-400 to-orange-400' : 'from-blue-400 to-indigo-400'
        } opacity-60`}
      />

      <div className="p-5">
        <div className="flex items-start justify-between mb-3">
          <div>
            <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">
              AI Cost (this month)
            </p>
            {isLoading ? (
              <div className="mt-1 h-8 w-28 rounded bg-gray-200 animate-pulse" />
            ) : isError ? (
              <p className="mt-1 text-2xl font-bold text-gray-400">N/A</p>
            ) : (
              <div className="flex items-baseline gap-2">
                <p className="mt-1 text-3xl font-bold text-gray-900 tracking-tight">
                  {formatUSD(totalCost)}
                </p>
                {momChangePercent !== null && (
                  <span
                    className={`text-xs font-medium flex items-center gap-0.5 ${
                      momChangePercent >= 0 ? 'text-red-600' : 'text-green-600'
                    }`}
                  >
                    {momChangePercent >= 0 ? (
                      <TrendingUp size={12} />
                    ) : (
                      <TrendingDown size={12} />
                    )}
                    {Math.abs(momChangePercent).toFixed(1)}% MoM
                  </span>
                )}
              </div>
            )}
          </div>
          <div
            className={`flex h-10 w-10 items-center justify-center rounded-xl ${
              isNearBudget ? 'bg-red-50 text-red-600 ring-4 ring-red-100' : 'bg-blue-50 text-blue-600 ring-4 ring-blue-100'
            }`}
          >
            {isNearBudget ? <AlertTriangle size={18} /> : <DollarSign size={18} />}
          </div>
        </div>

        {!isLoading && !isError && (
          <p className="text-sm text-gray-500 mb-3">
            {requestCount} AI requests
            {budgetCap ? ` · Budget: ${formatUSD(budgetCap)}` : ''}
          </p>
        )}

        {budgetPct !== null && !isLoading && (
          <div className="mb-3">
            <div className="flex justify-between text-xs text-gray-500 mb-1">
              <span>Budget used</span>
              <span className={isNearBudget ? 'text-red-600 font-semibold' : ''}>
                {budgetPct.toFixed(0)}%
              </span>
            </div>
            <div className="w-full bg-gray-100 rounded-full h-2 overflow-hidden">
              <div
                className={`h-2 rounded-full transition-all ${progressColor}`}
                style={{ width: `${Math.min(budgetPct, 100)}%` }}
              />
            </div>
            {isNearBudget && (
              <p className="text-xs text-red-600 mt-1 flex items-center gap-1">
                <AlertTriangle size={10} />
                Budget nearly reached — consider adjusting.
              </p>
            )}
          </div>
        )}

        {providers.length > 0 && !isLoading && (
          <div className="space-y-1.5 mb-3">
            {providers.map(({ provider, cost, percentage }, i) => (
              <div key={provider} className="flex items-center gap-2">
                <div
                  className={`h-2 flex-shrink-0 rounded-full ${PROVIDER_COLORS[i] ?? 'bg-gray-400'}`}
                  style={{ width: `${Math.max(percentage, 4)}%`, maxWidth: '60%' }}
                />
                <span className="text-xs text-gray-600 capitalize flex-1 truncate">
                  {provider}
                </span>
                <span className="text-xs font-medium text-gray-700">{formatUSD(cost)}</span>
              </div>
            ))}
          </div>
        )}

        <button
          onClick={() => navigate('/costs')}
          className="flex items-center gap-1 text-xs font-medium text-blue-600 hover:text-blue-800 transition-colors"
        >
          <Zap size={11} />
          View cost details <ChevronRight size={11} />
        </button>
      </div>
    </div>
  );
}

export default AICostWidget;
