import { useQuery } from '@tanstack/react-query';
import { Smile, TrendingUp, TrendingDown, Activity, Target } from 'lucide-react';
import { analyticsService } from '../../services/analyticsService';
import { StatCard } from './StatCard';

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
  const positivePct = Math.round((current?.positiveRate ?? 0) * 100);
  const metrics = benchmarkData?.metrics?.slice(0, 3) ?? [];

  const getPercentileColor = (percentile: number) => {
    if (percentile >= 75) return 'bg-[#00f5d4]';
    if (percentile >= 50) return 'bg-sky-400';
    if (percentile >= 25) return 'bg-yellow-400';
    return 'bg-rose-500';
  };

  const getPercentileLabel = (percentile: number) => {
    if (percentile >= 90) return 'ELITE';
    if (percentile >= 75) return 'HIGH';
    if (percentile >= 50) return 'MED';
    return 'LOW';
  };

  return (
    <StatCard
      title="Signal Quality"
      value={isLoading ? '...' : `${positivePct}%`}
      subValue="POSITIVE_SENTIMENT_RATIO"
      icon={<Smile size={18} />}
      accentColor={positivePct >= 75 ? 'mantis' : positivePct >= 50 ? 'yellow' : 'red'}
      data-testid="quality-metrics-widget"
      isLoading={isLoading}
    >
      <div className="space-y-4 mt-4">
        <div className="flex gap-4">
          <div className="flex flex-col items-center gap-2 w-20">
            <div className="relative w-16 h-16 group/gauge">
              <svg className="w-16 h-16 -rotate-90" viewBox="0 0 56 56">
                <circle cx="28" cy="28" r="24" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="4" />
                <circle
                  cx="28" cy="28" r="24" fill="none"
                  stroke={positivePct >= 75 ? '#00f5d4' : positivePct >= 50 ? '#fbbf24' : '#f43f5e'}
                  strokeWidth="4"
                  strokeDasharray={150.8}
                  strokeDashoffset={150.8 - (positivePct / 100) * 150.8}
                  strokeLinecap="round"
                  className="transition-all duration-1000 shadow-[0_0_10px_rgba(0,245,212,0.3)]"
                />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-xs font-black text-white">{positivePct}%</span>
                <Activity size={8} className="text-white/20 mt-0.5" />
              </div>
            </div>
          </div>

          <div className="flex-1 space-y-2">
            <div className="flex items-center justify-between text-[9px] font-black text-white/20 uppercase tracking-widest mb-1">
               <span>BENCHMARK_TELEMETRY</span>
               <span className="text-[#00f5d4]/40">LIVE</span>
            </div>
            {metrics.map((metric) => (
              <div key={metric.name} className="space-y-1 group/row">
                <div className="flex items-center justify-between">
                  <span className="text-[9px] font-black text-white/40 group-hover/row:text-white/60 transition-colors truncate uppercase tracking-tighter">
                    {formatMetricName(metric.name)}
                  </span>
                  <span className={`text-[8px] font-black px-1.5 py-0.5 rounded border border-white/5 opacity-40 group-hover:opacity-100 transition-opacity ${getPercentileColor(metric.percentile).replace('bg-', 'text-')}`}>
                    {getPercentileLabel(metric.percentile)}
                  </span>
                </div>
                <div className="h-1 w-full bg-white/5 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-1000 ${getPercentileColor(metric.percentile)}`}
                    style={{ width: `${metric.percentile}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-2 pt-2 border-t border-white/5">
           <div className="bg-white/5 p-2 rounded-lg border border-white/5 flex items-center justify-between">
              <span className="text-[9px] font-bold text-white/20 uppercase">SENTIMENT</span>
              {sentimentData?.trend === 'improving' ? <TrendingUp size={10} className="text-[#00f5d4]" /> : <TrendingDown size={10} className="text-rose-400" />}
           </div>
           <div className="bg-white/5 p-2 rounded-lg border border-white/5 flex items-center justify-between">
              <span className="text-[9px] font-bold text-white/20 uppercase">TARGET</span>
              <Target size={10} className="text-white/20" />
           </div>
        </div>
      </div>
    </StatCard>
  );
}

export default QualityMetricsWidget;
