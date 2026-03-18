/**
 * Provider Configuration Modal Component.
 *
 * Story 3.4: LLM Provider Switching
 * Re-imagined with high-fidelity Mantis aesthetic for professional calibration.
 */

import React, { useEffect, useRef, useState, useCallback } from 'react';
import { X, Loader2, RefreshCw, Terminal, Cpu, Zap, Info, ShieldCheck } from 'lucide-react';
import { useLLMProviderStore } from '../../stores/llmProviderStore';
import { getProviderModels, refreshModelsCache, DiscoveredModel } from '../../services/llmProvider';
import { GlassCard } from '../ui/GlassCard';

export const ProviderConfigModal: React.FC = () => {
  const {
    selectedProvider,
    isSwitching,
    switchError,
    switchProvider,
    closeConfigModal,
    validationInProgress,
    currentProvider,
  } = useLLMProviderStore();

  const [apiKey, setApiKey] = React.useState('');
  const [serverUrl, setServerUrl] = React.useState('http://localhost:11434');
  const [selectedModel, setSelectedModel] = useState<string>('');
  const [models, setModels] = useState<DiscoveredModel[]>([]);
  const [loadingModels, setLoadingModels] = useState(false);
  const modalRef = useRef<HTMLDivElement>(null);
  const cancelButtonRef = useRef<HTMLButtonElement>(null);

  const loadModels = useCallback(async (providerId: string) => {
    setLoadingModels(true);
    try {
      const response = await getProviderModels(providerId);
      setModels(response.data.models);
      const downloadableModels = response.data.models.filter(m => !m.isLocal || m.isDownloaded);
      if (downloadableModels.length > 0) {
        setSelectedModel(downloadableModels[0].id);
      } else if (response.data.models.length > 0) {
        setSelectedModel(response.data.models[0].id);
      }
    } catch (err) {
      console.error('Failed to load models:', err);
    } finally {
      setLoadingModels(false);
    }
  }, []);

  const handleRefreshModels = async () => {
    if (!selectedProvider) return;
    setLoadingModels(true);
    try {
      await refreshModelsCache();
      await loadModels(selectedProvider.id);
    } catch (err) {
      console.error('Failed to refresh models:', err);
    } finally {
      setLoadingModels(false);
    }
  };

  useEffect(() => {
    if (selectedProvider) {
      loadModels(selectedProvider.id);
    }
  }, [selectedProvider, loadModels]);

  useEffect(() => {
    if (selectedProvider && modalRef.current) {
      const focusableElements = modalRef.current.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );
      const firstElement = focusableElements[0] as HTMLElement;
      if (firstElement) {
        firstElement.focus();
      }
    }
  }, [selectedProvider]);

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && selectedProvider) {
        closeConfigModal();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [selectedProvider, closeConfigModal]);

  if (!selectedProvider) return null;

  const isCloudProvider = ['openai', 'anthropic', 'gemini', 'glm'].includes(
    selectedProvider.id
  );
  const isOllama = selectedProvider.id === 'ollama';

  const isUpdating = currentProvider?.id === selectedProvider.id;

  const handleSwitch = async () => {
    try {
      const apiKeyToSend = isUpdating && !apiKey.trim() ? undefined : (isCloudProvider ? apiKey : undefined);
      
      await switchProvider({
        providerId: selectedProvider.id,
        apiKey: apiKeyToSend,
        serverUrl: isOllama ? serverUrl : undefined,
        model: selectedModel || undefined,
      });
      setApiKey('');
      setServerUrl('');
      setSelectedModel('');
    } catch (error) {
      console.error('Switch error:', error);
    }
  };

  const handleCancel = () => {
    setApiKey('');
    setServerUrl('');
    setSelectedModel('');
    closeConfigModal();
  };

  const isDisabled = isSwitching || validationInProgress;
  
  const canSubmit = selectedModel.length > 0 && (
    isOllama 
      ? serverUrl.length > 0
      : isUpdating 
        ? true 
        : apiKey.length > 0 
  );

  const downloadedModels = models.filter(m => m.isDownloaded);
  const libraryModels = models.filter(m => m.isLocal && !m.isDownloaded);
  const cloudModels = models.filter(m => !m.isLocal);

  return (
    <div
      data-testid="provider-config-modal"
      className="fixed inset-0 bg-black/80 backdrop-blur-3xl flex items-center justify-center z-[100] p-6 animate-in fade-in duration-500"
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
      onClick={(e) => {
        if (e.target === e.currentTarget) handleCancel();
      }}
    >
      <GlassCard
        ref={modalRef}
        accent="mantis"
        className="w-full max-w-xl p-0 overflow-hidden shadow-[0_50px_100px_rgba(0,0,0,0.8)] border-emerald-500/20"
      >
        {/* Header Terminal */}
        <div className="bg-[#0a0a0a] border-b border-white/[0.05] p-8 flex items-center justify-between">
          <div className="space-y-1">
            <div className="flex items-center gap-3">
              <Terminal size={18} className="text-emerald-500" />
              <h2 id="modal-title" className="text-xl font-black text-white uppercase tracking-tight">
                {isUpdating ? 'Recalibration Sequence' : 'Link Initialization'}
              </h2>
            </div>
            <p className="text-[10px] font-black text-emerald-900/40 uppercase tracking-[0.2em] ml-7">
              Target Node: <span className="text-emerald-500">{selectedProvider.name}</span>
            </p>
          </div>
          <button
            ref={cancelButtonRef}
            onClick={handleCancel}
            className="w-10 h-10 flex items-center justify-center bg-white/5 border border-white/10 text-white/40 hover:text-white rounded-xl transition-all"
            aria-label="Close modal"
            disabled={isDisabled}
          >
            <X size={20} />
          </button>
        </div>

        <div className="p-10 space-y-10 max-h-[70vh] overflow-y-auto custom-scrollbar">
          {/* Diagnostic Stats Overlay */}
          <div className="grid grid-cols-2 gap-4">
            <div className="p-5 bg-emerald-500/[0.03] border border-emerald-500/10 rounded-2xl space-y-2">
               <span className="text-[9px] font-black text-emerald-900/40 uppercase tracking-widest block font-mono">Input Factor</span>
               <span className="text-lg font-black text-white tracking-tighter">${selectedProvider.pricing.inputCost.toFixed(2)}</span>
            </div>
            <div className="p-5 bg-emerald-500/[0.03] border border-emerald-500/10 rounded-2xl space-y-2">
               <span className="text-[9px] font-black text-emerald-900/40 uppercase tracking-widest block font-mono">Output Factor</span>
               <span className="text-lg font-black text-white tracking-tighter">${selectedProvider.pricing.outputCost.toFixed(2)}</span>
            </div>
          </div>

          {/* Core Configuration Forms */}
          <div className="space-y-8">
            {isCloudProvider && (
              <div className="space-y-4">
                <label htmlFor="api-key" className="flex items-center gap-3 text-[10px] font-black text-emerald-400 uppercase tracking-[0.3em]">
                  <ShieldCheck size={14} />
                  Access Credential (API KEY)
                </label>
                <div className="relative group">
                  <input
                    id="api-key"
                    type="password"
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    placeholder={isUpdating ? "Enter new neural key to update" : "Enter calibration key..."}
                    className="w-full h-14 bg-white/5 border border-white/10 rounded-2xl px-6 text-white text-sm font-black focus:outline-none focus:border-emerald-500/50 focus:bg-emerald-500/[0.03] transition-all placeholder:text-emerald-900/20"
                    disabled={isDisabled}
                    autoComplete="off"
                  />
                  <div className="absolute right-6 top-1/2 -translate-y-1/2 text-emerald-900/20">
                     <Zap size={18} />
                  </div>
                </div>
                <p className="text-[9px] font-black text-emerald-900/20 uppercase tracking-widest leading-relaxed">
                  {isUpdating 
                    ? "Leave null to preserve current encryption layer."
                    : "Calibration key is end-to-end encrypted within the neural mesh."}
                </p>
              </div>
            )}

            {isOllama && (
              <div className="space-y-4">
                <label htmlFor="server-url" className="flex items-center gap-3 text-[10px] font-black text-emerald-400 uppercase tracking-[0.3em]">
                  <Cpu size={14} />
                  Node Server URI
                </label>
                <input
                  id="server-url"
                  type="url"
                  value={serverUrl}
                  onChange={(e) => setServerUrl(e.target.value)}
                  placeholder="http://localhost:11434"
                  className="w-full h-14 bg-white/5 border border-white/10 rounded-2xl px-6 text-white text-sm font-black focus:outline-none focus:border-emerald-500/50 focus:bg-emerald-500/[0.03] transition-all"
                  disabled={isDisabled}
                />
              </div>
            )}

            {/* Model Selection Array */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <label htmlFor="model" className="flex items-center gap-3 text-[10px] font-black text-emerald-400 uppercase tracking-[0.3em]">
                  <Info size={14} />
                  Neural Model Index
                </label>
                <button
                  type="button"
                  onClick={handleRefreshModels}
                  disabled={loadingModels || isDisabled}
                  className="flex items-center gap-2 text-[10px] font-black text-emerald-990/40 uppercase tracking-[0.2em] hover:text-emerald-500 transition-colors"
                >
                  <RefreshCw size={12} className={loadingModels ? 'animate-spin' : ''} />
                  Purge Cache
                </button>
              </div>
              
              <div className="relative group">
                <select
                  id="model"
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  className="w-full h-14 bg-white/5 border border-white/10 rounded-2xl px-6 pr-12 text-white text-sm font-black appearance-none focus:outline-none focus:border-emerald-500/50 focus:bg-emerald-500/[0.03] transition-all cursor-pointer"
                  disabled={isDisabled}
                >
                  {models.length === 0 && (
                    <option value="" className="bg-[#0a0a0a]">Searching Registry...</option>
                  )}
                  {downloadedModels.length > 0 && (
                    <optgroup label="NODE_LOCAL (READY)" className="bg-[#0a0a0a] text-emerald-500 font-black">
                      {downloadedModels.map((m) => (
                        <option key={m.id} value={m.id} className="text-white">
                          {m.name.toUpperCase()}
                        </option>
                      ))}
                    </optgroup>
                  )}
                  {libraryModels.length > 0 && (
                    <optgroup label="REMOTE_LIBRARY" className="bg-[#0a0a0a] text-amber-500 font-black">
                      {libraryModels.map((m) => (
                        <option key={m.id} value={m.id} className="text-white">
                          {m.name.toUpperCase()} (PULL)
                        </option>
                      ))}
                    </optgroup>
                  )}
                  {cloudModels.length > 0 && (
                    <optgroup label="CLOUD_MATRICES" className="bg-[#0a0a0a] text-blue-500 font-black">
                      {cloudModels.map((m) => (
                        <option key={m.id} value={m.id} className="text-white">
                          {m.name.toUpperCase()}
                        </option>
                      ))}
                    </optgroup>
                  )}
                </select>
                <div className="absolute right-6 top-1/2 -translate-y-1/2 pointer-events-none text-emerald-900/20">
                   <Cpu size={18} />
                </div>
              </div>

              {/* Model Detail Spectral Analysis */}
              {selectedModel && models.find(m => m.id === selectedModel) && (
                <div className="animate-in fade-in slide-in-from-top-2 duration-500 p-5 bg-white/[0.02] border border-white/[0.05] rounded-2xl space-y-4">
                  {(() => {
                    const m = models.find(model => model.id === selectedModel)!;
                    return (
                      <>
                        <div className="space-y-2">
                          <span className="text-[9px] font-black text-emerald-500/60 uppercase tracking-widest font-mono">Neural Metadata</span>
                          <p className="text-xs text-white/60 font-medium leading-relaxed uppercase tracking-tight">
                            {m.description || 'No additional telemetry data available for this node.'}
                          </p>
                        </div>
                        
                        <div className="flex flex-wrap gap-4 pt-2 border-t border-white/[0.03]">
                          <div className="flex flex-col">
                            <span className="text-[8px] font-black text-emerald-900/20 uppercase tracking-widest mb-1">Context Density</span>
                            <span className="text-[10px] font-black text-white uppercase tabular-nums">{(m.contextLength / 1024).toFixed(0)}K Tokens</span>
                          </div>
                          <div className="flex flex-col">
                            <span className="text-[8px] font-black text-emerald-900/20 uppercase tracking-widest mb-1">Neural Flow</span>
                            <span className="text-[10px] font-black text-emerald-400 uppercase tracking-tight">
                              ${m.pricing.inputCostPerMillion.toFixed(2)} / ${m.pricing.outputCostPerMillion.toFixed(2)}
                            </span>
                          </div>
                          <div className="flex flex-col">
                             <span className="text-[8px] font-black text-emerald-900/20 uppercase tracking-widest mb-1">Architecture</span>
                             <div className="flex gap-1">
                               {m.features.slice(0, 2).map(f => (
                                 <span key={f} className="text-[8px] font-black text-white/30 uppercase tracking-tighter border border-white/5 px-1 rounded bg-white/[0.02]">{f}</span>
                               ))}
                             </div>
                          </div>
                        </div>
                      </>
                    );
                  })()}
                </div>
              )}
            </div>
          </div>

          {/* Validation Status */}
          {switchError && (
            <div
              className="p-5 bg-red-500/5 border border-red-500/20 rounded-2xl flex items-start gap-4 animate-in slide-in-from-top-4"
              role="alert"
              aria-live="polite"
            >
              <X size={18} className="text-red-500 mt-0.5" />
              <div className="space-y-1">
                <p className="text-[10px] font-black text-red-500 uppercase tracking-widest">Neural Reject</p>
                <p className="text-xs text-red-500/60 font-black uppercase tracking-tight leading-relaxed">{switchError}</p>
              </div>
            </div>
          )}
        </div>

        {/* Global Controls */}
        <div className="p-10 bg-[#0a0a0a] border-t border-white/[0.05] flex gap-4">
          <button
            onClick={handleCancel}
            disabled={isDisabled}
            className="flex-1 h-14 bg-white/5 border border-white/10 text-white/40 font-black text-[10px] uppercase tracking-[0.3em] rounded-2xl hover:bg-white/10 hover:text-white transition-all duration-300"
          >
            Abort
          </button>
          <button
            onClick={handleSwitch}
            disabled={isDisabled || !canSubmit}
            className="flex-[2] h-14 bg-emerald-500 text-black font-black text-[10px] uppercase tracking-[0.3em] rounded-2xl shadow-[0_15px_40px_rgba(16,185,129,0.3)] hover:shadow-[0_20px_50px_rgba(16,185,129,0.4)] disabled:opacity-50 flex items-center justify-center gap-3 transition-all duration-300"
          >
            {(isSwitching || validationInProgress) && (
              <Loader2 size={18} className="animate-spin" aria-hidden="true" />
            )}
            {isSwitching
              ? (isUpdating ? 'Recalibrating...' : 'Initializing...')
              : validationInProgress
              ? 'Parsing Vectors...'
              : isUpdating
              ? 'Commit Configuration'
              : 'Initialize Master Link'}
          </button>
        </div>
      </GlassCard>
    </div>
  );
};
