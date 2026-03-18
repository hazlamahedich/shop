import React from 'react';

interface StatCardProps {
  title: string;
  value: string | number;
  subValue?: string;
  icon: React.ReactNode;
  trend?: number; // positive = up, negative = down, 0 = neutral
  accentColor?: string; // Tailwind color token e.g. 'blue' | 'green' | 'purple' | 'orange' | 'red'
  onClick?: () => void;
  isLoading?: boolean;
  children?: React.ReactNode;
}

const COLOR_MAP: Record<string, { bg: string; text: string; border: string; glow: string }> = {
  blue: {
    bg: 'bg-blue-500/10',
    text: 'text-blue-400',
    border: 'border-blue-500/20',
    glow: 'shadow-[0_0_15px_rgba(59,130,246,0.1)]',
  },
  green: {
    bg: 'bg-emerald-500/10',
    text: 'text-emerald-400',
    border: 'border-emerald-500/20',
    glow: 'shadow-[0_0_15px_rgba(16,185,129,0.1)]',
  },
  purple: {
    bg: 'bg-violet-500/10',
    text: 'text-violet-400',
    border: 'border-violet-500/20',
    glow: 'shadow-[0_0_15px_rgba(139,92,246,0.1)]',
  },
  orange: {
    bg: 'bg-amber-500/10',
    text: 'text-amber-400',
    border: 'border-amber-500/20',
    glow: 'shadow-[0_0_15px_rgba(245,158,11,0.1)]',
  },
  red: {
    bg: 'bg-rose-500/10',
    text: 'text-rose-400',
    border: 'border-rose-500/20',
    glow: 'shadow-[0_0_15px_rgba(244,63,94,0.1)]',
  },
  teal: {
    bg: 'bg-teal-500/10',
    text: 'text-teal-400',
    border: 'border-teal-500/20',
    glow: 'shadow-[0_0_15px_rgba(20,184,166,0.1)]',
  },
};

function TrendBadge({ trend }: { trend: number }) {
  if (trend === 0) return null;
  const isUp = trend > 0;
  const cls = isUp
    ? 'bg-emerald-500/20 text-emerald-400'
    : 'bg-rose-500/20 text-rose-400';
  const arrow = isUp ? '↑' : '↓';
  return (
    <span
      className={`inline-flex items-center gap-0.5 rounded-lg px-2 py-0.5 text-xs font-bold ${cls} border border-white/5`}
    >
      {arrow} {Math.abs(trend)}%
    </span>
  );
}

function SkeletonLine({ width = 'w-full', height = 'h-4' }: { width?: string; height?: string }) {
  return (
    <div
      className={`${width} ${height} rounded bg-white/5 animate-pulse`}
    />
  );
}

export function StatCard({
  title,
  value,
  subValue,
  icon,
  trend,
  accentColor = 'blue',
  onClick,
  isLoading = false,
  children,
}: StatCardProps) {
  const colors = COLOR_MAP[accentColor] ?? COLOR_MAP.blue;

  const clickable = onClick
    ? 'cursor-pointer hover:scale-[1.02] active:scale-[0.98]'
    : '';

  return (
    <div
      className={`glass-card p-6 transition-all duration-300 ${clickable} ${colors.glow}`}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      onKeyDown={onClick ? (e) => e.key === 'Enter' && onClick() : undefined}
      data-testid="stat-card"
    >
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1 min-w-0">
          <p className="text-xs font-bold text-white/60 uppercase tracking-widest">{title}</p>
          {isLoading ? (
            <div className="mt-2 text-3xl font-bold tracking-tight text-transparent">
              <SkeletonLine width="w-28" height="h-8" />
            </div>
          ) : (
            <p className="mt-1 text-3xl font-bold text-white tracking-tight truncate mantis-glow-text">{value}</p>
          )}
        </div>
        <div
          className={`flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-2xl ${colors.bg} ${colors.text} border ${colors.border} shadow-lg backdrop-blur-md transition-transform duration-300 hover:rotate-6`}
        >
          {icon}
        </div>
      </div>

      <div className="flex items-center gap-2 flex-wrap min-h-[24px]">
        {isLoading ? (
          <SkeletonLine width="w-40" height="h-3" />
        ) : (
          <>
             {subValue && (
               <p className="text-sm font-medium text-white/60">{subValue}</p>
             )}
            {trend !== undefined && <TrendBadge trend={trend} />}
          </>
        )}
      </div>

      {!isLoading && children && (
        <div className="mt-6 border-t border-white/5 pt-4">{children}</div>
      )}
      {isLoading && children && (
        <div className="mt-6 border-t border-white/5 pt-4 space-y-2">
          <SkeletonLine />
          <SkeletonLine width="w-3/4" />
        </div>
      )}
    </div>
  );
}

export default StatCard;
