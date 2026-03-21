import React from 'react';
import { 
  Activity, 
  BarChart3, 
  Settings, 
  MessageSquare, 
  Zap, 
  Info, 
  LogOut,
  ChevronRight
} from 'lucide-react';
import { cn } from '../../../lib/utils';

interface SidebarItemProps {
  icon: React.ElementType;
  label: string;
  active?: boolean;
}

const SidebarItem: React.FC<SidebarItemProps> = ({ icon: Icon, label, active }) => (
  <div className={cn(
    "flex items-center gap-4 px-4 py-3 rounded-xl transition-all duration-300 cursor-pointer group",
    active 
      ? "bg-[var(--mantis-glow)]/10 border border-[var(--mantis-glow)]/20 text-[var(--mantis-glow)]" 
      : "text-white/40 hover:bg-white/5 hover:text-white"
  )}>
    <Icon size={18} className={cn("transition-transform group-hover:scale-110", active && "animate-pulse")} />
    <span className="text-[10px] font-black uppercase tracking-[0.2em]">{label}</span>
    {active && <ChevronRight size={14} className="ml-auto" />}
  </div>
);

export const TacticalHUDSidebar: React.FC = () => {
  return (
    <div className="w-64 flex flex-col h-full border-r border-white/[0.05] p-6 space-y-10 shrink-0">
      <div className="space-y-4">
        <div className="space-y-1">
          <h2 className="text-xl font-black text-white uppercase tracking-tight flex items-center gap-2">
            <div className="w-2 h-2 bg-[var(--mantis-glow)] rounded-full animate-ping" />
            Resource
          </h2>
          <p className="text-[10px] font-black text-white/20 uppercase tracking-[0.3em]">Consumption</p>
        </div>
        <div className="px-3 py-1 bg-white/5 border border-white/10 rounded-lg inline-block">
          <span className="text-[9px] font-black text-white/40 uppercase tracking-[0.2em]">Active Telemetry</span>
        </div>
      </div>

      <nav className="flex-1 space-y-2">
        <SidebarItem icon={BarChart3} label="Spectral Data" />
        <SidebarItem icon={Activity} label="Test Your Bot" />
        <SidebarItem icon={MessageSquare} label="Conversations" />
        <SidebarItem icon={Zap} label="Intelligence ROI" active />
      </nav>

      <div className="space-y-6 pt-10 border-t border-white/[0.05]">
        <button className="w-full py-4 bg-[var(--mantis-glow)] text-black font-black text-[11px] uppercase tracking-[0.3em] rounded-xl hover:bg-[#00e2c5] transition-all shadow-[0_0_20px_rgba(0,245,212,0.2)]">
          Optimize Sync
        </button>
        
        <div className="space-y-4">
          <div className="flex items-center gap-3 text-white/40 hover:text-white cursor-pointer transition-colors px-4">
            <Info size={16} />
            <span className="text-[10px] font-black uppercase tracking-[0.2em]">Support</span>
          </div>
          <div className="flex items-center gap-3 text-white/40 hover:text-rose-400 cursor-pointer transition-colors px-4">
            <LogOut size={16} />
            <span className="text-[10px] font-black uppercase tracking-[0.2em]">Logout</span>
          </div>
        </div>
      </div>
    </div>
  );
};
