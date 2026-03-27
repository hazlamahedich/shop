/**
 * Embed Code Preview Component
 *
 * Story 5.6: Merchant Widget Settings UI - AC6
 *
 * Displays embed code for merchants to copy and paste into their website.
 * Provides platform-specific instructions for HTML, Shopify, React, and WordPress.
 */

import React, { useState } from 'react';
import { Copy, Check, Code2, ChevronDown, ChevronUp } from 'lucide-react';
import { useToast } from '../../context/ToastContext';

interface EmbedCodePreviewProps {
  merchantId: number | null;
  primaryColor: string;
  enabled: boolean;
  apiBaseUrl?: string;
}

type Platform = 'html' | 'shopify' | 'react' | 'wordpress';

function generateEmbedCode(merchantId: number | null, primaryColor: string, apiBaseUrl?: string): string {
  const id = merchantId ?? 'YOUR_MERCHANT_ID';
  const baseUrl = apiBaseUrl || 'https://your-domain-name.com/api/v1/widget';
  const scriptUrl = baseUrl.replace('/api/v1/widget', '/static/widget/widget.umd.js');
  return `<script>
  window.ShopBotConfig = {
    merchantId: '${id}',
    theme: { primaryColor: '${primaryColor}' },
    apiBaseUrl: '${baseUrl}'
  };
</script>
<script src="https://unpkg.com/react@18/umd/react.production.min.js" crossorigin></script>
<script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js" crossorigin></script>
<script src="${scriptUrl}"></script>`;
}

function generateReactCode(merchantId: number | null, primaryColor: string, apiBaseUrl?: string): string {
  const id = merchantId ?? 'YOUR_MERCHANT_ID';
  const baseUrl = apiBaseUrl || 'https://your-domain-name.com/api/v1/widget';
  const scriptUrl = baseUrl.replace('/api/v1/widget', '/static/widget/widget.umd.js');
  return `// In your Next.js page or _app.tsx:
import Script from 'next/script';

// In your component:
<>
  <Script id="shopbot-config" strategy="beforeInteractive">
    {\`
      window.ShopBotConfig = {
        merchantId: '${id}',
        theme: {
          primaryColor: '${primaryColor}',
          position: 'bottom-right',
        },
        apiBaseUrl: '${baseUrl}'
      };
    \`}
  </Script>
  <Script src="https://unpkg.com/react@18/umd/react.production.min.js" strategy="beforeInteractive" />
  <Script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js" strategy="beforeInteractive" />
  <Script src="${scriptUrl}" strategy="afterInteractive" />
</>`;
}

function generateWordPressCode(merchantId: number | null, primaryColor: string, apiBaseUrl?: string): string {
  const id = merchantId ?? 'YOUR_MERCHANT_ID';
  const baseUrl = apiBaseUrl || 'https://your-domain-name.com/api/v1/widget';
  const scriptUrl = baseUrl.replace('/api/v1/widget', '/static/widget/widget.umd.js');
  return `// Add this to your theme's functions.php file:

function shop_bot_widget() {
  ?>
  <script>
    window.ShopBotConfig = {
      merchantId: '${id}',
      theme: { primaryColor: '${primaryColor}' },
      apiBaseUrl: '${baseUrl}'
    };
  </script>
  <script src="https://unpkg.com/react@18/umd/react.production.min.js" crossorigin></script>
  <script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js" crossorigin></script>
  <script src="${scriptUrl}"></script>
  <?php
}
add_action('wp_footer', 'shop_bot_widget');`;
}

