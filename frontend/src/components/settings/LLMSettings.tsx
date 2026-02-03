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

const PROVIDER_MODELS = {
  ollama: [
    { value: 'llama3', label: 'Llama 3 (Recommended)' },
    { value: 'mistral', label: 'Mistral 7B' },
    { value: 'codellama', label: 'Code Llama' },
    { value: 'qwen2', label: 'Qwen 2' },
  ],
  openai: [
    { value: 'gpt-4o-mini', label: 'GPT-4o Mini (Recommended)' },
    { value: 'gpt-4o', label: 'GPT-4O' },
    { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' },
  ],
  anthropic: [
    { value: 'claude-3-haiku', label: 'Claude 3 Haiku (Recommended)' },
    { value: 'claude-3-sonnet', label: 'Claude 3 Sonnet' },
  ],
  gemini: [
    { value: 'gemini-1.5-flash', label: 'Gemini 1.5 Flash (Recommended)' },
    { value: 'gemini-pro', label: 'Gemini Pro' },
  ],
  glm: [
    { value: 'glm-4-flash', label: 'GLM-4 Flash (Recommended)' },
    { value: 'glm-4-plus', label: 'GLM-4 Plus' },
  ],
};

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

  const currentProvider = configuration.provider || 'ollama';
  const currentModels = PROVIDER_MODELS[currentProvider as keyof typeof PROVIDER_MODELS] || [];
  const currentModel = configuration.ollamaModel || configuration.cloudModel || '';

  useEffect(() => {
    getLLMStatus();
  }, [getLLMStatus]);

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
          <Label>Model</Label>
          <Select value={currentModel} onValueChange={handleModelChange} disabled={updating}>
            <SelectTrigger disabled={updating}>
              <SelectValue placeholder="Select model" />
            </SelectTrigger>
            <SelectContent>
              {currentModels.map((model) => (
                <SelectItem key={model.value} value={model.value}>
                  {model.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
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
