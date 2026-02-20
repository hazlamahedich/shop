import { Badge } from '@/components/ui/Badge';
import { Card, CardContent } from '@/components/ui/Card';

interface LLMStatusProps {
  configuration: {
    provider: string | null;
    ollamaModel?: string;
    cloudModel?: string;
    status: string;
    configuredAt?: string;
    lastTestAt?: string;
    testResult?: {
      success: boolean;
      latency_ms?: number;
      tokens_used?: number;
    };
    totalTokensUsed?: number;
    totalCostUsd?: number;
  };
}

const PROVIDER_LABELS: Record<string, string> = {
  ollama: 'Ollama (Local)',
  openai: 'OpenAI',
  anthropic: 'Anthropic',
  gemini: 'Google Gemini',
  glm: 'GLM-4 (Zhipu AI)',
};

export function LLMStatus({ configuration }: LLMStatusProps) {
  if (!configuration.provider) {
    return (
    <Card>
      <CardContent className="p-6">
        <div className="text-center">
          <p className="text-sm text-slate-500">No LLM provider configured</p>
          <p className="text-xs text-slate-400 mt-1">
            Configure Ollama or a cloud provider to enable AI responses
          </p>
        </div>
      </CardContent>
    </Card>
    );
  }

  const model = configuration.ollamaModel || configuration.cloudModel || 'unknown';
  const isSuccess = configuration.status === 'active';
  const testSuccess = configuration.testResult?.success;
  const providerLabel = PROVIDER_LABELS[configuration.provider] || configuration.provider;

  return (
    <Card>
      <CardContent className="p-6">
        <div className="space-y-4">
          {/* Status Badge */}
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-slate-900">Status</span>
            <Badge variant={isSuccess ? "default" : "secondary"}>
              {isSuccess ? "Active" : configuration.status}
            </Badge>
          </div>

          {/* Provider Card */}
          <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium text-slate-900">Provider</p>
              {isSuccess && (
                <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
                  Connected
                </Badge>
              )}
            </div>
            <p className="text-lg font-semibold text-slate-700 mt-1">{providerLabel}</p>
            <div className="flex items-center gap-2 mt-2">
              <span className="text-xs text-slate-500">Model:</span>
              <Badge variant="secondary" className="font-mono text-xs">
                {model}
              </Badge>
            </div>
          </div>

          {/* Configuration Date */}
          {configuration.configuredAt && (
            <div>
              <p className="text-sm font-medium text-slate-900">Configured</p>
              <p className="text-sm text-slate-600">
                {new Date(configuration.configuredAt).toLocaleString()}
              </p>
            </div>
          )}

          {/* Last Test */}
          {configuration.lastTestAt && configuration.testResult && (
            <div>
              <p className="text-sm font-medium text-slate-900">Last Test</p>
              <div className="flex items-center gap-2">
                <Badge variant={testSuccess ? "default" : "destructive"}>
                  {testSuccess ? "Success" : "Failed"}
                </Badge>
                {configuration.testResult.latency_ms && (
                  <span className="text-xs text-slate-500">
                    {configuration.testResult.latency_ms.toFixed(0)}ms
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-500">
                {new Date(configuration.lastTestAt).toLocaleString()}
              </p>
            </div>
          )}

          {/* Cost Tracking */}
          {configuration.totalTokensUsed !== undefined && (
            <div>
              <p className="text-sm font-medium text-slate-900">Usage</p>
              <p className="text-sm text-slate-600">
                {configuration.totalTokensUsed.toLocaleString()} tokens used
              </p>
              {configuration.totalCostUsd !== undefined && configuration.totalCostUsd > 0 && (
                <p className="text-xs text-slate-500">
                  Total cost: ${configuration.totalCostUsd.toFixed(4)}
                </p>
              )}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
