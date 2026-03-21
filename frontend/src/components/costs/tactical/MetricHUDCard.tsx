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
    mantis: 'shadow-[inset_0_0_20px_rgba(0,245,212,0.05)]',
    amber: 'shadow-[inset_0_0_20px_rgba(245,158,11,0.05)]',
    rose: 'shadow-[inset_0_0_20px_rgba(244,63,94,0.05)]',
    default: 'shadow-[inset_0_0_20px_rgba(255,255,255,0.02)]'
  };

  return (
    <div 
      className={cn(
        "relative overflow-hidden bg-white/[0.03] backdrop-blur-md rounded-2xl p-6 transition-all duration-300 hover:bg-white/[0.05] group/card",
        accentGlows[accent],
        className
      )}
      {...props}
    >
      {/* Ghost Border (Low opacity outline for structure without "lines") */}
      <div className="absolute inset-0 rounded-2xl border border-white/[0.05] pointer-events-none group-hover/card:border-[var(--mantis-glow)]/10 transition-colors" />
      {/* Neural Background Grid */}
      <div className="absolute inset-0 opacity-[0.03] pointer-events-none" 
           style={{ backgroundImage: 'radial-gradient(circle at 2px 2px, rgba(255,255,255,0.2) 1px, transparent 0)', backgroundSize: '16px 16px' }} />
      
      <div className="relative z-10 space-y-2">
        <h4 className="text-[10px] font-black uppercase tracking-[0.2em] text-white/40">
          {title}
        </h4>
        
        <div className="flex items-baseline gap-3">
          <span className={cn("text-4xl font-black tracking-tighter leading-none", accentColors[accent])}>
            {value}
          </span>
          {subValue && (
            <span className="text-xl font-black text-white/20 tracking-tighter">
              {subValue}
            </span>
          )}
        </div>

        {(trend || children) && (
          <div className="flex items-center justify-between pt-2">
            {trend && (
              <div className={cn(
                "flex items-center gap-2 px-2 py-0.5 rounded-full text-[9px] font-black uppercase tracking-widest border",
                trend.isPositive ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" : "bg-rose-500/10 text-rose-400 border-rose-500/20"
              )}>
                <span>{trend.value}</span>
              </div>
            )}
            {children}
          </div>
        )}
      </div>
    </div>
  );
};
