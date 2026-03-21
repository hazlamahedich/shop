import * as React from 'react';
import { Smile, Briefcase, Zap, CheckCircle2 } from 'lucide-react';
import type { PersonalityType } from '../../types/enums';
import {
  PersonalityDisplay,
  PersonalityDescriptions,
  PersonalityDefaultGreetings,
} from '../../types/enums';

export interface PersonalityCardProps {
  personality: PersonalityType;
  isSelected: boolean;
  onSelect: (personality: PersonalityType) => void;
  className?: string;
}

const PERSONALITY_ICONS: Record<PersonalityType, React.ElementType> = {
  friendly: Smile,
  professional: Briefcase,
  enthusiastic: Zap,
};

const PERSONALITY_THEMES: Record<PersonalityType, { glow: string; icon: string; border: string; bg: string }> = {
  friendly: {
    glow: 'shadow-[0_0_20px_rgba(16,185,129,0.2)]',
    icon: 'text-emerald-400 bg-emerald-500/10',
    border: 'border-emerald-500/30',
    bg: 'group-hover:bg-emerald-500/5',
  },
  professional: {
    glow: 'shadow-[0_0_20px_rgba(99,102,241,0.2)]',
    icon: 'text-indigo-400 bg-indigo-500/10',
    border: 'border-indigo-500/30',
    bg: 'group-hover:bg-indigo-500/5',
  },
  enthusiastic: {
    glow: 'shadow-[0_0_20px_rgba(168,85,247,0.2)]',
    icon: 'text-purple-400 bg-purple-500/10',
    border: 'border-purple-500/30',
    bg: 'group-hover:bg-purple-500/5',
  },
};

export const PersonalityCard = React.forwardRef<HTMLButtonElement, PersonalityCardProps>(
  ({ personality, isSelected, onSelect, className = '' }, ref) => {
    const Icon = PERSONALITY_ICONS[personality];
    const theme = PERSONALITY_THEMES[personality];
    const displayName = PersonalityDisplay[personality];
    const description = PersonalityDescriptions[personality];
    const defaultGreeting = PersonalityDefaultGreetings[personality];

    return (
      <button
        ref={ref}
        type="button"
        onClick={() => onSelect(personality)}
        className={`
          group relative text-left p-6 rounded-[28px] border-2 transition-all duration-500
          backdrop-blur-xl font-space-grotesk overflow-hidden
          ${isSelected
            ? `bg-white/10 ${theme.border} ${theme.glow} ring-4 ring-white/5`
            : `bg-white/[0.02] border-white/5 hover:border-white/20 hover:scale-[1.02]`
          }
          focus:outline-none focus:ring-2 focus:ring-white/20
          disabled:opacity-50 disabled:cursor-not-allowed
          ${className}
        `}
        aria-pressed={isSelected}
      >
        {/* Dynamic Background Pulse */}
        {isSelected && (
          <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent animate-pulse" />
        )}
        
        {/* Header Section */}
        <div className="relative z-10 flex items-start justify-between mb-6">
          <div className={`p-3 rounded-2xl ${theme.icon} transition-transform duration-500 group-hover:scale-110`}>
            <Icon size={24} strokeWidth={2.5} />
          </div>
          
          {isSelected && (
            <div className="bg-emerald-500/20 p-1 rounded-full border border-emerald-500/40 animate-in zoom-in-50 duration-300">
              <CheckCircle2 size={16} className="text-emerald-400" />
            </div>
          )}
        </div>

        {/* Content Section */}
        <div className="relative z-10 space-y-4">
          <div>
            <h3 className={`text-xl font-black tracking-tight ${isSelected ? 'text-white' : 'text-white/70'} group-hover:text-white transition-colors`}>
              {displayName}
            </h3>
            <p className="text-[11px] font-black uppercase tracking-[0.2em] text-white/30 mt-1">
              Neural Archetype
            </p>
          </div>

          <p className={`text-sm leading-relaxed ${isSelected ? 'text-white/80' : 'text-white/50'} transition-colors`}>
            {description}
          </p>

          {/* Simulation Preview */}
          <div className={`mt-6 p-4 rounded-2xl border ${isSelected ? theme.border + ' bg-black/40' : 'border-white/5 bg-black/20'} transition-all duration-500`}>
            <div className="flex items-center gap-2 mb-2">
              <div className={`w-1.5 h-1.5 rounded-full ${isSelected ? 'bg-emerald-500 animate-pulse' : 'bg-white/20'}`} />
              <span className="text-[9px] font-black uppercase tracking-[0.2em] text-white/30">Output Simulation</span>
            </div>
            <p className={`text-xs font-medium italic ${isSelected ? 'text-white/90' : 'text-white/40'}`}>
              &quot;{defaultGreeting}&quot;
            </p>
          </div>
        </div>

        {/* Edge Accents */}
        {isSelected && (
          <>
            <div className="absolute top-0 right-0 w-24 h-24 bg-white/5 rounded-full -mr-12 -mt-12 blur-2xl" />
            <div className="absolute bottom-0 left-0 w-16 h-1 w-1/2 bg-gradient-to-r from-transparent via-white/20 to-transparent" />
          </>
        )}
      </button>
    );
  }
);

PersonalityCard.displayName = 'PersonalityCard';
