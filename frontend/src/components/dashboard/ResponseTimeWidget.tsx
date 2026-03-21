import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Clock, TrendingUp, TrendingDown, Minus, AlertTriangle } from 'lucide-react';
import { analyticsService } from '../../services/analyticsService';
import { StatCard } from './StatCard';

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
  const [days] = useState(7);

  const { data, isLoading, isError } = useQuery({
    queryKey: ['analytics', 'response-time-distribution', days],
    queryFn: () => analyticsService.getResponseTimeDistribution(days),
    staleTime: 60_000,
    refetchInterval: 120_000,
  });

  const responseData = data?.data;
  const percentiles = responseData?.percentiles;
  const histogram = responseData?.histogram ?? [];
  const warning = responseData?.warning;
  const previousPeriod = responseData?.previousPeriod;
  const comparison = previousPeriod?.comparison;
  const count = responseData?.count ?? 0;

  const p50 = percentiles?.p50 ?? null;
  const p95 = percentiles?.p95 ?? null;
  const p99 = percentiles?.p99 ?? null;

  const getAccentColor = (): 'mantis' | 'yellow' | 'red' => {
    if (p95 === null) return 'mantis';
    if (p95 > 5000) return 'red';
    if (p95 > 3000) return 'yellow';
    return 'mantis';
  };

  const maxCount = histogram.length > 0 ? Math.max(...histogram.map((b) => b.count)) : 0;

  return (
    <StatCard
      title="Response Time"
      value={isLoading ? '...' : formatMs(p95)}
      subValue="P95_LATENCY_SCORE"
      icon={<Clock size={18} />}
      accentColor={getAccentColor()}
      data-testid="response-time-widget"
      isLoading={isLoading}
    >
      <div className="space-y-4 mt-4">
        {isError ? (
          <div className="flex items-center justify-center py-8">
            <p className="text-[10px] font-black text-rose-400 uppercase tracking-widest">
              SIGNAL_DECODE_ERROR
            </p>
          </div>
        ) : (
          <>
            {warning && warning.show && (
              <div
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
              <div className="bg-white/5 border border-white/5 p-3 rounded-xl backdrop-blur-sm group/metric">
                <p className="text-[9px] font-bold text-white/30 uppercase tracking-tighter mb-1">
                  P50
                </p>
                <p className="text-lg font-black text-white group-hover/metric:text-[#00f5d4] transition-colors">
                  {formatMs(p50)}
                </p>
              </div>
              <div className="bg-white/5 border border-white/5 p-3 rounded-xl backdrop-blur-sm group/metric">
                <p className="text-[9px] font-bold text-white/30 uppercase tracking-tighter mb-1">
                  P95
                </p>
                <p className="text-lg font-black text-white group-hover/metric:text-[#00f5d4] transition-colors">
                  {formatMs(p95)}
                </p>
              </div>
              <div className="bg-white/5 border border-white/5 p-3 rounded-xl backdrop-blur-sm group/metric">
                <p className="text-[9px] font-bold text-white/30 uppercase tracking-tighter mb-1">
                  P99
                </p>
                <p className="text-lg font-black text-white group-hover/metric:text-[#00f5d4] transition-colors">
                  {formatMs(p99)}
                </p>
              </div>
            </div>

            {histogram.length > 0 && (
              <div className="space-y-2">
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
                      <div key={bucket.label} className="flex items-center gap-2">
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
              <div className="pt-3 border-t border-white/5">
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

            <div className="flex items-center justify-between pt-2 border-t border-white/5">
              <span className="text-[9px] font-black text-white/10 uppercase tracking-[0.2em]">
                {count} RESPONSES_TRACKED
              </span>
              <span className="text-[9px] font-bold text-white/20">{days}D_WINDOW</span>
            </div>
          </>
        )}
      </div>
    </StatCard>
  );
}

export default ResponseTimeWidget;
