import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Label } from '@/components/ui/Label';
import { Alert } from '@/components/ui/Alert';
import { Select } from '@/components/ui/Select';
import { Progress } from '@/components/ui/Progress';
import { apiClient } from '@/services/api';
import { RefreshCw, AlertTriangle, CheckCircle2, Loader2 } from 'lucide-react';

interface EmbeddingSettingsData {
  provider: string;
  model: string;
  dimension: number;
  re_embedding_required: boolean;
  document_count: number;
}

interface EmbeddingSettingsResponse {
  data: EmbeddingSettingsData;
}

interface ReEmbedStatusResponse {
  data: {
    status_counts: Record<string, number>;
    total_documents: number;
    completed_documents: number;
    progress_percent: number;
  };
}

const EMBEDDING_PROVIDERS = [
  { value: 'openai', label: 'OpenAI', model: 'text-embedding-3-small', dimension: 1536 },
  { value: 'gemini', label: 'Google Gemini', model: 'text-embedding-004', dimension: 768 },
  { value: 'ollama', label: 'Ollama (Local)', model: 'nomic-embed-text', dimension: 768 },
];

export function EmbeddingSettings() {
  const [settings, setSettings] = useState<EmbeddingSettingsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [selectedProvider, setSelectedProvider] = useState('openai');
  const [reEmbedStatus, setReEmbedStatus] = useState<ReEmbedStatusResponse['data'] | null>(null);

  useEffect(() => {
    loadSettings();
  }, []);

  useEffect(() => {
    if (settings?.re_embedding_required) {
      pollReEmbedStatus();
    }
  }, [settings?.re_embedding_required]);

  const loadSettings = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get<EmbeddingSettingsResponse>('/api/settings/embedding-provider');
      setSettings(response.data.data);
      setSelectedProvider(response.data.data.provider);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const pollReEmbedStatus = async () => {
    const poll = async () => {
      try {
        const response = await apiClient.get<ReEmbedStatusResponse>('/api/knowledge-base/re-embed/status');
        setReEmbedStatus(response.data.data);
        
        if (response.data.data.progress_percent < 100 && response.data.data.status_counts.queued > 0) {
          setTimeout(poll, 2000);
        }
      } catch (err) {
        console.error('Failed to poll re-embed status:', err);
      }
    };
    poll();
  };

  const handleProviderChange = async (newProvider: string) => {
    if (newProvider === selectedProvider) return;
    
    setSelectedProvider(newProvider);
    setError(null);
    setSuccess(null);
    setSaving(true);

    try {
      const providerConfig = EMBEDDING_PROVIDERS.find(p => p.value === newProvider);
      const response = await apiClient.patch<EmbeddingSettingsResponse>('/api/settings/embedding-provider', {
        provider: newProvider,
        model: providerConfig?.model || 'text-embedding-3-small',
      });
      
      setSettings(response.data.data);
      
      if (response.data.data.re_embedding_required) {
        setSuccess(`Provider changed. Re-embedding ${response.data.data.document_count} documents...`);
        pollReEmbedStatus();
      } else {
        setSuccess('Embedding provider updated successfully');
      }
      
      setTimeout(() => setSuccess(null), 5000);
    } catch (err) {
      setError((err as Error).message);
      setSelectedProvider(settings?.provider || 'openai');
    } finally {
      setSaving(false);
    }
  };

  const handleManualReEmbed = async () => {
    if (!confirm('This will re-embed all documents. Continue?')) return;
    
    setError(null);
    setSaving(true);
    
    try {
      await apiClient.post('/api/knowledge-base/re-embed', {});
      setSuccess('Re-embedding started...');
      pollReEmbedStatus();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <Card data-testid="embedding-settings-loading">
        <CardContent className="p-6">
          <div className="flex items-center justify-center">
            <Loader2 className="w-6 h-6 animate-spin text-slate-400" />
          </div>
        </CardContent>
      </Card>
    );
  }

  const currentProvider = EMBEDDING_PROVIDERS.find(p => p.value === settings?.provider);
  const dimensionChange = currentProvider?.dimension !== settings?.dimension;

  return (
    <Card data-testid="embedding-settings-card">
      <CardHeader>
        <CardTitle>Embedding Provider Settings</CardTitle>
        <CardDescription>
          Configure the embedding provider for document vectorization.
          Changing providers may require re-embedding existing documents.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {error && (
          <Alert variant="destructive" data-testid="embedding-error-alert">
            <AlertTriangle className="w-4 h-4" />
            {error}
          </Alert>
        )}

        {success && (
          <Alert className="bg-green-500/10 text-green-400 border-green-500/20" data-testid="embedding-success-alert">
            <CheckCircle2 className="w-4 h-4" />
            {success}
          </Alert>
        )}

        <div>
          <Label htmlFor="embedding-provider-select">Embedding Provider</Label>
          <Select
            id="embedding-provider-select"
            data-testid="embedding-provider-select"
            label=""
            value={selectedProvider}
            onChange={(e) => handleProviderChange(e.target.value)}
            disabled={saving}
            options={EMBEDDING_PROVIDERS.map(p => ({
              value: p.value,
              label: `${p.label} (${p.dimension}D)`,
            }))}
          />
        </div>

        {settings && (
          <div className="space-y-2 text-sm text-white/60" data-testid="embedding-settings-info">
            <div className="flex justify-between">
              <span>Current Model:</span>
              <span className="font-medium" data-testid="current-model">{settings.model}</span>
            </div>
            <div className="flex justify-between">
              <span>Vector Dimension:</span>
              <span className="font-medium" data-testid="current-dimension">{settings.dimension}</span>
            </div>
            <div className="flex justify-between">
              <span>Documents:</span>
              <span className="font-medium" data-testid="document-count">{settings.document_count}</span>
            </div>
          </div>
        )}

        {reEmbedStatus && reEmbedStatus.total_documents > 0 && (
          <div className="space-y-2" data-testid="re-embed-progress-container">
            <div className="flex justify-between text-sm">
              <span>Re-embedding Progress</span>
              <span data-testid="re-embed-progress-percent">{reEmbedStatus.progress_percent}%</span>
            </div>
            <Progress value={reEmbedStatus.progress_percent} data-testid="re-embed-progress-bar" />
            <div className="text-xs text-white/50" data-testid="re-embed-progress-text">
              {reEmbedStatus.completed_documents} of {reEmbedStatus.total_documents} documents
            </div>
          </div>
        )}

        {dimensionChange && (
          <Alert className="bg-amber-500/10 text-amber-400 border-amber-500/20" data-testid="dimension-change-warning">
            <AlertTriangle className="w-4 h-4" />
            Dimension change detected. Documents will need to be re-embedded.
          </Alert>
        )}

        <div className="pt-4 border-t">
          <Button
            onClick={handleManualReEmbed}
            variant="outline"
            disabled={saving || !settings?.document_count}
            data-testid="re-embed-button"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${saving ? 'animate-spin' : ''}`} />
            Re-embed All Documents
          </Button>
          <p className="text-xs text-white/50 mt-2">
            Manually trigger re-embedding of all documents with the current provider.
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
