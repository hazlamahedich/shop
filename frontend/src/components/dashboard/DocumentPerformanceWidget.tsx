import { useQuery } from '@tanstack/react-query';
import { FileText, TrendingUp, AlertCircle, CheckCircle2 } from 'lucide-react';
import { analyticsService } from '../../services/analyticsService';
import { StatCard } from './StatCard';
import type { DocumentPerformanceResponse } from '../../types/analytics';

export function DocumentPerformanceWidget() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['analytics', 'document-performance'],
    queryFn: () => analyticsService.getDocumentPerformance(),
    staleTime: 60_000,
    refetchInterval: 60_000,
    retry: 1,
  });

  const docData = data as DocumentPerformanceResponse | undefined;
  const documents = docData?.documents || [];

  // Calculate stats
  const activeDocs = documents.filter((d) => d.status === 'active').length;
  const unusedDocs = documents.filter((d) => d.status === 'unused').length;
  const outdatedDocs = documents.filter((d) => d.status === 'outdated').length;

  return (
    <StatCard
      title="Document Performance"
      value={isLoading ? '...' : `${activeDocs}`}
      subValue="ACTIVE_DOCUMENTS"
      icon={<FileText size={18} />}
      accentColor="mantis"
      isLoading={isLoading}
      expandable
    >
      <div className="space-y-4 mt-4">
        {isError ? (
          <div className="flex items-center justify-center py-8">
            <p className="text-[10px] font-black text-rose-400 uppercase tracking-widest">Performance Unavailable</p>
          </div>
        ) : documents.length === 0 ? (
          <div className="flex items-center justify-center py-8">
            <p className="text-[10px] font-black text-white/30 uppercase tracking-widest">No documents yet</p>
          </div>
        ) : (
          <>
            {/* Document Stats */}
            <div className="grid grid-cols-3 gap-2">
              <div className="bg-white/5 border border-white/5 p-3 rounded-xl backdrop-blur-sm group/metric text-center">
                <CheckCircle2 size={14} className="mx-auto mb-1.5 text-[#00f5d4]/60" />
                <p className="text-[9px] font-bold text-white/30 uppercase tracking-tighter mb-1">Active</p>
                <p className="text-lg font-black text-white group-hover/metric:text-[#00f5d4] transition-colors">
                  {activeDocs}
                </p>
              </div>

              <div className="bg-white/5 border border-white/5 p-3 rounded-xl backdrop-blur-sm group/metric text-center">
                <AlertCircle size={14} className="mx-auto mb-1.5 text-orange-400/60" />
                <p className="text-[9px] font-bold text-white/30 uppercase tracking-tighter mb-1">Unused</p>
                <p className="text-lg font-black text-white group-hover/metric:text-orange-400 transition-colors">
                  {unusedDocs}
                </p>
              </div>

              <div className="bg-white/5 border border-white/5 p-3 rounded-xl backdrop-blur-sm group/metric text-center">
                <TrendingUp size={14} className="mx-auto mb-1.5 text-rose-400/60" />
                <p className="text-[9px] font-bold text-white/30 uppercase tracking-tighter mb-1">Outdated</p>
                <p className="text-lg font-black text-white group-hover/metric:text-rose-400 transition-colors">
                  {outdatedDocs}
                </p>
              </div>
            </div>

            {/* Top Referenced Documents */}
            <div className="space-y-2">
              <div className="flex items-center justify-between mb-2">
                <p className="text-[9px] font-black text-white/20 uppercase tracking-widest">Most Referenced</p>
                <p className="text-[8px] text-white/30">Last 30 days</p>
              </div>
              <div className="space-y-1.5">
                {documents
                  .filter((d) => d.status === 'active')
                  .sort((a, b) => b.referenceCount - a.referenceCount)
                  .slice(0, 5)
                  .map((doc, idx) => (
                    <div
                      key={doc.documentId}
                      className="flex items-center justify-between text-[9px] p-2 rounded-lg bg-white/5 border border-white/5 hover:bg-white/10 transition-all"
                    >
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-white/80 truncate" title={doc.filename}>
                          {doc.filename}
                        </p>
                      </div>
                      <div className="flex items-center gap-3 flex-shrink-0 ml-3">
                        <span className="text-white/30">Ref: {doc.referenceCount}</span>
                        <span
                          className={`font-black ${
                            doc.avgConfidence >= 0.8
                              ? 'text-[#00f5d4]'
                              : doc.avgConfidence >= 0.6
                              ? 'text-orange-400'
                              : 'text-rose-400'
                          }`}
                        >
                          {Math.round(doc.avgConfidence * 100)}%
                        </span>
                      </div>
                    </div>
                  ))}
              </div>
            </div>

            {/* Unused Documents Alert */}
            {unusedDocs > 0 && (
              <div className="bg-orange-400/5 border border-orange-400/10 p-3 rounded-xl">
                <div className="flex items-center gap-2 mb-2">
                  <AlertCircle size={12} className="text-orange-400" />
                  <p className="text-[9px] font-black text-orange-400 uppercase tracking-wider">Action Needed</p>
                </div>
                <p className="text-[9px] text-white/60">
                  {unusedDocs} document{unusedDocs > 1 ? 's are' : ' is'} not being used in answers. Consider updating or removing to improve knowledge base quality.
                </p>
              </div>
            )}

            {/* Last Updated */}
            {docData?.lastUpdated && (
              <div className="pt-2 border-t border-white/5">
                <p className="text-[8px] font-black text-white/20 uppercase tracking-wider">
                  Last updated: {new Date(docData.lastUpdated).toLocaleString()}
                </p>
              </div>
            )}
          </>
        )}
      </div>
    </StatCard>
  );
}

export default DocumentPerformanceWidget;
