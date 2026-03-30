import { useQuery } from '@tanstack/react-query';
import { Target, AlertCircle, Plus, Upload, FileText, ArrowRight } from 'lucide-react';
import { analyticsService } from '../../services/analyticsService';
import { StatCard } from './StatCard';
import type { HighImpactImprovementsResponse } from '../../types/analytics';

export function HighImpactImprovementsWidget() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['analytics', 'high-impact-improvements'],
    queryFn: () => analyticsService.getHighImpactImprovements(),
    staleTime: 60_000,
    refetchInterval: 60_000,
    retry: 1,
  });

  const improvementsData = data as HighImpactImprovementsResponse | undefined;
  const actions = improvementsData?.actions || [];

  return (
    <StatCard
      title="High-Impact Improvements"
      value={isLoading ? '...' : `${actions.length}`}
      subValue="PRIORITY_ACTIONS"
      icon={<Target size={18} />}
      accentColor="red"
      isLoading={isLoading}
      expandable
    >
      <div className="space-y-4 mt-4">
        {isError ? (
          <div className="flex items-center justify-center py-8">
            <p className="text-[10px] font-black text-rose-400 uppercase tracking-widest">Improvements Unavailable</p>
          </div>
        ) : actions.length === 0 ? (
          <div className="flex items-center justify-center py-8">
            <p className="text-[10px] font-black text-[#00f5d4]/60 uppercase tracking-widest flex items-center gap-2">
              <AlertCircle size={14} />
              All systems optimal!
            </p>
          </div>
        ) : (
          <>
            {/* Estimated Impact Summary */}
            {improvementsData?.totalEstimatedImpact && improvementsData.totalEstimatedImpact > 0 && (
              <div className="bg-gradient-to-r from-[#00f5d4]/10 to-purple-400/10 border border-[#00f5d4]/20 p-3 rounded-xl">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-[9px] font-black text-white/30 uppercase tracking-widest mb-1">
                      Potential Handoff Reduction
                    </p>
                    <p className="text-lg font-black text-[#00f5d4]">
                      {Math.round(improvementsData.totalEstimatedImpact)}%
                    </p>
                  </div>
                  <Target size={24} className="text-[#00f5d4]/40" />
                </div>
              </div>
            )}

            {/* Priority Actions List */}
            <div className="space-y-2">
              <div className="flex items-center justify-between mb-2">
                <p className="text-[9px] font-black text-white/20 uppercase tracking-widest">Actions by Priority</p>
              </div>
              <div className="space-y-2">
                {actions.map((action, idx) => (
                  <div
                    key={action.id}
                    className={`bg-white/5 border ${
                      action.priority === 'high'
                        ? 'border-rose-400/30'
                        : action.priority === 'medium'
                        ? 'border-orange-400/20'
                        : 'border-white/10'
                    } p-3 rounded-xl backdrop-blur-sm hover:bg-white/10 transition-all`}
                  >
                    {/* Priority Badge */}
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span
                          className={`px-2 py-0.5 rounded text-[8px] font-black uppercase tracking-wider ${
                            action.priority === 'high'
                              ? 'bg-rose-400/20 text-rose-400'
                              : action.priority === 'medium'
                              ? 'bg-orange-400/20 text-orange-400'
                              : 'bg-white/10 text-white/40'
                          }`}
                        >
                          {action.priority}
                        </span>
                        <span className="text-[9px] text-white/30">
                          {action.frequency}x asked · {Math.round(action.matchRate)}% match
                        </span>
                      </div>
                      <div className="text-[9px] font-black text-[#00f5d4]">
                        -{Math.round(action.estimatedHandoffReduction)}% handoffs
                      </div>
                    </div>

                    {/* Question */}
                    <p className="text-[10px] font-semibold text-white/90 mb-3">
                      {action.question}
                    </p>

                    {/* Action Button */}
                    <button
                      className={`w-full flex items-center justify-between p-2 rounded-lg text-[9px] font-black uppercase tracking-wider transition-all ${
                        action.suggestedAction === 'add_faq'
                          ? 'bg-purple-400/10 text-purple-400 border border-purple-400/20 hover:bg-purple-400/20'
                          : action.suggestedAction === 'upload_document'
                          ? 'bg-[#00f5d4]/10 text-[#00f5d4] border border-[#00f5d4]/20 hover:bg-[#00f5d4]/20'
                          : 'bg-orange-400/10 text-orange-400 border border-orange-400/20 hover:bg-orange-400/20'
                      }`}
                    >
                      <span className="flex items-center gap-2">
                        {action.suggestedAction === 'add_faq' && <Plus size={12} />}
                        {action.suggestedAction === 'upload_document' && <Upload size={12} />}
                        {action.suggestedAction === 'update_document' && <FileText size={12} />}
                        {action.suggestedAction === 'add_faq'
                          ? 'Add to FAQs'
                          : action.suggestedAction === 'upload_document'
                          ? 'Upload Documentation'
                          : 'Update Document'}
                      </span>
                      <ArrowRight size={12} />
                    </button>
                  </div>
                ))}
              </div>
            </div>

            {/* Quick Actions Section */}
            <div className="pt-2 border-t border-white/5">
              <div className="flex items-center justify-between mb-2">
                <p className="text-[9px] font-black text-white/20 uppercase tracking-widest">Quick Actions</p>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <button className="flex items-center justify-center gap-2 p-2 bg-white/5 border border-white/5 rounded-lg text-[9px] font-black text-white/60 uppercase tracking-wider hover:bg-white/10 hover:text-white transition-all">
                  <Plus size={12} />
                  Add FAQ
                </button>
                <button className="flex items-center justify-center gap-2 p-2 bg-white/5 border border-white/5 rounded-lg text-[9px] font-black text-white/60 uppercase tracking-wider hover:bg-white/10 hover:text-white transition-all">
                  <Upload size={12} />
                  Upload Doc
                </button>
              </div>
            </div>

            {/* Last Updated */}
            {improvementsData?.lastUpdated && (
              <div className="pt-2 border-t border-white/5">
                <p className="text-[8px] font-black text-white/20 uppercase tracking-wider">
                  Last updated: {new Date(improvementsData.lastUpdated).toLocaleString()}
                </p>
              </div>
            )}
          </>
        )}
      </div>
    </StatCard>
  );
}

export default HighImpactImprovementsWidget;
