import { useQuery } from '@tanstack/react-query';
import { FileText, AlertCircle, Loader2, Upload, ChevronRight } from 'lucide-react';
import { knowledgeBaseApi } from '../../services/knowledgeBase';
import type { KnowledgeBaseStats } from '../../types/knowledgeBase';
import { StatCard } from './StatCard';

export function KnowledgeBaseWidget() {
  const { data: stats, isLoading, error, refetch } = useQuery<KnowledgeBaseStats>({
    queryKey: ['knowledge-base', 'stats'],
    queryFn: () => knowledgeBaseApi.getStats(),
    staleTime: 5 * 60 * 1000,
    refetchInterval: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  });

  if (error) {
    return (
      <StatCard title="Knowledge Core" value="ERR" icon={<FileText size={18} />} accentColor="red">
        <div className="flex flex-col items-center justify-center py-8 gap-3">
          <AlertCircle size={24} className="text-rose-400" />
          <p className="text-[10px] font-black text-rose-400 uppercase tracking-widest text-center">CORE_SYNC_FAILURE</p>
          <button onClick={() => refetch()} className="text-[9px] font-black text-white/40 hover:text-white uppercase tracking-tighter transition-colors">RETRY_HANDSHAKE</button>
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
      accentColor="mantis"
      data-testid="knowledge-base-widget"
      isLoading={isLoading}
    >
      <div className="space-y-0.5 mt-4">
        {stats && stats.totalDocs === 0 ? (
          <div className="flex flex-col items-center justify-center py-6 gap-3 group/upload">
             <div className="relative">
                <Upload size={24} className="text-white/20 group-hover/upload:text-[#00f5d4] transition-colors" />
                <div className="absolute inset-0 bg-[#00f5d4]/0 group-hover/upload:bg-[#00f5d4]/10 blur-xl transition-all" />
             </div>
             <p className="text-[10px] font-black text-white/20 uppercase tracking-[0.2em]">STORAGE_EMPTY</p>
             <a href="/knowledge-base" className="text-[10px] font-black text-[#00f5d4] uppercase tracking-widest border border-[#00f5d4]/20 px-3 py-1.5 rounded-lg hover:bg-[#00f5d4]/10 transition-all shadow-inner">INITIALIZE_DATAFEED</a>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-2 gap-2 mb-4">
               <div className="bg-white/5 border border-white/5 p-3 rounded-xl backdrop-blur-sm group/hex">
                  <p className="text-[9px] font-bold text-white/30 uppercase tracking-tighter mb-1">PROCESSED</p>
                  <p className="text-xl font-black text-white group-hover/hex:text-[#00f5d4] transition-colors">{stats?.readyCount ?? 0}</p>
               </div>
               <div className="bg-white/5 border border-white/5 p-3 rounded-xl backdrop-blur-sm">
                  <p className="text-[9px] font-bold text-white/30 uppercase tracking-tighter mb-1">ERR_LOGS</p>
                  <p className={`text-xl font-black ${stats?.errorCount ? 'text-rose-500' : 'text-white/20'}`}>{stats?.errorCount ?? 0}</p>
               </div>
            </div>

            <div className="flex items-center justify-between py-2 border-t border-white/5">
               <span className="text-[10px] font-black text-white/20 uppercase tracking-widest">ACTIVE_QUEUE</span>
               <div className="flex items-center gap-1.5">
                  <Loader2 size={10} className={`animate-spin ${stats?.processingCount ? 'text-yellow-400' : 'text-white/10'}`} />
                  <span className={`text-[10px] font-black ${stats?.processingCount ? 'text-yellow-400' : 'text-white/10'}`}>{stats?.processingCount ?? 0}</span>
               </div>
            </div>

            <div className="flex items-center justify-between py-2 border-t border-white/5">
               <span className="text-[10px] font-black text-white/20 uppercase tracking-widest">LAST_INJECT</span>
               <span className="text-[10px] font-black text-white/40">{stats?.lastUploadDate ? new Date(stats.lastUploadDate).toLocaleDateString() : 'N/A'}</span>
            </div>

            <a href="/knowledge-base" className="flex items-center justify-center gap-2 mt-2 py-2 text-[10px] font-black text-[#00f5d4]/60 hover:text-[#00f5d4] transition-all uppercase tracking-[0.2em] group/manage">
               MANAGE_CORE <ChevronRight size={12} className="group-hover/manage:translate-x-1 transition-transform" />
            </a>
          </>
        )}
      </div>
    </StatCard>
  );
}

export default KnowledgeBaseWidget;
