import { useQuery } from '@tanstack/react-query';
import { ThumbsUp, ThumbsDown, MessageSquare, TrendingUp } from 'lucide-react';
import { analyticsService } from '../../services/analyticsService';
import { Sparkline } from './Sparkline';

export function FeedbackAnalyticsWidget() {
  const { data, isLoading } = useQuery({
    queryKey: ['analytics', 'feedback'],
    queryFn: () => analyticsService.getFeedbackAnalytics(),
    refetchInterval: 120_000,
    staleTime: 60_000,
  });

  const totalRatings = data?.totalRatings ?? 0;
  const positivePercent = data?.positivePercent ?? 0;
  const negativePercent = data?.negativePercent ?? 0;
  const recentNegative = data?.recentNegative ?? [];
  const trend = data?.trend ?? [];

  const trendData = trend.map((d) => d.positive);

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  return (
    <div
      className="relative overflow-hidden glass-card transition-all duration-300 h-full"
      data-testid="feedback-analytics-widget"
    >
      <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-green-400 to-emerald-400 opacity-60" />

      <div className="p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-white">Feedback Ratings</h3>
          <div className="flex items-center gap-1">
            <TrendingUp size={12} className="text-green-400" />
            <span className="text-xs text-white/50">7 days</span>
          </div>
        </div>

        {isLoading ? (
          <div className="space-y-4">
            <div className="h-10 bg-white/5 rounded animate-pulse" />
            <div className="h-6 bg-white/5 rounded animate-pulse" />
            <div className="h-16 bg-white/5 rounded animate-pulse" />
          </div>
        ) : totalRatings === 0 ? (
          <div className="flex flex-col items-center justify-center py-6 text-white/40">
            <MessageSquare size={24} className="mb-2 opacity-50" />
            <p className="text-xs text-center">No feedback ratings yet</p>
            <p className="text-[10px] text-white/30 mt-1">Ratings will appear here</p>
          </div>
        ) : (
          <>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-1.5">
                  <ThumbsUp size={14} className="text-green-400" />
                  <span className="text-lg font-bold text-white">{positivePercent}%</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <ThumbsDown size={14} className="text-red-400" />
                  <span className="text-lg font-bold text-white">{negativePercent}%</span>
                </div>
              </div>
              <span className="text-xs text-white/50">{totalRatings} total</span>
            </div>

            <div className="h-2 bg-white/10 rounded-full overflow-hidden mb-4">
              <div
                className="h-full bg-green-500 transition-all duration-500"
                style={{ width: `${positivePercent}%` }}
              />
            </div>

            {trendData.length > 0 && (
              <div className="mb-4">
                <p className="text-[10px] text-white/50 uppercase tracking-wide mb-2">Positive Trend</p>
                <Sparkline data={trendData} width={180} height={30} color="#22c55e" />
              </div>
            )}

            {recentNegative.length > 0 && (
              <div>
                <p className="text-[10px] text-white/50 uppercase tracking-wide mb-2">Recent Comments</p>
                <div className="space-y-2 max-h-24 overflow-y-auto">
                  {recentNegative.slice(0, 3).map((item, idx) => (
                    <div
                      key={idx}
                      className="text-[10px] text-white/60 bg-white/5 rounded px-2 py-1.5"
                    >
                      {item.comment || '(no comment)'}
                      <span className="text-white/30 ml-2">{formatDate(item.createdAt)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

export default FeedbackAnalyticsWidget;
