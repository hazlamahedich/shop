import { useQuery } from '@tanstack/react-query';
import { Cpu, AlertTriangle, CheckCircle, TrendingUp, TrendingDown, Star } from 'lucide-react';
import { analyticsService } from '../../services/analyticsService';
import { StatCard } from './StatCard';

const HEALTH_CONFIG = {
  healthy: {
    color: 'mantis',
    label: 'OPTIMAL',
    icon: CheckCircle,
  },
  warning: {
    color: 'orange',
    label: 'DEGRADED',
    icon: AlertTriangle,
  },
  critical: {
    color: 'red',
    label: 'CRITICAL',
    icon: AlertTriangle,
  },
} as const;

function renderStars(score: number | null): React.ReactNode {
  if (score === null) return <span className="text-white/20">N/A</span>;
  const fullStars = Math.floor(score);
  const hasHalf = score - fullStars >= 0.5;
  const stars = [];
  for (let i = 0; i < 5; i++) {
    if (i < fullStars) {
      stars.push(<Star key={i} size={10} className="fill-[#00f5d4] text-[#00f5d4] drop-shadow-[0_0_5px_rgba(0,245,212,0.5)]" />);
    } else if (i === fullStars && hasHalf) {
      stars.push(<Star key={i} size={10} className="fill-[#00f5d4]/40 text-[#00f5d4] opacity-70" />);
    } else {
      stars.push(<Star key={i} size={10} className="text-white/10" />);
    }
  }
  return (
    <span className="flex items-center gap-1">
      {stars}
      <span className="ml-1 text-[10px] font-black text-[#00f5d4]">{score.toFixed(1)}</span>
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
    <div className="flex items-center justify-between gap-1 py-1.5 border-b border-white/5 last:border-0 group/row">
      <span className="text-[10px] font-bold text-white/30 uppercase tracking-widest group-hover/row:text-white/50 transition-colors uppercase">{label}</span>
      <div className="flex items-center gap-2">
        <span className="text-[10px] font-black text-white/80 group-hover/row:text-white transition-colors">{value}</span>
        {trend !== null && trend !== undefined && (
          <span
            className={`text-[9px] font-black flex items-center gap-0.5 rounded px-1.5 py-0.5 ${
              trend >= 0 ? 'bg-[#00f5d4]/10 text-[#00f5d4]' : 'bg-rose-500/10 text-rose-400'
            } border border-white/5`}
          >
            {trend >= 0 ? <TrendingUp size={9} strokeWidth={3} /> : <TrendingDown size={9} strokeWidth={3} />}
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
    : '0.0%';
  const resolutionRate = data?.resolutionRate != null
    ? `${(data.resolutionRate * 100).toFixed(1)}%`
    : '0.0%';

  return (
    <StatCard
      title="Neural Performance"
      value={data?.csatScore != null ? data.csatScore.toFixed(1) : '--'}
      icon={<Cpu size={18} />}
      accentColor={healthConfig.color}
      data-testid="bot-quality-widget"
      isLoading={isLoading}
    >
      <div className="space-y-0.5 mt-2">
        <div className="flex items-center justify-between gap-1 py-2 border-b border-white/5">
          <span className="text-[10px] font-black text-white/20 uppercase tracking-[0.2em]">STATUS_ARRAY</span>
          <span className={`flex items-center gap-1.5 text-[10px] font-black px-2 py-0.5 rounded bg-[#00f5d4]/5 border border-[#00f5d4]/20 text-[#00f5d4] shadow-[0_0_10px_rgba(0,245,212,0.1)]`}>
            <HealthIcon size={10} strokeWidth={3} />
            {healthConfig.label}
          </span>
        </div>

        <MetricRow label="GRID CSAT" value={renderStars(data?.csatScore ?? null)} trend={data?.csatChange ?? null} />
        <MetricRow label="RESP_LATENCY" value={avgResponseTime} />
        <MetricRow label="FALLBACK_RATE" value={fallbackRate} />
        <MetricRow label="RESOLVE_MESH" value={resolutionRate} />
      </div>
    </StatCard>
  );
}

export default BotQualityWidget;
