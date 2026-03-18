import React from 'react';
import { cn } from '../../lib/utils';

interface GlassCardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  accent?: 'blue' | 'violet' | 'pink' | 'teal' | 'amber' | 'mantis' | 'red';
}

export const GlassCard = React.forwardRef<HTMLDivElement, GlassCardProps>(({ 
  children, 
  className, 
  accent,
  ...props 
}, ref) => {
  const accentClasses = {
    blue: 'border-blue-500/20 shadow-blue-500/10',
    violet: 'border-violet-500/20 shadow-violet-500/10',
    pink: 'border-pink-500/20 shadow-pink-500/10',
    teal: 'border-teal-500/20 shadow-teal-500/10',
    amber: 'border-amber-500/20 shadow-amber-500/10',
    mantis: 'border-[var(--mantis-glow)]/20 shadow-[var(--mantis-glow)]/10',
    red: 'border-red-500/20 shadow-red-500/10',
  };

  return (
    <div 
      ref={ref}
      className={cn(
        "glass-card p-6 transition-all duration-300 hover:shadow-2xl",
        accent && accentClasses[accent],
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
});

GlassCard.displayName = 'GlassCard';
