import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { BookOpen, ChevronRight, Plus, EyeOff, MessageSquare, FileText, X, Target } from 'lucide-react';
import { analyticsService } from '../../services/analyticsService';
import { StatCard } from './StatCard';
import { useState } from 'react';
import { BubbleChart, MiniBubbleChart } from '../charts/BubbleChart';
import { Collapsible, CollapsibleTrigger, CollapsibleContent } from '../ui/Collapsible';

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
  const [selectedGap, setSelectedGap] = useState<KnowledgeGap | null>(null);
  const [isExpanded, setIsExpanded] = useState(false);

  const { data, isLoading, isError } = useQuery({
    queryKey: ['analytics', 'knowledge-gaps'],
    queryFn: () => analyticsService.getKnowledgeGapsData(),
    staleTime: 60_000,
    refetchInterval: 120_000,
  });

  const gapsData = data as KnowledgeGapsData | undefined;
  const gaps = gapsData?.gaps || [];
  const displayGaps = gaps.slice(0, 3);
  const remainingGaps = gaps.slice(3);

  // Prepare bubble chart data (opportunity matrix)
  // Map gaps to quadrants based on count (impact) and suggested action (ease)
  const bubbleData = gaps.map((gap) => {
    const impact = Math.min(100, gap.count * 10); // More frequent = higher impact
    const ease = gap.suggestedAction === 'add-doc' ? 80 :
              gap.suggestedAction === 'add-faq' ? 60 :
              gap.suggestedAction === 'improve-search' ? 40 : 20;
    const size = gap.count;

    return {
      id: gap.id,
      name: gap.intent,
      x: ease,
      y: impact,
      size,
      category:
        ease >= 60 && impact >= 60 ? 'quick-win' :
        ease >= 60 && impact < 60 ? 'fill-in' :
        ease < 60 && impact >= 60 ? 'major-project' : 'low-priority',
    };
  });

  const handleBubbleClick = (bubble: any) => {
    const gap = gaps.find(g => g.id === bubble.id);
    if (gap) {
      setSelectedGap(gap);
    }
  };

  return (
    <StatCard
      title="Intelligence Gaps"
      value={isLoading ? '...' : gaps.length.toString()}
      subValue="OPPORTUNITY_MATRIX"
      icon={<Target size={18} />}
      accentColor={gaps.length > 0 ? 'orange' : 'mantis'}
      data-testid="knowledge-gap-widget"
      isLoading={isLoading}
      expandable
      miniChart={
        !isLoading && gaps.length > 0 && (
          <div className="mt-2">
            <MiniBubbleChart
              data={bubbleData}
              width={200}
              height={50}
              maxBubbles={5}
            />
          </div>
        )
      }
    >
      {/* Bubble Chart Visualization */}
      {!isLoading && gaps.length > 0 && (
        <div className="mb-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[9px] font-black text-white/30 uppercase tracking-wider">
              IMPACT vs EFFORT MATRIX
            </span>
            <Target size={12} className="text-white/20" />
          </div>
          <BubbleChart
            data={bubbleData}
            height={200}
            onClick={handleBubbleClick}
            showLabels={true}
            showQuadrants={true}
            quadrantLabels={{
              topLeft: 'MAJOR PROJECTS\n(Hard + High Impact)',
              topRight: 'QUICK WINS\n(Easy + High Impact)',
              bottomLeft: 'FILL IN\n(Easy + Low Impact)',
              bottomRight: 'DEFER\n(Hard + Low Impact)',
            }}
            xLabel='EASY TO FIX →'
            yLabel='↑ IMPACT'
            ariaLabel="Knowledge gap opportunity matrix"
          />
        </div>
      )}

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
            <div key={gap.id}>
              <div
                className="group/gap flex items-center justify-between p-3 rounded-xl bg-white/5 border border-white/5 hover:border-[#00f5d4]/20 hover:bg-[#00f5d4]/5 transition-all cursor-pointer"
                onClick={() => setSelectedGap(gap)}
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

              {/* Action Menu */}
              {selectedGap?.id === gap.id && (
                <div className="mt-2 p-3 bg-[#0d0d12] border border-[#00f5d4]/30 rounded-xl animate-in fade-in slide-in-from-top-2 duration-200">
                  <div className="flex items-center justify-between mb-3">
                    <p className="text-[10px] font-black text-[#00f5d4] uppercase tracking-widest">
                      Bridge Knowledge Gap
                    </p>
                    <button
                      onClick={() => setSelectedGap(null)}
                      className="p-1 text-white/30 hover:text-white/60 transition-colors"
                      aria-label="Close knowledge gap menu"
                    >
                      <X size={14} />
                    </button>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <button
                      onClick={() => {
                        navigate(`/business-info-faq?addFaq=true&question=${encodeURIComponent(gap.intent)}`);
                        setSelectedGap(null);
                      }}
                      className="flex flex-col items-center gap-2 p-3 bg-[#00f5d4]/5 border border-[#00f5d4]/20 rounded-lg hover:bg-[#00f5d4]/10 transition-all group"
                      aria-label={`Add "${gap.intent}" as FAQ`}
                    >
                      <MessageSquare size={18} className="text-[#00f5d4] group-hover:scale-110 transition-transform" />
                      <span className="text-[9px] font-black text-white/80 uppercase tracking-tight">Add as FAQ</span>
                    </button>
                    <button
                      onClick={() => {
                        navigate('/knowledge-base?add=true');
                        setSelectedGap(null);
                      }}
                      className="flex flex-col items-center gap-2 p-3 bg-[#00bbf9]/5 border border-[#00bbf9]/20 rounded-lg hover:bg-[#00bbf9]/10 transition-all group"
                      aria-label="Upload document to knowledge base"
                    >
                      <FileText size={18} className="text-[#00bbf9] group-hover:scale-110 transition-transform" />
                      <span className="text-[9px] font-black text-white/80 uppercase tracking-tight">Add Document</span>
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>

        {remainingGaps.length > 0 && (
          <Collapsible open={isExpanded} onOpenChange={setIsExpanded}>
            <CollapsibleTrigger
              className="w-full mt-2 py-2 text-[9px] font-black text-[#00f5d4] hover:text-white/80 transition-all uppercase tracking-[0.2em] flex items-center justify-center gap-2"
              aria-expanded={isExpanded}
            >
              <span>
                {isExpanded ? 'Hide' : `View ${remainingGaps.length} more questions`}
              </span>
              <ChevronRight
                size={12}
                className={`transition-transform duration-200 ${isExpanded ? 'rotate-90' : ''}`}
              />
            </CollapsibleTrigger>
            <CollapsibleContent className="mt-2 space-y-2">
              {remainingGaps.map((gap) => (
                <div key={gap.id}>
                  <div
                    className="group/gap flex items-center justify-between p-3 rounded-xl bg-white/5 border border-white/5 hover:border-[#00f5d4]/20 hover:bg-[#00f5d4]/5 transition-all cursor-pointer"
                    onClick={() => setSelectedGap(gap)}
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

                  {/* Action Menu */}
                  {selectedGap?.id === gap.id && (
                    <div className="mt-2 p-3 bg-[#0d0d12] border border-[#00f5d4]/30 rounded-xl animate-in fade-in slide-in-from-top-2 duration-200">
                      <div className="flex items-center justify-between mb-3">
                        <p className="text-[10px] font-black text-[#00f5d4] uppercase tracking-widest">
                          Bridge Knowledge Gap
                        </p>
                        <button
                          onClick={() => setSelectedGap(null)}
                          className="p-1 text-white/30 hover:text-white/60 transition-colors"
                          aria-label="Close knowledge gap menu"
                        >
                          <X size={14} />
                        </button>
                      </div>
                      <div className="grid grid-cols-2 gap-2">
                        <button
                          onClick={() => {
                            navigate(`/business-info-faq?addFaq=true&question=${encodeURIComponent(gap.intent)}`);
                            setSelectedGap(null);
                          }}
                          className="flex flex-col items-center gap-2 p-3 bg-[#00f5d4]/5 border border-[#00f5d4]/20 rounded-lg hover:bg-[#00f5d4]/10 transition-all group"
                          aria-label={`Add "${gap.intent}" as FAQ`}
                        >
                          <MessageSquare size={18} className="text-[#00f5d4] group-hover:scale-110 transition-transform" />
                          <span className="text-[9px] font-black text-white/80 uppercase tracking-tight">Add as FAQ</span>
                        </button>
                        <button
                          onClick={() => {
                            navigate('/knowledge-base?add=true');
                            setSelectedGap(null);
                          }}
                          className="flex flex-col items-center gap-2 p-3 bg-[#00bbf9]/5 border border-[#00bbf9]/20 rounded-lg hover:bg-[#00bbf9]/10 transition-all group"
                          aria-label="Upload document to knowledge base"
                        >
                          <FileText size={18} className="text-[#00bbf9] group-hover:scale-110 transition-transform" />
                          <span className="text-[9px] font-black text-white/80 uppercase tracking-tight">Add Document</span>
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </CollapsibleContent>
          </Collapsible>
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
