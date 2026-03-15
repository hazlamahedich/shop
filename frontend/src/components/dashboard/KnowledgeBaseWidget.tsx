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
      <Card>
        <div className="p-6">
          <div className="flex items-center justify-center">
            <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
          </div>
        </div>
      </Card>
    );
  }

  // Error state
  if (error) {
    return (
      <Card>
        <div className="p-6">
          <div className="flex items-center gap-3">
            <AlertCircle className="h-5 w-5 text-red-500" />
            <div className="flex-1">
              <p className="text-sm font-medium text-red-800">Failed to load</p>
              <p className="text-xs text-red-600">Unable to fetch knowledge base stats</p>
            </div>
            <button
              onClick={() => refetch()}
              className="text-xs text-red-600 hover:text-red-800 underline"
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
      <Card>
        <div className="p-6">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-blue-100 text-blue-600">
              <Upload className="h-5 w-5" />
            </div>
            <div className="flex-1">
              <p className="text-sm font-semibold text-gray-900">Knowledge Base</p>
              <p className="text-xs text-gray-500 mt-0.5">
                Upload your first document to get started
              </p>
            </div>
          </div>
          <a
            href="/knowledge-base"
            className="mt-4 block w-full rounded-md bg-blue-600 px-3 py-2 text-center text-sm font-medium text-white hover:bg-blue-700 transition-colors"
          >
            Upload Document
          </a>
        </div>
      </Card>
    );
  }

  // Data state - show stats
  return (
    <Card>
      <div className="p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <FileText className="h-5 w-5 text-gray-600" />
            <h3 className="text-sm font-semibold text-gray-900">Knowledge Base</h3>
          </div>
          <a
            href="/knowledge-base"
            className="text-xs text-blue-600 hover:text-blue-800 font-medium"
          >
            Manage →
          </a>
        </div>

        {/* Stats Grid */}
        <div className="space-y-3">
          {/* Total Documents */}
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-500">Total Documents</span>
            <span className="text-sm font-semibold text-gray-900">
              {stats?.totalDocs ?? 0}
            </span>
          </div>

          {/* Status Breakdown */}
          {stats && stats.processingCount > 0 && (
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-500">Processing</span>
              <div className="flex items-center gap-1.5">
                <Loader2 className="h-3 w-3 animate-spin text-amber-500" />
                <span className="text-sm font-medium text-amber-600">
                  {stats.processingCount}
                </span>
              </div>
            </div>
          )}

          {stats && stats.readyCount > 0 && (
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-500">Ready</span>
              <span className="text-sm font-medium text-green-600">
                {stats.readyCount}
              </span>
            </div>
          )}

          {stats && stats.errorCount > 0 && (
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-500">Errors</span>
              <span className="text-sm font-medium text-red-600">
                {stats.errorCount}
              </span>
            </div>
          )}

          {/* Last Upload */}
          {stats?.lastUploadDate && (
            <div className="pt-3 border-t border-gray-100">
              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-500">Last Upload</span>
                <span className="text-xs text-gray-600">
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
