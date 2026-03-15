import { useQuery } from '@tanstack/react-query';
import { Smile, TrendingUp, TrendingDown, AlertTriangle } from 'lucide-react';
import { analyticsService } from '../../services/analyticsService';
import { StatCard } from './StatCard';

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

  const trendIcon = trend === 'improving' ? <TrendingUp size={14} className="text-green-600" /> 
    : trend === 'declining' ? <TrendingDown size={14} className="text-red-600" /> 
    : null;

  const trendLabel = trend === 'improving' ? 'Improving' 
    : trend === 'declining' ? 'Declining' 
    : 'Stable';

  const positivePct = Math.round((current?.positiveRate ?? 0) * 100);

  return (
    <StatCard
      title="Sentiment"
      value={`${positivePct}%`}
      subValue="Customer satisfaction"
      icon={<Smile size={18} />}
      accentColor={trend === 'improving' ? 'green' : trend === 'declining' ? 'red' : 'blue'}
      data-testid="customer-sentiment-widget"
      isLoading={isLoading}
    >
      <div className="space-y-2 mt-2">
        {alert && (
          <div className="flex items-center gap-1.5 p-2 bg-red-50 rounded-lg text-red-700">
            <AlertTriangle size={12} />
            <span className="text-xs">{alert}</span>
          </div>
        )}

        <div className="flex items-center justify-between">
          <span className="text-xs text-gray-500">Trend</span>
          <div className="flex items-center gap-1">
            {trendIcon}
            <span className={`text-xs font-medium ${trend === 'improving' ? 'text-green-600' : trend === 'declining' ? 'text-red-600' : 'text-gray-600'}`}>
              {trendLabel}
              {trendChange != null && ` (${trendChange > 0 ? '+' : ''}${trendChange}%)`}
            </span>
          </div>
        </div>

        <div className="flex items-center justify-between text-xs">
          <span className="text-green-600 flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-green-400" />
            Positive
          </span>
          <span className="font-semibold text-gray-700">{current?.positiveCount ?? 0}</span>
        </div>

        <div className="flex items-center justify-between text-xs">
          <span className="text-red-600 flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-red-400" />
            Negative
          </span>
          <span className="font-semibold text-gray-700">{current?.negativeCount ?? 0}</span>
        </div>

        <div className="flex items-center justify-between text-xs">
          <span className="text-gray-500 flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-gray-300" />
            Neutral
          </span>
          <span className="font-semibold text-gray-600">{current?.neutralCount ?? 0}</span>
        </div>

        {dailyBreakdown.length > 0 && (
          <div className="pt-2 border-t border-gray-100">
            <div className="text-xs text-gray-400 mb-1">Last 7 days</div>
            <div className="flex gap-1">
              {dailyBreakdown.slice(-7).map((day, i) => (
                <div
                  key={i}
                  className="flex-1 h-6 rounded-sm"
                  style={{
                    backgroundColor: day.positiveRate > 0.6 ? '#86efac' : day.positiveRate > 0.4 ? '#fcd34d' : '#fca5a5',
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
