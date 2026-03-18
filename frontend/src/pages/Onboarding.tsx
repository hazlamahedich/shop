import React, { useEffect, useState } from 'react';
import { onboardingStore } from '../stores/onboardingStore';
import { InteractiveTutorial } from '../components/onboarding/InteractiveTutorial';
import { PrerequisiteChecklist } from '../components/onboarding/PrerequisiteChecklist';
import { DeploymentWizard } from '../components/onboarding/DeploymentWizard';
import { FacebookConnection } from '../components/onboarding/FacebookConnection';
import { ShopifyConnection } from '../components/onboarding/ShopifyConnection';
import { LLMConfiguration } from '../components/onboarding/LLMConfiguration';
import { ModeSelection } from '../components/onboarding/ModeSelection';
import { useDeploymentStore } from '../stores/deploymentStore';
import { useIntegrationsStore } from '../stores/integrationsStore';
import { useLLMStore } from '../stores/llmStore';
import { OnboardingMode, DEFAULT_ONBOARDING_MODE } from '../types/onboarding';
import { GlassCard } from '../components/ui/GlassCard';
import { Button } from '../components/ui/Button';
import { Check, Cpu, Zap, Rocket, Settings2, Sparkles } from 'lucide-react';

const Onboarding = () => {
  const { isComplete, loadFromBackend, onboardingMode, setOnboardingMode } = onboardingStore();
  const { status: deploymentStatus, merchantKey } = useDeploymentStore();
  const { facebookConnection, shopifyConnection } = useIntegrationsStore();
  const { configuration: llmConfig } = useLLMStore();

  const [wizardStep, setWizardStep] = useState(0);
  const [showTutorial, setShowTutorial] = useState(false);
  const [selectedMode, setSelectedMode] = useState<OnboardingMode | null>(null);
  const [modeSelected, setModeSelected] = useState(false);
  const [isModeLoading, setIsModeLoading] = useState(false);
  const [modeError, setModeError] = useState<string | null>(null);

  useEffect(() => {
    loadFromBackend();
  }, [loadFromBackend]);

  // Check if mode already selected from store
  useEffect(() => {
    if (onboardingMode) {
      setSelectedMode(onboardingMode);
      setModeSelected(true);
    }
  }, [onboardingMode]);

  // Determine current wizard step based on state if not manually set
  useEffect(() => {
    if (modeSelected && isComplete()) {
      if (merchantKey || deploymentStatus === 'success') {
        setWizardStep(3);
      } else {
        setWizardStep(2);
      }
    } else if (modeSelected) {
      setWizardStep(1);
    } else {
      setWizardStep(0);
    }
  }, [isComplete, deploymentStatus, merchantKey, modeSelected]);

  // Transitions
  const handleModeSelect = (mode: OnboardingMode) => {
    setSelectedMode(mode);
  };

  const handleModeContinue = async () => {
    if (selectedMode) {
      setIsModeLoading(true);
      setModeError(null);
      try {
        await setOnboardingMode(selectedMode);
        // Only navigate to next step if API succeeds
        setModeSelected(true);
      } catch (error) {
        setModeError(
          error instanceof Error
            ? error.message
            : 'Failed to save mode selection. Please try again.'
        );
      } finally {
        setIsModeLoading(false);
      }
    }
  };

  const handleModeRetry = () => {
    setModeError(null);
    handleModeContinue();
  };

  const handlePrerequisitesDone = () => setWizardStep(2);
  const handleDeploymentDone = () => setWizardStep(3);
  const startTutorial = () => setShowTutorial(true);

  // Determine if e-commerce connections are required based on mode
  const isEcommerce = selectedMode === 'ecommerce';
  const canStartTutorial = isEcommerce
    ? facebookConnection.connected && shopifyConnection.connected && llmConfig.provider
    : llmConfig.provider;

  if (showTutorial) {
    return (
      <div
        className="min-h-screen bg-[#050505] flex flex-col items-center justify-center p-4 overflow-hidden relative"
      >
        <div className="absolute inset-0 bg-gradient-to-b from-emerald-500/5 to-transparent opacity-20" />
        <div className="max-w-4xl w-full relative z-10">
          <InteractiveTutorial
            onComplete={() => (window.location.pathname = '/onboarding/success')}
          />
        </div>
      </div>
    );
  }

  const steps = [
    { id: 0, label: 'Mode', icon: Cpu },
    { id: 1, label: 'Protocols', icon: Zap },
    { id: 2, label: 'Deployment', icon: Rocket },
    { id: 3, label: 'Sync', icon: Settings2 },
  ];

  return (
    <div className="min-h-screen bg-[#050505] flex flex-col items-center py-20 px-6 relative overflow-hidden">
      {/* Background Ambience */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-7xl h-[500px] bg-emerald-500/10 blur-[120px] rounded-full -z-10 opacity-30" />
      
      <div className="max-w-5xl w-full space-y-16 relative z-10">
        {/* Header */}
        <div className="text-center space-y-6 max-w-2xl mx-auto">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-500/5 border border-emerald-500/10 rounded-full text-[10px] font-black uppercase tracking-[0.3em] text-emerald-400 mb-4 animate-in fade-in slide-in-from-top-4 duration-700">
            <Sparkles size={12} className="animate-pulse" />
            Neural Initialization Protocol
          </div>
          <h1 className="text-6xl font-black tracking-tight text-white leading-none mantis-glow-text">
            Awaken Your Agent
          </h1>
          <p className="text-xl text-emerald-900/60 font-medium leading-relaxed">
            {selectedMode === 'general'
              ? 'Initialize your core autonomous protocols and neural pathways.'
              : 'Synchronize your e-commerce engine with our advanced AI core.'}
          </p>
        </div>

        {/* Stepper Redesigned */}
        <div className="relative max-w-3xl mx-auto">
          <div className="absolute top-6 left-0 right-0 h-px bg-white/[0.03] -z-10" />
          <div className="flex items-center justify-between">
            {steps.map((s, i) => {
              const Icon = s.icon;
              const isActive = s.id === wizardStep;
              const isCompleted = s.id < wizardStep;
              
              return (
                <div key={s.id} className="flex flex-col items-center relative group">
                  <div
                    className={`
                      w-14 h-14 rounded-2xl flex items-center justify-center transition-all duration-700 border
                      ${isActive 
                        ? 'bg-emerald-500 text-black border-emerald-400 scale-110 shadow-[0_0_30px_rgba(16,185,129,0.4)]' 
                        : isCompleted
                          ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                          : 'bg-white/[0.02] text-white/20 border-white/[0.05] group-hover:border-white/10 group-hover:text-white/40'}
                    `}
                  >
                    {isCompleted ? <Check size={20} strokeWidth={3} /> : <Icon size={20} />}
                  </div>
                  <span
                    className={`
                      mt-4 text-[10px] font-black uppercase tracking-[0.2em] transition-all duration-500
                      ${isActive ? 'text-emerald-400' : 'text-white/20'}
                    `}
                  >
                    {s.label}
                  </span>
                  
                  {isActive && (
                    <div className="absolute -bottom-2 w-1 h-1 bg-emerald-400 rounded-full shadow-[0_0_10px_rgba(16,185,129,1)]" />
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Wizard Content with Glassmorphic Transition */}
        <div className="animate-in fade-in slide-in-from-bottom-8 duration-1000">
          {wizardStep === 0 && (
            <ModeSelection
              selectedMode={selectedMode}
              onModeSelect={handleModeSelect}
              onContinue={handleModeContinue}
              isLoading={isModeLoading}
              error={modeError}
              onRetry={handleModeRetry}
            />
          )}

          {wizardStep === 1 && (
            <div className="space-y-12">
              <GlassCard accent="mantis" className="p-10 border-emerald-500/10 bg-emerald-500/[0.01]">
                <PrerequisiteChecklist mode={selectedMode || DEFAULT_ONBOARDING_MODE} />
              </GlassCard>
              {isComplete() && (
                <div className="flex justify-center">
                  <button
                    onClick={handlePrerequisitesDone}
                    className="h-16 px-16 bg-emerald-500 text-black font-black text-[11px] uppercase tracking-[0.3em] rounded-2xl hover:bg-emerald-400 transition-all duration-500 shadow-[0_0_40px_rgba(16,185,129,0.2)] hover:shadow-[0_0_50px_rgba(16,185,129,0.4)] hover:-translate-y-1"
                  >
                    Proceed to Deployment
                  </button>
                </div>
              )}
            </div>
          )}

          {wizardStep === 2 && (
            <div className="space-y-12">
              <GlassCard accent="mantis" className="p-10 border-emerald-500/10 bg-emerald-500/[0.01]">
                <DeploymentWizard />
              </GlassCard>
              {(deploymentStatus === 'success' || merchantKey) && (
                <div className="flex justify-center">
                  <button
                    onClick={handleDeploymentDone}
                    className="h-16 px-16 bg-emerald-500 text-black font-black text-[11px] uppercase tracking-[0.3em] rounded-2xl hover:bg-emerald-400 transition-all duration-500 shadow-[0_0_40px_rgba(16,185,129,0.2)] hover:shadow-[0_0_50px_rgba(16,185,129,0.4)] hover:-translate-y-1"
                  >
                    Configure Neural Sync
                  </button>
                </div>
              )}
            </div>
          )}

          {wizardStep === 3 && (
            <div className="space-y-12 pb-20">
              {isEcommerce && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                  <GlassCard className="p-8 border-white/[0.03] bg-white/[0.01]">
                    <FacebookConnection />
                  </GlassCard>
                  <GlassCard className="p-8 border-white/[0.03] bg-white/[0.01]">
                    <ShopifyConnection />
                  </GlassCard>
                </div>
              )}

              <GlassCard accent="mantis" className="p-10 border-emerald-500/10 bg-emerald-500/[0.01]">
                <LLMConfiguration />
              </GlassCard>

              <GlassCard className="bg-emerald-500/[0.02] border-emerald-500/10 relative overflow-hidden group">
                <div className="absolute inset-0 bg-gradient-to-r from-emerald-500/[0.05] to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-1000" />
                <div className="p-12 text-center space-y-8 relative z-10">
                  <div className="space-y-4">
                    <h3 className="text-3xl font-black text-white tracking-tight leading-none uppercase">Final Verification</h3>
                    <p className="text-lg text-emerald-900/60 max-w-2xl mx-auto font-medium">
                      {isEcommerce
                        ? "Neural pathways established. Synchronize your platforms and finalize the calibration to initiate the agent."
                        : "Neural pathways established. Finalize the calibration to initiate the agent."}
                    </p>
                  </div>
                  
                  <div className="flex flex-col sm:flex-row justify-center gap-6 pt-4">
                    <button
                      onClick={startTutorial}
                      disabled={!canStartTutorial}
                      className={`
                        h-14 px-10 rounded-2xl flex items-center justify-center gap-3 font-black text-[10px] uppercase tracking-[0.3em] transition-all duration-500
                        ${canStartTutorial 
                          ? 'bg-emerald-500 text-black hover:bg-emerald-400 shadow-[0_0_30px_rgba(16,185,129,0.2)]' 
                          : 'bg-white/5 border border-white/10 text-white/20 cursor-not-allowed'}
                      `}
                    >
                      <Sparkles size={16} />
                      Interactive Calibration
                    </button>
                    <button
                      onClick={() => (window.location.pathname = '/onboarding/success')}
                      className="h-14 px-10 rounded-2xl bg-white/5 border border-white/10 text-white font-black text-[10px] uppercase tracking-[0.3em] hover:bg-white/10 hover:border-white/20 transition-all duration-500"
                    >
                      Bypass to Dashboard
                    </button>
                  </div>
                  
                  {!canStartTutorial && (
                    <div className="inline-flex items-center gap-2 px-4 py-2 bg-red-500/5 border border-red-500/10 rounded-xl text-[9px] font-black text-red-500 uppercase tracking-widest animate-pulse">
                      <Settings2 size={12} />
                      Core protocols pending calibration
                    </div>
                  )}
                </div>
              </GlassCard>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Onboarding;
