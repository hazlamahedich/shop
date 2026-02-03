/**
 * Shopify Callback Component
 * Handles OAuth callback from Shopify popup window
 */

import { useEffect } from 'react';

/**
 * Shopify callback handler component
 * Processes the OAuth callback and notifies parent window
 */
export function ShopifyCallback() {
  useEffect(() => {
    const handleCallback = async () => {
      const urlParams = new URLSearchParams(window.location.search);
      const code = urlParams.get('code');
      const state = urlParams.get('state');
      const shop = urlParams.get('shop');

      if (code && state && shop) {
        try {
          // Call backend callback endpoint
          const response = await fetch(
            `/api/integrations/shopify/callback?code=${code}&state=${state}&shop=${shop}`
          );

          if (response.ok) {
            const { data } = await response.json();
            // Notify parent window of success
            if (window.opener) {
              window.opener.postMessage(
                {
                  type: 'shopify-oauth-success',
                  data,
                },
                window.location.origin
              );
            }
            // Close popup
            window.close();
          } else {
            const error = await response.json();
            if (window.opener) {
              window.opener.postMessage(
                {
                  type: 'shopify-oauth-error',
                  error: error.data?.message || 'Connection failed',
                },
                window.location.origin
              );
            }
            window.close();
          }
        } catch (error) {
          console.error('Shopify callback error:', error);
          if (window.opener) {
            window.opener.postMessage(
              {
                type: 'shopify-oauth-error',
                error: 'Connection failed',
              },
              window.location.origin
            );
          }
          window.close();
        }
      } else {
        // OAuth denied or error
        if (window.opener) {
          window.opener.postMessage(
            {
              type: 'shopify-oauth-error',
              error: 'Authorization was denied or invalid parameters',
            },
            window.location.origin
          );
        }
        window.close();
      }
    };

    handleCallback();
  }, []);

  // Show loading message while processing
  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        <div className="inline-block w-8 h-8 border-4 border-green-600 border-t-transparent rounded-full animate-spin" />
        <p className="mt-4 text-sm">Connecting your Shopify store...</p>
      </div>
    </div>
  );
}
