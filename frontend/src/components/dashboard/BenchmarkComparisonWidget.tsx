import { useQuery } from '@tanstack/react-query';
import { BarChart3, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { analyticsService } from '../../services/analyticsService';
import { StatCard } from './StatCard';

interface BenchmarkMetric {
  name: string;
  yourValue: number;
  industryAvg: number;
  percentile: number;
  status: 'above_avg' | 'below_avg' | 'at_avg';
  unit: string;
}

interface BenchmarkData {
  period: { days: number };
  metrics: BenchmarkMetric[];
  overallPercentile: number;
  summary: string;
}

function formatValue(value: number, unit: string): string {
  if (unit === 'USD') return `$${value.toFixed(3)}`;
  if (unit === 'percentage') return `${(value * 100).toFixed(1)}%`;
  if (unit === 'seconds') return `${value.toFixed(1)}s`;
  if (unit === 'score') return value.toFixed(1);
  return value.toFixed(2);
}

function formatMetricName(name: string): string {
  const names: Record<string, string> = {
    costPerConversation: 'Cost/Conv',
    responseTime: 'Response Time',
    resolutionRate: 'Resolution',
    csatScore: 'CSAT',
    fallbackRate: 'Fallback',
  };
  return names[name] || name;
}

function MetricRow({ metric }: { metric: BenchmarkMetric }) {
  const percentile = Math.max(0, Math.min(100, metric.percentile));
  const isAboveAvg = metric.status === 'above_avg';
  const isBelowAvg = metric.status === 'below_avg';

  return (
    <div className="flex items-center justify-between gap-2 py-1.5 border-b border-white/5 last:border-0">
      <span className="text-xs text-white/60">{formatMetricName(metric.name)}</span>
      <div className="flex items-center gap-2">
        <span className="text-xs font-semibold text-white">
          {formatValue(metric.yourValue, metric.unit)}
        </span>
        <span className={`text-[10px] ${isAboveAvg ? 'text-green-400' : isBelowAvg ? 'text-red-400' : 'text-white/60'}`}>
          {isAboveAvg ? <TrendingUp size={10} /> : isBelowAvg ? <TrendingDown size={10} /> : <Minus size={10} />}
        </span>
        <div className="w-12 h-1.5 bg-white/10 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full ${isAboveAvg ? 'bg-green-500' : isBelowAvg ? 'bg-red-500' : 'bg-gray-400'}`}
            style={{ width: `${percentile}%` }}
          />
        </div>
      </div>
    </div>
  );
}

export function BenchmarkComparisonWidget() {
  const { data, isLoading } = useQuery({
    queryKey: ['analytics', 'benchmarks'],
    queryFn: () => analyticsService.getBenchmarks(30) as Promise<BenchmarkData>,
    refetchInterval: 120_000,
    staleTime: 60_000,
  });

  const overallPercentile = data?.overallPercentile ?? 50;
  const metrics = data?.metrics ?? [];

  return (
    <StatCard
      title="vs Industry"
      value={`${overallPercentile}%ile`}
      subValue={data?.summary || 'Compare your metrics to industry averages'}
      icon={<BarChart3 size={18} />}
      accentColor={overallPercentile >= 50 ? 'blue' : 'orange'}
      data-testid="benchmark-comparison-widget"
      isLoading={isLoading}
    >
      <div className="space-y-0.5 mt-2">
        {metrics.slice(0, 5).map((metric) => (
          <MetricRow key={metric.name} metric={metric} />
        ))}
        <div className="pt-2 mt-2 border-t border-white/10">
          <div className="flex items-center justify-between">
            <span className="text-xs text-white/60">Industry avg</span>
            <span className="text-xs text-white/60">
              {metrics.length > 0 ? formatValue(metrics[0].industryAvg, metrics[0].unit) : '--'}
            </span>
          </div>
        </div>
      </div>
    </StatCard>
  );
}

export default BenchmarkComparisonWidget;
