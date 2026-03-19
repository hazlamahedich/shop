/** BotPreview page.
 *
 * Story 1.13: Bot Preview Mode
 * Re-imagined with Mantis aesthetic for a high-end neural testing experience.
 */

import { useEffect } from 'react';
import { PreviewChat } from '../components/preview/PreviewChat';
import { usePreviewStore } from '../stores/previewStore';
import { useBotConfigStore } from '../stores/botConfigStore';
import { useAuthStore } from '../stores/authStore';
import { GlassCard } from '../components/ui/GlassCard';
import { ArrowLeft, Terminal, Cpu, Zap, Activity, ShieldCheck, Radio, FileText, ShoppingBag } from 'lucide-react';

export function BotPreview() {
  const { botName } = useBotConfigStore();
  const { startSession, sessionId, isLoading: isPreviewLoading } = usePreviewStore();
  const merchant = useAuthStore((state) => state.merchant);
  const merchantId = merchant?.id;

  // Start preview session on mount
  useEffect(() => {
    if (!sessionId) {
      startSession();
    }
  }, [sessionId, startSession]);

  const handleBack = () => {
    window.history.pushState({}, '', '/dashboard');
    window.dispatchEvent(new PopStateEvent('popstate'));
  };

  return (
    <div className="min-h-screen bg-[#030303] text-white flex flex-col relative overflow-hidden animate-in fade-in duration-1000">
      {/* Neural Background Overlays */}
      <div className="absolute inset-x-0 top-0 h-[600px] bg-gradient-to-b from-emerald-500/[0.08] via-emerald-500/[0.03] to-transparent pointer-events-none"></div>
      <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-[0.15] pointer-events-none mix-blend-overlay"></div>

      {/* Header */}
      <header className="relative z-10 bg-[#0a0a0a]/80 backdrop-blur-3xl border-b border-white/[0.03] py-8">
        <div className="max-w-7xl mx-auto px-10">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-8">
              <button
                type="button"
                onClick={handleBack}
                className="w-12 h-12 flex items-center justify-center bg-white/5 hover:bg-emerald-500/10 text-white/40 hover:text-emerald-400 rounded-2xl border border-white/5 hover:border-emerald-500/20 transition-all duration-500 group"
                aria-label="Go back to dashboard"
              >
                <ArrowLeft size={20} className="group-hover:-translate-x-1 transition-transform" />
              </button>
              <div>
                <div className="flex items-center gap-4">
                  <h1 className="text-3xl font-black tracking-tight uppercase mantis-glow-text leading-none">
                    Neural Calibration
                  </h1>
                  <div className="flex items-center gap-2 px-3 py-1 bg-emerald-500/10 border border-emerald-500/20 rounded-full shadow-[0_0_15px_rgba(16,185,129,0.1)]">
                    <Radio size={12} className="text-emerald-400" />
                    <span className="text-[9px] font-black text-emerald-400 uppercase tracking-[0.2em]">Sandbox Mode</span>
                  </div>
                </div>
                <p className="text-[11px] font-black text-emerald-500/50 mt-2 uppercase tracking-[0.2em]">
                  Test your bot configuration in an isolated neural environment
                </p>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation / Breadcrumb */}
      <nav className="relative z-10 bg-[#0a0a0a]/40 border-b border-white/[0.03] py-3" aria-label="Breadcrumb">
        <div className="max-w-7xl mx-auto px-10 flex items-center gap-4 text-[10px] font-black uppercase tracking-[0.2em] text-emerald-500/50">
          <button onClick={handleBack} className="hover:text-emerald-400 transition-colors">Dashboard</button>
          <span className="opacity-20">/</span>
          <span className="text-emerald-500">Preview Engine</span>
        </div>
      </nav>

      {/* Main content */}
      <main className="relative z-10 flex-1 max-w-7xl mx-auto w-full px-10 py-12 flex flex-col gap-10">
        {/* Protocol Header Card */}
        <GlassCard accent="mantis" className="p-10 border-emerald-500/10 bg-emerald-500/[0.02]">
           <div className="flex flex-col lg:flex-row gap-8 lg:items-center justify-between">
             <div className="space-y-4">
               <h2 className="text-xl font-black text-white uppercase tracking-tight flex items-center gap-4">
                 <Terminal size={22} className="text-emerald-500" />
                 Preview Protocol
               </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-4">
                  <div className="flex items-start gap-4">
                     <Zap size={16} className="text-emerald-500 mt-1" />
                     <p className="text-[11px] font-black text-emerald-400/70 uppercase tracking-widest leading-relaxed">Use quick-try buttons for automated neural firing</p>
                  </div>
                  <div className="flex items-start gap-4">
                     <Cpu size={16} className="text-emerald-500 mt-1" />
                     <p className="text-[11px] font-black text-emerald-400/70 uppercase tracking-widest leading-relaxed">Neural analysis provides real-time accuracy scoring</p>
                  </div>
                  <div className="flex items-start gap-4">
                     <Activity size={16} className="text-emerald-500 mt-1" />
                     <p className="text-[11px] font-black text-emerald-400/70 uppercase tracking-widest leading-relaxed">Transient mode: Data streams are not persisted</p>
                  </div>
                  <div className="flex items-start gap-4">
                     <ShieldCheck size={16} className="text-emerald-500 mt-1" />
                     <p className="text-[11px] font-black text-emerald-400/70 uppercase tracking-widest leading-relaxed">Isolated sandbox: External systems are shielded</p>
                  </div>
                </div>
             </div>
           </div>
        </GlassCard>

        {/* Loading state */}
        {isPreviewLoading && !sessionId && (
          <div className="flex-1 flex flex-col items-center justify-center gap-6">
            <div className="relative w-20 h-20">
              <div className="absolute inset-0 border-2 border-emerald-500/10 rounded-full"></div>
              <div className="absolute inset-0 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin"></div>
              <div className="absolute inset-4 bg-emerald-500/10 rounded-full animate-pulse"></div>
            </div>
            <p className="text-[10px] font-black text-emerald-400 uppercase tracking-[0.5em] animate-pulse">Initializing Neural Link...</p>
          </div>
        )}

        {/* Chat Interface Container */}
        {sessionId && (
          <div className="flex-1 animate-in fade-in slide-in-from-bottom-8 duration-1000">
            <GlassCard className="h-[700px] p-0 overflow-hidden border-white/[0.05] shadow-[0_40px_100px_rgba(0,0,0,0.5)]">
              <PreviewChat botName={botName || 'Neural Node'} merchantId={merchantId} />
            </GlassCard>
          </div>
        )}

        {/* Analysis Matrices */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 pb-12">
           <div className="p-8 bg-white/[0.02] border border-white/[0.05] rounded-[32px] space-y-6 hover:bg-emerald-500/[0.02] hover:border-emerald-500/20 transition-all duration-500 group">
             <div className="w-12 h-12 bg-white/5 rounded-2xl flex items-center justify-center text-emerald-400/60 group-hover:bg-emerald-500 group-hover:text-black transition-all">
               <Zap size={22} />
             </div>
             <div className="space-y-2">
               <h3 className="font-black text-white uppercase tracking-tight">Personality Core</h3>
               <p className="text-xs text-white/50 font-medium leading-relaxed uppercase tracking-widest">
                 Real-time validation of configured tone (Friendly, Professional, or Enthusiastic).
               </p>
             </div>
           </div>

           <div className="p-8 bg-white/[0.02] border border-white/[0.05] rounded-[32px] space-y-6 hover:bg-emerald-500/[0.02] hover:border-emerald-500/20 transition-all duration-500 group">
             <div className="w-12 h-12 bg-white/5 rounded-2xl flex items-center justify-center text-emerald-400/60 group-hover:bg-emerald-500 group-hover:text-black transition-all">
               <FileText size={22} />
             </div>
             <div className="space-y-2">
               <h3 className="font-black text-white uppercase tracking-tight">Intelligence Matrix</h3>
               <p className="text-xs text-white/50 font-medium leading-relaxed uppercase tracking-widest">
                 FAQ and Business Hour integration analysis across all neural responses.
               </p>
             </div>
           </div>

           <div className="p-8 bg-white/[0.02] border border-white/[0.05] rounded-[32px] space-y-6 hover:bg-emerald-500/[0.02] hover:border-emerald-500/20 transition-all duration-500 group">
             <div className="w-12 h-12 bg-white/5 rounded-2xl flex items-center justify-center text-emerald-400/60 group-hover:bg-emerald-500 group-hover:text-black transition-all">
               <ShoppingBag size={22} />
             </div>
             <div className="space-y-2">
               <h3 className="font-black text-white uppercase tracking-tight">Commerce Array</h3>
               <p className="text-xs text-white/50 font-medium leading-relaxed uppercase tracking-widest">
                 Testing catalog lookup efficiency and product recommendation fidelity.
               </p>
             </div>
           </div>
        </div>
      </main>
    </div>
  );
}
