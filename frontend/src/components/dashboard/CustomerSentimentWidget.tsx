import { useQuery } from '@tanstack/react-query';
import { Smile, TrendingUp, TrendingDown, AlertTriangle, Meh, Frown } from 'lucide-react';
import { analyticsService } from '../../services/analyticsService';
import { StatCard } from './StatCard';
import { MiniAreaChart } from '../charts/AreaChart';

interface SentimentData {
  period: { days: number };
  current: {
    positiveRate: number;
    positiveCount: number;
    negativeCount: number;
    neutralCount: number;
    totalMessages: number;
  };
  previous: {
    positiveRate: number;
  } | null;
  trend: 'improving' | 'declining' | 'stable';
  trendChange: number | null;
  dailyBreakdown: Array<{
    date: string;
    positiveRate: number;
    negativeRate: number;
    neutralRate: number;
  }>;
  alert: string | null;
}

export function CustomerSentimentWidget() {
  const { data, isLoading } = useQuery({
    queryKey: ['analytics', 'sentimentTrend'],
    queryFn: () => analyticsService.getSentimentTrend(30) as Promise<SentimentData>,
    refetchInterval: 120_000,
    staleTime: 60_000,
  });

  const current = data?.current;
  const trend = data?.trend ?? 'stable';
  const trendChange = data?.trendChange;
  const dailyBreakdown = data?.dailyBreakdown ?? [];
  const alert = data?.alert;

  const trendIcon = trend === 'improving' ? <TrendingUp size={14} className="text-green-400" /> 
    : trend === 'declining' ? <TrendingDown size={14} className="text-red-400" /> 
    : null;

  const trendLabel = trend === 'improving' ? 'Improving' 
    : trend === 'declining' ? 'Declining' 
    : 'Stable';

  const positivePct = Math.round((current?.positiveRate ?? 0) * 100);
  const negativeCount = current?.negativeCount ?? 0;
  const neutralCount = current?.neutralCount ?? 0;
  const totalMessages = current?.totalMessages ?? 1;
  const negativePct = Math.round((negativeCount / totalMessages) * 100);
  const neutralPct = Math.round((neutralCount / totalMessages) * 100);

  // Animated emoji indicator
  const getSentimentEmoji = () => {
    if (positivePct >= 80) return <Smile size={48} className="text-[#00f5d4] animate-pulse" />;
    if (positivePct >= 60) return <Smile size={48} className="text-[#fb923c]" />;
    if (positivePct >= 40) return <Meh size={48} className="text-yellow-400" />;
    return <Frown size={48} className="text-rose-400" />;
  };

  // Prepare timeline data for mini chart
  const timelineData = dailyBreakdown.slice(-14).map(day => ({
    name: day.date,
    value: day.positiveRate * 100,
  }));

  return (
    <StatCard
      title="Sentiment"
      value={`${positivePct}%`}
      subValue="Customer satisfaction"
      icon={getSentimentEmoji()}
      accentColor={trend === 'improving' ? 'mantis' : trend === 'declining' ? 'red' : 'purple'}
      data-testid="customer-sentiment-widget"
      isLoading={isLoading}
      miniChart={
        !isLoading && (
          <div className="mt-4">
            {/* Sentiment Timeline Mini Chart */}
            {timelineData.length > 0 && (
              <MiniAreaChart
                data={timelineData}
                dataKey="value"
                height={60}
                color={trend === 'improving' ? '#00f5d4' : trend === 'declining' ? '#f87171' : '#a78bfa'}
              />
            )}
          </div>
        )
      }
      expandable
    >
      <div className="space-y-2 mt-2">
        {alert && (
          <div className="flex items-center gap-1.5 p-2 bg-red-500/10 rounded-lg text-red-400 border border-red-500/20">
            <AlertTriangle size={12} />
            <span className="text-xs">{alert}</span>
          </div>
        )}

        <div className="flex items-center justify-between">
          <span className="text-xs text-white/60">Trend</span>
          <div className="flex items-center gap-1">
            {trendIcon}
            <span className={`text-xs font-medium ${trend === 'improving' ? 'text-green-400' : trend === 'declining' ? 'text-red-400' : 'text-white/60'}`}>
              {trendLabel}
              {trendChange != null && ` (${trendChange > 0 ? '+' : ''}${trendChange}%)`}
            </span>
          </div>
        </div>

        <div className="flex items-center justify-between text-xs">
          <span className="text-green-400 flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-green-400" />
            Positive
          </span>
          <span className="font-semibold text-white">{current?.positiveCount ?? 0}</span>
        </div>

        <div className="flex items-center justify-between text-xs">
          <span className="text-red-400 flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-red-400" />
            Negative
          </span>
          <span className="font-semibold text-white">{current?.negativeCount ?? 0}</span>
        </div>

        <div className="flex items-center justify-between text-xs">
          <span className="text-white/60 flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-white/30" />
            Neutral
          </span>
          <span className="font-semibold text-white/60">{current?.neutralCount ?? 0}</span>
        </div>

        {dailyBreakdown.length > 0 && (
          <div className="pt-2 border-t border-white/10">
            <div className="flex items-center justify-between mb-2">
              <div className="text-xs text-white/60">Last 14 days</div>
              <div className="flex items-center gap-1">
                {trendIcon}
                <span className={`text-xs font-medium ${
                  trend === 'improving' ? 'text-[#00f5d4]' :
                  trend === 'declining' ? 'text-rose-400' :
                  'text-white/60'
                }`}>
                  {trendLabel}
                  {trendChange != null && ` (${trendChange > 0 ? '+' : ''}${trendChange}%)`}
                </span>
              </div>
            </div>

            {/* Visual sentiment timeline bar */}
            <div className="flex gap-0.5 h-8">
              {dailyBreakdown.slice(-14).map((day, i) => (
                <div
                  key={i}
                  className="flex-1 rounded-sm transition-all hover:opacity-100 cursor-pointer border border-white/5"
                  style={{
                    backgroundColor: day.positiveRate > 0.6 ? 'rgba(0, 245, 212, 0.6)' :
                                   day.positiveRate > 0.4 ? 'rgba(251, 191, 36, 0.6)' :
                                   'rgba(248, 113, 113, 0.6)',
                    opacity: 0.8,
                  }}
                  title={`${day.date}: ${Math.round(day.positiveRate * 100)}% positive`}
                />
              ))}
            </div>
          </div>
        )}
      </div>
    </StatCard>
  );
}

export default CustomerSentimentWidget;
