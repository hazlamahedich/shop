import { useQuery } from '@tanstack/react-query';
import { FileText, AlertCircle, Loader2, Upload, CheckCircle2, Activity } from 'lucide-react';
import { knowledgeBaseApi } from '../../services/knowledgeBase';
import type { KnowledgeBaseStats } from '../../types/knowledgeBase';
import { StatCard } from './StatCard';
import { MiniTreemap } from '../charts/TreemapChart';

export function KnowledgeBaseWidget() {
  const { data: stats, isLoading, error, refetch } = useQuery<KnowledgeBaseStats>({
    queryKey: ['knowledge-base', 'stats'],
    queryFn: () => knowledgeBaseApi.getStats(),
    staleTime: 5 * 60 * 1000,
    refetchInterval: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  });

  const treemapData = stats && stats.totalDocs > 0 ? [
    { name: 'Ready', value: stats.readyCount, color: '#00f5d4' },
    { name: 'Processing', value: stats.processingCount, color: '#fb923c' },
    { name: 'Errors', value: stats.errorCount, color: '#f87171' },
    { name: 'Other', value: Math.max(0, stats.totalDocs - stats.readyCount - stats.processingCount - stats.errorCount), color: '#a78bfa' },
  ] : [];

  if (error) {
    return (
      <StatCard title="Knowledge Core" value="ERR" icon={<FileText size={18} />} accentColor="red">
        <div className="flex flex-col items-center justify-center py-8 gap-3">
          <AlertCircle size={24} className="text-rose-400 animate-pulse" />
          <p className="text-[10px] font-black text-rose-400 uppercase tracking-widest text-center">CORE_SYNC_FAILURE</p>
          <button onClick={() => refetch()} className="text-[9px] font-black bg-rose-500/20 hover:bg-rose-500/40 text-rose-300 px-4 py-2 rounded-lg transition-colors uppercase tracking-widest border border-rose-500/20 mt-2 shadow-[0_0_10px_rgba(244,63,94,0.1)]">RETRY_HANDSHAKE</button>
        </div>
      </StatCard>
    );
  }

  return (
    <StatCard
      title="Knowledge Core"
      value={stats?.totalDocs?.toString() ?? '0'}
      subValue="DOCS_INDEXED"
      icon={<FileText size={18} />}
      accentColor="purple"
      data-testid="knowledge-base-widget"
      isLoading={isLoading}
    >
      <div className="space-y-4 !pb-2">
        {/* Actionable Health Box */}
        {stats && stats.totalDocs === 0 ? (
           <div className="flex flex-col items-center justify-center py-6 gap-3 group/upload border border-white/5 rounded-2xl bg-white/5 relative overflow-hidden">
             <div className="absolute inset-0 bg-gradient-to-br from-[#00f5d4]/5 to-transparent opacity-0 group-hover/upload:opacity-100 transition-opacity duration-500" />
             <div className="bg-white/5 p-3 rounded-xl"><Upload size={20} className="text-[#00f5d4]/60 group-hover/upload:text-[#00f5d4] transition-colors" /></div>
             <p className="text-[11px] font-black text-white/50 uppercase tracking-[0.2em]">STORAGE_EMPTY</p>
             <a href="/knowledge-base" className="relative z-10 text-[10px] font-black bg-[#00f5d4]/10 text-[#00f5d4] uppercase tracking-widest border border-[#00f5d4]/30 px-4 py-2 rounded-lg hover:bg-[#00f5d4]/20 hover:scale-105 transition-all shadow-[0_0_15px_rgba(0,245,212,0.1)] mt-1">INITIALIZE_DATAFEED</a>
           </div>
        ) : (
          <>
            {stats?.errorCount ? (
              <div className="bg-gradient-to-br from-rose-500/10 to-rose-600/5 border border-rose-500/30 rounded-xl p-3.5 flex items-start gap-3.5 relative overflow-hidden shadow-[0_0_20px_rgba(244,63,94,0.05)]">
                 <div className="absolute -right-4 -top-4 w-16 h-16 bg-rose-500/20 rounded-full blur-2xl" />
                 <div className="mt-0.5 bg-rose-500/20 p-2 rounded-lg relative z-10"><AlertCircle size={16} className="text-rose-400" /></div>
                 <div className="relative z-10">
                   <p className="text-[11px] font-black text-rose-400 uppercase tracking-widest leading-none mb-1.5 flex items-center gap-2">Attention Required <span className="bg-rose-500 text-white px-1.5 py-0.5 rounded text-[8px]">{stats.errorCount}</span></p>
                   <p className="text-[11px] text-rose-300/80 leading-relaxed mb-3 pr-2">Failed vectorization detected. Neural accuracy is compromised.</p>
                   <a href="/knowledge-base?filter=errors" className="inline-block text-[10px] font-black bg-rose-500/20 hover:bg-rose-500/40 text-rose-200 px-3 py-1.5 rounded-md transition-colors uppercase tracking-widest border border-rose-500/20 w-auto text-center shadow-lg">Review Error Logs</a>
                 </div>
              </div>
            ) : stats?.processingCount ? (
              <div className="bg-gradient-to-br from-yellow-500/10 to-amber-600/5 border border-yellow-500/30 rounded-xl p-3.5 flex items-start gap-3.5 relative overflow-hidden shadow-[0_0_20px_rgba(234,179,8,0.05)]">
                 <div className="absolute -right-4 -top-4 w-16 h-16 bg-yellow-500/20 rounded-full blur-2xl" />
                 <div className="mt-0.5 bg-yellow-500/20 p-2 rounded-lg relative z-10"><Loader2 size={16} className="text-yellow-400 animate-spin" /></div>
                 <div className="relative z-10">
                   <p className="text-[11px] font-black text-yellow-400 uppercase tracking-widest leading-none mb-1.5">Processing Queue Active</p>
                   <p className="text-[11px] text-yellow-300/80 leading-relaxed mb-3 pr-2">{stats.processingCount} documents are currently being parsed and vectorized.</p>
                   <a href="/knowledge-base?filter=processing" className="inline-block text-[10px] font-black bg-yellow-500/20 hover:bg-yellow-500/30 text-yellow-200 px-3 py-1.5 rounded-md transition-colors uppercase tracking-widest border border-yellow-500/20 shadow-lg">View Active Queue</a>
                 </div>
              </div>
            ) : stats?.readyCount ? (
              <div className="bg-gradient-to-br from-emerald-500/10 to-teal-600/5 border border-emerald-500/30 rounded-xl p-3.5 flex items-center gap-3 relative overflow-hidden shadow-[0_0_20px_rgba(16,185,129,0.05)]">
                 <div className="absolute -right-8 -top-8 w-24 h-24 bg-emerald-500/10 rounded-full blur-2xl" />
                 <div className="bg-emerald-500/20 p-2 rounded-lg relative z-10"><CheckCircle2 size={16} className="text-emerald-400" /></div>
                 <div className="flex-1 relative z-10">
                   <p className="text-[11px] font-black text-emerald-400 uppercase tracking-widest leading-none mb-1">System Healthy</p>
                   <p className="text-[10px] text-emerald-300/70 font-medium">All data nodes are vectorized.</p>
                 </div>
                 <a href="/knowledge-base" className="relative z-10 text-[10px] font-black bg-emerald-500/20 hover:bg-emerald-500/40 text-emerald-200 px-3 py-2 rounded-lg transition-all uppercase tracking-widest border border-emerald-500/20 flex items-center gap-1.5 shadow-lg group"><Upload size={12} className="group-hover:-translate-y-0.5 transition-transform" /> INJECT</a>
              </div>
            ) : null}

            {/* Compact Distribution Treemap using the Hover Tooltips */}
            {!isLoading && treemapData.length > 0 && (
               <div className="bg-white/5 border border-white/5 rounded-xl p-3.5">
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-[10px] font-black text-white/50 uppercase tracking-widest flex items-center gap-1.5"><Activity size={12} className="text-purple-400" /> Global Distribution</span>
                  </div>
                  
                  <MiniTreemap data={treemapData} height={80} color="#a78bfa" />
                  
                  {/* Dynamic Legend */}
                  <div className="flex items-center gap-x-4 gap-y-2 mt-3 flex-wrap">
                    {treemapData.filter(i => i.value > 0).map(item => (
                       <div key={item.name} className="flex items-center gap-1.5 group cursor-default">
                         <div className="w-2.5 h-2.5 rounded shadow-sm border border-white/10 group-hover:scale-125 transition-transform" style={{ backgroundColor: item.color }} />
                         <span className="text-[9px] font-black text-white/60 group-hover:text-white transition-colors uppercase tracking-wider">{item.name} <span className="text-white/30 ml-0.5">({item.value})</span></span>
                       </div>
                    ))}
                  </div>
               </div>
            )}
            
            <div className="flex items-center justify-between pt-2">
               <span className="text-[9px] font-black text-white/30 uppercase tracking-[0.2em]">Latest Injection</span>
               <span className="text-[10px] font-bold text-white/50 bg-white/5 px-2 py-0.5 rounded border border-white/5">{stats?.lastUploadDate ? new Date(stats.lastUploadDate).toLocaleDateString() : 'Never'}</span>
            </div>
          </>
        )}
      </div>
    </StatCard>
  );
}

export default KnowledgeBaseWidget;
