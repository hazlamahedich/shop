import { useQuery } from '@tanstack/react-query';
import { MessageSquare, Clock, CheckCircle2, TrendingUp, TrendingDown } from 'lucide-react';
import { analyticsService } from '../../services/analyticsService';
import { StatCard } from './StatCard';
import type { KnowledgeEffectivenessResponse } from '../../services/analyticsService';

export function QueryPerformanceWidget() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['analytics', 'query-performance'],
    queryFn: async () => {
      // Get both knowledge effectiveness and response time data
      const effectiveness = await analyticsService.getKnowledgeEffectiveness();
      const responseTime = await analyticsService.getResponseTimeDistribution();
      return { effectiveness, responseTime };
    },
    staleTime: 60_000,
    refetchInterval: 60_000,
    retry: 1,
  });

  const effectiveness = data?.effectiveness as KnowledgeEffectivenessResponse | undefined;
  const responseTime = data?.responseTime as any;

  // Calculate metrics
  const matchRate = effectiveness
    ? effectiveness.totalQueries > 0
      ? (effectiveness.successfulMatches / effectiveness.totalQueries) * 100
      : 0
    : 0;
  const avgConfidence = effectiveness?.avgConfidence ?? 0;
  const noMatchRate = effectiveness?.noMatchRate ?? 0;

  return (
    <StatCard
      title="Query Performance"
      value={isLoading ? '...' : `${Math.round(matchRate)}%`}
      subValue="MATCH_RATE"
      icon={<MessageSquare size={18} />}
      accentColor={matchRate >= 80 ? 'mantis' : matchRate >= 60 ? 'orange' : 'red'}
      isLoading={isLoading}
      expandable
    >
      <div className="space-y-4 mt-4">
        {isError ? (
          <div className="flex items-center justify-center py-8">
            <p className="text-[10px] font-black text-rose-400 uppercase tracking-widest">Performance Unavailable</p>
          </div>
        ) : (
          <>
            {/* Key Metrics */}
            <div className="grid grid-cols-3 gap-2">
              <div className="bg-white/5 border border-white/5 p-3 rounded-xl backdrop-blur-sm group/metric text-center">
                <CheckCircle2 size={14} className="mx-auto mb-1.5 text-[#00f5d4]/60" />
                <p className="text-[9px] font-bold text-white/30 uppercase tracking-tighter mb-1">Match Rate</p>
                <p className="text-lg font-black text-white group-hover/metric:text-[#00f5d4] transition-colors">
                  {Math.round(matchRate)}%
                </p>
              </div>

              <div className="bg-white/5 border border-white/5 p-3 rounded-xl backdrop-blur-sm group/metric text-center">
                <TrendingUp size={14} className="mx-auto mb-1.5 text-purple-400/60" />
                <p className="text-[9px] font-bold text-white/30 uppercase tracking-tighter mb-1">Confidence</p>
                <p className="text-lg font-black text-white group-hover/metric:text-purple-400 transition-colors">
                  {Math.round(avgConfidence * 100)}%
                </p>
              </div>

              <div className="bg-white/5 border border-white/5 p-3 rounded-xl backdrop-blur-sm group/metric text-center">
                <Clock size={14} className="mx-auto mb-1.5 text-orange-400/60" />
                <p className="text-[9px] font-bold text-white/30 uppercase tracking-tighter mb-1">P95 Time</p>
                <p className="text-lg font-black text-white group-hover/metric:text-orange-400 transition-colors">
                  {responseTime?.percentiles?.p95 ? `${Math.round(responseTime.percentiles.p95 / 1000)}s` : '-'}
                </p>
              </div>
            </div>

            {/* Detailed Metrics */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-[9px] font-black text-white/20 uppercase tracking-widest">
                <span>Performance Breakdown</span>
              </div>

              {/* Total Queries */}
              <div className="flex items-center justify-between text-[9px]">
                <span className="text-white/40">Total Queries</span>
                <span className="font-black text-white">{effectiveness?.totalQueries ?? 0}</span>
              </div>

              {/* Successful Matches */}
              <div className="flex items-center justify-between text-[9px]">
                <span className="text-white/40">Successful Matches</span>
                <span className="font-black text-[#00f5d4]">{effectiveness?.successfulMatches ?? 0}</span>
              </div>

              {/* No Match Rate */}
              <div className="flex items-center justify-between text-[9px]">
                <span className="text-white/40">No Match Rate</span>
                <span className={`font-black ${noMatchRate < 20 ? 'text-[#00f5d4]' : noMatchRate < 40 ? 'text-orange-400' : 'text-rose-400'}`}>
                  {Math.round(noMatchRate)}%
                </span>
              </div>

              {/* Response Times */}
              {responseTime?.percentiles && (
                <>
                  <div className="flex items-center justify-between text-[9px]">
                    <span className="text-white/40">P50 Response</span>
                    <span className="font-black text-white">{responseTime.percentiles.p50 ? `${Math.round(responseTime.percentiles.p50 / 1000)}s` : '-'}</span>
                  </div>
                  <div className="flex items-center justify-between text-[9px]">
                    <span className="text-white/40">P99 Response</span>
                    <span className="font-black text-white">{responseTime.percentiles.p99 ? `${Math.round(responseTime.percentiles.p99 / 1000)}s` : '-'}</span>
                  </div>
                </>
              )}
            </div>

            {/* Trend Chart */}
            {effectiveness?.trend && effectiveness.trend.length > 0 && (
              <div className="space-y-2">
                <div className="flex items-center justify-between text-[9px] font-black text-white/20 uppercase tracking-widest">
                  <span>7-Day Trend</span>
                  <div className="flex items-center gap-1">
                    {effectiveness.trend.length > 1 && (
                      <>
                        {effectiveness.trend[effectiveness.trend.length - 1] > effectiveness.trend[effectiveness.trend.length - 2] ? (
                          <TrendingUp size={10} className="text-[#00f5d4]" />
                        ) : effectiveness.trend[effectiveness.trend.length - 1] < effectiveness.trend[effectiveness.trend.length - 2] ? (
                          <TrendingDown size={10} className="text-rose-400" />
                        ) : null}
                      </>
                    )}
                  </div>
                </div>
                <div className="flex items-end gap-1 h-12">
                  {effectiveness.trend.slice(-7).map((val, idx) => (
                    <div
                      key={idx}
                      className="flex-1 bg-gradient-to-t from-[#00f5d4]/20 to-[#00f5d4] rounded-t transition-all hover:from-[#00f5d4]/30 hover:to-[#00f5d4]"
                      style={{ height: `${val}%` }}
                      title={`${Math.round(val)}%`}
                    />
                  ))}
                </div>
              </div>
            )}

            {/* Last Updated */}
            {effectiveness?.lastUpdated && (
              <div className="pt-2 border-t border-white/5">
                <p className="text-[8px] font-black text-white/20 uppercase tracking-wider">
                  Last updated: {new Date(effectiveness.lastUpdated).toLocaleString()}
                </p>
              </div>
            )}
          </>
        )}
      </div>
    </StatCard>
  );
}

export default QueryPerformanceWidget;
