import { useQuery } from '@tanstack/react-query';
import { AlertCircle, Plus, Upload, FileText, TrendingUp } from 'lucide-react';
import { analyticsService } from '../../services/analyticsService';
import { StatCard } from './StatCard';

interface FailedQuery {
  query: string;
  frequency: number;
  lastAsked: string;
  suggestedAction: 'add_faq' | 'upload_document' | 'update_document';
  estimatedImpact: number;
  category: string;
}

export function FailedQueriesWidget() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['analytics', 'failed-queries'],
    queryFn: () => analyticsService.getFailedQueries(),
    staleTime: 60_000,
    refetchInterval: 60_000,
    retry: 1,
  });

  const failedQueries = data as FailedQuery[] | undefined;
  const totalImpact = failedQueries?.reduce((sum, q) => sum + q.estimatedImpact, 0) || 0;

  return (
    <StatCard
      title="Failed Queries"
      value={isLoading ? '...' : `${failedQueries?.length || 0}`}
      subValue="UNANSWERED_QUESTIONS"
      icon={<AlertCircle size={18} />}
      accentColor="red"
      isLoading={isLoading}
      expandable
    >
      <div className="space-y-4 mt-4">
        {isError ? (
          <div className="flex items-center justify-center py-8">
            <p className="text-[10px] font-black text-rose-400 uppercase tracking-widest">Failed Queries Unavailable</p>
          </div>
        ) : !failedQueries || failedQueries.length === 0 ? (
          <div className="flex items-center justify-center py-8">
            <p className="text-[10px] font-black text-[#00f5d4]/60 uppercase tracking-widest flex items-center gap-2">
              <AlertCircle size={14} />
              No failed queries!
            </p>
          </div>
        ) : (
          <>
            {/* Impact Summary */}
            {totalImpact > 0 && (
              <div className="bg-gradient-to-r from-rose-400/10 to-orange-400/10 border border-rose-400/20 p-3 rounded-xl">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-[9px] font-black text-white/30 uppercase tracking-widest mb-1">
                      Potential Handoff Reduction
                    </p>
                    <p className="text-lg font-black text-rose-400">
                      {Math.round(totalImpact * 100)}%
                    </p>
                  </div>
                  <TrendingUp size={24} className="text-rose-400/40" />
                </div>
              </div>
            )}

            {/* Failed Queries List */}
            <div className="space-y-2">
              <div className="flex items-center justify-between mb-2">
                <p className="text-[9px] font-black text-white/20 uppercase tracking-widest">Questions Without Answers</p>
                <p className="text-[8px] text-white/30">Sorted by impact</p>
              </div>
              <div className="space-y-2">
                {failedQueries.map((item, idx) => (
                  <div
                    key={idx}
                    className="bg-white/5 border border-rose-400/20 p-3 rounded-xl backdrop-blur-sm hover:bg-white/10 transition-all"
                  >
                    {/* Query & Frequency */}
                    <div className="flex items-start justify-between gap-3 mb-2">
                      <div className="flex-1 min-w-0">
                        <p className="text-[10px] font-semibold text-white/90 mb-2">
                          {item.query}
                        </p>
                        <div className="flex items-center gap-3 text-[9px] text-white/40">
                          <span>Asked {item.frequency}x</span>
                          <span>·</span>
                          <span>{item.category}</span>
                          <span>·</span>
                          <span>Last: {new Date(item.lastAsked).toLocaleDateString()}</span>
                        </div>
                      </div>
                      <div className="flex-shrink-0 text-right">
                        <p className="text-[9px] text-white/30 uppercase tracking-wider">Impact</p>
                        <p className="text-lg font-black text-rose-400">
                          {Math.round(item.estimatedImpact * 100)}%
                        </p>
                      </div>
                    </div>

                    {/* Action Button */}
                    <button
                      className={`w-full flex items-center justify-between p-2 rounded-lg text-[9px] font-black uppercase tracking-wider transition-all ${
                        item.suggestedAction === 'add_faq'
                          ? 'bg-purple-400/10 text-purple-400 border border-purple-400/20 hover:bg-purple-400/20'
                          : item.suggestedAction === 'upload_document'
                          ? 'bg-[#00f5d4]/10 text-[#00f5d4] border border-[#00f5d4]/20 hover:bg-[#00f5d4]/20'
                          : 'bg-orange-400/10 text-orange-400 border border-orange-400/20 hover:bg-orange-400/20'
                      }`}
                    >
                      <span className="flex items-center gap-2">
                        {item.suggestedAction === 'add_faq' && <Plus size={12} />}
                        {item.suggestedAction === 'upload_document' && <Upload size={12} />}
                        {item.suggestedAction === 'update_document' && <FileText size={12} />}
                        {item.suggestedAction === 'add_faq'
                          ? 'Add FAQ Entry'
                          : item.suggestedAction === 'upload_document'
                          ? 'Upload Documentation'
                          : 'Update Document'}
                      </span>
                      <span className="text-[8px] opacity-60">
                        →
                      </span>
                    </button>
                  </div>
                ))}
              </div>
            </div>

            {/* Quick Actions */}
            <div className="pt-2 border-t border-white/5">
              <div className="flex items-center justify-between mb-2">
                <p className="text-[9px] font-black text-white/20 uppercase tracking-widest">Quick Actions</p>
              </div>
              <div className="grid grid-cols-3 gap-2">
                <button className="flex flex-col items-center gap-1.5 p-3 bg-white/5 border border-white/5 rounded-lg hover:bg-white/10 transition-all group">
                  <Plus size={14} className="text-purple-400 group-hover:scale-110 transition-transform" />
                  <span className="text-[8px] font-black text-white/60 uppercase tracking-wider">Add FAQ</span>
                </button>
                <button className="flex flex-col items-center gap-1.5 p-3 bg-white/5 border border-white/5 rounded-lg hover:bg-white/10 transition-all group">
                  <Upload size={14} className="text-[#00f5d4] group-hover:scale-110 transition-transform" />
                  <span className="text-[8px] font-black text-white/60 uppercase tracking-wider">Upload Doc</span>
                </button>
                <button className="flex flex-col items-center gap-1.5 p-3 bg-white/5 border border-white/5 rounded-lg hover:bg-white/10 transition-all group">
                  <FileText size={14} className="text-orange-400 group-hover:scale-110 transition-transform" />
                  <span className="text-[8px] font-black text-white/60 uppercase tracking-wider">Update KB</span>
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </StatCard>
  );
}

export default FailedQueriesWidget;