export const EmbedCodePreview: React.FC<EmbedCodePreviewProps> = ({
  merchantId,
  primaryColor,
  enabled,
  apiBaseUrl,
}) => {
  const [copied, setCopied] = useState(false);
  const [activePlatform, setActivePlatform] = useState<Platform>('html');
  const [showInstructions, setShowInstructions] = useState(true);
  const { toast } = useToast();

  const getCodeForPlatform = (platform: Platform): string => {
    switch (platform) {
      case 'shopify':
        return generateEmbedCode(merchantId, primaryColor, apiBaseUrl);
      case 'react':
        return generateReactCode(merchantId, primaryColor, apiBaseUrl);
      case 'wordpress':
        return generateWordPressCode(merchantId, primaryColor, apiBaseUrl);
      default:
        return generateEmbedCode(merchantId, primaryColor, apiBaseUrl);
    }
  };

  const embedCode = getCodeForPlatform(activePlatform);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(embedCode);
      setCopied(true);
      toast('Embed code copied to clipboard', 'success');
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      toast('Failed to copy to clipboard', 'error');
    }
  };

  if (!enabled) {
    return (
      <div className="bg-gray-50 rounded-lg p-6 text-center">
        <Code2 className="mx-auto h-8 w-8 text-gray-400 mb-2" />
        <p className="text-gray-500 text-sm">
          Enable the widget to get your embed code
        </p>
      </div>
    );
  }

  const platformInstructions: Record<Platform, { title: string; steps: string[] }> = {
    html: {
      title: 'Plain HTML / Any Website',
      steps: [
        'Replace YOUR_API_DOMAIN with your actual API server URL',
        'Copy the code below',
        'Paste it into your website\'s HTML, just before the closing </body> tag',
        'Save and publish your changes',
        'Note: React and ReactDOM are loaded from CDN automatically',
      ],
    },
    shopify: {
      title: 'Shopify Store',
      steps: [
        'Replace YOUR_API_DOMAIN with your actual API server URL',
        'Go to your Shopify Admin → Online Store → Themes',
        'Click "..." next to your active theme → Edit code',
        'Find and open theme.liquid in the Layout folder',
        'Scroll to the bottom and paste the code just before </body>',
        'Click Save',
        'Note: React and ReactDOM are loaded from CDN automatically',
      ],
    },
    react: {
      title: 'React / Next.js',
      steps: [
        'Replace YOUR_API_DOMAIN with your actual API server URL',
        'Install Next.js Script component if not already available',
        'Copy the code below to your page component or root layout',
        'The widget will load after React dependencies are ready',
        'Note: Uses Next.js Script component for optimal loading',
      ],
    },
    wordpress: {
      title: 'WordPress',
      steps: [
        'Replace YOUR_API_DOMAIN with your actual API server URL',
        'Option 1: Add to functions.php (recommended)',
        'Copy the code below to your theme\'s functions.php file',
        'Option 2: Use a plugin like "Insert Headers and Footers"',
        'Paste the HTML version in the Footer section',
        'Note: React and ReactDOM are loaded from CDN automatically',
      ],
    },
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <label className="block text-sm font-medium text-gray-700">
          Embed Code
        </label>
        <button
          onClick={handleCopy}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors"
        >
          {copied ? (
            <>
              <Check className="h-4 w-4 text-green-500" />
              Copied!
            </>
          ) : (
            <>
              <Copy className="h-4 w-4" />
              Copy to Clipboard
            </>
          )}
        </button>
      </div>

      <div className="flex flex-wrap gap-2">
        {(['html', 'shopify', 'react', 'wordpress'] as Platform[]).map((platform) => (
          <button
            key={platform}
            onClick={() => setActivePlatform(platform)}
            className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
              activePlatform === platform
                ? 'bg-indigo-100 text-indigo-700 border border-indigo-200'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {platform === 'html' ? 'HTML' : platform.charAt(0).toUpperCase() + platform.slice(1)}
          </button>
        ))}
      </div>

      <div className="relative">
        <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg text-xs overflow-x-auto font-mono max-h-64">
          <code>{embedCode}</code>
        </pre>
      </div>

      <div className="border border-gray-200 rounded-lg overflow-hidden">
        <button
          onClick={() => setShowInstructions(!showInstructions)}
          className="w-full flex items-center justify-between p-3 bg-gray-50 hover:bg-gray-100 transition-colors"
        >
          <span className="text-sm font-medium text-gray-700">
            {platformInstructions[activePlatform].title} - How to Install
          </span>
          {showInstructions ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </button>

        {showInstructions && (
          <div className="p-4 border-t border-gray-200 bg-white">
            <ol className="text-sm text-gray-600 space-y-2 list-decimal list-inside">
              {platformInstructions[activePlatform].steps.map((step, index) => (
                <li key={index}>{step}</li>
              ))}
            </ol>
          </div>
        )}
      </div>
    </div>
  );
};
