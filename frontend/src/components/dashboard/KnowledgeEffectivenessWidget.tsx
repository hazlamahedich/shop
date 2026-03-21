import { useQuery } from '@tanstack/react-query';
import { GitCompare, Target, Zap } from 'lucide-react';
import { analyticsService } from '../../services/analyticsService';
import { StatCard } from './StatCard';

interface KnowledgeEffectivenessData {
  period: {
    days: number;
    startDate: string;
    endDate: string;
  };
  totalConversations: number;
  totalResolvedByRag: number;
  effectivenessRate: number;
  dailyStats: any[];
}

export function KnowledgeEffectivenessWidget() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['analytics', 'knowledge-effectiveness'],
    queryFn: () => analyticsService.getKnowledgeEffectiveness(),
    staleTime: 60_000,
    refetchInterval: 120_000,
  });

  const effectivenessData = data as KnowledgeEffectivenessData | undefined;
  const rate = effectivenessData?.effectivenessRate !== undefined 
    ? Math.round(effectivenessData.effectivenessRate * 100) 
    : 0;
  
  const resolved = effectivenessData?.totalResolvedByRag || 0;
  const total = effectivenessData?.totalConversations || 0;

  return (
    <StatCard
      title="Knowledge Effectiveness"
      value={isLoading ? '...' : `${rate}%`}
      subValue="CORE_RELIABILITY_SCORE"
      icon={<GitCompare size={18} />}
      accentColor={rate > 70 ? 'mantis' : rate > 40 ? 'yellow' : 'red'}
      data-testid="knowledge-effectiveness-widget"
      isLoading={isLoading}
    >
      <div className="space-y-4 mt-4">
        {isError ? (
           <div className="flex items-center justify-center py-8">
             <p className="text-[10px] font-black text-rose-400 uppercase tracking-widest">SIGNAL_DECAP_ERROR</p>
           </div>
        ) : (
          <>
            <div className="relative group/gauge">
               <div className="flex items-center justify-between mb-2">
                  <span className="text-[9px] font-black text-white/20 uppercase tracking-widest">AUTONOMOUS_RESOLUTION</span>
                  <span className="text-[10px] font-black text-[#00f5d4]">{rate}%</span>
               </div>
               <div className="h-6 w-full bg-white/5 rounded-xl border border-white/5 overflow-hidden p-1 relative">
                  <div 
                    className="h-full bg-gradient-to-r from-[#00f5d4]/40 to-[#00f5d4] rounded-lg transition-all duration-1000 shadow-[0_0_15px_rgba(0,245,212,0.3)]"
                    style={{ width: `${rate}%` }}
                  />
                  <div className="absolute inset-y-0 left-0 flex items-center px-3">
                     <span className="text-[9px] font-black text-white/40 group-hover/gauge:text-white/80 transition-colors uppercase">LINK_ESTABLISHED</span>
                  </div>
               </div>
            </div>

            <div className="grid grid-cols-2 gap-2">
                <div className="bg-white/5 border border-white/5 p-3 rounded-xl backdrop-blur-sm group/metric">
                   <p className="text-[9px] font-bold text-white/30 uppercase tracking-tighter mb-1">RESOLVED</p>
                   <p className="text-xl font-black text-white group-hover/metric:text-[#00f5d4] transition-colors">{resolved}</p>
                   <Target size={12} className="mt-2 text-white/10 group-hover/metric:text-[#00f5d4]/40 transition-colors" />
                </div>
                <div className="bg-white/5 border border-white/5 p-3 rounded-xl backdrop-blur-sm group/metric">
                   <p className="text-[9px] font-bold text-white/30 uppercase tracking-tighter mb-1">SESSIONS</p>
                   <p className="text-xl font-black text-white">{total}</p>
                   <Zap size={12} className="mt-2 text-white/10" />
                </div>
            </div>

            <div className="flex items-center justify-between pt-2 border-t border-white/5">
                <span className="text-[9px] font-black text-white/10 uppercase tracking-[0.2em]">INTEL_SYNC_ACTIVE</span>
                <div className="flex items-center gap-1.5 px-2 py-0.5 bg-[#00f5d4]/5 border border-[#00f5d4]/10 rounded text-[9px] font-black text-[#00f5d4]">
                   HIGH_CONF_AUTO_PASS
                </div>
            </div>
          </>
        )}
      </div>
    </StatCard>
  );
}

export default KnowledgeEffectivenessWidget;