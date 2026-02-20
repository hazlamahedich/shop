import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Facebook, ShoppingBag, Bot, Eye, EyeOff, ChevronDown, ChevronUp, ExternalLink, MessageSquare } from 'lucide-react';
import { useIntegrationsStore } from '../stores/integrationsStore';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Alert } from '../components/ui/Alert';
import { Input } from '../components/ui/Input';
import { Label } from '../components/ui/Label';

const Settings = () => {
  const [activeTab, setActiveTab] = useState('integrations');
  const [showApiKey, setShowApiKey] = useState(false);
  const [showFacebookConfig, setShowFacebookConfig] = useState(false);
  const [facebookAppId, setFacebookAppId] = useState('');
  const [facebookAppSecret, setFacebookAppSecret] = useState('');
  const [isSavingFacebook, setIsSavingFacebook] = useState(false);

  const {
    facebookStatus,
    facebookConnection,
    facebookError,
    initiateFacebookOAuth,
    checkFacebookStatus,
    disconnectFacebook,
    saveFacebookCredentials,
    clearError,
  } = useIntegrationsStore();

  React.useEffect(() => {
    checkFacebookStatus();
  }, [checkFacebookStatus]);

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
                <Badge variant={facebookConnection.connected ? 'default' : 'secondary'}>
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
                                <li>Click "Add Product" → Find "Messenger" → Click "Set Up"</li>
                              </ul>
                            </li>
                            <li>
                              <strong>Get your credentials</strong> from Settings → Basic:
                              <ul className="list-disc list-inside ml-4 mt-1 text-blue-700">
                                <li><strong>App ID</strong>: Copy the numeric ID at the top</li>
                                <li><strong>App Secret</strong>: Click "Show" to reveal</li>
                              </ul>
                            </li>
                            <li>
                              <strong>Configure OAuth Redirect</strong>:
                              <ul className="list-disc list-inside ml-4 mt-1 text-blue-700">
                                <li>In Settings → Basic, add this to "Valid OAuth Redirect URIs":</li>
                                <li className="font-mono text-xs bg-blue-100 p-1 rounded mt-1 inline-block">
                                  {window.location.origin}/api/integrations/facebook/callback
                                </li>
                              </ul>
                            </li>
                            <li>
                              <strong>Required Permissions</strong> (will be requested during OAuth):
                              <ul className="list-disc list-inside ml-4 mt-1 text-blue-700">
                                <li><code className="bg-blue-100 px-1 rounded">pages_messaging</code></li>
                                <li><code className="bg-blue-100 px-1 rounded">pages_manage_metadata</code></li>
                              </ul>
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
                <div className="flex-1">
                  <h3 className="text-lg font-medium text-gray-900">Shopify Integration</h3>
                  <p className="text-sm text-gray-500 mt-1">Connect your product catalog.</p>

                  <div className="mt-4 flex max-w-md">
                    <input
                      type="text"
                      placeholder="your-store.myshopify.com"
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-l-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
                    />
                    <button className="px-4 py-2 bg-success text-white text-sm font-medium rounded-r-lg hover:bg-green-600 transition-colors">
                      Connect
                    </button>
                  </div>
                </div>
              </div>
            </div>
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
