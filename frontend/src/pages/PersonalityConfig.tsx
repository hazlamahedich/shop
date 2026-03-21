import React, { useEffect, useState, useCallback, useRef } from 'react';
import { Save, AlertCircle, Loader2, Binary, Activity, ShieldCheck, Zap } from 'lucide-react';
import { usePersonalityStore, selectPersonality, selectCustomGreeting, selectPersonalityLoading, selectPersonalityError, selectPersonalityIsDirty } from '../stores/personalityStore';
import { useOnboardingPhaseStore } from '../stores/onboardingPhaseStore';
import { useBotConfigStore } from '../stores/botConfigStore';
import { useBusinessInfoStore } from '../stores/businessInfoStore';
import { PersonalityCard } from '../components/personality/PersonalityCard';
import { GreetingConfig } from '../components/business-info/GreetingConfig';
import type { PersonalityType } from '../types/enums';
import { PersonalityDisplay, PersonalityDefaultGreetings } from '../types/enums';
import { isToneMatch, getToneMismatchMessage, hasToneMismatch } from '../utils/toneDetection';
import { merchantConfigApi } from '../services/merchantConfig';

const PersonalityConfig: React.FC = () => {
  const personality = usePersonalityStore(selectPersonality);
  const customGreeting = usePersonalityStore(selectCustomGreeting);
  const loading = usePersonalityStore(selectPersonalityLoading);
  const error = usePersonalityStore(selectPersonalityError);
  const isDirty = usePersonalityStore(selectPersonalityIsDirty);
  const markBotConfigComplete = useOnboardingPhaseStore((state) => state.markBotConfigComplete);
  const botName = useBotConfigStore((state) => state.botName);
  const businessName = useBusinessInfoStore((state) => state.businessName);
  const businessHours = useBusinessInfoStore((state) => state.businessHours);

  const [selectedPersonality, setSelectedPersonality] = useState<PersonalityType | null>(null);
  const [greetingValue, setGreetingValue] = useState<string>('');
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'success' | 'error'>('idle');
  const [localError, setLocalError] = useState<string | null>(null);
  const [showToneWarning, setShowToneWarning] = useState(false);
  const [dismissedWarning, setDismissedWarning] = useState(false);
  const [transformLoading, setTransformLoading] = useState(false);
  const [transformedGreeting, setTransformedGreeting] = useState<string | null>(null);
  const [suggestionApplied, setSuggestionApplied] = useState(false);

  const fetchPersonalityConfig = usePersonalityStore((state) => state.fetchPersonalityConfig);
  const updatePersonalityConfig = usePersonalityStore((state) => state.updatePersonalityConfig);
  const setPersonality = usePersonalityStore((state) => state.setPersonality);
  const setCustomGreeting = usePersonalityStore((state) => state.setCustomGreeting);
  const resetToDefault = usePersonalityStore((state) => state.resetToDefault);
  const clearError = usePersonalityStore((state) => state.clearError);

  const prevGreetingRef = useRef<string>('');
  const prevPersonalityRef = useRef<PersonalityType | null>(null);

  useEffect(() => {
    const init = async () => {
      try {
        await fetchPersonalityConfig();
      } catch (err) {
        setLocalError('Neural link failure: Failed to retrieve personality configuration.');
        console.error('Failed to initialize personality config:', err);
      }
    };
    init();
  }, [fetchPersonalityConfig]);

  useEffect(() => {
    if (personality) {
      setSelectedPersonality(personality);
    }
  }, [personality]);

  useEffect(() => {
    setGreetingValue(customGreeting || '');
  }, [customGreeting]);

  useEffect(() => {
    if (!selectedPersonality || !greetingValue || greetingValue.trim().length === 0) {
      setTransformedGreeting(null);
      return;
    }

    if (isToneMatch(greetingValue, selectedPersonality)) {
      setTransformedGreeting(null);
      return;
    }

    if (
      prevGreetingRef.current === greetingValue &&
      prevPersonalityRef.current === selectedPersonality
    ) {
      return;
    }

    prevGreetingRef.current = greetingValue;
    prevPersonalityRef.current = selectedPersonality;

    let cancelled = false;

    const transformExistingGreeting = async () => {
      setTransformLoading(true);
      setTransformedGreeting(null);
      setSuggestionApplied(false);

      try {
        const response = await merchantConfigApi.transformGreeting({
          custom_greeting: greetingValue,
          target_personality: selectedPersonality,
          bot_name: botName,
          business_name: businessName,
        });

        if (!cancelled) {
          if (response.transformed_greeting && response.transformed_greeting !== greetingValue) {
            setTransformedGreeting(response.transformed_greeting);
          } else {
            setTransformedGreeting(null);
          }
        }
      } catch (error) {
        console.error('[GreetingTransform] Failed:', error);
        if (!cancelled) {
          setTransformedGreeting(null);
        }
      } finally {
        if (!cancelled) {
          setTransformLoading(false);
        }
      }
    };

    transformExistingGreeting();

    return () => {
      cancelled = true;
    };
  }, [selectedPersonality, greetingValue, botName, businessName]);

  const handlePersonalitySelect = (newPersonality: PersonalityType) => {
    setSelectedPersonality(newPersonality);
    setPersonality(newPersonality);
    setSaveStatus('idle');
    setLocalError(null);
    clearError();
    setSuggestionApplied(false);
  };

  const handleGreetingChange = (value: string) => {
    setGreetingValue(value);
    setCustomGreeting(value);
    setSaveStatus('idle');
    setLocalError(null);
    clearError();
    setDismissedWarning(false);
    setShowToneWarning(false);
    setSuggestionApplied(false);
  };

  const handleResetGreeting = () => {
    setGreetingValue('');
    resetToDefault();
    setSaveStatus('idle');
    setShowToneWarning(false);
    setDismissedWarning(false);
    setTransformedGreeting(null);
    setSuggestionApplied(false);
  };

  const getSuggestedGreeting = useCallback((): string => {
    if (!selectedPersonality) return '';

    if (transformedGreeting) {
      return transformedGreeting;
    }

    const template = PersonalityDefaultGreetings[selectedPersonality];

    return template
      .replace(/{bot_name}/g, botName || 'your shopping assistant')
      .replace(/{business_name}/g, businessName || 'our store')
      .replace(/{business_hours}/g, businessHours || '');
  }, [selectedPersonality, botName, businessName, businessHours, transformedGreeting]);

  const handleApplySuggestion = () => {
    const suggested = getSuggestedGreeting();
    setGreetingValue(suggested);
    setCustomGreeting(suggested);
    setShowToneWarning(false);
    setDismissedWarning(false);
    setSaveStatus('idle');
    setTransformedGreeting(null);
    prevGreetingRef.current = suggested;
    setSuggestionApplied(true);
  };

  const handleDismissWarning = () => {
    setShowToneWarning(false);
    setDismissedWarning(true);
  };

  const handleSaveAnyway = () => {
    setShowToneWarning(false);
    performSave();
  };

  const performSave = async () => {
    if (!selectedPersonality) {
      setLocalError('ARCHETYPE_NOT_SELECTED: Please select a neural profile.');
      return;
    }

    setSaveStatus('saving');
    setLocalError(null);
    clearError();

    try {
      await updatePersonalityConfig({
        personality: selectedPersonality,
        custom_greeting: greetingValue || null,
      });
      markBotConfigComplete('personality');
      setSaveStatus('success');
      setShowToneWarning(false);
      setDismissedWarning(false);

      setTimeout(() => {
        setSaveStatus('idle');
      }, 3000);
    } catch (err) {
      setSaveStatus('error');
      const errorMessage = err instanceof Error ? err.message : 'UPLINK_FAILURE: Protocol sync interrupted.';
      setLocalError(errorMessage);
    }
  };

  const handleSave = async () => {
    if (!selectedPersonality) {
      setLocalError('ARCHETYPE_NOT_SELECTED: Please select a neural profile.');
      return;
    }

    if (!dismissedWarning && hasToneMismatch(greetingValue, selectedPersonality)) {
      setShowToneWarning(true);
      return;
    }

    await performSave();
  };

  const getDefaultGreeting = (): string => {
    if (!selectedPersonality) return '';
    return PersonalityDefaultGreetings[selectedPersonality];
  };

  return (
    <div className="max-w-6xl mx-auto space-y-12 animate-in fade-in slide-in-from-bottom-8 duration-1000 pb-20 font-space-grotesk">
      {/* HUD Header */}
      <div className="relative group">
        <div className="flex flex-col gap-4 relative z-10">
          <div className="flex items-center gap-4">
            <div className="w-12 h-1 bg-emerald-500 rounded-full shadow-[0_0_15px_#10b981]" />
            <span className="text-[10px] font-black uppercase tracking-[0.4em] text-emerald-500/60">System Configuration</span>
          </div>
          <h1 className="text-5xl font-black text-white tracking-tighter mantis-glow-text leading-[1.1]">
            Behavioral Matrix
          </h1>
          <p className="text-white/50 font-medium leading-relaxed max-w-2xl text-lg">
            Calibrate neural archetypes and refine output sequences for optimal brand alignment and high-precision customer interaction.
          </p>
        </div>
        
        {/* Background Accents */}
        <div className="absolute -top-20 -left-20 w-64 h-64 bg-emerald-500/5 rounded-full blur-[100px] pointer-events-none" />
      </div>

      {/* Global Status Interface */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 relative z-20">
        {(error || localError) && (
          <div className="md:col-span-3 p-6 bg-red-500/5 border border-red-500/20 rounded-[32px] flex items-start gap-4 backdrop-blur-3xl animate-in shake duration-500" role="alert">
            <div className="p-3 bg-red-500/20 rounded-2xl text-red-400">
              <AlertCircle className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-xs font-black uppercase tracking-[0.2em] text-red-500">Neural Sync Error</h3>
              <p className="text-sm text-red-400/80 mt-1 font-medium italic">{error || localError}</p>
            </div>
          </div>
        )}

        {saveStatus === 'success' && (
          <div className="md:col-span-3 p-6 bg-emerald-500/5 border border-emerald-500/20 rounded-[32px] flex items-start gap-4 backdrop-blur-3xl animate-in slide-in-from-top-4 duration-500" role="status">
            <div className="p-3 bg-emerald-500/20 rounded-2xl text-emerald-400">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-xs font-black uppercase tracking-[0.2em] text-emerald-500">Parameters Synchronized</h3>
              <p className="text-sm text-emerald-400/80 mt-1 font-medium italic">
                Archetype calibration complete. Neural output sequences have been propogated to all active customer sessions.
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Primary Archetype Selection */}
      <section className="space-y-8">
        <div className="flex items-center justify-between border-b border-white/5 pb-6">
          <div className="flex items-center gap-4">
            <Binary className="text-white/20 w-5 h-5" />
            <h2 className="text-[11px] font-black uppercase tracking-[0.3em] text-white/40">Select Neural Archetype</h2>
          </div>
          {selectedPersonality && (
            <div className="px-4 py-1.5 bg-emerald-500/10 border border-emerald-500/20 rounded-full">
              <span className="text-[9px] font-black uppercase tracking-widest text-emerald-400">
                Active Protocol: {PersonalityDisplay[selectedPersonality]}
              </span>
            </div>
          )}
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {(Object.keys(PersonalityDisplay) as PersonalityType[]).map((type) => (
            <PersonalityCard
              key={type}
              personality={type}
              isSelected={selectedPersonality === type}
              onSelect={handlePersonalitySelect}
            />
          ))}
        </div>
      </section>

      {/* Logic Customization Interface */}
      {selectedPersonality && (
        <section className="space-y-8 animate-in fade-in slide-in-from-bottom-8 duration-700">
          <div className="flex items-center gap-4 border-b border-white/5 pb-6">
            <Activity className="text-white/20 w-5 h-5" />
            <h2 className="text-[11px] font-black uppercase tracking-[0.3em] text-white/40">Greeting Logic Modulation</h2>
          </div>

          <GreetingConfig
            personality={selectedPersonality}
            greetingTemplate={greetingValue || null}
            useCustomGreeting={!!greetingValue}
            defaultTemplate={getDefaultGreeting()}
            availableVariables={['bot_name', 'business_name', 'business_hours']}
            botName={botName}
            businessName={businessName}
            businessHours={businessHours}
            onUpdate={(data) => {
              if (data.greeting_template !== undefined) {
                handleGreetingChange(data.greeting_template);
              }
            }}
            onReset={handleResetGreeting}
            disabled={loading}
            showSuggestion={!suggestionApplied && !!transformedGreeting}
            suggestedGreeting={getSuggestedGreeting()}
            suggestionLoading={transformLoading}
            onApplySuggestion={handleApplySuggestion}
            toneMismatchWarning={showToneWarning ? getToneMismatchMessage(greetingValue) : null}
            onDismissWarning={handleDismissWarning}
            onSaveAnyway={handleSaveAnyway}
          />
        </section>
      )}

      {/* Global Controls Footer */}
      <div className="fixed bottom-0 left-0 right-0 p-8 bg-gradient-to-t from-black via-black/80 to-transparent z-50 pointer-events-none">
        <div className="max-w-6xl mx-auto flex items-center justify-between pointer-events-auto">
          <div className="flex items-center gap-6 glass-card px-8 py-4 rounded-full border-white/10">
            <div className="flex items-center gap-3">
              <div className={`w-2.5 h-2.5 rounded-full ${isDirty ? 'bg-amber-500 animate-pulse shadow-[0_0_10px_#f59e0b]' : 'bg-emerald-500 shadow-[0_0_10px_#10b981]'}`} />
              <span className="text-[10px] font-black uppercase tracking-[0.2em] text-white/50">
                {isDirty ? 'Awaiting Calibration' : 'Core Logic Synchronized'}
              </span>
            </div>
            <div className="w-px h-4 bg-white/10" />
            <div className="flex items-center gap-2">
              <Zap size={14} className="text-white/20" />
              <span className="text-[10px] font-black uppercase tracking-widest text-white/20">Version 2.4.0</span>
            </div>
          </div>
          
          <button
            type="button"
            onClick={handleSave}
            disabled={loading || !selectedPersonality || saveStatus === 'saving'}
            className="group relative inline-flex items-center gap-4 px-12 py-5 rounded-2xl font-black text-xs uppercase tracking-[0.3em] transition-all overflow-hidden disabled:opacity-50 disabled:cursor-not-allowed shadow-[0_0_30px_rgba(16,185,129,0.2)]"
          >
            {/* Action Background */}
            <div className={`absolute inset-0 bg-emerald-600 transition-all duration-500 group-hover:bg-emerald-500 group-disabled:bg-zinc-800`} />
            <div className="absolute inset-0 bg-gradient-to-tr from-white/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
            
            <span className="relative z-10 flex items-center gap-3 text-white">
              {saveStatus === 'saving' ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Calibrating...
                </>
              ) : (
                <>
                  <Save className="w-5 h-5 group-hover:rotate-12 transition-transform" />
                  Apply Matrix Configuration
                </>
              )}
            </span>
            
            {/* Terminal accent */}
            <div className="absolute right-0 bottom-0 p-1 opacity-20 group-hover:opacity-40 transition-opacity font-mono text-[8px] text-white">
              SNC_v2
            </div>
          </button>
        </div>
      </div>
    </div>
  );
};

export default PersonalityConfig;
