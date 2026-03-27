import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { BookOpen, ChevronRight, Plus, EyeOff } from 'lucide-react';
import { analyticsService } from '../../services/analyticsService';
import { StatCard } from './StatCard';

interface KnowledgeGap {
  id: string;
  intent: string;
  count: number;
  lastOccurrence: string;
  suggestedAction: string;
}

interface KnowledgeGapsData {
  gaps: KnowledgeGap[];
  period: {
    days: number;
    startDate: string;
    endDate: string;
  };
  totalGaps: number;
}

export function KnowledgeGapWidget() {
  const navigate = useNavigate();

  const { data, isLoading, isError } = useQuery({
    queryKey: ['analytics', 'knowledge-gaps'],
    queryFn: () => analyticsService.getKnowledgeGapsData(),
    staleTime: 60_000,
    refetchInterval: 120_000,
  });

  const gapsData = data as KnowledgeGapsData | undefined;
  const gaps = gapsData?.gaps || [];
  const displayGaps = gaps.slice(0, 5);

  return (
    <StatCard
      title="Intelligence Gaps"
      value={isLoading ? '...' : gaps.length.toString()}
      subValue="BLIND_SPOTS"
      icon={<EyeOff size={18} />}
      accentColor={gaps.length > 0 ? 'orange' : 'mantis'}
      data-testid="knowledge-gap-widget"
      isLoading={isLoading}
    >
      <div className="space-y-2 mt-4">
        {isError && (
          <div className="flex items-center justify-center py-8">
            <p className="text-[10px] font-black text-rose-400 uppercase tracking-widest text-center">TELEMETRY_GAP_ERROR</p>
          </div>
        )}

        {!isLoading && !isError && gaps.length === 0 && (
          <div className="flex flex-col items-center justify-center py-10 opacity-30 grayscale group-hover:grayscale-0 group-hover:opacity-100 transition-all duration-700">
             <div className="relative">
                <BookOpen size={32} className="text-[#00f5d4]" />
                <div className="absolute inset-0 bg-[#00f5d4]/20 blur-xl" />
             </div>
             <p className="text-[9px] font-black uppercase tracking-[0.3em] text-[#00f5d4] mt-3">CORE_SYMMETRY_OPTIMAL</p>
          </div>
        )}

        <div className="space-y-2">
          {displayGaps.map((gap) => (
            <div
              key={gap.id}
              className="group/gap flex items-center justify-between p-3 rounded-xl bg-white/5 border border-white/5 hover:border-[#00f5d4]/20 hover:bg-[#00f5d4]/5 transition-all cursor-pointer"
              onClick={() => navigate('/knowledge-base')}
            >
              <div className="flex-1 min-w-0">
                <p className="text-[11px] font-black text-white/80 group-hover/gap:text-white truncate uppercase tracking-tight">
                  {gap.intent}
                </p>
                <p className="text-[9px] font-bold text-white/30 uppercase tracking-widest mt-0.5">
                  {gap.count} DETECTIONS
                </p>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-[9px] font-black text-[#00f5d4] bg-[#00f5d4]/10 px-2 py-1 rounded border border-[#00f5d4]/20 uppercase tracking-tighter">
                  {gap.suggestedAction}
                </span>
                <ChevronRight size={12} className="text-white/20 group-hover/gap:translate-x-1 group-hover/gap:text-white/60 transition-all" />
              </div>
            </div>
          ))}
        </div>

        {gaps.length > 5 && (
          <button
            onClick={() => navigate('/knowledge-base')}
            className="w-full mt-2 py-2 text-[9px] font-black text-white/30 hover:text-white transition-all uppercase tracking-[0.2em]"
          >
            +{gaps.length - 5} ADDITIONAL_GAPS
          </button>
        )}

        <button
          onClick={() => navigate('/knowledge-base?add=true')}
          className="w-full mt-1 flex items-center justify-center gap-2 py-2.5 text-[10px] font-black text-[#00f5d4] hover:bg-[#00f5d4]/10 transition-all uppercase tracking-widest rounded-xl border border-[#00f5d4]/10"
        >
          <Plus size={12} strokeWidth={3} />
          EXPAND_KNOWLEDGE_CORE
        </button>
      </div>
    </StatCard>
  );
}

export default KnowledgeGapWidget;
