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

const COLOR_MAP: Record<string, { bg: string; text: string; ring: string }> = {
  blue: {
    bg: 'bg-blue-50',
    text: 'text-blue-600',
    ring: 'ring-blue-100',
  },
  green: {
    bg: 'bg-green-50',
    text: 'text-green-600',
    ring: 'ring-green-100',
  },
  purple: {
    bg: 'bg-purple-50',
    text: 'text-purple-600',
    ring: 'ring-purple-100',
  },
  orange: {
    bg: 'bg-orange-50',
    text: 'text-orange-600',
    ring: 'ring-orange-100',
  },
  red: {
    bg: 'bg-red-50',
    text: 'text-red-600',
    ring: 'ring-red-100',
  },
  teal: {
    bg: 'bg-teal-50',
    text: 'text-teal-600',
    ring: 'ring-teal-100',
  },
};

function TrendBadge({ trend }: { trend: number }) {
  if (trend === 0) return null;
  const isUp = trend > 0;
  const cls = isUp
    ? 'bg-green-100 text-green-700'
    : 'bg-red-100 text-red-700';
  const arrow = isUp ? '▲' : '▼';
  return (
    <span
      className={`inline-flex items-center gap-0.5 rounded-full px-2 py-0.5 text-xs font-semibold ${cls}`}
    >
      {arrow} {Math.abs(trend)}%
    </span>
  );
}

function SkeletonLine({ width = 'w-full', height = 'h-4' }: { width?: string; height?: string }) {
  return (
    <div
      className={`${width} ${height} rounded bg-gray-200 animate-pulse`}
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

  const cardBase =
    'relative overflow-hidden rounded-2xl bg-white border border-gray-100 shadow-sm transition-all duration-200';
  const clickable = onClick
    ? 'cursor-pointer hover:shadow-md hover:-translate-y-0.5 active:translate-y-0'
    : '';

  return (
    <div
      className={`${cardBase} ${clickable}`}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      onKeyDown={onClick ? (e) => e.key === 'Enter' && onClick() : undefined}
      data-testid="stat-card"
    >
      {/* Subtle gradient accent strip at the top */}
      <div
        className={`absolute inset-x-0 top-0 h-1 ${colors.bg.replace('bg-', 'bg-gradient-to-r from-').replace('-50', '-400')} to-transparent opacity-60`}
      />

      <div className="p-5">
        <div className="flex items-start justify-between mb-3">
          <div>
            <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">{title}</p>
            {isLoading ? (
              <SkeletonLine width="w-28" height="h-8" />
            ) : (
              <p className="mt-1 text-3xl font-bold text-gray-900 tracking-tight">{value}</p>
            )}
          </div>
          <div
            className={`flex h-10 w-10 items-center justify-center rounded-xl ${colors.bg} ${colors.text} ring-4 ${colors.ring}`}
          >
            {icon}
          </div>
        </div>

        {/* Sub value row */}
        {isLoading ? (
          <SkeletonLine width="w-40" height="h-3" />
        ) : (
          <div className="flex items-center gap-2 flex-wrap">
            {subValue && (
              <p className="text-sm text-gray-500">{subValue}</p>
            )}
            {trend !== undefined && <TrendBadge trend={trend} />}
          </div>
        )}

        {/* Slot for extra content */}
        {!isLoading && children && (
          <div className="mt-4">{children}</div>
        )}
        {isLoading && children && (
          <div className="mt-4 space-y-2">
            <SkeletonLine />
            <SkeletonLine width="w-3/4" />
          </div>
        )}
      </div>
    </div>
  );
}

export default StatCard;
