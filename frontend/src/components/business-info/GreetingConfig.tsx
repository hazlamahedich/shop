import React from 'react';
import { Info, RotateCcw, AlertTriangle, Loader2, Terminal, Cpu } from 'lucide-react';

interface GreetingConfigProps {
  personality: string | null;
  greetingTemplate: string | null;
  useCustomGreeting: boolean;
  defaultTemplate: string | null;
  availableVariables: string[];
  onUpdate: (data: {
    greeting_template?: string;
    use_custom_greeting?: boolean;
  }) => void;
  onReset: () => void;
  disabled?: boolean;
  botName?: string | null;
  businessName?: string | null;
  businessHours?: string | null;
  showSuggestion?: boolean;
  suggestedGreeting?: string;
  suggestionLoading?: boolean;
  onApplySuggestion?: () => void;
  toneMismatchWarning?: string | null;
  onDismissWarning?: () => void;
  onSaveAnyway?: () => void;
}

const VariableBadges: React.FC<{ variables: string[] }> = ({ variables }) => {
  if (variables.length === 0) return null;

  return (
    <div className="flex flex-wrap gap-2 mt-3">
      {variables.map((v) => (
        <span
          key={v}
          className="inline-flex items-center px-2.5 py-1 bg-white/5 border border-white/10 text-[10px] font-black uppercase tracking-widest text-emerald-400 rounded-lg shadow-sm backdrop-blur-md"
          dangerouslySetInnerHTML={{ __html: '{' + v + '}' }}
        />
      ))}
    </div>
  );
};

const GreetingPreview: React.FC<{ message: string; personality: string | null }> = ({ message, personality }) => {
  const getGlowColor = (p: string | null) => {
    switch (p) {
      case 'professional': return 'shadow-[0_0_20px_rgba(99,102,241,0.2)] text-indigo-500';
      case 'enthusiastic': return 'shadow-[0_0_20px_rgba(168,85,247,0.2)] text-purple-500';
      default: return 'shadow-[0_0_20px_rgba(16,185,129,0.2)] text-emerald-500';
    }
  };

  const glowClass = getGlowColor(personality);

  return (
    <div className={`mt-8 p-6 bg-black/40 border border-white/5 rounded-[24px] backdrop-blur-2xl relative overflow-hidden group ${glowClass}`}>
      <div className="absolute top-0 right-0 p-4 opacity-20 group-hover:opacity-40 transition-opacity">
        <Cpu size={32} />
      </div>
      
      <div className="flex items-center gap-2 mb-4">
        <div className={`w-1.5 h-1.5 rounded-full animate-pulse ${personality === 'professional' ? 'bg-indigo-500' : personality === 'enthusiastic' ? 'bg-purple-500' : 'bg-emerald-500'}`} />
        <span className="text-[10px] font-black uppercase tracking-[0.2em] text-white/30">Neural Output Preview</span>
      </div>
      
      <div className="relative">
        <p className="text-sm text-white/90 leading-relaxed font-medium italic pl-4 border-l-2 border-white/10">
          &quot;{message || 'Awaiting input for intelligence synthesis...'}&quot;
        </p>
      </div>
    </div>
  );
};

