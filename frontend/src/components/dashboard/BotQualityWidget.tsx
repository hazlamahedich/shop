import { useQuery } from '@tanstack/react-query';
import { Cpu, AlertTriangle, CheckCircle, TrendingUp, TrendingDown, Star } from 'lucide-react';
import { analyticsService } from '../../services/analyticsService';
import { StatCard } from './StatCard';

const HEALTH_CONFIG = {
  healthy: {
    color: 'green',
    label: 'Healthy',
    icon: CheckCircle,
  },
  warning: {
    color: 'orange',
    label: 'Needs Attention',
    icon: AlertTriangle,
  },
  critical: {
    color: 'red',
    label: 'Critical',
    icon: AlertTriangle,
  },
} as const;

function renderStars(score: number | null): React.ReactNode {
  if (score === null) return <span className="text-gray-400">N/A</span>;
  const fullStars = Math.floor(score);
  const hasHalf = score - fullStars >= 0.5;
  const stars = [];
  for (let i = 0; i < 5; i++) {
    if (i < fullStars) {
      stars.push(<Star key={i} size={12} className="fill-yellow-400 text-yellow-400" />);
    } else if (i === fullStars && hasHalf) {
      stars.push(<Star key={i} size={12} className="fill-yellow-400/50 text-yellow-400" />);
    } else {
      stars.push(<Star key={i} size={12} className="text-gray-300" />);
    }
  }
  return (
    <span className="flex items-center gap-0.5">
      {stars}
      <span className="ml-1 text-xs text-gray-600">{score.toFixed(1)}</span>
    </span>
  );
}

function MetricRow({
  label,
  value,
  trend,
}: {
  label: string;
  value: string | React.ReactNode;
  trend?: number | null;
}) {
  return (
    <div className="flex items-center justify-between gap-1 py-1 border-b border-gray-50 last:border-0">
      <span className="text-xs font-medium text-gray-400">{label}</span>
      <div className="flex items-center gap-1.5">
        <span className="text-xs font-semibold text-gray-700">{value}</span>
        {trend !== null && trend !== undefined && (
          <span
            className={`text-[10px] font-medium flex items-center ${
              trend >= 0 ? 'text-green-600' : 'text-red-600'
            }`}
          >
            {trend >= 0 ? <TrendingUp size={10} /> : <TrendingDown size={10} />}
            {Math.abs(trend).toFixed(0)}%
          </span>
        )}
      </div>
    </div>
  );
}

export function BotQualityWidget() {
  const { data, isLoading } = useQuery({
    queryKey: ['analytics', 'botQuality'],
    queryFn: () => analyticsService.getBotQuality(30),
    refetchInterval: 60_000,
    staleTime: 30_000,
  });

  const healthStatus = data?.healthStatus ?? 'healthy';
  const healthConfig = HEALTH_CONFIG[healthStatus];
  const HealthIcon = healthConfig.icon;

  const avgResponseTime = data?.avgResponseTimeSeconds
    ? `${data.avgResponseTimeSeconds.toFixed(1)}s`
    : '--';
  const fallbackRate = data?.fallbackRate != null
    ? `${(data.fallbackRate * 100).toFixed(1)}%`
    : '--';
  const resolutionRate = data?.resolutionRate != null
    ? `${(data.resolutionRate * 100).toFixed(1)}%`
    : '--';

  return (
    <StatCard
      title="Bot Quality"
      value={data?.csatScore != null ? data.csatScore.toFixed(1) : '--'}
      icon={<Cpu size={18} />}
      accentColor={healthConfig.color}
      data-testid="bot-quality-widget"
      isLoading={isLoading}
    >
      <div className="space-y-0.5">
        <div className="flex items-center justify-between gap-1 py-1">
          <span className="text-xs font-medium text-gray-400">Health</span>
          <span className={`flex items-center gap-1 text-xs font-medium text-${healthConfig.color}-600`}>
            <HealthIcon size={12} />
            {healthConfig.label}
          </span>
        </div>

        <MetricRow label="CSAT Score" value={renderStars(data?.csatScore ?? null)} trend={data?.csatChange ?? null} />
        <MetricRow label="Avg Response" value={avgResponseTime} />
        <MetricRow label="Fallback Rate" value={fallbackRate} />
        <MetricRow label="Resolution Rate" value={resolutionRate} />
      </div>
    </StatCard>
  );
}

export default BotQualityWidget;
