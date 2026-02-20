import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { Alert } from '@/components/ui/Alert';
import { Select } from '@/components/ui/Select';
import { useLLMStore } from '@/stores/llmStore';
import { LLMStatus } from '../onboarding/LLMStatus';
import { TestConnection } from '../onboarding/TestConnection';
import { getProviderModels, refreshModelsCache, DiscoveredModel } from '@/services/llmProvider';
import { Eye, EyeOff, Key, RefreshCw } from 'lucide-react';

export function LLMSettings() {
  const {
    configuration,
    isConfiguring,
    updateLLM,
    clearLLM,
    getLLMStatus,
    switchProvider,
  } = useLLMStore();

  const [updating, setUpdating] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');
  const [error, setError] = useState<string>();
  const [models, setModels] = useState<DiscoveredModel[]>([]);
  const [loadingModels, setLoadingModels] = useState(false);
  const [modelsCached, setModelsCached] = useState(false);
  const [apiKey, setApiKey] = useState('');
  const [showApiKey, setShowApiKey] = useState(false);

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

        {/* API Key Update (for cloud providers) */}
        {currentProvider !== 'ollama' && (
          <div>
            <Label className="flex items-center gap-2 mb-2">
              <Key className="w-4 h-4" />
              API Key
            </Label>
            <div className="flex gap-2">
              <div className="relative flex-1">
                <Input
                  type={showApiKey ? 'text' : 'password'}
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="Enter new API key to update"
                  className="pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowApiKey(!showApiKey)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                >
                  {showApiKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              <Button
                onClick={async () => {
                  if (!apiKey.trim()) {
                    setError('Please enter an API key');
                    return;
                  }
                  setError('');
                  setSuccessMsg('');
                  setUpdating(true);
                  try {
                    await switchProvider(currentProvider, apiKey.trim(), currentModel);
                    setApiKey('');
                    setSuccessMsg('API key updated successfully');
                    setTimeout(() => setSuccessMsg(''), 3000);
                  } catch (err) {
                    setError((err as Error).message);
                  } finally {
                    setUpdating(false);
                  }
                }}
                disabled={updating || !apiKey.trim()}
              >
                {updating ? 'Updating...' : 'Update Key'}
              </Button>
            </div>
            <p className="text-xs text-slate-500 mt-1">
              Your API key is encrypted and stored securely. Enter a new key above to update it.
            </p>
          </div>
        )}

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
              <RefreshCw className={`w-3 h-3 mr-1 ${loadingModels ? 'animate-spin' : ''}`} />
              {loadingModels ? 'Refreshing...' : 'Refresh Models'}
            </Button>
          </div>
          {modelsCached && (
            <p className="text-xs text-slate-400 mb-2">Models cached (24h TTL)</p>
          )}
          <Select
            label=""
            value={currentModel}
            onChange={(e) => handleModelChange(e.target.value)}
            disabled={updating || loadingModels}
            options={[
              ...(models.length === 0 && !loadingModels
                ? [{ value: '_none', label: 'No models available', disabled: true }]
                : []),
              ...models.map((model) => ({
                value: model.id,
                label: `${model.name}${model.pricing.inputCostPerMillion === 0 ? ' (Free)' : model.pricing.inputCostPerMillion > 0 ? ` ($${model.pricing.inputCostPerMillion.toFixed(2)}/1M)` : ''}`,
              })),
            ]}
          />
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
