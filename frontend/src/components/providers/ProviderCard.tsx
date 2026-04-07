/**
 * Provider Card Component.
 *
 * Story 3.4: LLM Provider Switching
 * Re-imagined with Mantis aesthetic.
 */

import React from 'react';
import { Zap, DollarSign, Server, Settings, Activity, Cpu } from 'lucide-react';
import { useLLMProviderStore } from '../../stores/llmProviderStore';
import type { Provider } from '../../stores/llmProviderStore';
import { GlassCard } from '../ui/GlassCard';

interface ProviderCardProps {
  provider: Provider;
  isActive: boolean;
}

export const ProviderCard: React.FC<ProviderCardProps> = ({ provider, isActive }) => {
  const { selectProvider } = useLLMProviderStore();

  const handleSelect = () => {
    selectProvider(provider.id);
  };

  const getFeatureIcon = (feature: string): React.ReactNode => {
    switch (feature) {
      case 'local':
        return <Server size={14} aria-hidden="true" />;
      case 'free':
        return <DollarSign size={14} aria-hidden="true" />;
      case 'fast':
        return <Zap size={14} aria-hidden="true" />;
      default:
        return null;
    }
  };

  return (
    <GlassCard
      accent={isActive ? 'mantis' : undefined}
      data-testid={`provider-card-${provider.id}`}
      className={`p-6 flex flex-col justify-between transition-all duration-500 overflow-hidden group ${
        isActive
          ? 'border-emerald-500/30 bg-emerald-500/[0.03] shadow-[0_20px_60px_rgba(16,185,129,0.1)]'
          : 'border-white/[0.03] bg-white/[0.01] hover:border-emerald-500/20 hover:bg-emerald-500/[0.02]'
      }`}
      role="option"
      aria-selected={isActive}
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          handleSelect();
        }
      }}
    >
      <div>
        <div className="flex items-start justify-between mb-6">
          <div className="space-y-1">
            <h3 className="font-black text-xl text-white uppercase tracking-tight group-hover:mantis-glow-text transition-all">
              {provider.name}
            </h3>
            <p className="text-[10px] font-black text-emerald-500/60 uppercase tracking-widest leading-relaxed">
              {provider.description}
            </p>
          </div>
          {isActive && (
            <div className="flex items-center gap-3 px-3 py-1 bg-emerald-500/10 border border-emerald-500/20 rounded-full shadow-[0_0_15px_rgba(16,185,129,0.1)]">
              <Activity size={12} className="text-emerald-400 animate-pulse" />
              <span className="text-[9px] font-black text-emerald-400 uppercase tracking-widest">Active Service</span>
            </div>
          )}
        </div>

        {/* Pricing Matrix */}
        <div className="mb-6 p-4 bg-white/[0.02] border border-white/[0.05] rounded-2xl group-hover:border-emerald-500/10 transition-colors">
          <p className="text-[9px] font-black text-emerald-500/60 uppercase tracking-[0.3em] mb-2">Price per 1M Requests</p>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-black text-white tracking-tighter">${provider.pricing.inputCost.toFixed(2)}</span>
            <span className="text-xs text-emerald-900/20 font-black">/</span>
            <span className="text-lg font-black text-emerald-500/60">${provider.pricing.outputCost.toFixed(2)}</span>
          </div>
          <div className="mt-2 flex items-center justify-between text-[10px] font-black uppercase tracking-widest text-emerald-500/60">
             <div className="flex flex-col">
               <span className="text-[8px] opacity-40">Input</span>
               <span className="mt-0.5">Inbound</span>
             </div>
             <div className="flex flex-col text-right">
               <span className="text-[8px] opacity-40">Output</span>
               <span className="mt-0.5">Outbound</span>
             </div>
          </div>
        </div>

        {/* Service Type */}
        <div className="mb-6 flex items-center justify-between px-4 py-3 bg-white/[0.01] border border-white/[0.03] rounded-xl">
          <div className="flex items-center gap-2">
            <Cpu size={14} className="text-emerald-500/40" />
            <span className="text-[10px] font-black text-emerald-500/60 uppercase tracking-widest">Service Type</span>
          </div>
          <span className="text-xs font-black text-white">{provider.models.length} Models</span>
        </div>

        {/* Capabilities Array */}
        <div className="mb-6 flex flex-wrap gap-2" role="list" aria-label="Provider features">
          {provider.features.map((feature) => (
            <span
              key={feature}
              className="px-3 py-1.5 bg-white/[0.03] border border-white/[0.05] text-emerald-500/60 text-[9px] font-black uppercase tracking-widest rounded-xl flex items-center gap-2 group-hover:border-emerald-500/20 group-hover:text-emerald-500 transition-all"
              role="listitem"
            >
              {getFeatureIcon(feature)}
              <span>{feature}</span>
            </span>
          ))}
        </div>

        {/* Monthly Projection */}
        {provider.estimatedMonthlyCost !== undefined && (
          <div className="mb-8 flex items-center justify-between">
            <span className="text-[10px] font-black text-emerald-900/20 uppercase tracking-[0.2em]">Spectral Forecast</span>
            <div className="flex flex-col items-end">
              <span className="text-sm font-black text-white/50 group-hover:text-emerald-500/60 transition-colors">
                ${provider.estimatedMonthlyCost.toFixed(2)}/mo
              </span>
              <span className="text-[8px] font-black text-emerald-900/10 uppercase mt-0.5">Est. Volume: 150K Tokens</span>
            </div>
          </div>
        )}
      </div>

      {/* Control Interface */}
      <button
        onClick={handleSelect}
        className={`w-full h-14 rounded-2xl font-black text-[10px] uppercase tracking-[0.3em] transition-all duration-300 flex items-center justify-center gap-3 ${
          isActive
            ? 'bg-emerald-500 text-black shadow-[0_10px_30px_rgba(16,185,129,0.3)] hover:shadow-[0_15px_40px_rgba(16,185,129,0.4)]'
            : 'bg-white/5 border border-white/10 text-white hover:bg-emerald-500/[0.05] hover:border-emerald-500/30'
        }`}
        aria-label={isActive ? `Update ${provider.name} configuration` : `Select ${provider.name} provider`}
      >
        {isActive ? (
          <>
            <Settings size={16} aria-hidden="true" />
            Recalibrate Node
          </>
        ) : (
          <>
            <Zap size={16} aria-hidden="true" />
            Initialize Link
          </>
        )}
      </button>
    </GlassCard>
  );
};
