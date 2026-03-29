import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Clock, TrendingUp, TrendingDown, Minus, AlertTriangle, RefreshCw, BarChart3 } from 'lucide-react';
import { analyticsService } from '../../services/analyticsService';
import { StatCard } from './StatCard';
import { BoxPlot, PercentileComparison } from '../charts/BoxPlot';

function formatMs(ms: number | null): string {
  if (ms === null) return '--';
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

function getTrendIcon(trend: string | undefined) {
  switch (trend) {
    case 'improving':
      return <TrendingUp size={12} className="text-[#00f5d4]" />;
    case 'degrading':
      return <TrendingDown size={12} className="text-rose-400" />;
    default:
      return <Minus size={12} className="text-white/20" />;
  }
}

function getTrendColor(trend: string | undefined): string {
  switch (trend) {
    case 'improving':
      return 'text-[#00f5d4] bg-[#00f5d4]/5';
    case 'degrading':
      return 'text-rose-400 bg-rose-400/5';
    default:
      return 'text-white/10';
  }
}

export function ResponseTimeWidget() {
  const [days, setDays] = useState(7);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [showBreakdown, setShowBreakdown] = useState(false);

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['analytics', 'response-time-distribution', days],
    queryFn: () => analyticsService.getResponseTimeDistribution(days),
    staleTime: 60_000,
    refetchInterval: 120_000,
  });

  const percentiles = data?.percentiles;
  const histogram = data?.histogram ?? [];
  const warning = data?.warning;
  const previousPeriod = data?.previousPeriod;
  const comparison = previousPeriod?.comparison;
  const count = data?.count ?? 0;
  const responseTypeBreakdown = data?.responseTypeBreakdown;

  const p50 = percentiles?.p50 ?? null;
  const p95 = percentiles?.p95 ?? null;
  const p99 = percentiles?.p99 ?? null;

  // Prepare box plot data
  const boxPlotData = p50 && p95 && p99 && histogram.length > 0 ? {
    min: Math.min(...histogram.map(h => parseFloat(h.label.replace(/\D/g, '')))),
    max: Math.max(...histogram.map(h => parseFloat(h.label.replace(/\D/g, '')))),
    q1: p50,
    median: p95,
    q3: p99,
  } : null;

  const getAccentColor = (): 'mantis' | 'yellow' | 'red' => {
    if (p95 === null) return 'mantis';
    if (p95 > 5000) return 'red';
    if (p95 > 3000) return 'yellow';
    return 'mantis';
  };

  const maxCount = histogram.length > 0 ? Math.max(...histogram.map((b) => b.count)) : 0;

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await refetch();
    setIsRefreshing(false);
  };

  return (
    <StatCard
      title="Response Time"
      value={isLoading ? '...' : formatMs(p95)}
      subValue="P95_LATENCY_SCORE"
      icon={<Clock size={18} />}
      accentColor={getAccentColor()}
      data-testid="response-time-widget"
      isLoading={isLoading}
      expandable
    >
      {/* Box Plot Visualization */}
      {!isLoading && boxPlotData && (
        <div className="mb-4">
          <div className="flex items-center justify-between mb-3">
            <span className="text-[9px] font-black text-white/30 uppercase tracking-wider">
              LATENCY_DISTRIBUTION
            </span>
            <BarChart3 size={12} className="text-white/20" />
          </div>
          <BoxPlot
            data={boxPlotData}
            height={100}
            color={p95 && p95 > 3000 ? '#f87171' : p95 && p95 > 5000 ? '#fb923c' : '#00f5d4'}
            showLabels={true}
            ariaLabel="Response time distribution box plot"
          />
        </div>
      )}

      {/* Percentile Comparison */}
      {!isLoading && previousPeriod && (
        <div className="mb-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[9px] font-black text-white/30 uppercase tracking-wider">
              PERIOD_COMPARISON
            </span>
          </div>
          <PercentileComparison
            current={{ p50: p50 || 0, p95: p95 || 0, p99: p99 || 0 }}
            previous={previousPeriod?.percentiles}
            height={60}
          />
        </div>
      )}

      <div className="space-y-4 mt-4">
        <div className="flex items-center justify-between gap-2">
          <select
            data-testid="time-range-selector"
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            className="bg-white/5 border border-white/10 rounded px-2 py-1 text-xs text-white/70 focus:outline-none focus:border-[#00f5d4]"
          >
            <option value={7}>7 days</option>
            <option value={14}>14 days</option>
            <option value={30}>30 days</option>
          </select>
          <button
            data-testid="refresh-button"
            onClick={handleRefresh}
            disabled={isRefreshing || isLoading}
            className="flex items-center gap-1 px-2 py-1 text-xs text-white/50 hover:text-white/80 disabled:opacity-50 transition-colors"
          >
            <RefreshCw size={12} className={isRefreshing ? 'animate-spin' : ''} />
            <span>Refresh</span>
          </button>
        </div>
        {isError ? (
          <div
            data-testid="response-time-error"
            className="flex items-center justify-center py-8"
          >
            <p className="text-[10px] font-black text-rose-400 uppercase tracking-widest">
              SIGNAL_DECODE_ERROR
            </p>
          </div>
        ) : (
          <>
            {warning && warning.show && (
              <div
                data-testid="response-time-warning"
                className={`flex items-center gap-2 px-3 py-2 rounded-lg border ${
                  warning.severity === 'critical'
                    ? 'bg-rose-400/10 border-rose-400/20 text-rose-400'
                    : 'bg-amber-400/10 border-amber-400/20 text-amber-400'
                }`}
              >
                <AlertTriangle size={12} />
                <span className="text-[9px] font-bold uppercase tracking-wider">
                  {warning.message}
                </span>
              </div>
            )}

            <div className="grid grid-cols-3 gap-2">
              <div
                data-testid="p50-metric"
                className="bg-white/5 border border-white/5 p-3 rounded-xl backdrop-blur-sm group/metric"
              >
                <p className="text-[9px] font-bold text-white/30 uppercase tracking-tighter mb-1">
                  P50
                </p>
                <p className="text-lg font-black text-white group-hover/metric:text-[#00f5d4] transition-colors">
                  {formatMs(p50)}
                </p>
              </div>
              <div
                data-testid="p95-metric"
                className="bg-white/5 border border-white/5 p-3 rounded-xl backdrop-blur-sm group/metric"
              >
                <p className="text-[9px] font-bold text-white/30 uppercase tracking-tighter mb-1">
                  P95
                </p>
                <p className="text-lg font-black text-white group-hover/metric:text-[#00f5d4] transition-colors">
                  {formatMs(p95)}
                </p>
              </div>
              <div
                data-testid="p99-metric"
                className="bg-white/5 border border-white/5 p-3 rounded-xl backdrop-blur-sm group/metric"
              >
                <p className="text-[9px] font-bold text-white/30 uppercase tracking-tighter mb-1">
                  P99
                </p>
                <p className="text-lg font-black text-white group-hover/metric:text-[#00f5d4] transition-colors">
                  {formatMs(p99)}
                </p>
              </div>
            </div>

            {histogram.length > 0 && (
              <div data-testid="histogram-container" className="space-y-2">
                <p className="text-[9px] font-bold text-white/30 uppercase tracking-tighter">
                  DISTRIBUTION
                </p>
                <div className="space-y-1.5">
                  {histogram.map((bucket) => {
                    const widthPercent = maxCount > 0 ? (bucket.count / maxCount) * 100 : 0;
                    const barColor =
                      bucket.color === 'green'
                        ? 'bg-[#00f5d4]'
                        : bucket.color === 'yellow'
                          ? 'bg-amber-400'
                          : 'bg-rose-400';

                    return (
                      <div
                        key={bucket.label}
                        data-testid={`histogram-bar-${bucket.label}`}
                        className="flex items-center gap-2"
                      >
                        <span className="text-[9px] font-bold text-white/40 w-10 text-right">
                          {bucket.label}
                        </span>
                        <div className="flex-1 h-4 bg-white/5 rounded overflow-hidden">
                          <div
                            className={`h-full ${barColor} rounded transition-all duration-500`}
                            style={{ width: `${widthPercent}%` }}
                          />
                        </div>
                        <span className="text-[9px] font-bold text-white/60 w-8 text-right">
                          {bucket.count}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {comparison && comparison.p95 && (
              <div data-testid="comparison-trend" className="pt-3 border-t border-white/5">
                <div className="flex items-center justify-between">
                  <span className="text-[9px] font-black text-white/10 uppercase tracking-[0.2em]">
                    PERIOD_COMPARISON
                  </span>
                  <div
                    className={`flex items-center gap-1 px-2 py-0.5 rounded text-[9px] font-bold ${getTrendColor(
                      comparison.p95.trend
                    )}`}
                  >
                    {getTrendIcon(comparison.p95.trend)}
                    <span>
                      {comparison.p95.trend === 'stable'
                        ? 'NO_CHANGE'
                        : `${Math.abs(comparison.p95.deltaPercent)}%`}
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* Response Type Breakdown (AC5) */}
            {responseTypeBreakdown && (
              <div className="mt-4 pt-3 border-t border-white/5">
                <h4 className="text-[10px] font-bold text-white/30 uppercase tracking-wider mb-2">
                  Response Type Breakdown
                </h4>
                <div className="grid grid-cols-2 gap-4">
                  {/* RAG Responses */}
                  <div data-testid="rag-responses" className="p-3 rounded-lg bg-white/5">
                    <div className="text-[9px] font-bold text-[#00f5d4] uppercase tracking-wider">
                      RAG
                    </div>
                    <div className="mt-2 space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] text-white/50">P50</span>
                        <span data-testid="rag-p50" className="text-sm font-bold text-white/80">
                          {formatMs(responseTypeBreakdown.rag.percentiles.p50)}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] text-white/50">P95</span>
                        <span data-testid="rag-p95" className="text-sm font-bold text-white/80">
                          {formatMs(responseTypeBreakdown.rag.percentiles.p95)}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] text-white/50">P99</span>
                        <span data-testid="rag-p99" className="text-sm font-bold text-white/80">
                          {formatMs(responseTypeBreakdown.rag.percentiles.p99)}
                        </span>
                      </div>
                      <div className="text-[9px] text-white/40 mt-2">
                        {responseTypeBreakdown.rag.count} responses
                      </div>
                    </div>
                    {/* General Responses */}
                    <div data-testid="general-responses" className="p-3 rounded-lg bg-white/5">
                      <div className="text-[9px] font-bold text-white/30 uppercase tracking-wider">
                        General
                      </div>
                      <div className="mt-2 space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-[10px] text-white/50">P50</span>
                          <span data-testid="general-p50" className="text-sm font-bold text-white/80">
                            {formatMs(responseTypeBreakdown.general.percentiles.p50)}
                          </span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-[10px] text-white/50">P95</span>
                          <span data-testid="general-p95" className="text-sm font-bold text-white/80">
                            {formatMs(responseTypeBreakdown.general.percentiles.p95)}
                          </span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-[10px] text-white/50">P99</span>
                          <span data-testid="general-p99" className="text-sm font-bold text-white/80">
                            {formatMs(responseTypeBreakdown.general.percentiles.p99)}
                          </span>
                        </div>
                        <div className="text-[9px] text-white/40 mt-2">
                          {responseTypeBreakdown.general.count} responses
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {count === 0 && !responseTypeBreakdown && (
              <div data-testid="response-time-empty" className="text-center py-8">
                <p className="text-sm text-white/50">No response time data available yet</p>
                <p className="text-xs text-gray-400 mt-4">
                  Response times will appear after customers start conversations with your bot.
                </p>
              </div>
            )}
          </>
        )}
      </div>
    </StatCard>
  );
}

export default ResponseTimeWidget;
