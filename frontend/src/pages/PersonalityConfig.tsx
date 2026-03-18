/**
 * Personality Configuration Page
 *
 * Story 1.10: Bot Personality Configuration
 *
 * Allows merchants to:
 * - Select their bot's personality from predefined options
 * - Customize the bot's greeting message
 * - Save and persist their configuration
 */

import React, { useEffect, useState, useCallback, useRef } from 'react';
import { Save, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { Badge } from '../components/ui/Badge';
import { usePersonalityStore, selectPersonality, selectCustomGreeting, selectPersonalityLoading, selectPersonalityError, selectPersonalityIsDirty } from '../stores/personalityStore';
import { useOnboardingPhaseStore } from '../stores/onboardingPhaseStore';
import { useBotConfigStore } from '../stores/botConfigStore';
import { useBusinessInfoStore } from '../stores/businessInfoStore';
import { PersonalityCard } from '../components/personality/PersonalityCard';
import { GreetingConfig } from '../components/business-info/GreetingConfig';
import type { PersonalityType } from '../types/enums';
import { PersonalityDisplay, PersonalityDefaultGreetings } from '../types/enums';
import { hasToneMismatch, getToneMismatchMessage, isToneMatch } from '../utils/toneDetection';
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
        setLocalError('Failed to load personality configuration');
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
      setLocalError('Please select a personality');
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
      const errorMessage = err instanceof Error ? err.message : 'Failed to save configuration';
      setLocalError(errorMessage);
    }
  };

  const handleSave = async () => {
    if (!selectedPersonality) {
      setLocalError('Please select a personality');
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
    <div className="max-w-5xl mx-auto space-y-10 animate-in fade-in slide-in-from-bottom-4 duration-1000">
      {/* Page Header */}
      <div className="flex flex-col gap-2 border-b border-white/5 pb-8">
        <h1 className="text-4xl font-black text-white tracking-tight mantis-glow-text leading-tight">Bot Personality</h1>
        <p className="text-white/60 font-medium leading-relaxed max-w-2xl">
          Define your brand voice with precision. Choose a personality archetype and fine-tune your bot&apos;s initial greeting for a premium customer experience.
        </p>
      </div>

      {/* Status Messages */}
      <div className="space-y-4 relative z-20">
        {(error || localError) && (
          <div className="p-5 bg-red-500/5 border border-red-500/10 rounded-[24px] flex items-start gap-4 backdrop-blur-xl animate-in shake duration-500" role="alert">
            <div className="p-2 bg-red-500/20 rounded-xl text-red-400">
              <AlertCircle className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-black uppercase tracking-widest text-red-400">Configuration Error</h3>
              <p className="text-sm text-red-400/80 mt-1 font-medium italic">{error || localError}</p>
            </div>
          </div>
        )}

        {saveStatus === 'success' && (
          <div className="p-5 bg-emerald-500/5 border border-emerald-500/10 rounded-[24px] flex items-start gap-4 backdrop-blur-xl animate-in slide-in-from-top-4 duration-500" role="status" aria-live="polite">
            <div className="p-2 bg-emerald-500/20 rounded-xl text-emerald-400">
              <CheckCircle className="w-5 h-5 flex-shrink-0" />
            </div>
            <div>
              <h3 className="text-sm font-black uppercase tracking-widest text-emerald-400">Profile Updated</h3>
              <p className="text-sm text-emerald-400/80 mt-1 font-medium italic">
                Personality metrics calibrated. Your bot is now utilizing the updated brand voice for all active sessions.
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Personality Selection */}
      <section className="space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-[10px] font-black uppercase tracking-[0.3em] text-white/30 border-l-2 border-emerald-500 pl-4 py-1">Archetype Selection</h2>
          {selectedPersonality && (
            <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/30 font-black uppercase tracking-tighter shadow-lg">
              Active: {PersonalityDisplay[selectedPersonality]}
            </Badge>
          )}
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
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

      {/* Greeting Customization */}
      {selectedPersonality && (
        <section className="space-y-6 pt-10 border-t border-white/5 relative group">
          <div className="absolute top-0 right-0 w-64 h-64 bg-emerald-500/5 rounded-full -mr-32 -mt-32 blur-[100px] transition-all duration-700 group-hover:bg-emerald-500/10" />
          
          <div className="flex items-center justify-between relative z-10">
            <h2 className="text-[10px] font-black uppercase tracking-[0.3em] text-white/30 border-l-2 border-emerald-500 pl-4 py-1">Greeting Logic</h2>
          </div>

          <div className="glass-card p-1 border-none shadow-2xl relative z-10 overflow-hidden rounded-[32px]">
            <div className="p-8">
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
            </div>
          </div>
        </section>
      )}

      {/* Footer Controls */}
      <div className="flex items-center justify-between pt-10 border-t border-white/5 pb-20">
        <div className="flex items-center gap-3">
          <div className={`w-2 h-2 rounded-full ${isDirty ? 'bg-amber-500 animate-pulse' : 'bg-emerald-500'} shadow-[0_0_10px_currentColor]`} />
          <p className="text-[10px] font-black uppercase tracking-[0.2em] text-white/30 italic">
            {isDirty ? 'Awaiting Calibration' : 'Core Logic Synchronized'}
          </p>
        </div>
        
        <button
          type="button"
          onClick={handleSave}
          disabled={loading || !selectedPersonality || saveStatus === 'saving'}
          className="group relative inline-flex items-center gap-3 px-10 py-4 rounded-2xl font-black text-[10px] uppercase tracking-[0.3em] text-white transition-all overflow-hidden disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {/* Button Background */}
          <div className={`absolute inset-0 bg-emerald-600 transition-all duration-500 group-hover:bg-emerald-500 group-disabled:bg-zinc-800`} />
          <div className="absolute inset-x-0 bottom-0 h-1 bg-white/20 shadow-[0_0_20px_rgba(255,255,255,0.3)] opacity-0 group-hover:opacity-100 transition-opacity" />
          
          <span className="relative z-10 flex items-center gap-3">
            {saveStatus === 'saving' ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Optimizing...
              </>
            ) : (
              <>
                <Save className="w-4 h-4 group-hover:scale-110 transition-transform" />
                Apply Configuration
              </>
            )}
          </span>
        </button>
      </div>
    </div>
  );
};

export default PersonalityConfig;
