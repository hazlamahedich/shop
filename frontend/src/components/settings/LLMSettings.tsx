import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/Label';
import { Alert } from '@/components/ui/Alert';
import { Badge } from '@/components/ui/Badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/Select';
import { useLLMStore } from '@/stores/llmStore';
import { LLMStatus } from '../onboarding/LLMStatus';
import { TestConnection } from '../onboarding/TestConnection';
import { getProviderModels, refreshModelsCache, DiscoveredModel } from '@/services/llmProvider';

export function LLMSettings() {
  const {
    configuration,
    isConfiguring,
    updateLLM,
    clearLLM,
    getLLMStatus,
  } = useLLMStore();

  const [updating, setUpdating] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');
  const [error, setError] = useState<string>();
  const [models, setModels] = useState<DiscoveredModel[]>([]);
  const [loadingModels, setLoadingModels] = useState(false);
  const [modelsCached, setModelsCached] = useState(false);

  const currentProvider = configuration.provider || 'ollama';
  const currentModel = configuration.ollamaModel || configuration.cloudModel || '';

  useEffect(() => {
    getLLMStatus();
  }, [getLLMStatus]);

  useEffect(() => {
    async function fetchModels() {
      if (!currentProvider) return;
      setLoadingModels(true);
      try {
        const response = await getProviderModels(currentProvider);
        setModels(response.data.models);
        setModelsCached(response.data.cached);
      } catch (err) {
        console.error('Failed to fetch models:', err);
        setModels([]);
      } finally {
        setLoadingModels(false);
      }
    }
    fetchModels();
  }, [currentProvider]);

  const handleRefreshModels = async () => {
    setLoadingModels(true);
    try {
      await refreshModelsCache();
      const response = await getProviderModels(currentProvider);
      setModels(response.data.models);
      setModelsCached(response.data.cached);
      setSuccessMsg('Models refreshed successfully');
      setTimeout(() => setSuccessMsg(''), 3000);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoadingModels(false);
    }
  };

  const handleModelChange = async (newModel: string) => {
    setError('');
    setSuccessMsg('');
    setUpdating(true);

    try {
      if (currentProvider === 'ollama') {
        await updateLLM({ ollama_model: newModel });
      } else {
        await updateLLM({ model: newModel });
      }
      setSuccessMsg('Model updated successfully');
      setTimeout(() => setSuccessMsg(''), 3000);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setUpdating(false);
    }
  };

  const handleClear = async () => {
    if (!confirm('Are you sure you want to clear the LLM configuration?')) {
      return;
    }

    try {
      await clearLLM();
      setSuccessMsg('Configuration cleared');
    } catch (err) {
      setError((err as Error).message);
    }
  };

  if (!configuration.provider) {
    return (
    <Card>
      <CardContent className="p-6">
        <p className="text-center text-slate-500">
          No LLM provider configured. Please complete the onboarding process first.
        </p>
      </CardContent>
    </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>LLM Provider Settings</CardTitle>
        <CardDescription>
          Manage your LLM provider configuration and switch providers anytime.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {error && (
          <Alert variant="destructive">
            {error}
          </Alert>
        )}

        {successMsg && (
          <Alert className="bg-green-50 text-green-800 border-green-200">
            {successMsg}
          </Alert>
        )}

        {/* Current Status */}
        <LLMStatus configuration={configuration} />

        {/* Model Selection */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <Label>Model</Label>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleRefreshModels}
              disabled={loadingModels}
              className="text-xs text-slate-500 hover:text-slate-700"
            >
              {loadingModels ? 'Refreshing...' : 'Refresh Models'}
            </Button>
          </div>
          {modelsCached && (
            <p className="text-xs text-slate-400 mb-2">Models cached (24h TTL)</p>
          )}
          <Select value={currentModel} onValueChange={handleModelChange} disabled={updating || loadingModels}>
            <SelectTrigger disabled={updating || loadingModels}>
              <SelectValue placeholder={loadingModels ? "Loading models..." : "Select model"} />
            </SelectTrigger>
            <SelectContent>
              {models.length === 0 && !loadingModels && (
                <SelectItem value="_none" disabled>No models available</SelectItem>
              )}
              {models.filter(m => m.isDownloaded).length > 0 && (
                <div className="px-2 py-1.5 text-xs font-semibold text-slate-500">Downloaded</div>
              )}
              {models.filter(m => m.isDownloaded).map((model) => (
                <SelectItem key={model.id} value={model.id}>
                  <div className="flex items-center gap-2">
                    <span>{model.name}</span>
                    {model.pricing.inputCostPerMillion === 0 && (
                      <Badge variant="secondary" className="text-xs">Free</Badge>
                    )}
                  </div>
                </SelectItem>
              ))}
              {models.filter(m => m.isLocal && !m.isDownloaded).length > 0 && (
                <div className="px-2 py-1.5 text-xs font-semibold text-slate-500 mt-2">Available to Pull</div>
              )}
              {models.filter(m => m.isLocal && !m.isDownloaded).map((model) => (
                <SelectItem key={model.id} value={model.id}>
                  <div className="flex items-center gap-2">
                    <span>{model.name}</span>
                    <Badge variant="outline" className="text-xs">Pull required</Badge>
                  </div>
                </SelectItem>
              ))}
              {models.filter(m => !m.isLocal).length > 0 && (
                <div className="px-2 py-1.5 text-xs font-semibold text-slate-500 mt-2">Cloud Models</div>
              )}
              {models.filter(m => !m.isLocal).map((model) => (
                <SelectItem key={model.id} value={model.id}>
                  <div className="flex items-center gap-2">
                    <span>{model.name}</span>
                    {model.pricing.inputCostPerMillion > 0 && (
                      <span className="text-xs text-slate-400">
                        ${model.pricing.inputCostPerMillion.toFixed(2)}/1M in
                      </span>
                    )}
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {models.find(m => m.id === currentModel)?.description && (
            <p className="text-xs text-slate-500 mt-1">
              {models.find(m => m.id === currentModel)?.description}
            </p>
          )}
        </div>

        {/* Test Connection */}
        <div>
          <h3 className="text-sm font-medium text-slate-900 mb-3">Test Connection</h3>
          <TestConnection
            onTest={async (prompt) => {
              const { testLLM, getLLMStatus } = useLLMStore.getState();
              await testLLM(prompt);
              await getLLMStatus();
            }}
          />
        </div>

        {/* Clear Configuration */}
        <div className="pt-4 border-t">
          <Button
            onClick={handleClear}
            variant="outline"
            className="text-red-600 hover:text-red-700"
          >
            Clear LLM Configuration
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
