/** BotPreview page.
 *
 * Story 1.13: Bot Preview Mode
 *
 * Standalone page for merchants to test their bot configuration
 * in a sandbox environment before going live.
 */

import { useEffect } from 'react';
import { PreviewChat } from '../components/preview/PreviewChat';
import { usePreviewStore } from '../stores/previewStore';
import { useBotConfigStore } from '../stores/botConfigStore';
import { Card } from '../components/ui/Card';
export function BotPreview() {
  const { botName } = useBotConfigStore();
  const { startSession, sessionId, isLoading: isPreviewLoading } = usePreviewStore();

  // Start preview session on mount
  useEffect(() => {
    if (!sessionId) {
      startSession();
    }
  }, [sessionId, startSession]);

  const handleBack = () => {
    window.history.pushState({}, '', '/dashboard');
    window.dispatchEvent(new PopStateEvent('popstate'));
  };

  return (
    <div className="bot-preview-page min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                type="button"
                onClick={handleBack}
                className="text-gray-600 hover:text-gray-900 transition-colors"
                aria-label="Go back to dashboard"
              >
                <svg
                  className="w-6 h-6"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  aria-hidden="true"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M10 19l-7-7m0 0l7-7m-7 7h18"
                  />
                </svg>
              </button>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Test Your Bot</h1>
                <p className="text-sm text-gray-600">
                  Preview your bot configuration in a safe sandbox environment
                </p>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Breadcrumb */}
      <nav className="bg-white border-b border-gray-100" aria-label="Breadcrumb">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-2">
          <ol className="flex items-center space-x-2 text-sm">
            <li>
              <button
                type="button"
                onClick={handleBack}
                className="text-gray-500 hover:text-gray-700"
              >
                Dashboard
              </button>
            </li>
            <li className="text-gray-400">/</li>
            <li className="text-gray-900 font-medium" aria-current="page">
              Test Your Bot
            </li>
          </ol>
        </div>
      </nav>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Help text */}
        <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <h2 className="text-lg font-semibold text-blue-900 mb-2">How to use Preview Mode</h2>
          <ul className="text-sm text-blue-800 space-y-1">
            <li>• Use the quick-try buttons or type your own message to test your bot</li>
            <li>• See confidence scores for each response to understand bot accuracy</li>
            <li>• Reset the conversation anytime to start fresh</li>
            <li>
              • <strong>Preview conversations are NOT saved</strong> - they disappear when you leave
            </li>
            <li>
              • <strong>No customers will see these messages</strong> - this is a sandbox
            </li>
          </ul>
        </div>

        {/* Loading state */}
        {isPreviewLoading && !sessionId && (
          <div className="flex items-center justify-center h-96">
            <div className="text-center">
              <svg
                className="animate-spin h-12 w-12 text-blue-500 mx-auto"
                fill="none"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
              <p className="mt-2 text-gray-600">Starting preview session...</p>
            </div>
          </div>
        )}

        {/* Chat interface */}
        {sessionId && (
          <Card className="h-[600px]">
            <PreviewChat botName={botName || 'Bot'} />
          </Card>
        )}

        {/* Configuration tips */}
        <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 bg-white border border-gray-200 rounded-lg">
            <h3 className="font-semibold text-gray-900 mb-2">💡 Personality</h3>
            <p className="text-sm text-gray-600">
              Your bot will use the personality you configured (Friendly, Professional, or
              Enthusiastic).
            </p>
          </div>
          <div className="p-4 bg-white border border-gray-200 rounded-lg">
            <h3 className="font-semibold text-gray-900 mb-2">📝 Business Info</h3>
            <p className="text-sm text-gray-600">
              Business hours and FAQ entries will be included in bot responses automatically.
            </p>
          </div>
          <div className="p-4 bg-white border border-gray-200 rounded-lg">
            <h3 className="font-semibold text-gray-900 mb-2">🛍️ Products</h3>
            <p className="text-sm text-gray-600">
              Product search results will appear when you ask about items in your catalog.
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
