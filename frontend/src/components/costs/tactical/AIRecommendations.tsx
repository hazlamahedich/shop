import React from 'react';
import { Zap, ChevronRight } from 'lucide-react';
import { cn } from '../../../lib/utils';

interface Recommendation {
  id: string;
  priority: 'HIGH' | 'MED' | 'LOW';
  text: string;
}

export const AIRecommendations: React.FC = () => {
  const recommendations: Recommendation[] = [
    { 
      id: 'MB-9831', 
      priority: 'HIGH', 
      text: 'Shift #MB-9831 processing to Claude-3-Haiku during off-peak hours to save 22% daily spend.' 
    },
    { 
      id: 'CLUSTER-4', 
      priority: 'MED', 
      text: 'Redundant embeddings detected in Spectral Cluster 4. Consolidate to local cache.' 
    }
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Zap size={18} className="text-amber-500 animate-pulse" />
        <h3 className="text-sm font-black text-white uppercase tracking-[0.2em]">AI Recommendations</h3>
      </div>
      
      <div className="space-y-4">
        {recommendations.map((rec) => (
          <div 
            key={rec.id} 
            className={cn(
              "group p-5 bg-white/[0.03] rounded-2xl relative overflow-hidden backdrop-blur-md hover:bg-white/[0.05] transition-all duration-300",
              rec.priority === 'HIGH' ? "border-l-4 border-l-rose-500 shadow-[inset_1px_0_10px_rgba(244,63,94,0.05)]" : "border-l-4 border-l-amber-500 shadow-[inset_1px_0_10px_rgba(245,158,11,0.05)]"
            )}
          >
            {/* Ghost Border */}
            <div className="absolute inset-0 rounded-2xl border border-white/[0.05] pointer-events-none group-hover:border-[var(--mantis-glow)]/10 transition-colors" />
            <div className="flex justify-between items-start mb-3">
              <span className={cn(
                "text-[9px] font-black uppercase tracking-[0.2em]",
                rec.priority === 'HIGH' ? "text-rose-400" : "text-amber-400"
              )}>
                Priority: {rec.priority}
              </span>
              <span className="text-[9px] font-mono text-white/20 tracking-widest">{rec.id}</span>
            </div>
            
            <p className="text-xs text-white/80 leading-relaxed mb-6 font-medium">
              {rec.text}
            </p>

            <button className="flex items-center gap-2 text-[10px] font-black text-white/40 uppercase tracking-[0.2em] group-hover:text-white transition-colors">
              Deploy Optimization
              <ChevronRight size={14} />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};