export const GreetingConfig: React.FC<GreetingConfigProps> = ({
  personality,
  greetingTemplate,
  useCustomGreeting,
  defaultTemplate,
  availableVariables,
  onUpdate,
  onReset,
  disabled = false,
  botName,
  businessName,
  businessHours,
  showSuggestion = false,
  suggestedGreeting,
  suggestionLoading = false,
  onApplySuggestion,
  toneMismatchWarning,
  onDismissWarning,
  onSaveAnyway,
}) => {
  const [customText, setCustomText] = React.useState(greetingTemplate || '');
  const [useCustom, setUseCustom] = React.useState(useCustomGreeting);

  const buildPreviewMessage = (): string => {
    let message: string;

    if (useCustom && customText.trim().length > 0) {
      message = customText;
    } else if (defaultTemplate) {
      message = defaultTemplate;
    } else {
      message = "Protocol active. Awaiting merchant identity for greeting initialization.";
    }

    return message
      .replace(/{bot_name}/g, botName || '[BOT_ID]')
      .replace(/{business_name}/g, businessName || '[CORE_ENTITY]')
      .replace(/{business_hours}/g, businessHours || '[TEMPORAL_WINDOW]');
  };

  const previewMessage = buildPreviewMessage();

  const handleTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value;
    setCustomText(value);

    if (value.trim().length > 0 && !useCustom) {
      setUseCustom(true);
    }

    onUpdate({
      greeting_template: value || undefined,
      use_custom_greeting: useCustom || value.trim().length > 0 ? true : false,
    });
  };

  const handleToggleChange = (checked: boolean) => {
    setUseCustom(checked);
    onUpdate({
      greeting_template: customText || undefined,
      use_custom_greeting: checked,
    });
  };

  const handleReset = () => {
    setCustomText('');
    setUseCustom(false);
    onReset();
  };

  return (
    <div className="space-y-8 font-space-grotesk">
      {/* Configuration Hub */}
      <div className="relative p-8 bg-white/[0.02] border border-white/5 rounded-[32px] backdrop-blur-3xl overflow-hidden group">
        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-emerald-500/50 to-transparent opacity-30" />
        
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-8 relative z-10">
          <div>
            <h3 className="text-xl font-black text-white tracking-tight flex items-center gap-3">
              <Terminal size={20} className="text-emerald-400" />
              Greeting Logic
            </h3>
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-white/30 mt-1">
              Command Sequence Override
            </p>
          </div>

          <div className="flex items-center gap-4">
            <label className="flex items-center gap-3 cursor-pointer group/toggle">
              <div className="relative">
                <input
                  type="checkbox"
                  checked={useCustom}
                  onChange={(e) => handleToggleChange(e.target.checked)}
                  disabled={disabled}
                  className="sr-only"
                />
                <div className={`w-10 h-6 rounded-full transition-all duration-300 ${useCustom ? 'bg-emerald-600' : 'bg-white/10'}`} />
                <div className={`absolute top-1 left-1 w-4 h-4 bg-white rounded-full transition-transform duration-300 ${useCustom ? 'translate-x-4' : ''}`} />
              </div>
              <span className="text-[10px] font-black uppercase tracking-widest text-white/60 group-hover/toggle:text-white transition-colors">
                Manual Protocol
              </span>
            </label>

            <button
              type="button"
              onClick={handleReset}
              disabled={disabled}
              className="flex items-center gap-2 px-4 py-2 text-[9px] font-black uppercase tracking-[0.2em] text-white/50 bg-white/5 border border-white/5 rounded-xl hover:bg-white/10 hover:text-white transition-all disabled:opacity-20"
            >
              <RotateCcw size={12} />
              Reset Core
            </button>
          </div>
        </div>

        {/* Neural Input Interface */}
        <div className="relative z-10">
          <div className="relative group/input">
            <textarea
              id="custom-greeting"
              value={customText}
              onChange={handleTextChange}
              disabled={disabled}
              rows={5}
              maxLength={500}
              placeholder={`Synthesize your custom greeting protocol...`}
              className="w-full px-6 py-5 bg-black/40 border-2 border-white/5 rounded-2xl text-sm text-white placeholder:text-white/20 focus:border-emerald-500/50 focus:ring-0 transition-all duration-500 font-medium resize-none"
            />
            <div className="absolute top-4 right-4 text-[10px] font-black text-white/20 font-mono tracking-tighter">
              {customText.length}/500
            </div>
          </div>

          <div className="mt-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="space-y-1">
              <p className="text-[9px] font-black uppercase tracking-[0.2em] text-white/20">Available Tokens</p>
              <VariableBadges variables={availableVariables} />
            </div>
            
            <div className="flex items-center gap-2 text-[9px] font-black uppercase tracking-[0.2em] text-white/20">
              <Info size={12} className="text-emerald-500/50" />
              Tokens auto-hydrate on execution
            </div>
          </div>
        </div>

        {/* AI Suggestion Pulse */}
        {showSuggestion && (
          <div className="mt-8 p-6 bg-emerald-500/5 border border-emerald-500/10 rounded-2xl animate-in slide-in-from-bottom-4 duration-500">
            <div className="flex items-start justify-between gap-6">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-3">
                  <Cpu size={14} className="text-emerald-400 animate-pulse" />
                  <p className="text-[10px] font-black uppercase tracking-[0.2em] text-emerald-400/80">
                    AI Intent Alignment Suggestion
                  </p>
                </div>
                {suggestionLoading ? (
                  <div className="flex items-center gap-3 text-xs text-emerald-400/60 font-medium">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Neural mapping in progress...
                  </div>
                ) : suggestedGreeting ? (
                  <p className="text-sm text-white/90 italic font-medium">
                    &quot;{suggestedGreeting}&quot;
                  </p>
                ) : null}
              </div>
              {onApplySuggestion && suggestedGreeting && !suggestionLoading && (
                <button
                  type="button"
                  onClick={onApplySuggestion}
                  disabled={disabled}
                  className="px-6 py-2.5 text-[10px] font-black uppercase tracking-[0.2em] text-white bg-emerald-500/20 border border-emerald-500/30 rounded-xl hover:bg-emerald-500/30 transition-all shadow-[0_0_15px_rgba(16,185,129,0.1)]"
                >
                  Sync Logic
                </button>
              )}
            </div>
          </div>
        )}

        {/* Hazard Warning UI */}
        {toneMismatchWarning && (
          <div className="mt-6 p-6 bg-amber-500/5 border border-amber-500/10 rounded-2xl animate-in shake duration-500">
            <div className="flex items-start gap-4">
              <AlertTriangle className="w-5 h-5 text-amber-500 flex-shrink-0" />
              <div className="flex-1">
                <p className="text-[11px] font-black uppercase tracking-[0.1em] text-amber-500 mb-2">Tone Parity Alert</p>
                <p className="text-sm text-white/80 font-medium">{toneMismatchWarning}</p>
                <div className="flex gap-4 mt-4">
                  {onSaveAnyway && (
                    <button
                      type="button"
                      onClick={onSaveAnyway}
                      disabled={disabled}
                      className="px-6 py-2 text-[9px] font-black uppercase tracking-[0.2em] text-white bg-amber-500/20 border border-amber-500/30 rounded-xl hover:bg-amber-500/30 transition-all"
                    >
                      Bypass & Save
                    </button>
                  )}
                  {onDismissWarning && (
                    <button
                      type="button"
                      onClick={onDismissWarning}
                      disabled={disabled}
                      className="px-4 py-2 text-[9px] font-black uppercase tracking-[0.2em] text-white/40 hover:text-white transition-colors"
                    >
                      Recalibrate
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Output Simulation */}
      <GreetingPreview message={previewMessage} personality={personality} />
    </div>
  );
};

export default GreetingConfig;
