import React, { useEffect, useState } from 'react';
import { Zap, ChevronRight, Loader2 } from 'lucide-react';
import { cn } from '../../../lib/utils';
import { useToast } from '../../../context/ToastContext';
import { costTrackingService } from '../../../services/costTracking';
import type { AIRecommendation } from '../../../types/cost';

export const AIRecommendations: React.FC = () => {
  const { toast } = useToast();
  const [recommendations, setRecommendations] = useState<AIRecommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchRecommendations = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await costTrackingService.getAIRecommendations();
        setRecommendations(response.data.recommendations || []);
      } catch (err) {
        setError('Failed to load recommendations');
        console.error('Failed to fetch AI recommendations:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchRecommendations();
  }, []);

  const handleDeploy = (id: string) => {
    toast(`Optimization ${id} queued for deployment.`, 'success');
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Zap size={18} className="text-amber-500 animate-pulse" />
        <h3 className="text-sm font-black text-white uppercase tracking-[0.2em]">AI Recommendations</h3>
      </div>
      
      {loading && (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="w-6 h-6 animate-spin text-[var(--mantis-glow)]" />
          <span className="ml-2 text-sm text-white/60">Analyzing costs...</span>
        </div>
      )}

      {error && (
        <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/20">
          <p className="text-sm text-red-400">{error}</p>
        </div>
      )}

      {!loading && !error && recommendations.length === 0 && (
        <div className="p-4 rounded-lg bg-white/[0.02] border border-white/5">
          <p className="text-sm text-white/60">No optimization recommendations at this time. Great job!</p>
        </div>
      )}
      
      {!loading && !error && recommendations.length > 0 && (
        <div className="space-y-4">
          {recommendations.map((rec) => (
            <div 
              key={rec.id} 
              className={cn(
                "group p-6 bg-white/[0.02] rounded-2xl relative overflow-hidden backdrop-blur-xl hover:bg-white/[0.04] transition-all duration-500",
                rec.priority === 'HIGH' ? "border-l-4 border-l-rose-500 shadow-[inset_1px_0_10px_rgba(244,63,94,0.05)] hover:shadow-[inset_1px_0_20px_rgba(244,63,94,0.1)]" : 
                rec.priority === 'MED' ? "border-l-4 border-l-amber-500 shadow-[inset_1px_0_10px_rgba(245,158,11,0.05)] hover:shadow-[inset_1px_0_20px_rgba(245,158,11,0.1)]" :
                "border-l-4 border-l-blue-500 shadow-[inset_1px_0_10px_rgba(59,130,246,0.05)] hover:shadow-[inset_1px_0_20px_rgba(59,130,246,0.1)]"
              )}
            >
              <div className="absolute inset-0 rounded-2xl border border-white/[0.05] pointer-events-none transition-colors duration-500 group-hover:border-white/10" />
              
              <div className="flex justify-between items-start mb-4 relative z-10">
                <span className={cn(
                  "text-[9px] font-black uppercase tracking-[0.2em] px-2 py-0.5 rounded border",
                  rec.priority === 'HIGH' ? "text-rose-400 bg-rose-500/10 border-rose-500/20" : 
                  rec.priority === 'MED' ? "text-amber-400 bg-amber-500/10 border-amber-500/20" :
                  "text-blue-400 bg-blue-500/10 border-blue-500/20"
                )}>
                  Priority: {rec.priority}
                </span>
                <span className="text-[10px] font-mono text-[var(--mantis-glow)]/40 tracking-widest">{rec.id}</span>
              </div>
              
              <p className="text-xs text-white/80 leading-relaxed mb-6 font-medium relative z-10">
                {rec.text}
              </p>

              {rec.potentialSavingsUsd !== undefined && rec.potentialSavingsUsd > 0 && (
                <p className="text-xs text-[var(--mantis-glow)] mb-4 relative z-10">
                  Potential savings: ${rec.potentialSavingsUsd.toFixed(2)}/month
                </p>
              )}

              <button 
                onClick={() => handleDeploy(rec.id)}
                className="relative z-10 flex items-center justify-between w-full p-3 rounded-lg bg-black/40 border border-white/5 text-[10px] font-black text-white/50 uppercase tracking-[0.2em] hover:bg-[var(--mantis-glow)]/10 hover:border-[var(--mantis-glow)]/30 hover:text-[var(--mantis-glow)] hover:shadow-[0_0_15px_rgba(0,245,212,0.1)] transition-all duration-300 group/btn"
              >
                Deploy Optimization
                <ChevronRight size={14} className="group-hover/btn:translate-x-1 transition-transform" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
