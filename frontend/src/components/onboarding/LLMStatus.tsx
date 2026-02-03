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

          {/* Provider and Model */}
          <div>
            <p className="text-sm font-medium text-slate-900">Provider</p>
            <p className="text-lg font-semibold text-slate-700 capitalize">{configuration.provider}</p>
            <p className="text-sm text-slate-600">Model: {model}</p>
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
                  Total cost: ${configuration.totalCostUsd.toFixed(2)}
                </p>
              )}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
