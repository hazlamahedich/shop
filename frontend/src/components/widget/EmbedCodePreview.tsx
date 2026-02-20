/**
 * Embed Code Preview Component
 *
 * Story 5.6: Merchant Widget Settings UI - AC6
 *
 * Displays embed code for merchants to copy and paste into their website.
 */

import React, { useState } from 'react';
import { Copy, Check, Code2 } from 'lucide-react';
import { useToast } from '../../context/ToastContext';

interface EmbedCodePreviewProps {
  merchantId: number | null;
  primaryColor: string;
  enabled: boolean;
}

function generateEmbedCode(merchantId: number | null, primaryColor: string): string {
  const id = merchantId ?? 'YOUR_MERCHANT_ID';
  return `<script>
  window.ShopBotConfig = {
    merchantId: '${id}',
    theme: { primaryColor: '${primaryColor}' }
  };
</script>
<script src="https://cdn.yourbot.com/widget.umd.js" async></script>`;
}

export const EmbedCodePreview: React.FC<EmbedCodePreviewProps> = ({
  merchantId,
  primaryColor,
  enabled,
}) => {
  const [copied, setCopied] = useState(false);
  const { toast } = useToast();

  const embedCode = generateEmbedCode(merchantId, primaryColor);

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

  return (
    <div className="space-y-3">
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
      <div className="relative">
        <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg text-xs overflow-x-auto font-mono">
          <code>{embedCode}</code>
        </pre>
      </div>
      <p className="text-xs text-gray-500">
        Copy this code and paste it into your website&apos;s HTML, just before the closing &lt;/body&gt; tag.
      </p>
    </div>
  );
};
