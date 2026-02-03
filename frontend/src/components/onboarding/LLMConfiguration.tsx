import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { useLLMStore } from '@/stores/llmStore';
import { OllamaConfig } from './OllamaConfig';
import { CloudConfig } from './CloudConfig';
import { LLMStatus } from './LLMStatus';
import { TestConnection } from './TestConnection';

export function LLMConfiguration() {
  const {
    configuration,
    isConfiguring,
    isTesting,
    configureLLM,
    testLLM,
    getLLMStatus,
  } = useLLMStore();

  const [providerType, setProviderType] = useState<'ollama' | 'cloud'>('ollama');
  const [showTest, setShowTest] = useState(false);

  useEffect(() => {
    getLLMStatus();
  }, [getLLMStatus]);

  const handleConfigure = async (config: any) => {
    const provider = providerType === 'ollama' ? 'ollama' : config.provider;
    await configureLLM(provider, config);
    setShowTest(true);
  };

  const handleTest = async (testPrompt: string) => {
    await testLLM(testPrompt);
    await getLLMStatus();
  };

  const isConfigured = configuration.provider !== null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>LLM Provider Configuration</span>
          {isConfigured && (
            <Badge variant="default">Configured</Badge>
          )}
        </CardTitle>
        <CardDescription>
          Configure your AI provider to enable intelligent customer responses.
          Choose between free local (Ollama) or paid cloud providers.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Current Status */}
        {isConfigured && <LLMStatus configuration={configuration} />}

        {/* Provider Selection */}
        {!isConfigured && (
          <div>
            <h3 className="text-sm font-medium text-slate-900 mb-4">
              Choose Provider Type
            </h3>
            <div className="grid grid-cols-2 gap-4">
              <button
                onClick={() => setProviderType('ollama')}
                className={`p-4 border rounded-lg text-left transition-colors ${
                  providerType === 'ollama'
                    ? 'border-indigo-500 bg-indigo-50'
                    : 'border-slate-200 hover:border-slate-300'
                }`}
              >
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-3 h-3 rounded-full bg-green-500" />
                  <span className="font-medium text-slate-900">Ollama (Free)</span>
                </div>
                <p className="text-sm text-slate-600">
                  Runs locally on your server. No API costs.
                </p>
              </button>

              <button
                onClick={() => setProviderType('cloud')}
                className={`p-4 border rounded-lg text-left transition-colors ${
                  providerType === 'cloud'
                    ? 'border-indigo-500 bg-indigo-50'
                    : 'border-slate-200 hover:border-slate-300'
                }`}
              >
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-3 h-3 rounded-full bg-blue-500" />
                  <span className="font-medium text-slate-900">Cloud Provider</span>
                </div>
                <p className="text-sm text-slate-600">
                  OpenAI, Anthropic, Gemini, or GLM-4.7.
                </p>
              </button>
            </div>
          </div>
        )}

        {/* Configuration Forms */}
        {!isConfigured && (
          <>
            {providerType === 'ollama' ? (
              <OllamaConfig
                onConfigure={handleConfigure}
                isConfiguring={isConfiguring}
              />
            ) : (
              <CloudConfig
                onConfigure={handleConfigure}
                isConfiguring={isConfiguring}
              />
            )}
          </>
        )}

        {/* Test Connection */}
        {isConfigured && (
          <>
            <TestConnection
              onTest={handleTest}
              isTesting={isTesting}
            />
          </>
        )}
      </CardContent>
    </Card>
  );
}
