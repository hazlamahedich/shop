import React from 'react';
import { Bell, Settings, User } from 'lucide-react';
import { cn } from '../../../lib/utils';

export const TacticalHUDHeader: React.FC = () => {
  return (
    <header className="h-20 border-b border-white/[0.05] flex items-center justify-between px-10 shrink-0 backdrop-blur-md sticky top-0 z-50">
      <div className="flex items-center gap-12">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 flex items-center justify-center">
            {/* Neural Sync Logo SVG */}
            <svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M16 4L4 28H28L16 4Z" stroke="var(--mantis-glow)" strokeWidth="2" strokeLinejoin="round" />
              <circle cx="16" cy="18" r="4" fill="var(--mantis-glow)" className="animate-pulse" />
            </svg>
          </div>
          <h1 className="text-2xl font-black text-white italic tracking-tighter">
            Neural<span className="text-[var(--mantis-glow)]">Sync</span>
          </h1>
        </div>

        <nav className="hidden md:flex items-center gap-8">
          <a href="#" className="text-[11px] font-black uppercase tracking-[0.2em] text-[var(--mantis-glow)] border-b-2 border-[var(--mantis-glow)] pb-1">Intelligence ROI</a>
          <a href="#" className="text-[11px] font-black uppercase tracking-[0.2em] text-white/40 hover:text-white transition-colors">Spectral Data</a>
          <a href="#" className="text-[11px] font-black uppercase tracking-[0.2em] text-white/40 hover:text-white transition-colors">Orchestration</a>
        </nav>
      </div>

      <div className="flex items-center gap-6">
        <button className="text-white/40 hover:text-white transition-colors relative">
          <Bell size={20} />
          <div className="absolute top-0 right-0 w-2 h-2 bg-rose-500 rounded-full border-2 border-[#0d0d12]" />
        </button>
        <button className="text-white/40 hover:text-white transition-colors">
          <Settings size={20} />
        </button>
        <div className="w-10 h-10 rounded-full border border-white/10 bg-white/5 flex items-center justify-center text-[var(--mantis-glow)]">
          <User size={20} />
        </div>
      </div>
    </header>
  );
};
