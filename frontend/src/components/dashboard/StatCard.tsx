import React, { useState } from 'react';
import { Maximize2, Minimize2 } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string | number;
  subValue?: string;
  icon: React.ReactNode;
  trend?: number; // positive = up, negative = down, 0 neutral
  accentColor?: string; // Tailwind color token e.g. 'blue' | 'green' | 'purple' | 'orange' | 'red'
  onClick?: () => void;
  isLoading?: boolean;
  children?: React.ReactNode;
  'data-testid'?: string;
  // NEW: Chart support props
  miniChart?: React.ReactNode; // Mini visualization to show below stats
  chartType?: 'none' | 'sparkline' | 'donut' | 'bar' | 'area';
  chartData?: number[] | Array<{ value: number; label?: string }>;
  expandable?: boolean; // Can expand to show full chart
  onExpand?: () => void;
}

const COLOR_MAP: Record<string, { bg: string; text: string; border: string; glow: string }> = {
  blue: {
    bg: 'bg-blue-500/10',
    text: 'text-blue-400',
    border: 'border-blue-500/20',
    glow: 'shadow-[0_0_15px_rgba(34,197,94,0.05)]',
  },
  mantis: {
    bg: 'bg-[#00f5d4]/10',
    text: 'text-[#00f5d4]',
    border: 'border-[#00f5d4]/20',
    glow: 'shadow-[0_0_20px_rgba(0,245,212,0.1)]',
  },
  purple: {
    bg: 'bg-violet-500/10',
    text: 'text-violet-400',
    border: 'border-violet-500/20',
    glow: 'shadow-[0_0_15px_rgba(139,92,246,0.05)]',
  },
  orange: {
    bg: 'bg-amber-500/10',
    text: 'text-amber-400',
    border: 'border-amber-500/20',
    glow: 'shadow-[0_0_15px_rgba(245,158,11,0.05)]',
  },
  red: {
    bg: 'bg-rose-500/10',
    text: 'text-rose-400',
    border: 'border-rose-500/20',
    glow: 'shadow-[0_0_15px_rgba(244,63,94,0.05)]',
  },
  teal: {
    bg: 'bg-teal-500/10',
    text: 'text-teal-400',
    border: 'border-teal-500/20',
    glow: 'shadow-[0_0_15px_rgba(20,184,166,0.05)]',
  },
};

function TrendBadge({ trend }: { trend: number }) {
  if (trend === 0) return null;
  const isUp = trend > 0;
  const cls = isUp
    ? 'bg-[#00f5d4]/20 text-[#00f5d4]'
    : 'bg-rose-500/20 text-rose-400';
  const arrow = isUp ? '↑' : '↓';
  return (
    <span
      className={`inline-flex items-center gap-0.5 rounded-lg px-2 py-0.5 text-[10px] font-black uppercase tracking-wider ${cls} border border-white/5`}
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
  accentColor = 'mantis',
  onClick,
  isLoading = false,
  children,
  'data-testid': testId = 'stat-card',
  miniChart,
  chartType = 'none',
  chartData,
  expandable = false,
  onExpand,
}: StatCardProps) {
  const colors = COLOR_MAP[accentColor] ?? COLOR_MAP.mantis;
  const [isExpanded, setIsExpanded] = useState(false);

  const clickable = onClick || expandable
    ? 'cursor-pointer hover:scale-[1.02] active:scale-[0.98]'
    : '';

  const handleClick = () => {
    if (expandable && onExpand) {
      onExpand();
      setIsExpanded(!isExpanded);
    } else if (onClick) {
      onClick();
    }
  };

  return (
    <div
      className={`glass-card p-6 transition-all duration-400 ${clickable} ${colors.glow} group overflow-hidden relative ${isExpanded ? 'fixed inset-4 z-50 rounded-2xl' : ''}`}
      onClick={handleClick}
      role={onClick || expandable ? 'button' : undefined}
      tabIndex={onClick || expandable ? 0 : undefined}
      onKeyDown={(e) => (e.key === 'Enter' && handleClick())}
      data-testid={testId}
    >
      <div className="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-transparent via-[#00f5d4]/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />

      {/* Expand button */}
      {expandable && (
        <button
          className="absolute top-4 right-4 p-1.5 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-white/30 hover:text-white/60 transition-all"
          onClick={(e) => {
            e.stopPropagation();
            setIsExpanded(!isExpanded);
          }}
          aria-label={isExpanded ? 'Collapse' : 'Expand'}
        >
          {isExpanded ? <Minimize2 size={14} /> : <Maximize2 size={14} />}
        </button>
      )}
      
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1 min-w-0">
          <p className="text-[10px] font-black text-white/50 uppercase tracking-[0.2em]">{title}</p>
          {isLoading ? (
            <div className="mt-2 text-3xl font-black tracking-tighter text-transparent">
              <SkeletonLine width="w-28" height="h-8" />
            </div>
          ) : (
            <p className="mt-1 text-4xl font-black text-white tracking-tighter truncate font-heading group-hover:text-[#00f5d4] transition-colors duration-300 drop-shadow-[0_0_10px_rgba(0,245,212,0.1)]">{value}</p>
          )}
        </div>
        <div
          className={`flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-2xl ${colors.bg} ${colors.text} border ${colors.border} shadow-lg backdrop-blur-xl transition-all duration-500 group-hover:rotate-[360deg] group-hover:scale-110 shadow-[inner_0_0_10px_rgba(255,255,255,0.05)]`}
        >
          {React.cloneElement(icon as React.ReactElement, { size: 20, strokeWidth: 2.5 })}
        </div>
      </div>

      <div className="flex items-center gap-3 flex-wrap min-h-[24px]">
        {isLoading ? (
          <SkeletonLine width="w-40" height="h-3" />
        ) : (
          <>
             {subValue && (
                <p className="text-[11px] font-bold text-white/50 uppercase tracking-widest">{subValue}</p>
             )}
            {trend !== undefined && <TrendBadge trend={trend} />}
          </>
        )}
      </div>

      {!isLoading && (children || miniChart) && (
        <div className="mt-6 border-t border-white/5 pt-4">
          {children}
          {/* Render mini chart if provided */}
          {miniChart && !isExpanded && (
            <div className="mt-4" aria-hidden="true">
              {miniChart}
            </div>
          )}
          {/* Expanded chart view */}
          {isExpanded && miniChart && (
            <div className="mt-4 h-64">
              {miniChart}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default StatCard;
