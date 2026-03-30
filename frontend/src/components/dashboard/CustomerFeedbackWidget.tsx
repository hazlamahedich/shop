import { useQuery } from '@tanstack/react-query';
import { ThumbsUp, ThumbsDown, MessageSquare, TrendingUp } from 'lucide-react';
import { analyticsService } from '../../services/analyticsService';
import { StatCard } from './StatCard';
import type { CustomerFeedbackMetrics } from '../../types/analytics';

export function CustomerFeedbackWidget() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['analytics', 'customer-feedback'],
    queryFn: () => analyticsService.getCustomerFeedback(),
    staleTime: 60_000,
    refetchInterval: 60_000,
    retry: 1,
  });

  const feedbackData = data as CustomerFeedbackMetrics | undefined;
  const totalFeedback = feedbackData?.totalFeedback ?? 0;
  const positiveRate = feedbackData?.positiveRate ?? 0;
  const negativeRate = feedbackData?.negativeRate ?? 0;

  return (
    <StatCard
      title="Customer Feedback"
      value={isLoading ? '...' : `${Math.round(positiveRate)}%`}
      subValue="POSITIVE_RATE"
      icon={<MessageSquare size={18} />}
      accentColor={positiveRate >= 70 ? 'mantis' : positiveRate >= 50 ? 'orange' : 'red'}
      isLoading={isLoading}
      expandable
    >
      <div className="space-y-4 mt-4">
        {isError ? (
          <div className="flex items-center justify-center py-8">
            <p className="text-[10px] font-black text-rose-400 uppercase tracking-widest">Feedback Unavailable</p>
          </div>
        ) : (
          <>
            {/* Feedback Overview */}
            <div className="grid grid-cols-2 gap-2">
              <div className="bg-white/5 border border-white/5 p-3 rounded-xl backdrop-blur-sm group/metric">
                <div className="flex items-center gap-2 mb-1">
                  <ThumbsUp size={12} className="text-[#00f5d4]" />
                  <p className="text-[9px] font-bold text-white/30 uppercase tracking-tighter">Positive</p>
                </div>
                <p className="text-xl font-black text-white group-hover/metric:text-[#00f5d4] transition-colors">
                  {Math.round(positiveRate)}%
                </p>
                <p className="text-[8px] text-white/20 mt-1">
                  {Math.round(totalFeedback * (positiveRate / 100))} ratings
                </p>
              </div>

              <div className="bg-white/5 border border-white/5 p-3 rounded-xl backdrop-blur-sm group/metric">
                <div className="flex items-center gap-2 mb-1">
                  <ThumbsDown size={12} className="text-rose-400" />
                  <p className="text-[9px] font-bold text-white/30 uppercase tracking-tighter">Negative</p>
                </div>
                <p className="text-xl font-black text-white group-hover/metric:text-rose-400 transition-colors">
                  {Math.round(negativeRate)}%
                </p>
                <p className="text-[8px] text-white/20 mt-1">
                  {Math.round(totalFeedback * (negativeRate / 100))} ratings
                </p>
              </div>
            </div>

            {/* Feedback Themes */}
            {feedbackData?.themes && feedbackData.themes.length > 0 && (
              <div className="space-y-2">
                <div className="flex items-center gap-2 mb-2">
                  <TrendingUp size={12} className="text-white/40" />
                  <p className="text-[9px] font-black text-white/20 uppercase tracking-widest">Top Themes</p>
                </div>
                <div className="space-y-1.5">
                  {feedbackData.themes.slice(0, 5).map((theme, idx) => (
                    <div
                      key={idx}
                      className={`flex items-center justify-between text-[9px] p-2 rounded-lg ${
                        theme.sentiment === 'positive'
                          ? 'bg-[#00f5d4]/5 border border-[#00f5d4]/10'
                          : 'bg-rose-400/5 border border-rose-400/10'
                      }`}
                    >
                      <span className={`font-medium ${
                        theme.sentiment === 'positive' ? 'text-[#00f5d4]/80' : 'text-rose-400/80'
                      }`}>
                        {theme.theme}
                      </span>
                      <span className={`font-black ${
                        theme.sentiment === 'positive' ? 'text-[#00f5d4]' : 'text-rose-400'
                      }`}>
                        {theme.count}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Total Feedback Count */}
            <div className="pt-2 border-t border-white/5">
              <div className="flex items-center justify-between">
                <span className="text-[9px] font-black text-white/20 uppercase tracking-widest">Total Feedback</span>
                <span className="text-[10px] font-black text-white">{totalFeedback}</span>
              </div>
            </div>

            {/* Last Updated */}
            {feedbackData?.lastUpdated && (
              <div className="pt-2 border-t border-white/5">
                <p className="text-[8px] font-black text-white/20 uppercase tracking-wider">
                  Last updated: {new Date(feedbackData.lastUpdated).toLocaleString()}
                </p>
              </div>
            )}
          </>
        )}
      </div>
    </StatCard>
  );
}

export default CustomerFeedbackWidget;
