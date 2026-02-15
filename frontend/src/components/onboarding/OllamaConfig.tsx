import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/Label';
import { Alert } from '@/components/ui/Alert';
import { Badge } from '@/components/ui/Badge';

interface OllamaConfigProps {
  onConfigure: (config: { ollama_url: string; ollama_model: string }) => Promise<void>;
  isConfiguring?: boolean;
}

const OLLAMA_DEFAULT_URL = 'http://localhost:11434';

interface OllamaModel {
  id: string;
  name: string;
  isDownloaded: boolean;
  description?: string;
}

async function fetchOllamaModels(ollamaUrl: string): Promise<OllamaModel[]> {
  try {
    const response = await fetch(`${ollamaUrl}/api/tags`);
    if (response.ok) {
      const data = await response.json();
      return (data.models || []).map((m: { name: string }) => ({
        id: m.name.split(':')[0],
        name: m.name,
        isDownloaded: true,
      }));
    }
  } catch {
    // Ollama not reachable
  }
  return [];
}

const POPULAR_LIBRARY_MODELS: OllamaModel[] = [
  { id: 'llama3', name: 'Llama 3', isDownloaded: false, description: "Meta's latest open model" },
  { id: 'llama3.1', name: 'Llama 3.1', isDownloaded: false, description: 'Improved reasoning' },
  { id: 'mistral', name: 'Mistral 7B', isDownloaded: false, description: 'Efficient model' },
  { id: 'qwen2', name: 'Qwen 2', isDownloaded: false, description: "Alibaba's model" },
  { id: 'codellama', name: 'Code Llama', isDownloaded: false, description: 'Coding focused' },
  { id: 'gemma2', name: 'Gemma 2', isDownloaded: false, description: "Google's open model" },
  { id: 'phi3', name: 'Phi-3', isDownloaded: false, description: "Microsoft's small model" },
  { id: 'deepseek-r1', name: 'DeepSeek R1', isDownloaded: false, description: 'Reasoning model' },
];

export function OllamaConfig({ onConfigure, isConfiguring = false }: OllamaConfigProps) {
  const [ollamaUrl, setOllamaUrl] = useState(OLLAMA_DEFAULT_URL);
  const [model, setModel] = useState('llama3');
  const [error, setError] = useState<string>();
  const [models, setModels] = useState<OllamaModel[]>([]);
  const [loadingModels, setLoadingModels] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'unknown' | 'connected' | 'failed'>('unknown');

  useEffect(() => {
    async function loadModels() {
      setLoadingModels(true);
      const downloaded = await fetchOllamaModels(ollamaUrl);
      
      if (downloaded.length > 0) {
        setConnectionStatus('connected');
        const downloadedIds = new Set(downloaded.map(m => m.id));
        const libraryModels = POPULAR_LIBRARY_MODELS.filter(m => !downloadedIds.has(m.id));
        setModels([...downloaded, ...libraryModels]);
        setModel(downloaded[0].id);
      } else {
        setConnectionStatus('failed');
        setModels(POPULAR_LIBRARY_MODELS);
      }
      setLoadingModels(false);
    }
    
    const debounce = setTimeout(loadModels, 500);
    return () => clearTimeout(debounce);
  }, [ollamaUrl]);

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

  const downloadedModels = models.filter(m => m.isDownloaded);
  const libraryModels = models.filter(m => !m.isDownloaded);

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
            onChange={(e) => {
              setOllamaUrl(e.target.value);
              setConnectionStatus('unknown');
            }}
            disabled={isConfiguring}
          />
          <div className="flex items-center gap-2 mt-1">
            <p className="text-xs text-slate-500">Default: {OLLAMA_DEFAULT_URL}</p>
            {connectionStatus === 'connected' && (
              <Badge variant="secondary" className="text-xs bg-green-100 text-green-700">Connected</Badge>
            )}
            {connectionStatus === 'failed' && (
              <Badge variant="secondary" className="text-xs bg-yellow-100 text-yellow-700">Not reachable</Badge>
            )}
          </div>
        </div>

        <div>
          <Label htmlFor="ollama-model">Model</Label>
          <select
            id="ollama-model"
            value={model}
            onChange={(e) => setModel(e.target.value)}
            disabled={isConfiguring || loadingModels}
            className="flex h-9 w-full rounded-md border border-slate-300 bg-white px-3 py-1 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-600"
          >
            {loadingModels && (
              <option value="">Loading models...</option>
            )}
            {downloadedModels.length > 0 && (
              <optgroup label="Downloaded (Ready to use)">
                {downloadedModels.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.name}
                  </option>
                ))}
              </optgroup>
            )}
            {libraryModels.length > 0 && (
              <optgroup label="Available to Pull">
                {libraryModels.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.name} {m.description && `- ${m.description}`}
                  </option>
                ))}
              </optgroup>
            )}
          </select>
          <p className="text-xs text-slate-500 mt-1">
            {models.find(m => m.id === model)?.isDownloaded 
              ? 'Model is downloaded and ready'
              : 'Model will be pulled on first use'}
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
