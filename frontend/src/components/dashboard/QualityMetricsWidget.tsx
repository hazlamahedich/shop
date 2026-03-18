import { useQuery } from '@tanstack/react-query';
import { Smile, TrendingUp, TrendingDown, AlertTriangle } from 'lucide-react';
import { analyticsService } from '../../services/analyticsService';

interface SentimentData {
  current: {
    positiveRate: number;
    positiveCount: number;
    negativeCount: number;
    neutralCount: number;
    totalMessages: number;
  };
  trend: 'improving' | 'declining' | 'stable';
  trendChange: number | null;
}

interface BenchmarkMetric {
  name: string;
  yourValue: number;
  unit: string;
  percentile: number;
  status: 'above_avg' | 'below_avg' | 'average';
}

interface BenchmarkData {
  metrics: BenchmarkMetric[];
}

function formatMetricName(name: string): string {
  return name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

function formatValue(value: number, unit: string): string {
  if (unit === '%') return `${Math.round(value)}%`;
  if (unit === 's') return `${value.toFixed(1)}s`;
  if (unit === '$') return `$${value.toFixed(2)}`;
  return value.toString();
}

export function QualityMetricsWidget() {
  const { data: sentimentData, isLoading: sentimentLoading } = useQuery({
    queryKey: ['analytics', 'sentimentTrend'],
    queryFn: () => analyticsService.getSentimentTrend(30) as Promise<SentimentData>,
    refetchInterval: 120_000,
    staleTime: 60_000,
  });

  const { data: benchmarkData, isLoading: benchmarkLoading } = useQuery({
    queryKey: ['analytics', 'benchmark'],
    queryFn: () => analyticsService.getBenchmarks(30) as Promise<BenchmarkData>,
    refetchInterval: 120_000,
    staleTime: 60_000,
  });

  const isLoading = sentimentLoading || benchmarkLoading;

  const current = sentimentData?.current;
  const trend = sentimentData?.trend ?? 'stable';
  const positivePct = Math.round((current?.positiveRate ?? 0) * 100);

  const metrics = benchmarkData?.metrics?.slice(0, 3) ?? [];

  const getPercentileColor = (percentile: number) => {
    if (percentile >= 75) return 'bg-green-500';
    if (percentile >= 50) return 'bg-blue-500';
    if (percentile >= 25) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const getPercentileTextColor = (percentile: number) => {
    if (percentile >= 75) return 'text-green-400';
    if (percentile >= 50) return 'text-blue-400';
    if (percentile >= 25) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getPercentileLabel = (percentile: number) => {
    if (percentile >= 90) return 'Top 10%';
    if (percentile >= 75) return 'Top 25%';
    if (percentile >= 50) return 'Top 50%';
    if (percentile >= 25) return 'Top 75%';
    return 'Below Avg';
  };

  const circumference = 2 * Math.PI * 24;
  const strokeDashoffset = circumference - (positivePct / 100) * circumference;

  return (
    <div
      className="relative overflow-hidden glass-card transition-all duration-300 h-full"
      data-testid="quality-metrics-widget"
    >
      <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-pink-400 to-purple-400 opacity-60" />

      <div className="p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-white">Quality Metrics</h3>
          {trend !== 'stable' && (
            <div className="flex items-center gap-1">
              {trend === 'improving' ? (
                <TrendingUp size={12} className="text-green-400" />
              ) : (
                <TrendingDown size={12} className="text-red-400" />
              )}
              <span className={`text-xs font-medium ${trend === 'improving' ? 'text-green-400' : 'text-red-400'}`}>
                {trend === 'improving' ? 'Improving' : 'Declining'}
              </span>
            </div>
          )}
        </div>

        <div className="flex gap-6">
          <div className="flex flex-col items-center gap-3 w-24">
            {isLoading ? (
              <div className="w-14 h-14 rounded-full bg-white/5 animate-pulse" />
            ) : (
              <div className="relative w-14 h-14">
                <svg className="w-14 h-14 -rotate-90" viewBox="0 0 56 56">
                  <circle
                    cx="28"
                    cy="28"
                    r="24"
                    fill="none"
                    stroke="rgba(255,255,255,0.1)"
                    strokeWidth="6"
                  />
                  <circle
                    cx="28"
                    cy="28"
                    r="24"
                    fill="none"
                    stroke={positivePct >= 70 ? '#22c55e' : positivePct >= 50 ? '#eab308' : '#ef4444'}
                    strokeWidth="6"
                    strokeDasharray={circumference}
                    strokeDashoffset={strokeDashoffset}
                    strokeLinecap="round"
                    className="transition-all duration-500"
                  />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-sm font-bold text-white">{positivePct}%</span>
                </div>
              </div>
            )}
            <p className="text-[10px] text-white/50 font-medium">Positive</p>

            {!isLoading && current && (
              <div className="space-y-1 w-full">
                <div className="flex items-center justify-between text-[10px]">
                  <span className="flex items-center gap-1 text-green-400">
                    <span className="w-1.5 h-1.5 rounded-full bg-green-400" />
                    +
                  </span>
                  <span className="text-white/70">{current.positiveCount}</span>
                </div>
                <div className="flex items-center justify-between text-[10px]">
                  <span className="flex items-center gap-1 text-red-400">
                    <span className="w-1.5 h-1.5 rounded-full bg-red-400" />
                    −
                  </span>
                  <span className="text-white/70">{current.negativeCount}</span>
                </div>
                <div className="flex items-center justify-between text-[10px]">
                  <span className="flex items-center gap-1 text-white/40">
                    <span className="w-1.5 h-1.5 rounded-full bg-white/30" />
                    ~
                  </span>
                  <span className="text-white/50">{current.neutralCount}</span>
                </div>
              </div>
            )}
          </div>

          <div className="flex-1 min-w-0">
            <p className="text-[10px] text-white/50 uppercase tracking-wide mb-3">vs Industry Average</p>
            {isLoading ? (
              <div className="space-y-3">
                {[1, 2, 3].map(i => (
                  <div key={i} className="h-5 bg-white/5 rounded animate-pulse" />
                ))}
              </div>
            ) : metrics.length > 0 ? (
              <div className="space-y-3">
                {metrics.map((metric) => (
                  <div key={metric.name} className="space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] text-white/60 truncate pr-2">
                        {formatMetricName(metric.name)}
                      </span>
                      <span className={`text-[10px] font-semibold ${getPercentileTextColor(metric.percentile)}`}>
                        {getPercentileLabel(metric.percentile)}
                      </span>
                    </div>
                    <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all duration-500 ${getPercentileColor(metric.percentile)}`}
                        style={{ width: `${metric.percentile}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-white/30 italic">No benchmark data available</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default QualityMetricsWidget;
