import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Facebook, ShoppingBag, ChevronDown, ChevronUp, ExternalLink, MessageSquare, Webhook } from 'lucide-react';
import { useIntegrationsStore } from '../stores/integrationsStore';
import { useAuthStore } from '../stores/authStore';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Input } from '../components/ui/Input';
import { Label } from '../components/ui/Label';

const Settings = () => {
  const [activeTab, setActiveTab] = useState('integrations');
  const [showFacebookConfig, setShowFacebookConfig] = useState(false);
  const [facebookAppId, setFacebookAppId] = useState('');
  const [facebookAppSecret, setFacebookAppSecret] = useState('');
  const [isSavingFacebook, setIsSavingFacebook] = useState(false);
  const [shopDomain, setShopDomain] = useState('');
  const [showShopifyConfig, setShowShopifyConfig] = useState(false);
  const [shopifyApiKey, setShopifyApiKey] = useState('');
  const [shopifyApiSecret, setShopifyApiSecret] = useState('');
  const [isSavingShopify, setIsSavingShopify] = useState(false);
  const [shopifyCredentialsStatus, setShopifyCredentialsStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [shopifyCredentialsMessage, setShopifyCredentialsMessage] = useState('');

  const merchant = useAuthStore((state) => state.merchant);

  const {
    facebookStatus,
    facebookConnection,
    facebookError,
    initiateFacebookOAuth,
    checkFacebookStatus,
    disconnectFacebook,
    saveFacebookCredentials,
    clearError,
    shopifyStatus,
    shopifyConnection,
    shopifyError,
    initiateShopifyOAuth,
    checkShopifyStatus,
    disconnectShopify,
    saveShopifyCredentials,
    clearShopifyError,
    setMerchantId,
  } = useIntegrationsStore();

  useEffect(() => {
    if (merchant?.id) {
      setMerchantId(merchant.id);
    }
  }, [merchant?.id, setMerchantId]);

  React.useEffect(() => {
    checkFacebookStatus();
    checkShopifyStatus();
  }, [checkFacebookStatus, checkShopifyStatus]);

  const handleFacebookConnect = () => {
    clearError();
    initiateFacebookOAuth();
  };

  const handleFacebookDisconnect = async () => {
    clearError();
    await disconnectFacebook();
  };

  const handleSaveFacebookCredentials = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!facebookAppId || !facebookAppSecret) return;
    setIsSavingFacebook(true);
    await saveFacebookCredentials(facebookAppId, facebookAppSecret);
    setIsSavingFacebook(false);
    handleFacebookConnect();
  };

  const handleShopifyConnect = () => {
    clearShopifyError();
    if (!shopDomain.trim()) return;
    initiateShopifyOAuth(shopDomain.trim());
  };

  const handleShopifyDisconnect = async () => {
    clearShopifyError();
    await disconnectShopify();
    setShopDomain('');
  };

  const handleSaveShopifyCredentials = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!shopifyApiKey || !shopifyApiSecret) return;
    setIsSavingShopify(true);
    setShopifyCredentialsStatus('idle');
    setShopifyCredentialsMessage('');
    
    try {
      await saveShopifyCredentials(shopifyApiKey, shopifyApiSecret);
      setShopifyCredentialsStatus('success');
      setShopifyCredentialsMessage('Credentials saved successfully! You can now connect your store.');
    } catch (error) {
      setShopifyCredentialsStatus('error');
      setShopifyCredentialsMessage(error instanceof Error ? error.message : 'Failed to save credentials. Please check your inputs and try again.');
    } finally {
      setIsSavingShopify(false);
    }
  };

  return (
    <div className="space-y-6">
      <h2 className="text-3xl font-bold text-gray-900">Settings</h2>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {['General', 'Integrations', 'Billing', 'Widget'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab.toLowerCase().replace(' ', '-'))}
              className={`whitespace-nowrap pb-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === tab.toLowerCase().replace(' ', '-')
                  ? 'border-primary text-primary'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab}
            </button>
          ))}
        </nav>
      </div>

      {/* Content - Showing Integrations Only for MVP */}
      {activeTab === 'integrations' && (
        <div className="space-y-6 max-w-4xl">
          {/* Facebook Messenger */}
          <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
            <div className="flex items-start justify-between">
              <div className="flex items-start space-x-4">
                <div className="p-3 bg-blue-50 rounded-lg text-primary">
                  <Facebook size={24} />
                </div>
                <div>
                  <h3 className="text-lg font-medium text-gray-900">Facebook Messenger</h3>
                  <p className="text-sm text-gray-500 mt-1">
                    Connect the Facebook Page where your bot will live.
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant={facebookConnection.connected ? 'success' : 'outline'}>
                  {facebookConnection.connected ? 'Connected' : 'Not Connected'}
                </Badge>
              </div>
            </div>

            {/* Error Alert */}
            {facebookError && (
              <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-sm font-medium text-red-800">Connection Error</p>
                <p className="text-sm text-red-600">{facebookError}</p>
              </div>
            )}

            {/* Connected State */}
            {facebookConnection.connected ? (
              <div className="mt-4 pt-4 border-t border-gray-200">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    {facebookConnection.pagePictureUrl && (
                      <img
                        src={facebookConnection.pagePictureUrl}
                        alt={facebookConnection.pageName}
                        className="w-10 h-10 rounded-full"
                      />
                    )}
                    <div>
                      <p className="font-medium">{facebookConnection.pageName}</p>
                      <p className="text-sm text-gray-500">Page ID: {facebookConnection.pageId}</p>
                    </div>
                  </div>
                  <Button
                    variant="outline"
                    onClick={handleFacebookDisconnect}
                    disabled={facebookStatus === 'connecting'}
                  >
                    Disconnect
                  </Button>
                </div>
              </div>
            ) : (
              <div className="mt-4 pt-4 border-t border-gray-200">
                <Button
                  onClick={handleFacebookConnect}
                  disabled={facebookStatus === 'connecting'}
                >
                  {facebookStatus === 'connecting' ? 'Connecting...' : 'Connect Page'}
                </Button>

                {/* Advanced Configuration */}
                <div className="mt-4 border border-gray-200 rounded-lg overflow-hidden">
                  <button
                    onClick={() => setShowFacebookConfig(!showFacebookConfig)}
                    className="w-full flex items-center justify-between p-3 bg-gray-50 hover:bg-gray-100 transition-colors"
                  >
                    <span className="text-sm font-medium text-gray-700">
                      Advanced: Configure Facebook App Credentials
                    </span>
                    {showFacebookConfig ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                  </button>

                  {showFacebookConfig && (
                    <div className="p-4 border-t border-gray-200">
                      <form onSubmit={handleSaveFacebookCredentials} className="space-y-4">
                        {/* Instructions */}
                        <div className="p-4 bg-blue-50 rounded-lg space-y-3">
                          <h4 className="font-medium text-blue-900">How to get Facebook App credentials from Meta Business Suite</h4>
                          <ol className="text-sm text-blue-800 space-y-2 list-decimal list-inside">
                            <li>
                              Go to{' '}
                              <a
                                href="https://developers.facebook.com/apps/"
                                target="_blank"
                                rel="noopener noreferrer"
                                className="underline inline-flex items-center gap-1"
                              >
                                Meta for Developers Dashboard
                                <ExternalLink size={12} />
                              </a>
                            </li>
                            <li>
                              <strong>Create a new app</strong> (or select existing):
                              <ul className="list-disc list-inside ml-4 mt-1 text-blue-700">
                                <li>App Type: <strong>Business</strong></li>
                                <li>Provide App Name (e.g., "My Shop Bot")</li>
                              </ul>
                            </li>
                            <li>
                              <strong>Add Messenger product</strong>:
                              <ul className="list-disc list-inside ml-4 mt-1 text-blue-700">
                                <li>Click "Add Product" - Find "Messenger" - Click "Set Up"</li>
                              </ul>
                            </li>
                            <li>
                              <strong>Get your credentials</strong> from Settings - Basic:
                              <ul className="list-disc list-inside ml-4 mt-1 text-blue-700">
                                <li><strong>App ID</strong>: Copy the numeric ID at the top</li>
                                <li><strong>App Secret</strong>: Click "Show" to reveal</li>
                              </ul>
                            </li>
                            <li>
                              <strong>Configure OAuth Redirect</strong>:
                              <ul className="list-disc list-inside ml-4 mt-1 text-blue-700">
                                <li>In Settings - Basic, add this to "Valid OAuth Redirect URIs":</li>
                                <li className="font-mono text-xs bg-blue-100 p-1 rounded mt-1 inline-block">
                                  {window.location.origin}/api/integrations/facebook/callback
                                </li>
                              </ul>
                            </li>
                            <li>
                              <strong>Configure Access Scopes</strong> (in Configuration - API credentials):
                              <ul className="list-disc list-inside ml-4 mt-1 text-green-700">
                                <li><code className="bg-green-100 px-1 rounded">read_products</code> - View products and collections</li>
                                <li><code className="bg-green-100 px-1 rounded">write_products</code> - Required for checkout integration</li>
                                <li><code className="bg-green-100 px-1 rounded">read_inventory</code> - Check stock levels</li>
                                <li><code className="bg-green-100 px-1 rounded">read_orders</code> - View orders, checkouts, transactions</li>
                                <li><code className="bg-green-100 px-1 rounded">read_fulfillments</code> - Check shipping/tracking status</li>
                                <li><code className="bg-green-100 px-1 rounded">read_customers</code> - Look up customer info</li>
                              </ul>
                              <p className="text-xs text-green-600 mt-2 ml-4">
                                <code className="bg-green-100 px-1 rounded">read_all_orders</code> is optional (requires Shopify approval for orders older than 60 days). See{' '}
                                <a 
                                  href="https://shopify.dev/docs/api/usage/access-scopes" 
                                  target="_blank" 
                                  rel="noopener noreferrer"
                                  className="underline"
                                >
                                  Shopify Access Scopes Docs
                                </a>
                                .
                              </p>
                            </li>
                          </ol>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <Label htmlFor="facebook-app-id">App ID</Label>
                            <Input
                              id="facebook-app-id"
                              value={facebookAppId}
                              onChange={(e) => setFacebookAppId(e.target.value)}
                              placeholder="e.g., 123456789012345"
                            />
                          </div>
                          <div>
                            <Label htmlFor="facebook-app-secret">App Secret</Label>
                            <Input
                              id="facebook-app-secret"
                              type="password"
                              value={facebookAppSecret}
                              onChange={(e) => setFacebookAppSecret(e.target.value)}
                              placeholder="e.g., a1b2c3d4e5f6..."
                            />
                          </div>
                        </div>

                        <Button
                          type="submit"
                          disabled={isSavingFacebook || !facebookAppId || !facebookAppSecret}
                          variant="outline"
                        >
                          {isSavingFacebook ? 'Saving...' : 'Save & Connect'}
                        </Button>
                      </form>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Shopify */}
          <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
            <div className="flex items-start justify-between">
              <div className="flex items-start space-x-4">
                <div className="p-3 bg-green-50 rounded-lg text-success">
                  <ShoppingBag size={24} />
                </div>
                <div>
                  <h3 className="text-lg font-medium text-gray-900">Shopify Integration</h3>
                  <p className="text-sm text-gray-500 mt-1">
                    Connect your Shopify store to sync products and orders.
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant={shopifyConnection.connected ? 'success' : 'outline'}>
                  {shopifyConnection.connected ? 'Connected' : 'Not Connected'}
                </Badge>
              </div>
            </div>

            {shopifyError && (
              <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-sm font-medium text-red-800">Connection Error</p>
                <p className="text-sm text-red-600">{shopifyError}</p>
              </div>
            )}

            {shopifyConnection.connected ? (
              <div className="mt-4 pt-4 border-t border-gray-200">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
                      <ShoppingBag size={20} className="text-success" />
                    </div>
                    <div>
                      <p className="font-medium">{shopifyConnection.shopName || 'Shopify Store'}</p>
                      <p className="text-sm text-gray-500">{shopifyConnection.shopDomain}</p>
                    </div>
                  </div>
                  <Button
                    variant="outline"
                    onClick={handleShopifyDisconnect}
                    disabled={shopifyStatus === 'connecting'}
                  >
                    Disconnect
                  </Button>
                </div>

                <div className="mt-6 border border-gray-200 rounded-lg overflow-hidden">
                  <div className="flex items-center justify-between p-4 bg-gray-50">
                    <div className="flex items-center gap-3">
                      <Webhook size={20} className="text-green-600" />
                      <div>
                        <p className="font-medium text-gray-900">Webhook Configuration</p>
                        <p className="text-xs text-gray-500">Required for order sync and inventory updates</p>
                      </div>
                    </div>
                    <Badge variant={shopifyConnection.webhookSubscribed ? 'success' : 'outline'}>
                      {shopifyConnection.webhookSubscribed ? 'Auto-Configured' : 'Manual Setup Required'}
                    </Badge>
                  </div>

                  <div className="p-4 border-t border-gray-200">
                    {shopifyConnection.webhookSubscribed ? (
                      <div className="text-sm text-gray-600">
                        <p className="text-green-700 font-medium mb-2">Webhooks are automatically configured!</p>
                        <p>
                          When you connected your store, we automatically registered webhooks for orders, inventory, and product updates.
                          No manual configuration needed.
                        </p>
                      </div>
                    ) : (
                      <div className="space-y-4">
                        <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg">
                          <p className="text-sm text-amber-800">
                            <strong>Manual webhook setup required.</strong> If webhooks weren't auto-configured during connection,
                            follow the steps below to add them manually in your Shopify admin.
                          </p>
                        </div>

                        <div className="space-y-3">
                          <h4 className="font-medium text-gray-900">How to Add Webhooks in Shopify</h4>
                          <ol className="text-sm text-gray-600 space-y-3 list-decimal list-inside">
                            <li>
                              Go to your{' '}
                              <a
                                href={`https://admin.shopify.com/store/${shopifyConnection.shopDomain?.replace('.myshopify.com', '')}/settings/notifications/webhooks`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="underline inline-flex items-center gap-1 text-green-600"
                              >
                                Shopify Admin → Settings → Notifications → Webhooks
                                <ExternalLink size={12} />
                              </a>
                            </li>
                            <li>
                              Click <strong>&quot;Create webhook&quot;</strong>
                            </li>
                            <li>
                              Add the following webhooks using this URL:
                              <div className="mt-2 p-2 bg-gray-100 rounded font-mono text-xs overflow-x-auto">
                                {window.location.origin}/api/webhooks/shopify
                              </div>
                            </li>
                          </ol>

                          <div className="mt-4">
                            <h5 className="font-medium text-gray-900 mb-2">Required Webhooks</h5>
                            <p className="text-xs text-gray-500 mb-2">
                              For each webhook below, select:
                              <br />• <strong>Event:</strong> (as listed)
                              <br />• <strong>Format:</strong> JSON
                              <br />• <strong>URL:</strong> (the URL above)
                            </p>
                            <div className="bg-gray-50 p-3 rounded-lg space-y-1">
                              <p className="text-sm font-mono">orders/create</p>
                              <p className="text-sm font-mono">orders/updated</p>
                              <p className="text-sm font-mono">orders/cancelled</p>
                              <p className="text-sm font-mono">orders/fulfilled</p>
                              <p className="text-sm font-mono">products/create</p>
                              <p className="text-sm font-mono">products/update</p>
                              <p className="text-sm font-mono">products/delete</p>
                              <p className="text-sm font-mono">inventory_levels/update</p>
                            </div>
                          </div>

                          <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                            <p className="text-sm text-blue-800">
                              <strong>Tip:</strong> After creating each webhook, Shopify will show a <strong>Signing secret</strong>.
                              Keep this secret safe - it&apos;s used to verify webhook authenticity.
                            </p>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ) : (
              <div className="mt-4 pt-4 border-t border-gray-200">
                <div className="flex max-w-md">
                  <input
                    type="text"
                    placeholder="your-store.myshopify.com"
                    value={shopDomain}
                    onChange={(e) => setShopDomain(e.target.value)}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-l-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
                  />
                  <button
                    onClick={handleShopifyConnect}
                    disabled={shopifyStatus === 'connecting' || !shopDomain.trim()}
                    className="px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-r-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {shopifyStatus === 'connecting' ? 'Connecting...' : 'Connect'}
                  </button>
                </div>

                <div className="mt-4 border border-gray-200 rounded-lg overflow-hidden">
                  <button
                    onClick={() => setShowShopifyConfig(!showShopifyConfig)}
                    className="w-full flex items-center justify-between p-3 bg-gray-50 hover:bg-gray-100 transition-colors"
                  >
                    <span className="text-sm font-medium text-gray-700">
                      Advanced: Configure Shopify App Credentials
                    </span>
                    {showShopifyConfig ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                  </button>

                  {showShopifyConfig && (
                    <div className="p-4 border-t border-gray-200">
                      <form onSubmit={handleSaveShopifyCredentials} className="space-y-4">
                        <div className="p-4 bg-green-50 rounded-lg space-y-3">
                          <h4 className="font-medium text-green-900">How to create a Shopify App</h4>
                          <ol className="text-sm text-green-800 space-y-2 list-decimal list-inside">
                            <li>
                              Go to{' '}
                              <a
                                href="https://partners.shopify.com/"
                                target="_blank"
                                rel="noopener noreferrer"
                                className="underline inline-flex items-center gap-1"
                              >
                                Shopify Partners Dashboard
                                <ExternalLink size={12} />
                              </a>
                              {' '}(sign up for a free Partner account if needed)
                            </li>
                            <li>
                              <strong>Navigate to Apps</strong>:
                              <ul className="list-disc list-inside ml-4 mt-1 text-green-700">
                                <li>Click "Apps" in the left sidebar</li>
                                <li>Click "Create app" button</li>
                                <li>Enter an App name (e.g., "My Shop Bot")</li>
                                <li>Click "Create app"</li>
                              </ul>
                            </li>
                            <li>
                              <strong>Configure App URLs</strong>:
                              <ul className="list-disc list-inside ml-4 mt-1 text-green-700">
                                <li>Go to "Configuration" → "App setup"</li>
                                <li>Set App URL to:</li>
                                <li className="font-mono text-xs bg-green-100 p-1 rounded">{window.location.origin}</li>
                                <li className="mt-1">Under "Allowed redirection URL(s)", add:</li>
                                <li className="font-mono text-xs bg-green-100 p-1 rounded mt-1 inline-block">
                                  {window.location.origin}/api/integrations/shopify/callback
                                </li>
                              </ul>
                            </li>
                            <li>
                              <strong>Configure API Access Scopes (IMPORTANT!)</strong>:
                              <ul className="list-disc list-inside ml-4 mt-1 text-green-700">
                                <li>Go to "Configuration" → "API credentials"</li>
                                <li>Under "Admin API access scopes", select ALL of these:</li>
                              </ul>
                              <div className="bg-green-100 p-2 rounded mt-2 ml-4">
                                <p className="font-medium text-green-900 mb-1">Required scopes:</p>
                                <ul className="text-green-800 text-xs space-y-0.5">
                                  <li>✓ read_products</li>
                                  <li>✓ write_products</li>
                                  <li>✓ read_inventory</li>
                                  <li>✓ read_orders</li>
                                  <li>✓ read_fulfillments</li>
                                  <li>✓ read_customers</li>
                                </ul>
                              </div>
                            </li>
                            <li>
                              <strong>Save and Install</strong>:
                              <ul className="list-disc list-inside ml-4 mt-1 text-green-700">
                                <li>Click "Save" at the bottom</li>
                                <li>Go to "Configuration" → "API credentials"</li>
                                <li>Copy the <strong>Client ID</strong> and <strong>Client Secret</strong></li>
                              </ul>
                            </li>
                          </ol>
                          <p className="text-xs text-green-700 mt-2">
                            <strong>Note:</strong> Save credentials below, then enter your store domain (e.g., mystore.myshopify.com) and click Connect.
                          </p>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <Label htmlFor="shopify-api-key">API Key (Client ID)</Label>
                            <Input
                              id="shopify-api-key"
                              value={shopifyApiKey}
                              onChange={(e) => {
                                setShopifyApiKey(e.target.value);
                                if (shopifyCredentialsStatus !== 'idle') {
                                  setShopifyCredentialsStatus('idle');
                                  setShopifyCredentialsMessage('');
                                }
                              }}
                              placeholder="e.g., abc123def456..."
                            />
                          </div>
                          <div>
                            <Label htmlFor="shopify-api-secret">API Secret (Client Secret)</Label>
                            <Input
                              id="shopify-api-secret"
                              type="password"
                              value={shopifyApiSecret}
                              onChange={(e) => {
                                setShopifyApiSecret(e.target.value);
                                if (shopifyCredentialsStatus !== 'idle') {
                                  setShopifyCredentialsStatus('idle');
                                  setShopifyCredentialsMessage('');
                                }
                              }}
                              placeholder="e.g., shpss_xxx..."
                            />
                          </div>
                        </div>

                        <Button
                          type="submit"
                          disabled={isSavingShopify || !shopifyApiKey || !shopifyApiSecret}
                          variant="default"
                          className="bg-green-600 hover:bg-green-700"
                        >
                          {isSavingShopify ? 'Saving...' : 'Save Credentials'}
                        </Button>

                        {shopifyCredentialsStatus === 'success' && (
                          <div className="mt-3 p-3 bg-green-50 border border-green-200 rounded-lg">
                            <p className="text-sm text-green-800 font-medium">{shopifyCredentialsMessage}</p>
                          </div>
                        )}

                        {shopifyCredentialsStatus === 'error' && (
                          <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg">
                            <p className="text-sm text-red-800 font-medium">Error</p>
                            <p className="text-sm text-red-600 mt-1">{shopifyCredentialsMessage}</p>
                          </div>
                        )}
                      </form>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Placeholder for other tabs */}
      {activeTab === 'general' && (
        <div className="bg-white p-8 rounded-xl border border-gray-200 text-center">
          <p className="text-gray-500">General settings coming soon.</p>
        </div>
      )}

      {activeTab === 'billing' && (
        <div className="bg-white p-8 rounded-xl border border-gray-200 text-center">
          <p className="text-gray-500">Billing settings coming soon.</p>
        </div>
      )}

      {activeTab === 'widget' && (
        <div className="space-y-6 max-w-4xl">
          <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
            <div className="flex items-start justify-between">
              <div className="flex items-start space-x-4">
                <div className="p-3 bg-indigo-50 rounded-lg text-indigo-600">
                  <MessageSquare size={24} />
                </div>
                <div>
                  <h3 className="text-lg font-medium text-gray-900">Chat Widget</h3>
                  <p className="text-sm text-gray-500 mt-1">
                    Configure your embeddable chat widget for your website.
                  </p>
                </div>
              </div>
            </div>
            <div className="mt-4 pt-4 border-t border-gray-200">
              <Link
                to="/settings/widget"
                className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-indigo-600 border border-transparent rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                Configure Widget Settings
              </Link>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Settings;
