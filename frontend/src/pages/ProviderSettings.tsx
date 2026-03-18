/** 
 * LLM Provider Settings Page.
 *
 * Story 3.4: LLM Provider Switching
 * Re-imagined with high-fidelity Mantis aesthetic for a prestigious configuration experience.
 */

import React, { useEffect } from 'react';
import { useLLMProviderStore } from '../stores/llmProviderStore';
import { ProviderCard } from '../components/providers/ProviderCard';
import { ProviderConfigModal } from '../components/providers/ProviderConfigModal';
import { ProviderComparison } from '../components/providers/ProviderComparison';
import { ProviderSwitchSuccess } from '../components/providers/ProviderSwitchSuccess';
import { GlassCard } from '../components/ui/GlassCard';
import { Activity, ShieldCheck, Zap, Cpu, Terminal } from 'lucide-react';

export const ProviderSettings: React.FC = () => {
  const {
    currentProvider,
    availableProviders,
    isLoading,
    switchError,
    loadProviders,
    selectedProvider,
  } = useLLMProviderStore();

  useEffect(() => {
    loadProviders();
  }, [loadProviders]);

  if (isLoading) {
    return (
      <div className="h-full flex flex-col items-center justify-center gap-4 bg-[#030303]">
        <div className="w-12 h-12 border-2 border-emerald-500/20 border-t-emerald-500 rounded-full animate-spin" />
        <p className="text-[10px] font-black text-emerald-500/60 uppercase tracking-[0.4em]">Querying Node Registry...</p>
      </div>
    );
  }

  return (
    <div className="h-full space-y-12 animate-in fade-in slide-in-from-bottom-4 duration-700 pb-20">
      {/* Background Depth Components */}
      <div className="absolute inset-x-0 top-0 h-96 bg-gradient-to-b from-emerald-500/[0.05] via-emerald-500/[0.02] to-transparent pointer-events-none -mx-10 -mt-10"></div>

      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 relative z-10">
        <div className="space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-emerald-500/5 border border-emerald-500/10 rounded-full text-[10px] font-black uppercase tracking-[0.2em] text-emerald-400">
            <Cpu size={12} />
            Neural Core Configuration
          </div>
          <h1 className="text-5xl font-black tracking-tight text-white leading-none mantis-glow-text">
            LLM Providers
          </h1>
          <p className="text-lg text-emerald-500/60 font-medium max-w-xl">
            Calibrate the neural engine. Switch between low-latency local nodes or high-density cloud matrices.
          </p>
        </div>

        <div className="flex items-center gap-6">
           <div className="flex flex-col items-end">
             <span className="text-[9px] font-black text-emerald-500/60 uppercase tracking-widest block mb-1">System Health</span>
             <div className="flex items-center gap-2 px-4 py-2 bg-emerald-500/5 border border-emerald-500/10 rounded-xl">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_10px_rgba(16,185,129,0.8)]"></span>
                <span className="text-[10px] font-black text-emerald-400 uppercase tracking-widest">Nominal Status</span>
             </div>
           </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-10 relative z-10">
        <div className="lg:col-span-2 space-y-10">
           {/* Current Node Status Section */}
           <div className="space-y-6">
             <h2 className="text-[10px] font-black text-emerald-500/60 uppercase tracking-[0.4em] ml-2">Active Link Profile</h2>
             {currentProvider ? (
               <GlassCard accent="mantis" className="group p-10 border-emerald-500/20 bg-emerald-500/[0.03] shadow-[0_20px_80px_rgba(0,0,0,0.4)] transition-all duration-500 overflow-hidden relative">
                 <div className="absolute right-0 top-0 w-64 h-64 bg-emerald-500/[0.03] blur-3xl pointer-events-none translate-x-1/2 -translate-y-1/2"></div>
                 
                 <div className="flex flex-col md:flex-row md:items-center justify-between gap-10 relative z-10">
                   <div className="flex items-center gap-8">
                      <div className="w-24 h-24 bg-[#0a0a0a] border border-emerald-500/30 rounded-[32px] flex items-center justify-center shadow-2xl relative">
                        <Terminal size={40} className="text-emerald-500 group-hover:scale-110 transition-transform duration-500" />
                        <div className="absolute -right-2 -top-2 w-6 h-6 bg-emerald-500 rounded-full border-4 border-[#0a0a0a] shadow-[0_0_15px_rgba(16,185,129,0.8)]"></div>
                      </div>
                      <div className="space-y-2">
                        <div className="flex items-center gap-3">
                          <h3 className="text-3xl font-black text-white uppercase tracking-tight mantis-glow-text">{currentProvider.name}</h3>
                          <span className="px-3 py-1 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[9px] font-black rounded-full uppercase tracking-widest">Primary Node</span>
                        </div>
                        <div className="flex items-center gap-6">
                          <div className="flex items-center gap-2">
                             <Zap size={14} className="text-emerald-900/40" />
                             <span className="text-sm font-black text-emerald-500/60 font-mono">{currentProvider.model}</span>
                          </div>
                          <div className="flex items-center gap-2">
                             <ShieldCheck size={14} className="text-emerald-900/40" />
                             <span className="text-[10px] font-black text-emerald-900/40 uppercase tracking-widest whitespace-nowrap">
                               Initialized {new Date(currentProvider.configuredAt).toLocaleDateString()}
                             </span>
                          </div>
                        </div>
                      </div>
                   </div>
                   
                   <div className="h-20 w-px bg-white/[0.05] hidden md:block"></div>
                   
                   <div className="text-right">
                      <p className="text-[9px] font-black text-emerald-900/20 uppercase tracking-[0.3em] mb-3">Provisioning Status</p>
                      <div className="flex items-center justify-end gap-3 text-emerald-400">
                         <Activity size={18} className="animate-pulse" />
                         <span className="text-xl font-black uppercase tracking-tight">Full Sync</span>
                      </div>
                   </div>
                 </div>
               </GlassCard>
             ) : (
               <GlassCard className="p-20 text-center border-dashed border-white/[0.05] bg-white/[0.005]">
                  <p className="text-xs font-black text-emerald-900/20 uppercase tracking-[0.5em]">No Active Neural Link Detected</p>
               </GlassCard>
             )}
           </div>

           {/* Provider Grid Section */}
           <div className="space-y-8">
             <div className="flex items-center justify-between">
               <h2 className="text-[10px] font-black text-emerald-500/60 uppercase tracking-[0.4em] ml-2">Available Nodes</h2>
               <div className="h-px bg-white/[0.05] flex-1 mx-8 hidden sm:block"></div>
             </div>
             <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
               {availableProviders.map((provider) => (
                 <ProviderCard
                   key={provider.id}
                   provider={provider}
                   isActive={provider.id === currentProvider?.id}
                 />
               ))}
             </div>
           </div>
        </div>

        {/* Comparison & Diagnostics Sidebar */}
        <div className="space-y-10 relative z-10">
           <GlassCard className="p-8 space-y-8 border-white/[0.03] bg-white/[0.01]">
              <div className="flex items-center gap-4">
                 <div className="w-10 h-10 bg-emerald-500/10 border border-emerald-500/20 rounded-xl flex items-center justify-center text-emerald-500">
                    <Activity size={20} />
                 </div>
                 <h3 className="font-black text-white uppercase tracking-tight">Node Integrity</h3>
              </div>
              <p className="text-xs text-emerald-500/60 font-medium uppercase tracking-widest leading-relaxed">
                Regularly verify node connectivity. Latency spikes and credential expiration may interrupt neural flow. 
              </p>
              <div className="pt-4 space-y-3">
                 <div className="flex items-center justify-between text-[10px] font-black uppercase tracking-widest">
                    <span className="text-white/40">Uptime Mesh</span>
                    <span className="text-emerald-500">99.99%</span>
                 </div>
                 <div className="w-full h-1 bg-white/[0.05] rounded-full overflow-hidden">
                    <div className="h-full bg-emerald-500/40 w-[99.99%]"></div>
                 </div>
              </div>
           </GlassCard>

           <div className="p-10 border border-white/[0.03] rounded-[40px] bg-gradient-to-br from-emerald-500/[0.02] to-transparent space-y-6">
              <span className="px-3 py-1 bg-amber-500/10 border border-amber-500/20 text-amber-500 text-[9px] font-black rounded-full uppercase tracking-widest">Recommendation</span>
              <p className="text-sm font-black text-white uppercase tracking-tight leading-relaxed">
                For production deployments, Gemini-1.5-Pro offers the highest fidelity reasoning for merchant context.
              </p>
              <button className="text-[10px] font-black text-emerald-500 uppercase tracking-[.4em] hover:text-emerald-400 transition-colors">
                 Read Model Docs →
              </button>
           </div>
        </div>
      </div>

      {/* Footer Table Section */}
      <div className="relative z-10">
         <ProviderComparison providers={availableProviders} />
      </div>

      {/* Selection Modal Interface */}
      {selectedProvider && <ProviderConfigModal />}

      {/* Visual Response Notification */}
      <ProviderSwitchSuccess />

      {/* Error Overlay Hub */}
      {switchError && (
        <div className="fixed bottom-10 left-1/2 -translate-x-1/2 z-[110] max-w-lg w-full px-6">
           <GlassCard accent="red" className="py-6 px-8 flex items-center gap-6 border-red-500/30 bg-red-500/5 backdrop-blur-3xl shadow-[0_20px_60px_rgba(239,68,68,0.2)]">
              <div className="w-12 h-12 bg-red-500/10 border border-red-500/20 rounded-2xl flex items-center justify-center text-red-500 flex-shrink-0 animate-pulse">
                 <Terminal size={24} />
              </div>
              <div className="space-y-1">
                 <h4 className="text-[10px] font-black text-red-500 uppercase tracking-widest">Interlink Failure</h4>
                 <p className="text-xs text-white/60 font-black uppercase tracking-tight">{switchError}</p>
              </div>
           </GlassCard>
        </div>
      )}
    </div>
  );
};
