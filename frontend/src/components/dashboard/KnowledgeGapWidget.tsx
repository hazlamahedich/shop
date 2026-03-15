import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { AlertTriangle, BookOpen, ChevronRight, Plus } from 'lucide-react';
import { analyticsService } from '../../services/analyticsService';

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
    queryFn: () => analyticsService.getKnowledgeGaps(),
    staleTime: 60_000,
    refetchInterval: 120_000,
  });

  const gapsData = data as KnowledgeGapsData | undefined;
  const gaps = gapsData?.gaps || [];
  const displayGaps = gaps.slice(0, 5);

  return (
    <div
      className="relative overflow-hidden rounded-2xl bg-white border border-gray-100 shadow-sm"
      data-testid="knowledge-gap-widget"
    >
      <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-purple-400 to-pink-400 opacity-60" />

      <div className="p-5">
        <div className="flex items-start justify-between mb-4">
          <div>
            <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">
              Knowledge Gaps
            </p>
            <p className="text-xs text-gray-400 mt-0.5">
              What the bot doesn't know
            </p>
          </div>
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-purple-50 text-purple-600 ring-4 ring-purple-100">
            <AlertTriangle size={18} />
          </div>
        </div>

        {isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="h-12 bg-gray-100 rounded animate-pulse" />
            ))}
          </div>
        ) : isError ? (
          <div className="flex items-center justify-center py-8">
            <p className="text-sm text-gray-500">Unable to load knowledge gaps</p>
          </div>
        ) : gaps.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-8">
            <BookOpen size={32} className="text-gray-300 mb-2" />
            <p className="text-sm text-gray-500">No knowledge gaps detected</p>
            <p className="text-xs text-gray-400 mt-1">
              Your bot is handling all queries well
            </p>
          </div>
        ) : (
          <>
            <div className="space-y-2">
              {displayGaps.map((gap) => (
                <div
                  key={gap.id}
                  className="flex items-center justify-between p-3 rounded-lg bg-gray-50 hover:bg-gray-100 transition-colors cursor-pointer"
                  onClick={() => navigate('/knowledge')}
                >
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {gap.intent}
                    </p>
                    <p className="text-xs text-gray-500">
                      {gap.count} occurrences
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-purple-600 bg-purple-50 px-2 py-1 rounded-full">
                      {gap.suggestedAction}
                    </span>
                    <ChevronRight size={14} className="text-gray-400" />
                  </div>
                </div>
              ))}
            </div>

            {gaps.length > 5 && (
              <button
                onClick={() => navigate('/knowledge')}
                className="w-full mt-3 py-2 text-xs font-medium text-purple-600 hover:text-purple-800 transition-colors flex items-center justify-center gap-1"
              >
                View all {gaps.length} gaps
                <ChevronRight size={12} />
              </button>
            )}

            <div className="mt-4 pt-4 border-t border-gray-100">
              <button
                onClick={() => navigate('/knowledge?add=true')}
                className="flex items-center gap-2 text-xs font-medium text-purple-600 hover:text-purple-800 transition-colors"
              >
                <Plus size={12} />
                Add to Knowledge Base
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default KnowledgeGapWidget;
