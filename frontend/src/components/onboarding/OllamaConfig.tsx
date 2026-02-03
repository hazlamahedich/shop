import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/Label';
import { Alert } from '@/components/ui/Alert';

interface OllamaConfigProps {
  onConfigure: (config: { ollama_url: string; ollama_model: string }) => Promise<void>;
  isConfiguring?: boolean;
}

const OLLAMA_DEFAULT_URL = 'http://localhost:11434';
const OLLAMA_MODELS = ['llama3', 'mistral', 'qwen2', 'codellama', 'gemma:2b'];

export function OllamaConfig({ onConfigure, isConfiguring = false }: OllamaConfigProps) {
  const [ollamaUrl, setOllamaUrl] = useState(OLLAMA_DEFAULT_URL);
  const [model, setModel] = useState('llama3');
  const [error, setError] = useState<string>();

  const handleConfigure = async () => {
    setError('');

    if (!ollamaUrl.trim()) {
      setError('Ollama URL is required');
      return;
    }

    try {
      await onConfigure({ ollama_url: ollamaUrl, ollama_model: model });
    } catch (err) {
      setError((err as Error).message);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Ollama Configuration</CardTitle>
        <CardDescription>
          Configure your local Ollama server for free LLM processing.
          Ollama runs entirely on your server - no API keys needed.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && (
          <Alert variant="destructive">
            {error}
          </Alert>
        )}

        <div>
          <Label htmlFor="ollama-url">Ollama Server URL</Label>
          <Input
            id="ollama-url"
            type="url"
            placeholder={OLLAMA_DEFAULT_URL}
            value={ollamaUrl}
            onChange={(e) => setOllamaUrl(e.target.value)}
            disabled={isConfiguring}
          />
          <p className="text-xs text-slate-500 mt-1">
            Default: {OLLAMA_DEFAULT_URL}
          </p>
        </div>

        <div>
          <Label htmlFor="ollama-model">Model</Label>
          <select
            id="ollama-model"
            value={model}
            onChange={(e) => setModel(e.target.value)}
            disabled={isConfiguring}
            className="flex h-9 w-full rounded-md border border-slate-300 bg-white px-3 py-1 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-600"
          >
            {OLLAMA_MODELS.map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>
          <p className="text-xs text-slate-500 mt-1">
            Recommended: llama3 (fast and capable)
          </p>
        </div>

        <div className="flex items-center p-4 bg-slate-50 rounded-md">
          <div className="flex-1">
            <p className="text-sm font-medium text-slate-900">Cost: Free</p>
            <p className="text-xs text-slate-500">
              Ollama runs locally on your server - no per-token costs
            </p>
          </div>
        </div>

        <Button
          onClick={handleConfigure}
          disabled={isConfiguring}
          className="w-full"
        >
          {isConfiguring ? 'Configuring...' : 'Configure Ollama'}
        </Button>
      </CardContent>
    </Card>
  );
}
