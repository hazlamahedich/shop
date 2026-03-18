/**
 * BotConfig Page Component
 *
 * Story 1.12: Bot Naming
 * Story 1.15: Product Highlight Pins
 *
 * Main page for configuring bot settings including:
 * - Bot name input with live preview
 * - Display of current personality
 * - Product highlight pins management (Story 1.15)
 * - Save functionality for bot name changes
 * - Loading states and error handling
 * - Navigation breadcrumbs
 *
 * WCAG 2.1 AA accessible.
 */

import React from 'react';
import { useEffect } from 'react';
import { Info, CheckCircle2, AlertCircle, Palette } from 'lucide-react';
import { useToast } from '../context/ToastContext';
import { useBotConfigStore } from '../stores/botConfigStore';
import { useOnboardingPhaseStore } from '../stores/onboardingPhaseStore';
import { BotNameInput } from '../components/bot-config/BotNameInput';
import { ProductPinList } from '../components/business-info/ProductPinList';
import { TutorialPrompt } from '../components/onboarding/TutorialPrompt';
import { GlassCard } from '../components/ui/GlassCard';

/**
 * Get personality display name and color
 */
function getPersonalityInfo(personality: string | null) {
  switch (personality) {
    case 'professional':
      return { name: 'Professional', color: 'text-indigo-300', bgColor: 'bg-indigo-500/20', borderColor: 'border-indigo-500/30' };
    case 'enthusiastic':
      return { name: 'Enthusiastic', color: 'text-amber-300', bgColor: 'bg-amber-500/20', borderColor: 'border-amber-500/30' };
    case 'friendly':
    default:
      return { name: 'Friendly', color: 'text-emerald-300', bgColor: 'bg-emerald-500/20', borderColor: 'border-emerald-500/30' };
  }
}

/**
 * BotConfig Component
 *
 * Main configuration page for bot naming and personality display.
 *
 * Features:
 * - Bot name input with live preview
 * - Display of current personality
 * - Save functionality for bot name
 * - Automatic loading of existing configuration
 * - Success and error notifications
 */
