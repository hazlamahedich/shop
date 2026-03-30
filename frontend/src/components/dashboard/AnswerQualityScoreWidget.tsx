import { useQuery } from '@tanstack/react-query';
import { Brain, TrendingUp, TrendingDown } from 'lucide-react';
import { analyticsService } from '../../services/analyticsService';
import { StatCard } from './StatCard';
import { DonutGauge } from '../charts/DonutChart';
import { MiniAreaChart } from '../charts/AreaChart';
import type { AnswerQualityScore } from '../../types/analytics';

export function AnswerQualityScoreWidget() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['analytics', 'answer-quality'],
    queryFn: () => analyticsService.getAnswerQuality(),
    staleTime: 60_000,
    refetchInterval: 60_000,
    retry: 1,
  });

  const qualityData = data as AnswerQualityScore | undefined;
  const score = qualityData?.score ?? 0;

  // Calculate trend change
  const trend = qualityData?.trend || [];
  const recentTrend = trend.slice(-7);
  const previousTrend = trend.slice(-14, -7);
  const avgRecent = recentTrend.length > 0 ? recentTrend.reduce((a, b) => a + b, 0) / recentTrend.length : 0;
  const avgPrevious = previousTrend.length > 0 ? previousTrend.reduce((a, b) => a + b, 0) / previousTrend.length : 0;
  const trendChange = avgPrevious > 0 ? ((avgRecent - avgPrevious) / avgPrevious) * 100 : 0;

  // Determine status
  const getStatus = (): { label: string; color: 'mantis' | 'orange' | 'red' } => {
    if (score >= 80) return { label: 'Excellent', color: 'mantis' };
    if (score >= 60) return { label: 'Good', color: 'orange' };
    if (score >= 40) return { label: 'Fair', color: 'orange' };
    return { label: 'Needs Work', color: 'red' };
  };

  const status = getStatus();

  // Prepare sparkline data
  const sparklineData = trend.slice(-14).map((val, idx) => ({
    name: `Day ${idx + 1}`,
    value: val,
  }));

  return (
    <StatCard
      title="Answer Quality Score"
      value={isLoading ? '...' : `${Math.round(score)}`}
      subValue={status.label.toUpperCase()}
      icon={<Brain size={18} />}
      accentColor={status.color}
      isLoading={isLoading}
      miniChart={
        !isLoading && (
          <div className="flex items-center gap-4 mt-4">
            {/* Circular Gauge */}
            <DonutGauge
              value={Math.round(score)}
              maxValue={100}
              width={100}
              height={100}
              showLabel={false}
            />
            <div className="flex-1">
              {/* Mini sparkline chart */}
              <div className="mb-2">
                {sparklineData.length > 0 && (
                  <MiniAreaChart
                    data={sparklineData}
                    dataKey="value"
                    height={50}
                    color={score >= 80 ? '#00f5d4' : score >= 60 ? '#fb923c' : '#f87171'}
                  />
                )}
              </div>
              {/* Trend indicator */}
              <div className="flex items-center gap-2 text-[10px]">
                {trendChange > 5 ? (
                  <div className="flex items-center gap-1 text-[#00f5d4]">
                    <TrendingUp size={12} />
                    <span className="font-black">+{trendChange.toFixed(1)}%</span>
                  </div>
                ) : trendChange < -5 ? (
                  <div className="flex items-center gap-1 text-rose-400">
                    <TrendingDown size={12} />
                    <span className="font-black">{trendChange.toFixed(1)}%</span>
                  </div>
                ) : (
                  <div className="flex items-center gap-1 text-white/40">
                    <span className="font-black">Stable</span>
                  </div>
                )}
                <span className="text-white/30">14-day trend</span>
              </div>
            </div>
          </div>
        )
      }
      expandable
    >
      <div className="space-y-4 mt-4">
        {isError ? (
          <div className="flex items-center justify-center py-8">
            <p className="text-[10px] font-black text-rose-400 uppercase tracking-widest">Quality Score Unavailable</p>
          </div>
        ) : (
          <>
            {/* Quality Breakdown */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-[9px] font-black text-white/20 uppercase tracking-widest">
                <span>Score Breakdown</span>
                <span className={score >= 80 ? 'text-[#00f5d4]' : score >= 60 ? 'text-orange-400' : 'text-rose-400'}>
                  {status.label}
                </span>
              </div>

              {/* Match Rate Contribution */}
              <div className="relative group/metric">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[9px] font-bold text-white/30 uppercase tracking-tighter">Match Rate</span>
                  <span className="text-[10px] font-black text-white">40%</span>
                </div>
                <div className="h-2 w-full bg-white/5 rounded-lg overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-[#00f5d4]/40 to-[#00f5d4] rounded-full transition-all duration-500"
                    style={{ width: '40%' }}
                  />
                </div>
              </div>

              {/* Confidence Contribution */}
              <div className="relative group/metric">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[9px] font-bold text-white/30 uppercase tracking-tighter">Confidence</span>
                  <span className="text-[10px] font-black text-white">35%</span>
                </div>
                <div className="h-2 w-full bg-white/5 rounded-lg overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-purple-400/40 to-purple-400 rounded-full transition-all duration-500"
                    style={{ width: '35%' }}
                  />
                </div>
              </div>

              {/* Feedback Contribution */}
              <div className="relative group/metric">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[9px] font-bold text-white/30 uppercase tracking-tighter">User Feedback</span>
                  <span className="text-[10px] font-black text-white">25%</span>
                </div>
                <div className="h-2 w-full bg-white/5 rounded-lg overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-orange-400/40 to-orange-400 rounded-full transition-all duration-500"
                    style={{ width: '25%' }}
                  />
                </div>
              </div>
            </div>

            {/* Quality Indicators */}
            <div className="grid grid-cols-2 gap-2">
              <div className="bg-white/5 border border-white/5 p-3 rounded-xl backdrop-blur-sm group/metric">
                <p className="text-[9px] font-bold text-white/30 uppercase tracking-tighter mb-1">Strength</p>
                <p className="text-sm font-black text-white group-hover/metric:text-[#00f5d4] transition-colors">
                  {score >= 80 ? 'High Accuracy' : score >= 60 ? 'Reliable' : 'Inconsistent'}
                </p>
              </div>
              <div className="bg-white/5 border border-white/5 p-3 rounded-xl backdrop-blur-sm group/metric">
                <p className="text-[9px] font-bold text-white/30 uppercase tracking-tighter mb-1">Focus Area</p>
                <p className="text-sm font-black text-white group-hover/metric:text-orange-400 transition-colors">
                  {score >= 80 ? 'Maintain' : score >= 60 ? 'Improve' : 'Critical'}
                </p>
              </div>
            </div>

            {/* Last Updated */}
            {qualityData?.lastUpdated && (
              <div className="pt-2 border-t border-white/5">
                <p className="text-[8px] font-black text-white/20 uppercase tracking-wider">
                  Last updated: {new Date(qualityData.lastUpdated).toLocaleString()}
                </p>
              </div>
            )}
          </>
        )}
      </div>
    </StatCard>
  );
}

export default AnswerQualityScoreWidget;
