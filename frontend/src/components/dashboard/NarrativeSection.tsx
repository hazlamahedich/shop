import React from 'react';
import { LucideIcon } from 'lucide-react';

interface NarrativeSectionProps {
  title: string;
  description?: string;
  icon: LucideIcon;
  color?: 'mantis' | 'purple' | 'orange' | 'red' | 'blue';
  children: React.ReactNode;
  className?: string;
}

const COLOR_STYLES = {
  mantis: {
    text: 'text-[#00f5d4]',
    bg: 'bg-[#00f5d4]',
    border: 'border-[#00f5d4]',
    glow: 'shadow-[0_0_20px_rgba(0,245,212,0.2)]',
    iconBg: 'bg-[#00f5d4]/10',
  },
  purple: {
    text: 'text-violet-400',
    bg: 'bg-violet-400',
    border: 'border-violet-400',
    glow: 'shadow-[0_0_20px_rgba(167,139,250,0.2)]',
    iconBg: 'bg-violet-400/10',
  },
  orange: {
    text: 'text-amber-400',
    bg: 'bg-amber-400',
    border: 'border-amber-400',
    glow: 'shadow-[0_0_20px_rgba(251,191,36,0.2)]',
    iconBg: 'bg-amber-400/10',
  },
  red: {
    text: 'text-rose-400',
    bg: 'bg-rose-400',
    border: 'border-rose-400',
    glow: 'shadow-[0_0_20px_rgba(251,113,133,0.2)]',
    iconBg: 'bg-rose-400/10',
  },
  blue: {
    text: 'text-blue-400',
    bg: 'bg-blue-400',
    border: 'border-blue-400',
    glow: 'shadow-[0_0_20px_rgba(96,165,250,0.2)]',
    iconBg: 'bg-blue-400/10',
  },
};

/**
 * Narrative section wrapper that groups widgets by story act
 * Provides visual hierarchy with icon, title, and color coding
 */
export function NarrativeSection({
  title,
  description,
  icon: Icon,
  color = 'mantis',
  children,
  className = '',
}: NarrativeSectionProps) {
  const styles = COLOR_STYLES[color];

  return (
    <section
      className={`narrative-section space-y-4 ${className}`}
      aria-label={`${title} section`}
    >
      {/* Section Header */}
      <div className="flex items-center gap-3 pb-4 border-b border-white/5">
        <div
          className={`p-2 rounded-xl ${styles.iconBg} border ${styles.border} ${styles.glow}`}
        >
          <Icon size={18} className={styles.text} strokeWidth={2.5} />
        </div>
        <div className="flex-1">
          <h3 className={`text-sm font-black uppercase tracking-widest ${styles.text}`}>
            {title}
          </h3>
          {description && (
            <p className="text-[10px] text-white/30 font-bold uppercase tracking-wider mt-0.5">
              {description}
            </p>
          )}
        </div>
        <div className={`h-px flex-1 bg-gradient-to-r from-transparent via-white/10 to-transparent`} />
      </div>

      {/* Section Content */}
      <div className="animate-in fade-in slide-in-from-bottom-2 duration-500">
        {children}
      </div>
    </section>
  );
}

export default NarrativeSection;
