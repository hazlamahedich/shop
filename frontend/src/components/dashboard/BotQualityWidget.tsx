import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Cpu, AlertTriangle, CheckCircle, TrendingUp, TrendingDown, Star, ArrowRight, Lightbulb, Zap, Shield, Target } from 'lucide-react';
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

interface MetricBarProps {
  label: string;
  value: number;
  icon: React.ElementType;
  color: string;
  showLabel?: boolean;
}

function MetricBar({ label, value, icon: Icon, color, showLabel = true }: MetricBarProps) {
  const getGrade = (val: number) => {
    if (val >= 80) return { grade: 'A', color: '#00f5d4' };
    if (val >= 60) return { grade: 'B', color: '#fb923c' };
    return { grade: 'C', color: '#f87171' };
  };

  const { grade, color: gradeColor } = getGrade(value);

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Icon size={12} className="text-white/40" />
          {showLabel && <span className="text-[9px] font-bold text-white/40 uppercase tracking-wider">{label}</span>}
        </div>
        <span className="text-[10px] font-black" style={{ color: gradeColor }}>{value}%</span>
      </div>
      <div className="relative h-2 bg-white/5 rounded-full overflow-hidden">
        <div
          className="absolute inset-y-0 left-0 rounded-full transition-all duration-500"
          style={{
            width: `${value}%`,
            backgroundColor: color,
            boxShadow: `0 0 10px ${color}40`,
          }}
        />
      </div>
    </div>
  );
}

interface ImprovementTipProps {
  icon: React.ElementType;
  title: string;
  description: string;
  priority: 'high' | 'medium' | 'low';
}

function ImprovementTip({ icon: Icon, title, description, priority }: ImprovementTipProps) {
  const priorityConfig = {
    high: { color: 'bg-rose-500/10 border-rose-500/20 text-rose-400', dot: 'bg-rose-400' },
    medium: { color: 'bg-amber-500/10 border-amber-500/20 text-amber-400', dot: 'bg-amber-400' },
    low: { color: 'bg-[#00f5d4]/5 border-[#00f5d4]/20 text-[#00f5d4]', dot: 'bg-[#00f5d4]' },
  };

  const config = priorityConfig[priority];

  return (
    <div className={`p-2 rounded-lg border ${config.color} group/tip hover:border-opacity-40 transition-all cursor-help`}>
      <div className="flex items-start gap-2">
        <Icon size={14} className="mt-0.5 flex-shrink-0" />
        <div className="flex-1 min-w-0">
          <p className="text-[9px] font-black uppercase tracking-wider mb-0.5">{title}</p>
          <p className="text-[8px] text-white/60 leading-relaxed">{description}</p>
        </div>
        <div className={`w-1.5 h-1.5 rounded-full ${config.dot} flex-shrink-0 mt-1`} />
      </div>
    </div>
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

  // Calculate performance metrics (0-100 scale)
  const accuracyScore = data?.csatScore != null ? data.csatScore * 20 : 70;
  const speedScore = data?.avgResponseTimeSeconds != null
    ? Math.max(0, 100 - (data.avgResponseTimeSeconds / 10) * 100)
    : 75;
  const resolutionScore = data?.resolutionRate != null ? data.resolutionRate * 100 : 80;
  const stabilityScore = data?.fallbackRate != null ? (1 - data.fallbackRate) * 100 : 85;

  // Generate improvement tips based on performance
  const getImprovementTips = (): ImprovementTipProps[] => {
    const tips: ImprovementTipProps[] = [];

    if (accuracyScore < 70) {
      tips.push({
        icon: Star,
        title: 'Boost Accuracy',
        description: 'Review unresolved conversations to improve knowledge base',
        priority: 'high',
      });
    }

    if (speedScore < 70) {
      tips.push({
        icon: Zap,
        title: 'Improve Speed',
        description: 'Optimize knowledge base queries and response generation',
        priority: 'high',
      });
    }

    if (resolutionScore < 70) {
      tips.push({
        icon: Target,
        title: 'Increase Resolutions',
        description: 'Add more FAQs and improve conversation flow',
        priority: 'medium',
      });
    }

    if (stabilityScore < 70) {
      tips.push({
        icon: Shield,
        title: 'Enhance Stability',
        description: 'Reduce fallback rate by expanding knowledge coverage',
        priority: 'medium',
      });
    }

    // If everything is good, add positive tip
    if (tips.length === 0) {
      tips.push({
        icon: Lightbulb,
        title: 'Excellent Performance',
        description: 'Your bot is performing optimally. Keep monitoring trends.',
        priority: 'low',
      });
    }

    return tips.slice(0, 2); // Show max 2 tips
  };

  const improvementTips = getImprovementTips();

  return (
    <StatCard
      title="Neural Performance"
      value={data?.csatScore != null ? data.csatScore.toFixed(1) : '--'}
      icon={<Cpu size={18} />}
      accentColor={healthConfig.color}
      data-testid="bot-quality-widget"
      isLoading={isLoading}
      expandable
    >
      {/* Performance Bars */}
      {!isLoading && data?.csatScore && (
        <div className="space-y-3 mb-4">
          <div className="flex items-center justify-between">
            <span className="text-[9px] font-black text-white/30 uppercase tracking-wider">
              Performance_Metrics
            </span>
            <div className="flex items-center gap-2">
              <HealthIcon size={12} className={healthConfig.color === 'mantis' ? 'text-[#00f5d4]' : 'text-amber-400'} />
              <span className={`text-[9px] font-black ${healthConfig.color === 'mantis' ? 'text-[#00f5d4]' : 'text-amber-400'}`}>
                {healthConfig.label}
              </span>
            </div>
          </div>

          <MetricBar
            label="Accuracy"
            value={Math.round(accuracyScore)}
            icon={Star}
            color="#00f5d4"
          />
          <MetricBar
            label="Speed"
            value={Math.round(speedScore)}
            icon={Zap}
            color="#a855f7"
          />
          <MetricBar
            label="Resolution"
            value={Math.round(resolutionScore)}
            icon={Target}
            color="#3b82f6"
          />
          <MetricBar
            label="Stability"
            value={Math.round(stabilityScore)}
            icon={Shield}
            color="#f59e0b"
          />
        </div>
      )}

      {/* AI Improvement Tips */}
      {!isLoading && data?.csatScore && improvementTips.length > 0 && (
        <div className="mb-4">
          <div className="flex items-center gap-2 mb-2">
            <Lightbulb size={12} className="text-[#00f5d4]" />
            <span className="text-[9px] font-black text-white/30 uppercase tracking-wider">
              AI_Insights
            </span>
          </div>
          <div className="space-y-2">
            {improvementTips.map((tip, idx) => (
              <ImprovementTip key={idx} {...tip} />
            ))}
          </div>
        </div>
      )}

      {/* Quick Stats */}
      <div className="space-y-0.5 mt-2">
        <div className="flex items-center justify-between gap-1 py-2 border-b border-white/5">
          <span className="text-[10px] font-black text-white/20 uppercase tracking-[0.2em]">Quick_Stats</span>
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
