/**
 * Facebook OAuth Callback Handler Component
 * Handles the OAuth callback in the popup window
 * Communicates with parent window via postMessage
 */

import { useEffect } from 'react';

export function FacebookCallback() {
  useEffect(() => {
    const handleCallback = async () => {
      // Parse URL parameters
      const params = new URLSearchParams(window.location.search);
      const code = params.get('code');
      const state = params.get('state');
      const error = params.get('error');
      const errorReason = params.get('error_reason');
      const errorDescription = params.get('error_description');

      // Handle OAuth denial/error
      if (error || errorReason) {
        const errorMessage = errorDescription || errorReason || 'Authorization denied';
        sendErrorToParent(errorMessage);
        return;
      }

      // Handle successful callback
      if (code && state) {
        try {
          // Send code to backend for token exchange
          const response = await fetch(`/api/integrations/facebook/callback?code=${code}&state=${state}`);
          const result = await response.json();

          if (response.ok) {
            sendSuccessToParent(result.data);
          } else {
            const errorData = result;
            sendErrorToParent(errorData.message || 'Connection failed');
          }
        } catch (err) {
          sendErrorToParent(err instanceof Error ? err.message : 'Connection failed');
        }
      } else {
        sendErrorToParent('Invalid callback parameters');
      }
    };

    handleCallback();

    // Functions to communicate with parent window
    function sendSuccessToParent(data: unknown) {
      if (window.opener && window.opener !== window) {
        window.opener.postMessage(
          {
            type: 'facebook-oauth-success',
            data,
          },
          window.location.origin
        );
      }
      window.close();
    }

    function sendErrorToParent(errorMessage: string) {
      if (window.opener && window.opener !== window) {
        window.opener.postMessage(
          {
            type: 'facebook-oauth-error',
            error: errorMessage,
          },
          window.location.origin
        );
      }
      window.close();
    }
  }, []);

  // Show loading while processing
  return (
    <div className="flex items-center justify-center min-h-screen bg-slate-50">
      <div className="text-center space-y-4">
        <div className="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto" />
        <p className="text-sm text-muted-foreground">Connecting to Facebook...</p>
      </div>
    </div>
  );
}
