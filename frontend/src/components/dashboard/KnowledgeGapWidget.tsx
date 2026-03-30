import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { BookOpen, ChevronDown, Plus, MessageSquare, FileText, Target, ChevronRight } from 'lucide-react';
import { analyticsService } from '../../services/analyticsService';
import { StatCard } from './StatCard';
import { useState } from 'react';
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

interface PriorityCardProps {
  gap: KnowledgeGap;
  priority: 'urgent' | 'medium' | 'low';
}

function PriorityCard({ gap, priority }: PriorityCardProps) {
  const navigate = useNavigate();

  const priorityStyles = {
    urgent: 'bg-rose-500/10 border-rose-500/30 hover:border-rose-500/50',
    medium: 'bg-blue-500/10 border-blue-500/30 hover:border-blue-500/50',
    low: 'bg-white/5 border-white/10 hover:border-white/20',
  };

  const priorityBadge = {
    urgent: 'bg-rose-500/20 text-rose-400 border-rose-500/40',
    medium: 'bg-blue-500/20 text-blue-400 border-blue-500/40',
    low: 'bg-white/10 text-white/40 border-white/20',
  };

  return (
    <div
      className={`p-4 rounded-xl border ${priorityStyles[priority]} transition-all hover:scale-[1.02]`}
      role="article"
      aria-label={`Knowledge gap: ${gap.intent}, ${priority} priority`}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0">
          <p className="text-sm font-bold text-white mb-2 truncate">
            {gap.intent}
          </p>
          <div className="flex items-center gap-2 flex-wrap">
            <span className={`text-[10px] font-black px-2 py-0.5 rounded border uppercase tracking-wider ${priorityBadge[priority]}`}>
              {priority}
            </span>
            <span className="text-[10px] font-semibold text-white/40 uppercase tracking-wider">
              {gap.count} detections
            </span>
          </div>
        </div>
      </div>

      {/* Action Buttons - Always Visible */}
      <div className="grid grid-cols-2 gap-2 mt-3">
        <button
          onClick={() => navigate(`/business-info-faq?addFaq=true&question=${encodeURIComponent(gap.intent)}`)}
          className="flex items-center justify-center gap-2 py-2.5 bg-[#00f5d4]/10 hover:bg-[#00f5d4]/20 border border-[#00f5d4]/30 rounded-lg transition-all group"
          aria-label={`Add "${gap.intent}" as FAQ`}
        >
          <MessageSquare size={14} className="text-[#00f5d4] group-hover:scale-110 transition-transform" />
          <span className="text-[10px] font-black text-[#00f5d4] uppercase tracking-wider">
            Add FAQ
          </span>
        </button>
        <button
          onClick={() => navigate('/knowledge-base?add=true')}
          className="flex items-center justify-center gap-2 py-2.5 bg-[#00bbf9]/10 hover:bg-[#00bbf9]/20 border border-[#00bbf9]/30 rounded-lg transition-all group"
          aria-label="Upload document to knowledge base"
        >
          <FileText size={14} className="text-[#00bbf9] group-hover:scale-110 transition-transform" />
          <span className="text-[10px] font-black text-[#00bbf9] uppercase tracking-wider">
            Add Doc
          </span>
        </button>
      </div>
    </div>
  );
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

  // Group gaps by priority for better UX
  const quickWins = gaps.filter(g => g.count >= 10 || g.suggestedAction === 'add-faq');
  const mediumPriority = gaps.filter(g => !quickWins.includes(g) && g.count >= 5);
  const lowPriority = gaps.filter(g => !quickWins.includes(g) && !mediumPriority.includes(g));

  return (
    <StatCard
      title="Intelligence Gaps"
      value={isLoading ? '...' : gaps.length.toString()}
      subValue="PRIORITIZED_ACTION_LIST"
      icon={<Target size={18} />}
      accentColor={gaps.length > 0 ? 'orange' : 'mantis'}
      data-testid="knowledge-gap-widget"
      isLoading={isLoading}
      expandable
      miniChart={
        !isLoading && quickWins.length > 0 && (
          <div className="flex items-center gap-1 mt-2">
            {quickWins.slice(0, 5).map((_, i) => (
              <div
                key={i}
                className="h-1.5 w-8 rounded-full bg-gradient-to-r from-rose-500 to-orange-500"
              />
            ))}
          </div>
        )
      }
    >
      <div className="space-y-4 mt-4" role="region" aria-label="Knowledge gaps prioritized by urgency">
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

        {!isLoading && !isError && gaps.length > 0 && (
          <>
            {/* Quick Wins Section - Always Expanded */}
            {quickWins.length > 0 && (
              <div className="p-4 bg-gradient-to-br from-rose-500/10 to-orange-500/10 border border-rose-500/20 rounded-2xl">
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-lg">🔥</span>
                  <h3 className="text-xs font-black text-rose-400 uppercase tracking-widest">
                    Urgent - Quick Wins ({quickWins.length})
                  </h3>
                </div>
                <div className="space-y-2">
                  {quickWins.slice(0, 3).map(gap => (
                    <PriorityCard key={gap.id} gap={gap} priority="urgent" />
                  ))}
                </div>
              </div>
            )}

            {/* Medium Priority - Collapsible */}
            {mediumPriority.length > 0 && (
              <Collapsible>
                <CollapsibleTrigger className="w-full p-3 bg-white/5 hover:bg-white/10 rounded-xl flex items-center justify-between transition-colors">
                  <div className="flex items-center gap-2">
                    <span>📋</span>
                    <span className="text-xs font-black text-white/60 uppercase tracking-widest">
                      Medium Priority ({mediumPriority.length})
                    </span>
                  </div>
                  <ChevronDown size={14} className="text-white/40 transition-transform" />
                </CollapsibleTrigger>
                <CollapsibleContent className="mt-2 space-y-2">
                  {mediumPriority.map(gap => (
                    <PriorityCard key={gap.id} gap={gap} priority="medium" />
                  ))}
                </CollapsibleContent>
              </Collapsible>
            )}

            {/* Low Priority - Collapsible */}
            {lowPriority.length > 0 && (
              <Collapsible>
                <CollapsibleTrigger className="w-full p-3 bg-white/5 hover:bg-white/10 rounded-xl flex items-center justify-between transition-colors">
                  <div className="flex items-center gap-2">
                    <span>💡</span>
                    <span className="text-xs font-black text-white/40 uppercase tracking-widest">
                      Low Priority ({lowPriority.length})
                    </span>
                  </div>
                  <ChevronDown size={14} className="text-white/40 transition-transform" />
                </CollapsibleTrigger>
                <CollapsibleContent className="mt-2 space-y-2">
                  {lowPriority.map(gap => (
                    <PriorityCard key={gap.id} gap={gap} priority="low" />
                  ))}
                </CollapsibleContent>
              </Collapsible>
            )}
          </>
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
