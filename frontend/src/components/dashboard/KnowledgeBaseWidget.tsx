/**
 * Knowledge Base Widget for Dashboard
 *
 * Story 8-10: Frontend Dashboard Mode-Aware Widgets
 * Displays knowledge base statistics for General mode merchants
 */

import { useQuery } from '@tanstack/react-query';
import { FileText, AlertCircle, Loader2, Upload } from 'lucide-react';
import { Card } from '../ui/Card';
import { knowledgeBaseApi } from '../../services/knowledgeBase';
import type { KnowledgeBaseStats } from '../../types/knowledgeBase';

export function KnowledgeBaseWidget() {
  const { data: stats, isLoading, error, refetch } = useQuery<KnowledgeBaseStats>({
    queryKey: ['knowledge-base', 'stats'],
    queryFn: () => knowledgeBaseApi.getStats(),
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: false,
  });

  // Loading state
  if (isLoading) {
    return (
      <Card className="glass-card">
        <div className="p-6">
          <div className="flex items-center justify-center">
            <Loader2 className="h-8 w-8 animate-spin text-white/60" />
          </div>
        </div>
      </Card>
    );
  }

  // Error state
  if (error) {
    return (
      <Card className="glass-card">
        <div className="p-6">
          <div className="flex items-center gap-3">
            <AlertCircle className="h-5 w-5 text-red-400" />
            <div className="flex-1">
              <p className="text-sm font-medium text-red-400">Failed to load</p>
              <p className="text-xs text-red-400/80">Unable to fetch knowledge base stats</p>
            </div>
            <button
              onClick={() => refetch()}
              className="text-xs text-red-400 hover:text-red-300 underline"
            >
              Retry
            </button>
          </div>
        </div>
      </Card>
    );
  }

  // Empty state - no documents uploaded yet
  if (stats && stats.totalDocs === 0) {
    return (
      <Card className="glass-card">
        <div className="p-6">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-blue-500/10 text-blue-400">
              <Upload className="h-5 w-5" />
            </div>
            <div className="flex-1">
              <p className="text-sm font-semibold text-white">Knowledge Base</p>
              <p className="text-xs text-white/60 mt-0.5">
                Upload your first document to get started
              </p>
            </div>
          </div>
          <a
            href="/knowledge-base"
            className="mt-4 block w-full rounded-md bg-blue-500/20 px-3 py-2 text-center text-sm font-medium text-blue-400 hover:bg-blue-500/30 transition-colors border border-blue-500/20"
          >
            Upload Document
          </a>
        </div>
      </Card>
    );
  }

  // Data state - show stats
  return (
    <Card className="glass-card">
      <div className="p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <FileText className="h-5 w-5 text-white/60" />
            <h3 className="text-sm font-semibold text-white">Knowledge Base</h3>
          </div>
          <a
            href="/knowledge-base"
            className="text-xs text-blue-400 hover:text-blue-300 font-medium"
          >
            Manage →
          </a>
        </div>

        {/* Stats Grid */}
        <div className="space-y-3">
          {/* Total Documents */}
          <div className="flex items-center justify-between">
            <span className="text-xs text-white/60">Total Documents</span>
            <span className="text-sm font-semibold text-white">
              {stats?.totalDocs ?? 0}
            </span>
          </div>

          {/* Status Breakdown */}
          {stats && stats.processingCount > 0 && (
            <div className="flex items-center justify-between">
              <span className="text-xs text-white/60">Processing</span>
              <div className="flex items-center gap-1.5">
                <Loader2 className="h-3 w-3 animate-spin text-amber-400" />
                <span className="text-sm font-medium text-amber-400">
                  {stats.processingCount}
                </span>
              </div>
            </div>
          )}

          {stats && stats.readyCount > 0 && (
            <div className="flex items-center justify-between">
              <span className="text-xs text-white/60">Ready</span>
              <span className="text-sm font-medium text-green-400">
                {stats.readyCount}
              </span>
            </div>
          )}

          {stats && stats.errorCount > 0 && (
            <div className="flex items-center justify-between">
              <span className="text-xs text-white/60">Errors</span>
              <span className="text-sm font-medium text-red-400">
                {stats.errorCount}
              </span>
            </div>
          )}

          {/* Last Upload */}
          {stats?.lastUploadDate && (
            <div className="pt-3 border-t border-white/10">
              <div className="flex items-center justify-between">
                <span className="text-xs text-white/60">Last Upload</span>
                <span className="text-xs text-white/60">
                  {new Date(stats.lastUploadDate).toLocaleDateString()}
                </span>
              </div>
            </div>
          )}
        </div>
      </div>
    </Card>
  );
}
