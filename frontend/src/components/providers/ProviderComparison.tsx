/**
 * Provider Comparison Component.
 *
 * Story 3.4: LLM Provider Switching
 * Re-imagined with Mantis aesthetic for professional spectral analysis.
 */

import React from 'react';
import type { Provider } from '../../stores/llmProviderStore';
import { GlassCard } from '../ui/GlassCard';
import { Activity, BarChart3, TrendingUp, Cpu } from 'lucide-react';

interface ProviderComparisonProps {
  providers: Provider[];
}

export const ProviderComparison: React.FC<ProviderComparisonProps> = ({
  providers,
}) => {
  if (providers.length === 0) {
    return null;
  }

  return (
    <div className="mt-16 space-y-8 animate-in fade-in slide-in-from-bottom-8 duration-1000">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div className="space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-emerald-500/5 border border-emerald-500/10 rounded-full text-[10px] font-black uppercase tracking-[0.2em] text-emerald-400">
            <BarChart3 size={12} />
            Spectral Analysis
          </div>
          <h2 className="text-3xl font-black tracking-tight text-white uppercase leading-none mantis-glow-text">
            Node Comparison
          </h2>
          <p className="text-[11px] font-black text-emerald-500/60 uppercase tracking-[0.2em] max-w-xl leading-relaxed">
            Direct capability evaluation across the neural network mesh.
          </p>
        </div>
        
        <div className="flex items-center gap-4 text-emerald-900/20">
           < TrendingUp size={24} />
           <div className="h-10 w-px bg-white/[0.05]"></div>
           <Cpu size={24} />
        </div>
      </div>

      <GlassCard className="p-0 border-white/[0.03] overflow-hidden bg-white/[0.005]">
        <div className="overflow-x-auto custom-scrollbar">
          <table
            data-testid="provider-comparison-table"
            className="w-full border-collapse"
            role="table"
            aria-label="LLM Provider Pricing Comparison"
          >
            <thead>
              <tr className="bg-white/[0.02]">
                <th className="border-b border-white/[0.05] px-8 py-6 text-left text-[10px] font-black uppercase tracking-[0.3em] text-emerald-500/60">
                  Neural Node
                </th>
                <th className="border-b border-white/[0.05] px-8 py-6 text-right text-[10px] font-black uppercase tracking-[0.3em] text-emerald-500/60">
                   Input Load (1M)
                </th>
                <th className="border-b border-white/[0.05] px-8 py-6 text-right text-[10px] font-black uppercase tracking-[0.3em] text-emerald-500/60">
                   Output Load (1M)
                </th>
                <th className="border-b border-white/[0.05] px-8 py-6 text-right text-[10px] font-black uppercase tracking-[0.3em] text-emerald-500/60">
                   Context Density
                </th>
                <th className="border-b border-white/[0.05] px-8 py-6 text-right text-[10px] font-black uppercase tracking-[0.3em] text-emerald-500/60">
                   Forecast Index
                </th>
                <th className="border-b border-white/[0.05] px-8 py-6 text-left text-[10px] font-black uppercase tracking-[0.3em] text-emerald-500/60">
                  Core Attributes
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.02]">
              {providers.map((provider) => (
                <tr
                  key={provider.id}
                  className={`group transition-all duration-300 ${provider.isActive ? 'bg-emerald-500/[0.03]' : 'hover:bg-white/[0.01]'}`}
                >
                  <td className="px-8 py-6">
                    <div className="flex items-center gap-4">
                      {provider.isActive && (
                        <div className="relative">
                          <Activity size={14} className="text-emerald-500 animate-pulse" />
                          <div className="absolute inset-0 bg-emerald-500 blur-sm opacity-50 animate-pulse"></div>
                        </div>
                      )}
                      <div className="flex flex-col">
                         <span className={`font-black uppercase tracking-tight ${provider.isActive ? 'text-emerald-400 mantis-glow-text' : 'text-white/60'}`}>
                           {provider.name}
                         </span>
                         {provider.isActive && (
                           <span className="text-[9px] font-black text-emerald-900/40 uppercase tracking-[0.2em] mt-0.5">Primary Link</span>
                         )}
                      </div>
                    </div>
                  </td>
                  <td className="px-8 py-6 text-right">
                    <span className="font-mono text-sm font-black text-white/50 group-hover:text-emerald-400/60 transition-colors">
                      ${provider.pricing.inputCost.toFixed(2)}
                    </span>
                  </td>
                  <td className="px-8 py-6 text-right">
                    <span className="font-mono text-sm font-black text-white/50 group-hover:text-emerald-400/60 transition-colors">
                      ${provider.pricing.outputCost.toFixed(2)}
                    </span>
                  </td>
                  <td className="px-8 py-6 text-right">
                    <span className="font-mono text-[11px] font-black text-emerald-500/60 uppercase tabular-nums">
                      {Math.max(...provider.models.map(m => m.contextLength), 0) / 1024}K
                    </span>
                  </td>
                  <td className="px-8 py-6 text-right">
                    <span className="font-black text-white group-hover:mantis-glow-text transition-all">
                      ${provider.estimatedMonthlyCost?.toFixed(2) || '0.00'}
                    </span>
                  </td>
                  <td className="px-8 py-6">
                    <div className="flex flex-wrap gap-2">
                      {provider.features.slice(0, 3).map((feature) => (
                        <span
                          key={feature}
                          className="text-[9px] font-black uppercase tracking-widest bg-white/[0.05] border border-white/[0.05] px-2 py-0.5 rounded-lg text-emerald-900/40 group-hover:border-emerald-500/20 group-hover:text-emerald-500/60 transition-all"
                        >
                          {feature}
                        </span>
                      ))}
                      {provider.features.length > 3 && (
                        <span className="text-[9px] font-black text-emerald-900/20 uppercase tracking-widest pt-1 px-1">
                          +{provider.features.length - 3} more
                        </span>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </GlassCard>

      {/* Calculator Logic Banner */}
      <GlassCard accent="mantis" className="p-6 border-amber-500/10 bg-amber-500/[0.02]">
        <div className="flex items-start gap-4 text-amber-500/60">
          <Activity size={18} className="mt-0.5" />
          <p className="text-[10px] font-black text-amber-500/60 uppercase tracking-widest leading-relaxed">
            <strong className="text-amber-500">Spectral Calculation:</strong> Estimated costs are calibrated against a baseline of 100K inbound and 50K outbound tokens. Actual neural firing density will modulate final results.
          </p>
        </div>
      </GlassCard>
    </div>
  );
};
