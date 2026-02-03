import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/Label';
import { Alert } from '@/components/ui/Alert';

interface CloudConfigProps {
  onConfigure: (config: { provider: string; api_key: string; model: string }) => Promise<void>;
  isConfiguring?: boolean;
}

const PROVIDERS = [
  { id: 'openai', name: 'OpenAI', models: ['gpt-4o-mini', 'gpt-4o', 'gpt-3.5-turbo'] },
  { id: 'anthropic', name: 'Anthropic', models: ['claude-3-haiku', 'claude-3-sonnet'] },
  { id: 'gemini', name: 'Google Gemini', models: ['gemini-1.5-flash', 'gemini-pro'] },
  { id: 'glm', name: 'GLM-4.7 (Zhipu AI)', models: ['glm-4-flash', 'glm-4-plus'] },
];

const PRICING: Record<string, { input: number; output: number; currency: string }> = {
  openai: { input: 0.15, output: 0.60, currency: 'USD' },
  anthropic: { input: 0.25, output: 1.25, currency: 'USD' },
  gemini: { input: 0.075, output: 0.30, currency: 'USD' },
  glm: { input: 0.10, output: 0.10, currency: 'CNY' },
};

export function CloudConfig({ onConfigure, isConfiguring = false }: CloudConfigProps) {
  const [provider, setProvider] = useState('openai');
  const [apiKey, setApiKey] = useState('');
  const [model, setModel] = useState('gpt-4o-mini');
  const [error, setError] = useState<string>();

  const selectedProvider = PROVIDERS.find((p) => p.id === provider);
  const selectedModels = selectedProvider?.models || [];
  const pricing = PRICING[provider];

  const handleConfigure = async () => {
    setError('');

    if (!apiKey.trim()) {
      setError('API key is required');
      return;
    }

    try {
      await onConfigure({ provider, api_key: apiKey, model });
    } catch (err) {
      setError((err as Error).message);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Cloud LLM Configuration</CardTitle>
        <CardDescription>
          Configure a cloud provider for LLM processing.
          Requires API key and incurs per-token costs.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && (
          <Alert variant="destructive">
            {error}
          </Alert>
        )}

        <div>
          <Label htmlFor="provider">Provider</Label>
          <select
            id="provider"
            value={provider}
            onChange={(e) => {
              setProvider(e.target.value);
              const newProvider = PROVIDERS.find((p) => p.id === e.target.value);
              if (newProvider) {
                setModel(newProvider.models[0]);
              }
            }}
            disabled={isConfiguring}
            className="flex h-9 w-full rounded-md border border-slate-300 bg-white px-3 py-1 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-600"
          >
            {PROVIDERS.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        </div>

        <div>
          <Label htmlFor="api-key">API Key</Label>
          <Input
            id="api-key"
            type="password"
            placeholder="sk-..."
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            disabled={isConfiguring}
          />
          <p className="text-xs text-slate-500 mt-1">
            Your API key is encrypted and stored securely
          </p>
        </div>

        <div>
          <Label htmlFor="model">Model</Label>
          <select
            id="model"
            value={model}
            onChange={(e) => setModel(e.target.value)}
            disabled={isConfiguring}
            className="flex h-9 w-full rounded-md border border-slate-300 bg-white px-3 py-1 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-600"
          >
            {selectedModels.map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center p-4 bg-slate-50 rounded-md">
          <div className="flex-1">
            <p className="text-sm font-medium text-slate-900">Estimated Cost</p>
            <p className="text-xs text-slate-500">
              Input: {pricing?.input} / Output: {pricing?.output} {pricing?.currency} per 1M tokens
            </p>
          </div>
        </div>

        <Button
          onClick={handleConfigure}
          disabled={isConfiguring}
          className="w-full"
        >
          {isConfiguring ? 'Configuring...' : `Configure ${selectedProvider?.name}`}
        </Button>
      </CardContent>
    </Card>
  );
}
