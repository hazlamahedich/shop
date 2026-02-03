/**
 * Shopify Connection Component
 * Handles Shopify Store OAuth connection with status display
 */

import { useState } from 'react';
import { useIntegrationsStore } from '../../stores/integrationsStore';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import { Alert } from '../ui/Alert';
import { Card } from '../ui/Card';

export interface ShopifyConnectionProps {
  /** Whether to show in compact mode */
  compact?: boolean;
  /** Callback when connection status changes */
  onConnectionChange?: (connected: boolean) => void;
}

/**
 * ShopifyConnection component for OAuth flow and status display
 */
export function ShopifyConnection({
  compact = false,
  onConnectionChange,
}: ShopifyConnectionProps) {
  const {
    shopifyStatus,
    shopifyConnection,
    shopifyError,
    initiateShopifyOAuth,
    checkShopifyStatus,
    disconnectShopify,
    clearShopifyError,
  } = useIntegrationsStore();

  const [shopDomain, setShopDomain] = useState('');

  // Check status on mount
  const handleCheckShopifyStatus = () => {
    checkShopifyStatus();
  };

  // Notify parent of connection changes
  if (onConnectionChange) {
    onConnectionChange(shopifyConnection.connected);
  }

  // Handle connect action
  const handleConnect = () => {
    clearShopifyError();
    if (!shopDomain.trim()) {
      return;
    }
    initiateShopifyOAuth(shopDomain);
  };

  // Handle disconnect action
  const handleDisconnect = async () => {
    clearShopifyError();
    await disconnectShopify();
  };

  // Validate shop domain input
  const isDomainValid = shopDomain === '' || /^[a-zA-Z0-9][a-zA-Z0-9\-]*\.myshopify\.com$/.test(shopDomain);

  // Render compact version
  if (compact) {
    return (
    <div className="flex items-center justify-between p-4 border rounded-lg">
      <div className="flex items-center gap-3">
        <div>
          <p className="text-sm font-medium">
            {shopifyConnection.connected
              ? shopifyConnection.shopName || 'Shopify Store'
              : 'Connect Shopify Store'}
          </p>
          <StatusBadge status={shopifyStatus} connected={shopifyConnection.connected} />
        </div>
      </div>
      {shopifyConnection.connected ? (
        <Button variant="outline" size="sm" onClick={handleDisconnect} disabled={shopifyStatus === 'connecting'}>
          Disconnect
        </Button>
      ) : (
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="mystore.myshopify.com"
            value={shopDomain}
            onChange={(e) => setShopDomain(e.target.value)}
            className="px-3 py-1 text-sm border rounded"
            disabled={shopifyStatus === 'connecting'}
          />
          <Button size="sm" onClick={handleConnect} disabled={shopifyStatus === 'connecting' || !isDomainValid}>
            Connect
          </Button>
        </div>
      )}
    </div>
    );
  }

  // Full version
  return (
    <div className="space-y-4" data-testid="shopify-connection">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">Shopify Store Connection</h3>
          <p className="text-sm text-muted-foreground">
            Connect your Shopify store to enable product search and checkout functionality
          </p>
        </div>
        <StatusBadge status={shopifyStatus} connected={shopifyConnection.connected} />
      </div>

      {/* Error Alert */}
      {shopifyError && (
        <Alert variant="destructive" dismissible onDismiss={clearShopifyError}>
          <p className="font-medium">Connection Error</p>
          <p className="text-sm">{shopifyError}</p>
          <p className="text-sm mt-2">
            <strong>Troubleshooting:</strong>
            <ul className="list-disc list-inside mt-1">
              <li>Enter your store domain in the format: mystore.myshopify.com</li>
              <li>Make sure you have admin access to the Shopify store</li>
              <li>Grant all required permissions (products, inventory, orders, checkouts)</li>
              <li>Check that your Shopify App is properly configured</li>
            </ul>
          </p>
        </Alert>
      )}

      {/* Connected State */}
      {shopifyConnection.connected ? (
        <Card className="p-6 space-y-4">
          <div>
            <h4 className="font-semibold text-lg">{shopifyConnection.shopName || 'Shopify Store'}</h4>
            <p className="text-sm text-muted-foreground">Store: {shopifyConnection.shopDomain}</p>
            {shopifyConnection.connectedAt && (
              <p className="text-xs text-muted-foreground mt-1">
                Connected: {new Date(shopifyConnection.connectedAt).toLocaleDateString()}
              </p>
            )}
          </div>

          {/* API Status Indicators */}
          <div className="grid grid-cols-3 gap-4">
            <div>
              <p className="text-sm font-medium">Storefront API</p>
              <Badge variant={shopifyConnection.storefrontApiConnected ? 'default' : 'secondary'}>
                {shopifyConnection.storefrontApiConnected ? 'Connected' : 'Not Connected'}
              </Badge>
            </div>
            <div>
              <p className="text-sm font-medium">Admin API</p>
              <Badge variant={shopifyConnection.adminApiConnected ? 'default' : 'secondary'}>
                {shopifyConnection.adminApiConnected ? 'Connected' : 'Not Connected'}
              </Badge>
            </div>
            <div>
              <p className="text-sm font-medium">Webhooks</p>
              <Badge variant={shopifyConnection.webhookSubscribed ? 'default' : 'secondary'}>
                {shopifyConnection.webhookSubscribed ? 'Subscribed' : 'Not Subscribed'}
              </Badge>
            </div>
          </div>

          <Button variant="outline" onClick={handleDisconnect} disabled={shopifyStatus === 'connecting'}>
            Disconnect Store
          </Button>
        </Card>
      ) : (
        /* Not Connected State */
        <Card className="p-6">
          <div className="text-center space-y-4">
            <div className="w-16 h-16 mx-auto bg-green-100 rounded-full flex items-center justify-center">
              <svg className="w-8 h-8 text-green-600" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 0 1.72 1.73a.9.9 0 0 0-.26-.67l-.17-.17a.9.9 0 0 0-.25-.25 2.03 2.03 0 0 0-2.9 0 2.03 2.03 0 0 0-2.9 0 .9.9 0 0 0-.25.25l-.17.17a.9.9 0 0 0-.26-.67A2 2 0 0 0 11.78 2zm5.72.06a.9.9 0 0 0 .26.67l.17.17a.9.9 0 0 0 .25.25 2.03 2.03 0 0 0 2.9 0 2.03 2.03 0 0 0 2.9 0 .9.9 0 0 0 .25-.25l.17-.17a.9.9 0 0 0 .26-.67A2 2 0 0 0 17.94 2zm-9.44.01a.9.9 0 0 0-.26.67l-.17-.17a.9.9 0 0 0-.25.25 2.03 2.03 0 0 0-2.9 0 2.03 2.03 0 0 0-2.9 0 .9.9 0 0 0 .25.25l.17.17a.9.9 0 0 0 .26.67A2 2 0 0 0 8.5 2.07zm2.88.01a.9.9 0 0 0 .26.67l.17.17a.9.9 0 0 0 .25.25 2.03 2.03 0 0 0 2.9 0 2.03 2.03 0 0 0 2.9 0 .9.9 0 0 0-.25-.25l-.17-.17a.9.9 0 0 0-.26-.67A2 2 0 0 0 11.38 2.08z"/>
              </svg>
            </div>
            <div>
              <h4 className="font-semibold text-lg">Connect Your Shopify Store</h4>
              <p className="text-sm text-muted-foreground max-w-md mx-auto">
                Enter your Shopify store domain and click connect to authorize product search and checkout functionality.
              </p>
            </div>

            {/* Shop Domain Input */}
            <div className="max-w-sm mx-auto space-y-2">
              <input
                type="text"
                placeholder="your-store.myshopify.com"
                value={shopDomain}
                onChange={(e) => setShopDomain(e.target.value)}
                className="w-full px-4 py-2 text-sm border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={shopifyStatus === 'connecting'}
                aria-label="Shopify store domain"
              />
              {!isDomainValid && shopDomain !== '' && (
                <p className="text-xs text-destructive">
                  Please enter a valid store domain (e.g., mystore.myshopify.com)
                </p>
              )}
            </div>

            <Button
              onClick={handleConnect}
              disabled={shopifyStatus === 'connecting' || !isDomainValid}
              size="lg"
            >
              {shopifyStatus === 'connecting' ? 'Connecting...' : 'Connect Shopify Store'}
            </Button>

            <p className="text-xs text-muted-foreground">
              Required permissions: read_products, read_inventory, write_orders, read_orders, write_checkouts, read_checkouts
            </p>
          </div>
        </Card>
      )}

      {/* Loading State */}
      {shopifyStatus === 'connecting' && !shopifyConnection.connected && (
        <div className="text-center py-4">
          <div className="inline-block w-4 h-4 border-2 border-green-600 border-t-transparent rounded-full animate-spin" />
          <p className="text-sm text-muted-foreground mt-2">Connecting to Shopify...</p>
        </div>
      )}
    </div>
  );
}

/**
 * Status badge component
 */
function StatusBadge({
  status,
  connected,
}: {
  status: 'idle' | 'connecting' | 'connected' | 'error';
  connected: boolean;
}) {
  if (status === 'connecting') {
    return <Badge variant="secondary">Connecting...</Badge>;
  }

  if (status === 'error') {
    return <Badge variant="destructive">Error</Badge>;
  }

  if (connected) {
    return <Badge variant="default">Connected</Badge>;
  }

  return <Badge variant="secondary">Not Connected</Badge>;
}
