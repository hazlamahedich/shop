import * as React from "react";
import { Bot, ShoppingCart, Check, Cpu, Zap, Sparkles } from "lucide-react";
import { GlassCard } from "../ui/GlassCard";
import { OnboardingMode } from "../../types/onboarding";

export interface ModeSelectionProps {
  selectedMode: OnboardingMode | null;
  onModeSelect: (mode: OnboardingMode) => void;
  onContinue: () => void;
  isLoading?: boolean;
  error?: string | null;
  onRetry?: () => void;
}

interface ModeCardData {
  mode: OnboardingMode;
  icon: React.ElementType;
  title: string;
  description: string;
  features: string[];
}

const MODES: ModeCardData[] = [
  {
    mode: "general",
    icon: Bot,
    title: "Neural Core",
    description: "Autonomous knowledge synthesis and multi-channel support.",
    features: ["Knowledge Base Q&A", "Customer Support", "Universal Embed"],
  },
  {
    mode: "ecommerce",
    icon: ShoppingCart,
    title: "Commerce Engine",
    description: "Full-stack shopping integration with real-time inventory.",
    features: ["Shopify Sync", "Messenger Cart", "Stock Intelligence"],
  },
];

const DEBOUNCE_MS = 150;

export function ModeSelection({
  selectedMode,
  onModeSelect,
  onContinue,
  isLoading = false,
  error = null,
  onRetry,
}: ModeSelectionProps): React.ReactElement {
  const debounceRef = React.useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleModeSelect = React.useCallback((mode: OnboardingMode) => {
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    debounceRef.current = setTimeout(() => {
      onModeSelect(mode);
    }, DEBOUNCE_MS);
  }, [onModeSelect]);

  React.useEffect(() => {
    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, []);

  const handleKeyDown = (e: React.KeyboardEvent, mode: OnboardingMode) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      handleModeSelect(mode);
    }
  };

  return (
    <div
      className="w-full max-w-4xl mx-auto space-y-12 animate-in fade-in slide-in-from-bottom-8 duration-1000"
      data-testid="mode-selection"
    >
      <div className="text-center space-y-4">
        <div className="inline-flex items-center gap-2 px-3 py-1 bg-emerald-500/5 border border-emerald-500/10 rounded-full text-[8px] font-black uppercase tracking-[0.4em] text-emerald-500/60 mb-2">
          Step 01: Core Selection
        </div>
        <h2 className="text-4xl font-black text-white tracking-tight leading-none uppercase">Select Operational Mode</h2>
        <p className="text-emerald-900/40 font-bold text-xs uppercase tracking-widest leading-loose max-w-lg mx-auto">
          Choose the architectural foundation for your agent. You can reconfigure neural routes at any time.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {MODES.map((modeData) => {
          const isSelected = selectedMode === modeData.mode;
          const Icon = modeData.icon;
          
          return (
            <div
              key={modeData.mode}
              role="button"
              tabIndex={0}
              aria-pressed={isSelected}
              onKeyDown={(e) => handleKeyDown(e, modeData.mode)}
              onClick={() => handleModeSelect(modeData.mode)}
              className="relative group outline-none"
              data-testid={`mode-card-${modeData.mode}`}
            >
              <GlassCard
                accent={isSelected ? "mantis" : undefined}
                className={`
                  p-10 transition-all duration-700 cursor-pointer h-full border-white/[0.03] hover:border-emerald-500/20
                  ${isSelected ? "bg-emerald-500/[0.03] -translate-y-2" : "bg-white/[0.01] hover:bg-emerald-500/[0.01]"}
                `}
              >
                <div className="flex flex-col items-center text-center space-y-8">
                  <div className={`
                    w-20 h-20 rounded-[24px] border flex items-center justify-center transition-all duration-700
                    ${isSelected 
                      ? "bg-emerald-500 text-black border-emerald-400 rotate-[10deg] shadow-[0_0_40px_rgba(16,185,129,0.3)]" 
                      : "bg-white/[0.03] text-emerald-900/20 border-white/[0.05] group-hover:text-emerald-500 group-hover:border-emerald-500/20 group-hover:rotate-[-5deg]"}
                  `}>
                    <Icon size={32} strokeWidth={isSelected ? 2.5 : 2} />
                  </div>

                  <div className="space-y-3">
                    <h3 className={`text-2xl font-black tracking-tight leading-none uppercase transition-colors duration-500 ${isSelected ? "text-white" : "text-white/40"}`}>
                      {modeData.title}
                    </h3>
                    <p className={`text-xs font-bold leading-relaxed transition-colors duration-500 ${isSelected ? "text-emerald-900/60" : "text-emerald-900/20"}`}>
                      {modeData.description}
                    </p>
                  </div>

                  <div className="w-full space-y-3 pt-4">
                    {modeData.features.map((feature, idx) => (
                      <div key={idx} className="flex items-center gap-3 px-4 py-2 bg-black/20 rounded-xl border border-white/[0.02]">
                        <Check className={`w-3.5 h-3.5 flex-shrink-0 transition-colors duration-500 ${isSelected ? "text-emerald-400" : "text-emerald-900/20"}`} />
                        <span className={`text-[10px] font-black uppercase tracking-widest transition-colors duration-500 ${isSelected ? "text-white/90" : "text-white/20"}`}>
                          {feature}
                        </span>
                      </div>
                    ))}
                  </div>

                  {isSelected && (
                    <div className="absolute top-6 right-6 flex items-center justify-center w-8 h-8 rounded-full bg-emerald-500 text-black shadow-[0_0_20px_rgba(16,185,129,0.4)]">
                      <Check size={16} strokeWidth={4} />
                    </div>
                  )}
                </div>
              </GlassCard>
            </div>
          );
        })}
      </div>

      <div className="flex flex-col items-center gap-6 pt-12">
        <button
          onClick={onContinue}
          disabled={selectedMode === null || isLoading}
          className={`
            h-16 px-24 rounded-2xl font-black text-[11px] uppercase tracking-[0.4em] transition-all duration-700 relative overflow-hidden group
            ${selectedMode !== null && !isLoading
              ? "bg-emerald-500 text-black shadow-[0_0_40px_rgba(16,185,129,0.2)] hover:bg-emerald-400 hover:shadow-[0_0_60px_rgba(16,185,129,0.4)] hover:-translate-y-1"
              : "bg-white/5 border border-white/10 text-white/20 cursor-not-allowed"}
          `}
        >
          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:animate-shimmer" />
          <span className="relative z-10 flex items-center gap-3">
            {isLoading ? (
              <>
                <Zap size={16} className="animate-spin" />
                Initializing...
              </>
            ) : (
              "Initialize Core"
            )}
          </span>
        </button>

        {error && (
          <div
            className="p-6 bg-red-500/[0.03] border border-red-500/10 rounded-[24px] animate-in fade-in slide-in-from-top-4 duration-500 flex items-center gap-6 max-w-xl"
            role="alert"
          >
            <div className="w-10 h-10 rounded-xl bg-red-500/10 flex items-center justify-center text-red-500 border border-red-500/20 flex-shrink-0">
              <Cpu size={20} className="animate-pulse" />
            </div>
            <div className="flex-1 space-y-1">
              <p className="text-[10px] font-black text-red-500 uppercase tracking-[0.2em]">Synchronization Failure</p>
              <p className="text-xs font-bold text-red-400/80 tracking-tight italic">{error}</p>
            </div>
            {onRetry && (
              <button
                onClick={onRetry}
                className="h-10 px-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-500 font-black text-[9px] uppercase tracking-[0.2em] hover:bg-red-500 hover:text-white transition-all duration-300"
              >
                Retry Uplink
              </button>
            )}
          </div>
        )}

        {selectedMode === null && !isLoading && (
          <div className="flex items-center gap-2 text-[9px] font-black text-emerald-900/30 uppercase tracking-[0.3em]">
            <Sparkles size={12} className="opacity-50" />
            Awaiting Command Input
          </div>
        )}
      </div>
    </div>
  );
}
