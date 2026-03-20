import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { AlertTriangle, TrendingUp, ChevronRight, BookOpen } from 'lucide-react';
import { analyticsService } from '../../services/analyticsService';
import type { KnowledgeEffectivenessResponse } from '../../services/analyticsService';

interface KnowledgeEffectivenessWidgetProps {
  days?: number;
}

const formatRelativeTime = (date: Date): string => {
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  return `${diffDays}d ago`;
};

export function KnowledgeEffectivenessWidget({ days = 7 }: KnowledgeEffectivenessWidgetProps) {
  const navigate = useNavigate();

  const { data, isLoading, isError } = useQuery({
    queryKey: ['analytics', 'knowledge-effectiveness', days],
    queryFn: () => analyticsService.getKnowledgeEffectiveness(days),
    staleTime: 60_000,
    refetchInterval: 60_000,
  });

  const effectivenessData = data as KnowledgeEffectivenessResponse | undefined;
  const totalQueries = effectivenessData?.totalQueries ?? 0;
  const successfulMatches = effectivenessData?.successfulMatches ?? 0;
  const noMatchRate = effectivenessData?.noMatchRate ?? 0;
  const avgConfidence = effectivenessData?.avgConfidence ?? null;
  const trend = effectivenessData?.trend ?? [];
  const lastUpdated = effectivenessData?.lastUpdated ?? new Date().toISOString();

  const showWarning = noMatchRate > 20;

  return (
    <div
      className="relative overflow-hidden rounded-2xl glass-card border-none shadow-lg"
      data-testid="knowledge-effectiveness-widget"
    >
      <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-purple-500 to-pink-500 opacity-80" />

      <div className="p-5">
        <div className="flex items-start justify-between mb-4">
          <div>
            <p className="text-sm font-medium text-white/60 uppercase tracking-wide">
              Knowledge Effectiveness
            </p>
            <p className="text-xs text-white/40 mt-0.5">
              RAG Query Performance
            </p>
          </div>
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-purple-500/10 text-purple-400 ring-4 ring-purple-500/20">
            <TrendingUp size={18} />
          </div>
        </div>

        {isLoading ? (
          <div data-testid="knowledge-effectiveness-skeleton" className="space-y-4">
            <div className="h-8 bg-white/5 rounded animate-pulse" />
            <div className="h-8 bg-white/5 rounded animate-pulse" />
            <div className="h-8 bg-white/5 rounded animate-pulse" />
          </div>
        ) : isError ? (
          <div className="flex items-center justify-center py-8">
            <p className="text-sm text-white/60">Unable to load effectiveness data</p>
          </div>
        ) : !effectivenessData || effectivenessData.totalQueries === 0 ? (
          <div className="flex flex-col items-center justify-center py-8">
            <BookOpen size={32} className="text-white/30 mb-2" />
            <p className="text-sm text-white/60">No queries yet</p>
            <button
              onClick={() => navigate('/knowledge')}
              className="text-xs text-purple-400 hover:text-purple-300 transition-colors"
            >
              Add knowledge
            </button>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div className="bg-white/5 rounded-lg p-3">
                <div className="flex items-center justify-between">
                  <span className="text-2xl font-semibold text-white">{totalQueries}</span>
                  <span className="text-xs text-white/50">Total Queries</span>
                </div>
                <div className="text-sm text-white/40">{trend.length} days</div>
              </div>

              <div className="bg-white/5 rounded-lg p-3">
                <div className="flex items-center justify-between">
                  <span className="text-2xl font-semibold text-white">{successfulMatches}</span>
                  <span className="text-xs text-white/50">Matched</span>
                </div>
                <div className="text-sm text-white/40">
                  {((successfulMatches / totalQueries) * 100).toFixed(1)}% match rate
                </div>
              </div>

              <div className="bg-white/5 rounded-lg p-3">
                <div className="flex items-center justify-between">
                  <span className="text-2xl font-semibold text-white flex items-center gap-2">
                    {avgConfidence !== null ? (
                      `${((avgConfidence ?? 0) * 100).toFixed(0)}%`
                    ) : (
                      <span className="text-sm text-white/50">N/A</span>
                    )}
                  </span>
                  <span className="text-xs text-white/50">Avg Confidence</span>
                </div>
              </div>

              <div className="bg-white/5 rounded-lg p-3">
                <div className="flex items-center justify-between">
                  <span className="text-2xl font-semibold text-white flex items-center gap-2">
                    {noMatchRate !== null ? (
                      <>
                        {`${noMatchRate.toFixed(1)}%`}
                        {noMatchRate > 20 && <AlertTriangle size={16} className="text-yellow-500" />}
                      </>
                    ) : (
                      <span className="text-sm text-white/50">N/A</span>
                    )}
                  </span>
                  <span className="text-xs text-white/50">No-Match Rate</span>
                </div>
                {showWarning && (
                  <div className="mt-2 p-2 rounded bg-yellow-500/20 text-yellow-400">
                    <p className="text-xs font-medium">High no-match rate!</p>
                    <p className="text-xs text-white/50">Review knowledge base</p>
                  </div>
                )}
              </div>
            </div>

            <div className="mt-4 pt-4 border-t border-white/10">
              <p className="text-xs text-white/40">7-day trend</p>
              <div className="flex items-end gap-1 h-8">
                {trend.slice(-7).map((value, i) => (
                  <div
                    key={i}
                    className="flex-1 bg-purple-500/30 rounded-t transition-all hover:bg-purple-500/50"
                    style={{ height: `${Math.max(10, value * 100)}%` }}
                    title={`Day ${i + 1}: ${(value * 100).toFixed(0)}%`}
                  />
                ))}
              </div>
            </div>

            <div className="mt-4 pt-4 border-t border-white/10">
              <p className="text-xs text-white/50">Last updated</p>
              <p className="text-xs text-white/40">
                {formatRelativeTime(new Date(lastUpdated))}
              </p>
            </div>

            <div className="mt-4 pt-4 border-t border-white/10 flex items-center justify-between">
              <button
                data-testid="view-details-button"
                onClick={() => navigate('/analytics')}
                className="flex items-center gap-2 text-xs font-medium text-purple-400 hover:text-purple-300 transition-colors"
              >
                <ChevronRight size={12} />
                View details
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}