import { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Alert } from '@/components/ui/Alert';

interface TestConnectionProps {
  onTest: (prompt: string) => Promise<void>;
  isTesting?: boolean;
}

export function TestConnection({ onTest, isTesting = false }: TestConnectionProps) {
  const [testPrompt, setTestPrompt] = useState('Hello, this is a test.');
  const [result, setResult] = useState<{
    success: boolean;
    latency_ms?: number;
    response?: string;
    error?: string;
  } | null>(null);

  const handleTest = async () => {
    setResult(null);
    try {
      await onTest(testPrompt);
      setResult({ success: true });
    } catch (err) {
      setResult({
        success: false,
        error: (err as Error).message
      });
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-slate-900 mb-1">
          Test Prompt
        </label>
        <input
          type="text"
          value={testPrompt}
          onChange={(e) => setTestPrompt(e.target.value)}
          data-testid="test-prompt-input"
          className="flex h-9 w-full rounded-md border border-slate-300 bg-white px-3 py-1 text-sm shadow-sm placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-600"
          placeholder="Enter a test message..."
          disabled={isTesting}
        />
      </div>

      <Button
        onClick={handleTest}
        disabled={isTesting}
        className="w-full"
        variant="outline"
        dataTestId="test-connection-button"
      >
        {isTesting ? (
          <>
            <span className="animate-pulse">Testing...</span>
          </>
        ) : (
          'Test Connection'
        )}
      </Button>

      {result && (
        <div>
          {result.success ? (
            <div className="flex items-center gap-2 p-3 bg-green-50 border border-green-200 rounded-md">
              <Badge variant="default" className="bg-green-600">Success</Badge>
              <span className="text-sm text-green-800">
                Connection working
              </span>
            </div>
          ) : (
            <Alert variant="destructive">
              <p className="text-sm">{result.error}</p>
            </Alert>
          )}
        </div>
      )}
    </div>
  );
}
