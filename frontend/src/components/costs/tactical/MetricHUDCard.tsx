import React from 'react';
import { cn } from '../../../lib/utils';

interface MetricHUDCardProps extends React.HTMLAttributes<HTMLDivElement> {
  title: string;
  value: string | number;
  subValue?: string;
  trend?: {
    value: string;
    isPositive: boolean;
  };
  accent?: 'mantis' | 'amber' | 'rose' | 'default';
}

export const MetricHUDCard: React.FC<MetricHUDCardProps> = ({
  title,
  value,
  subValue,
  trend,
  accent = 'default',
  className,
  children,
  ...props
}) => {
  const accentColors = {
    mantis: 'text-[var(--mantis-glow)]',
    amber: 'text-amber-500',
    rose: 'text-rose-500',
    default: 'text-white'
  };

  const accentGlows = {
    mantis: 'shadow-[inset_0_0_20px_rgba(0,245,212,0.05)] group-hover/card:shadow-[inset_0_0_30px_rgba(0,245,212,0.1)]',
    amber: 'shadow-[inset_0_0_20px_rgba(245,158,11,0.05)] group-hover/card:shadow-[inset_0_0_30px_rgba(245,158,11,0.1)]',
    rose: 'shadow-[inset_0_0_20px_rgba(244,63,94,0.05)] group-hover/card:shadow-[inset_0_0_30px_rgba(244,63,94,0.1)]',
    default: 'shadow-[inset_0_0_20px_rgba(255,255,255,0.02)] group-hover/card:shadow-[inset_0_0_30px_rgba(255,255,255,0.05)]'
  };

  const borderGlows = {
    mantis: 'group-hover/card:border-[var(--mantis-glow)]/20',
    amber: 'group-hover/card:border-amber-500/20',
    rose: 'group-hover/card:border-rose-500/20',
    default: 'group-hover/card:border-white/10'
  };

  return (
    <div 
      className={cn(
        "relative overflow-hidden bg-white/[0.02] backdrop-blur-xl rounded-2xl p-8 transition-all duration-500 hover:bg-white/[0.04] group/card",
        accentGlows[accent],
        className
      )}
      {...props}
    >
      {/* Ghost Border */}
      <div className={cn("absolute inset-0 rounded-2xl border border-white/[0.05] pointer-events-none transition-colors duration-500", borderGlows[accent])} />
      {/* Neural Background Grid */}
      <div className="absolute inset-0 opacity-[0.03] pointer-events-none transition-opacity duration-500 group-hover/card:opacity-[0.05]" 
           style={{ backgroundImage: 'radial-gradient(circle at 2px 2px, rgba(255,255,255,0.2) 1px, transparent 0)', backgroundSize: '16px 16px' }} />
      
      <div className="relative z-10 space-y-4">
        <h4 className="text-[10px] font-black uppercase tracking-[0.2em] text-white/40">
          {title}
        </h4>
        
        <div className="flex items-baseline gap-3">
          <span className={cn("text-5xl font-black tracking-tighter leading-none relative", accentColors[accent], "group-hover/card:scale-[1.02] origin-left transition-transform duration-500")}>
            {value}
          </span>
          {subValue && (
            <span className="text-xl font-black text-white/20 tracking-tighter group-hover/card:text-white/40 transition-colors duration-500">
              {subValue}
            </span>
          )}
        </div>

        {(trend || children) && (
          <div className="flex items-center justify-between pt-4">
            {trend && (
              <div className={cn(
                "flex items-center gap-2 px-3 py-1 rounded border shadow-sm transition-all duration-500",
                trend.isPositive ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20 group-hover/card:border-emerald-500/40 group-hover/card:shadow-[0_0_10px_rgba(16,185,129,0.2)]" : "bg-rose-500/10 text-rose-400 border-rose-500/20 group-hover/card:border-rose-500/40 group-hover/card:shadow-[0_0_10px_rgba(244,63,94,0.2)]"
              )}>
                <span className="text-[10px] font-black uppercase tracking-widest">{trend.value}</span>
              </div>
            )}
            {children}
          </div>
        )}
      </div>
    </div>
  );
};
