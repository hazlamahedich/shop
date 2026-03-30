import { memo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Brain, TrendingUp, TrendingDown } from 'lucide-react';
import { analyticsService } from '../../services/analyticsService';
import { StatCard } from './StatCard';
import { DonutGauge } from '../charts/DonutChart';
import { MiniAreaChart } from '../charts/AreaChart';
import type { AnswerQualityScore } from '../../types/analytics';

// OPTIMIZATION: Use React.memo to prevent unnecessary re-renders
// Component only re-renders when props or query data changes
export const AnswerQualityScoreWidget = memo(function AnswerQualityScoreWidget() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['analytics', 'answer-quality'],
    queryFn: () => analyticsService.getAnswerQuality(),
    staleTime: 60_000,
    refetchInterval: 60_000,
    retry: 1,
  });

  const qualityData = data as AnswerQualityScore | undefined;
  const score = qualityData?.score ?? 0;

  // OPTIMIZATION: Memoize expensive trend calculations
  const { status, trendChange, sparklineData } = useMemo(() => {
    const trend = qualityData?.trend || [];
    const recentTrend = trend.slice(-7);
    const previousTrend = trend.slice(-14, -7);
    const avgRecent = recentTrend.length > 0 ? recentTrend.reduce((a, b) => a + b, 0) / recentTrend.length : 0;
    const avgPrevious = previousTrend.length > 0 ? previousTrend.reduce((a, b) => a + b, 0) / previousTrend.length : 0;
    const change = avgPrevious > 0 ? ((avgRecent - avgPrevious) / avgPrevious) * 100 : 0;

    const getStatus = () => {
      if (score >= 80) return { label: 'Excellent', color: 'mantis' as const };
      if (score >= 60) return { label: 'Good', color: 'orange' as const };
      if (score >= 40) return { label: 'Fair', color: 'orange' as const };
      return { label: 'Needs Work', color: 'red' as const };
    };

    const status = getStatus();
    const sparklineData = trend.slice(-14).map((val, idx) => ({
      x: idx,
      y: val * 100,
    }));

    return { status, trendChange: change, sparklineData };
  }, [qualityData?.trend, score]);

  return (
    <StatCard
      title="Answer Quality Score"
      value={isLoading ? '...' : Math.round(score)}
      subValue={status.label.toUpperCase()}
      icon={<Brain size={18} />}
      accentColor={status.color}
      isLoading={isLoading}
      isError={isError}
    >
      {!isLoading && !isError && (
        <div className="mt-4 space-y-3">
          {/* Sparkline Chart */}
          <div className="h-16">
            <MiniAreaChart
              data={sparklineData}
              color={status.color === 'mantis' ? '#00f5d4' : status.color === 'orange' ? '#ff8c00' : '#ff4444'}
              showGrid={false}
            />
          </div>

          {/* Trend Indicator */}
          {trendChange !== 0 && (
            <div className="flex items-center gap-2 text-xs font-bold">
              {trendChange > 0 ? (
                <TrendingUp size={14} className={trendChange > 5 ? "text-[#00f5d4]" : "text-white/40"} />
              ) : (
                <TrendingDown size={14} className={trendChange < -5 ? "text-[#ff4444]" : "text-white/40"} />
              )}
              <span className={trendChange > 5 ? "text-[#00f5d4]" : trendChange < -5 ? "text-[#ff4444]" : "text-white/40"}>
                {trendChange > 0 ? '+' : ''}{trendChange.toFixed(1)}% vs last period
              </span>
            </div>
          )}

          {/* Quality Gauge */}
          <div className="flex justify-center">
            <DonutGauge
              value={score}
              maxValue={100}
              color={status.color === 'mantis' ? '#00f5d4' : status.color === 'orange' ? '#ff8c00' : '#ff4444'}
              size={80}
              strokeWidth={8}
            />
          </div>
        </div>
      )}
    </StatCard>
  );
});