export const BotConfig: React.FC = () => {
  const {
    botName,
    personality,
    loadingState,
    error,
    isDirty,
    fetchBotConfig,
    updateBotName,
    clearError,
  } = useBotConfigStore();

  const markBotConfigComplete = useOnboardingPhaseStore((state) => state.markBotConfigComplete);

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

  // Handle save bot name
  const handleSaveBotName = async () => {
    clearError();

    try {
      await updateBotName({
        bot_name: botName,
      });

      markBotConfigComplete('botName');
      toast('Bot name saved successfully!', 'success');
    } catch (err) {
      console.error('Failed to save bot name:', err);
      toast('Failed to save bot name', 'error');
    }
  };

  // Is any operation in progress?
  const isLoading = loadingState === 'loading';
  const hasConfig = botName || personality;
  const personalityInfo = getPersonalityInfo(personality);

  return (
    <div className="min-h-screen bg-[var(--mantis-bg)] text-white/90">
      {/* Breadcrumb Navigation */}
      <nav className="glass py-4 mb-8 sticky top-0 z-30" aria-label="Breadcrumb">
        <div className="max-w-7xl mx-auto px-6">
          <ol className="flex items-center gap-3 text-sm">
            <li>
              <a href="/dashboard" className="text-white/50 hover:text-[var(--mantis-glow)] transition-all duration-300">
                Dashboard
              </a>
            </li>
            <li className="text-white/20">/</li>
            <li>
              <span className="font-medium text-white/90">Bot Configuration</span>
            </li>
          </ol>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 pb-12">
        {/* Page Header */}
        <div className="mb-10 animate-fade-in">
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-4xl font-bold tracking-tight mb-3 text-white">
                Bot Configuration
              </h1>
              <p className="text-lg text-emerald-500/60 max-w-3xl leading-relaxed">
                Customize how your bot introduces itself. Set a memorable bot name 
                and configure product highlights. For greeting customization, visit 
                the <a href="/personality" className="text-[var(--mantis-glow)] hover:underline decoration-2 underline-offset-4">Bot Personality</a> page.
              </p>
            </div>
            <div className="hidden md:flex items-center gap-2 px-4 py-2 bg-[var(--mantis-glow)]/10 border border-[var(--mantis-glow)]/20 text-[var(--mantis-glow)] rounded-xl text-sm font-medium">
              <Info size={18} />
              <span>Premium Configuration</span>
            </div>
          </div>
        </div>

        {/* Tutorial Prompt Banner - Post-configuration */}
      <TutorialPrompt />

      {/* Error Display (page-level) */}
        {error && (
          <GlassCard className="mb-8 animate-shake bg-red-500/10 border-red-500/20">
            <div className="flex items-start gap-4">
              <AlertCircle size={24} className="text-red-400 flex-shrink-0" />
              <div className="flex-1">
                <p className="text-lg font-semibold text-red-200">Configuration Error</p>
                <p className="text-white/70 mt-1">{error}</p>
              </div>
              <button
                type="button"
                onClick={clearError}
                className="text-white/40 hover:text-white transition-colors p-2"
                aria-label="Dismiss error"
              >
                ×
              </button>
            </div>
          </GlassCard>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-12">
          {/* Bot Name Input */}
          <div className="lg:col-span-2">
            <GlassCard className="h-full">
              <div className="flex items-center justify-between mb-8">
                <h2 className="text-2xl font-bold text-white flex items-center gap-3">
                  <span className="w-1.5 h-8 bg-[var(--mantis-glow)] rounded-full"></span>
                  Bot Identity
                </h2>
                {botName && (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-emerald-500/20 text-emerald-400 text-xs font-bold uppercase tracking-wider rounded-lg border border-emerald-500/30">
                    <CheckCircle2 size={14} />
                    Verified
                  </span>
                )}
              </div>

              <div className="space-y-8">
                <BotNameInput disabled={isLoading} />

                {/* Save Button */}
                <div className="pt-8 border-t border-white/5">
                  <button
                    type="button"
                    onClick={handleSaveBotName}
                    disabled={isLoading || !isDirty}
                    className="w-full relative px-6 py-4 text-base font-bold text-white bg-[var(--mantis-glow)] rounded-xl hover:brightness-110 active:scale-[0.98] transition-all disabled:opacity-30 disabled:scale-100 disabled:cursor-not-allowed shadow-[0_0_20px_rgba(34,197,94,0.2)]"
                  >
                    {isLoading ? (
                      <span className="flex items-center justify-center gap-3">
                        <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                          <circle
                            className="opacity-25"
                            cx="12"
                            cy="12"
                            r="10"
                            stroke="currentColor"
                            strokeWidth="4"
                            fill="none"
                          />
                          <path
                            className="opacity-75"
                            fill="currentColor"
                            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                          />
                        </svg>
                        Deploying Changes...
                      </span>
                    ) : (
                      'Save Identity Profile'
                    )}
                  </button>
                  {!isDirty && hasConfig && (
                    <p className="text-sm text-center text-white/40 mt-4 font-medium animate-fade-in">
                      Profile synchronized successfully
                    </p>
                  )}
                </div>
              </div>
            </GlassCard>
          </div>

          {/* Current Settings Display */}
          <div className="lg:col-span-1">
            <GlassCard className="h-full">
              <h2 className="text-2xl font-bold text-white mb-8">System Status</h2>

              <div className="space-y-6">
                {/* Personality Display */}
                {personality && (
                  <div className="p-5 rounded-2xl bg-white/5 border border-white/10 hover:bg-white/10 transition-all cursor-default">
                    <div className="flex items-center gap-3 mb-4">
                      <Palette size={20} className="text-white/40" />
                      <span className="text-sm font-semibold text-emerald-500/60 uppercase tracking-widest block mb-1">Core Personality</span>
                    </div>
                    <div
                      className={`inline-flex items-center px-4 py-2 text-sm font-bold rounded-xl border ${personalityInfo.borderColor} ${personalityInfo.bgColor} ${personalityInfo.color} shadow-lg`}
                    >
                      {personalityInfo.name}
                    </div>
                  </div>
                )}

                {/* No Settings Message */}
                {!personality && (
                  <div className="p-6 bg-white/5 rounded-2xl border border-dashed border-white/20">
                    <p className="text-base text-white/50 leading-relaxed">
                      Core personality matrix not initialized. Connect your voice modules in the personality configuration.
                    </p>
                  </div>
                )}

                {/* Configure Personality Link */}
                <div className="pt-6">
                  <a
                    href="/personality"
                    className="flex items-center justify-between p-4 rounded-xl bg-[var(--mantis-glow)]/5 text-[var(--mantis-glow)] hover:bg-[var(--mantis-glow)]/10 transition-all font-bold tracking-tight"
                  >
                    <span>Tune Personality</span>
                    <span>→</span>
                  </a>
                </div>
              </div>
            </GlassCard>
          </div>
        </div>

        {/* Story 1.15: Product Highlight Pins Section */}
        <div className="mb-12">
          <ProductPinList />
        </div>

        {/* Help Section */}
        <GlassCard className="from-[var(--mantis-glow)]/5 to-transparent border-[var(--mantis-glow)]/10">
          <h3 className="text-2xl font-bold text-white mb-6 flex items-center gap-3">
            <Info size={24} className="text-[var(--mantis-glow)]" />
            Neural Configuration Logic
          </h3>
          <div className="grid md:grid-cols-2 gap-10 text-base">
            {/* Story 1.12: Bot Names */}
            <div className="p-6 rounded-2xl bg-white/5 border border-white/10">
              <h4 className="font-bold text-white mb-3 text-lg uppercase tracking-tight">Identity Modules</h4>
              <p className="text-white/60 leading-relaxed mb-4">
                A custom bot identity creates a persistent neural presence for your customers. Choose a designation
                that resonates with your brand architecture.
              </p>
              <div className="p-4 bg-black/30 rounded-xl border border-white/5 text-sm text-[var(--mantis-glow)] font-mono">
                &gt; Hello, I am System.Mantis. How can I assist?
              </div>
            </div>

            {/* Story 1.15: Product Highlight Pins */}
            <div className="p-6 rounded-2xl bg-white/5 border border-white/10">
              <h4 className="font-bold text-white mb-3 text-lg uppercase tracking-tight">Priority Anchors</h4>
              <p className="text-white/60 leading-relaxed mb-4">
                Anchor high-value assets to top-level recommendation queues. Anchored assets
                receive a <span className="text-[var(--mantis-glow)] font-bold">200% relevance boost</span> in the retrieval matrix.
              </p>
              <ul className="text-sm text-white/50 space-y-2">
                <li className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 bg-[var(--mantis-glow)] rounded-full"></span>
                  Capacity: 10 Priority Anchors
                </li>
                <li className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 bg-[var(--mantis-glow)] rounded-full"></span>
                  Synchronization: Real-time global propagation
                </li>
              </ul>
            </div>
          </div>
        </GlassCard>
      </main>
    </div>
  );
};

export default BotConfig;
