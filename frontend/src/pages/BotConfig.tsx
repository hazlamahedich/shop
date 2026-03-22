/**
 * BotConfig Page Component
 *
 * Story 1.12: Bot Naming
 * Story 1.15: Product Highlight Pins
 *
 * Main page for configuring bot settings.
 * Redesigned with a "Tactical HUD" aesthetic.
 *
 * WCAG 2.1 AA accessible.
 */

import React, { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Info, AlertCircle, Palette, Settings } from 'lucide-react';
import { useAuthStore } from '../stores/authStore';
import { useToast } from '../context/ToastContext';
import { useBotConfigStore } from '../stores/botConfigStore';
import { ProductPinList } from '../components/business-info/ProductPinList';
import { TutorialPrompt } from '../components/onboarding/TutorialPrompt';
import { GlassCard } from '../components/ui/GlassCard';
import { BotIdentityHUD } from '../components/bot-config/BotIdentityHUD';
import { SystemStatusHUD } from '../components/bot-config/SystemStatusHUD';
import { OutputSimulationHUD } from '../components/bot-config/OutputSimulationHUD';

export const BotConfig: React.FC = () => {
  const merchant = useAuthStore((state) => state.merchant);
  const {
    fetchBotConfig,
    error,
    clearError,
  } = useBotConfigStore();

  const { toast } = useToast();

  // Load configuration on mount
  useEffect(() => {
    const loadConfig = async () => {
      try {
        await fetchBotConfig();
      } catch (err) {
        console.error('Failed to load configuration:', err);
        toast('Failed to load configuration', 'error');
      }
    };

    loadConfig();
  }, [fetchBotConfig, toast]);

  return (
    <div className="min-h-screen bg-[#131318] text-white/90 selection:bg-[var(--mantis-glow)]/30 font-body">
      {/* Breadcrumb Navigation - Refined for HUD */}
      <nav className="fixed top-0 w-full z-50 flex justify-between items-center px-6 h-16 bg-[#131318]/60 backdrop-blur-xl border-b border-white/10 shadow-[0_0_32px_rgba(0,187,249,0.08)]" aria-label="Breadcrumb">
        <div className="flex items-center gap-8">
          <span className="text-2xl font-bold bg-gradient-to-r from-[#d7fff3] to-[#00f5d4] bg-clip-text text-transparent font-headline tracking-tight">Mantis Shop</span>
          <ol className="hidden md:flex items-center gap-3 text-[10px] font-bold uppercase tracking-widest text-white/40">
            <li>
              <a href="/dashboard" className="hover:text-[var(--mantis-glow)] transition-all duration-300">
                Dashboard
              </a>
            </li>
            <li className="text-white/10">/</li>
            <li>
              <span className="text-[var(--mantis-glow)]">Bot Configuration</span>
            </li>
          </ol>
        </div>
        <div className="hidden md:flex items-center gap-2 px-4 py-1.5 bg-[var(--mantis-glow)]/10 border border-[var(--mantis-glow)]/20 text-[var(--mantis-glow)] rounded-full text-[10px] font-bold uppercase tracking-tighter">
          <Info size={14} />
          <span>Hyper-Luminous v2.1</span>
        </div>
      </nav>

      {/* Main Content Canvas */}
      <main className="pt-24 pb-12 px-6 max-w-7xl mx-auto">
        {/* Page Header - Technical Style */}
        <div className="mb-12 animate-fade-in">
          <div className="flex flex-col gap-2">
            <div className="flex items-center justify-between mb-2">
              <h1 className="text-4xl font-black font-headline tracking-tighter text-white uppercase italic">
                Bot Config <span className="text-[var(--mantis-glow)]">_HUD</span>
              </h1>
              
              <div className={`px-4 py-1.5 rounded-full border flex items-center gap-3 backdrop-blur-md transition-all ${
                merchant?.onboardingMode === 'ecommerce' 
                  ? 'bg-blue-500/10 border-blue-500/20 text-blue-400 shadow-[0_0_15px_rgba(59,130,246,0.1)]' 
                  : 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400 shadow-[0_0_15px_rgba(16,185,129,0.1)]'
              }`}>
                <div className={`w-2 h-2 rounded-full animate-pulse ${
                  merchant?.onboardingMode === 'ecommerce' ? 'bg-blue-400 shadow-[0_0_8px_#60a5fa]' : 'bg-emerald-400 shadow-[0_0_8px_#34d399]'
                }`} />
                <span className="text-[10px] font-black uppercase tracking-widest">
                  System Mode: {merchant?.onboardingMode === 'ecommerce' ? 'E-commerce' : 'General'}
                </span>
                <div className="w-px h-3 bg-white/10" />
                <Link 
                  to="/settings" 
                  className="flex items-center gap-1.5 hover:text-white transition-colors"
                >
                  <Settings size={12} className="animate-spin-slow" />
                  <span className="text-[9px] font-bold tracking-tighter">RECONFIG</span>
                </Link>
              </div>
            </div>
            <p className="text-sm text-white/40 max-w-2xl leading-relaxed uppercase font-bold tracking-tight">
              Tactical Interface for Neural Identity and Priority Alignment.
            </p>
          </div>
        </div>

        {/* Tutorial Prompt Banner */}
        <TutorialPrompt />

        {/* Error Display (page-level) */}
        {error && (
          <GlassCard className="mb-8 animate-shake bg-red-500/10 border-red-500/20">
            <div className="flex items-start gap-4">
              <AlertCircle size={24} className="text-red-400 flex-shrink-0" />
              <div className="flex-1">
                <p className="text-xs font-bold text-red-200 uppercase tracking-widest">Configuration Logic Failure</p>
                <p className="text-white/60 mt-1">{error}</p>
              </div>
              <button
                type="button"
                onClick={clearError}
                className="text-white/20 hover:text-white transition-colors p-2"
                aria-label="Dismiss error"
              >
                ×
              </button>
            </div>
          </GlassCard>
        )}

        {/* HUD Grid Layout */}
        <div className="grid grid-cols-12 gap-6 mb-12">
          {/* Left Column: Bot Identity */}
          <div className="col-span-12 lg:col-span-7 flex flex-col gap-6">
            <BotIdentityHUD />
            <OutputSimulationHUD />
          </div>

          {/* Right Column: System Status Intelligence */}
          <div className="col-span-12 lg:col-span-5 h-full">
            <SystemStatusHUD />
          </div>
        </div>

        {/* Story 1.15: Neural Priority Matrix */}
        <div className="mb-12">
          <ProductPinList />
        </div>

        {/* Footer: Intelligence Repository */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pb-12">
          <div className="bg-black/40 backdrop-blur-xl border border-white/10 p-6 rounded-2xl flex flex-col gap-3 group hover:border-[var(--mantis-glow)]/30 transition-all duration-500">
            <div className="w-10 h-10 rounded-xl bg-[var(--mantis-glow)]/10 flex items-center justify-center mb-2">
              <Palette size={20} className="text-[var(--mantis-glow)]" />
            </div>
            <h5 className="font-headline font-bold text-white uppercase tracking-tight">Identity Modules</h5>
            <p className="text-xs text-white/40 leading-relaxed font-medium">Custom bot identity creates a persistent neural presence for customers. Choose a designation that resonates with brand architecture.</p>
          </div>

          <div className="bg-black/40 backdrop-blur-xl border border-white/10 p-6 rounded-2xl flex flex-col gap-3 group hover:border-[var(--mantis-glow)]/30 transition-all duration-500">
            <div className="w-10 h-10 rounded-xl bg-[var(--mantis-glow)]/10 flex items-center justify-center mb-2">
              <Info size={20} className="text-[var(--mantis-glow)]" />
            </div>
            <h5 className="font-headline font-bold text-white uppercase tracking-tight">Sequence Control</h5>
            <p className="text-xs text-white/40 leading-relaxed font-medium">Link sequence determines propagation order. Assets with lower link indices are prioritized during the initial retrieval phase.</p>
          </div>

          <div className="bg-black/40 backdrop-blur-xl border border-white/10 p-6 rounded-2xl flex flex-col gap-3 group hover:border-[var(--mantis-glow)]/30 transition-all duration-500">
            <div className="w-10 h-10 rounded-xl bg-red-400/10 flex items-center justify-center mb-2">
              <AlertCircle size={20} className="text-red-400" />
            </div>
            <h5 className="font-headline font-bold text-white uppercase tracking-tight">Asset Status</h5>
            <p className="text-xs text-white/40 leading-relaxed font-medium">Cross-referencing Shopify SKU data reflects real-time stock levels. Inert and archived assets are excluded from active inference cycles.</p>
          </div>
        </div>
      </main>
    </div>
  );
};

export default BotConfig;
