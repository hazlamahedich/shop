import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Facebook, ShoppingBag, ChevronDown, ExternalLink, MessageSquare, Webhook, Download, Code } from 'lucide-react';
import { useIntegrationsStore } from '../stores/integrationsStore';
import { useAuthStore } from '../stores/authStore';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { ExportButton } from '../components/ExportButton';
import { ModeToggle } from '../components/settings/ModeToggle';
import { ModeChangeDialog } from '../components/settings/ModeChangeDialog';
import { merchantApi } from '../services/merchant';
import { useToast } from '../context/ToastContext';
import type { OnboardingMode } from '../types/onboarding';

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
  
  // Mode toggle state (Story 8.7)
  const [currentMode, setCurrentMode] = useState<OnboardingMode>('ecommerce');
  const [modeDialogOpen, setModeDialogOpen] = useState(false);
  const [targetMode, setTargetMode] = useState<OnboardingMode | null>(null);
  const [modeLoading, setModeLoading] = useState(false);
  const [modeFetching, setModeFetching] = useState(true);
  const { toast } = useToast();

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

  // Load current mode on mount (Story 8.7)
  useEffect(() => {
    const loadMode = async () => {
      setModeFetching(true);
      try {
        const response = await merchantApi.getMerchantMode();
        setCurrentMode(response.onboardingMode);
      } catch (error) {
        console.error('Failed to load merchant mode:', error);
        // Use default mode if loading fails
      } finally {
        setModeFetching(false);
      }
    };
    loadMode();
  }, []);

  React.useEffect(() => {
    checkFacebookStatus();
    checkShopifyStatus();
  }, [checkFacebookStatus, checkShopifyStatus]);

  // Mode change handlers (Story 8.7)
  const handleModeChangeRequest = (newMode: OnboardingMode) => {
    setTargetMode(newMode);
    setModeDialogOpen(true);
  };

  const handleModeChangeConfirm = async () => {
    if (!targetMode) return;
    
    setModeLoading(true);
    try {
      await merchantApi.updateMerchantMode(targetMode);
      
      const successMessage = targetMode === 'general'
        ? 'Mode updated! E-commerce features disabled. Your store data is preserved. Refreshing page...'
        : 'Mode updated! E-commerce features are now enabled. Refreshing page...';
      
      toast(successMessage, 'success', 3000);
      
      setModeDialogOpen(false);
      
      // Reload page after a short delay to show toast
      setTimeout(() => {
        window.location.reload();
      }, 500);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to update mode. Please try again later.';
      toast(errorMessage, 'error');
    } finally {
      setModeLoading(false);
    }
  };

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
    <div className="space-y-12 animate-in fade-in slide-in-from-bottom-8 duration-1000 max-w-5xl pb-20">
      <div className="flex flex-col gap-3">
        <h2 className="text-5xl font-black text-emerald-50 tracking-tight mantis-glow-text">
          Control Center
        </h2>
        <p className="text-emerald-900/60 font-medium leading-relaxed max-w-2xl text-lg">
          Master your shop configuration. Orchestrate integrations, manage intelligent fulfillment, and fine-tune your autonomous agent.
        </p>
      </div>

      {/* Tabs */}
      <div className="border-b border-emerald-500/10 mb-6">
        <nav className="-mb-px flex space-x-12">
          {['General', 'Integrations', 'Shipping', 'Billing', 'Widget'].map((tab) => {
            const tabId = tab.toLowerCase().replace(' ', '-');
            const isActive = activeTab === tabId;
            return (
              <button
                key={tab}
                onClick={() => setActiveTab(tabId)}
                className={`whitespace-nowrap pb-5 px-2 border-b-2 font-black text-[11px] uppercase tracking-[0.25em] transition-all duration-500 relative group ${
                  isActive
                    ? 'border-emerald-500 text-emerald-400 mantis-glow-text'
                    : 'border-transparent text-emerald-900/30 hover:text-emerald-900/60'
                }`}
              >
                {tab}
                {isActive && (
                  <span className="absolute inset-x-0 -bottom-px h-1 bg-emerald-500 shadow-[0_0_20px_rgba(16,185,129,0.5)] rounded-full" />
                )}
                {!isActive && (
                  <span className="absolute inset-x-0 -bottom-px h-1 bg-emerald-500/0 group-hover:bg-emerald-500/20 transition-all duration-500 rounded-full" />
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Content - Showing Integrations Only for MVP */}
      {activeTab === 'integrations' && (
        <div className="space-y-10">
          {/* Facebook Messenger */}
          <div className="bg-[#0a0a0a]/60 backdrop-blur-2xl border border-blue-500/10 p-10 rounded-[40px] shadow-2xl relative overflow-hidden group transition-all duration-500 hover:border-blue-500/20">
            <div className="absolute top-0 right-0 w-80 h-80 bg-blue-500/5 rounded-full -mr-40 -mt-40 blur-[120px] transition-all duration-700 group-hover:bg-blue-500/10" />
            
            <div className="flex flex-col md:flex-row md:items-start justify-between gap-10 relative z-10">
              <div className="flex items-start space-x-8">
                <div className="p-6 bg-blue-500/10 rounded-3xl text-blue-400 border border-blue-500/20 shadow-[0_0_30px_rgba(59,130,246,0.1)] backdrop-blur-md transition-all duration-700 group-hover:scale-105 group-hover:rotate-3">
                  <Facebook size={36} />
                </div>
                <div>
                  <h3 className="text-3xl font-black text-emerald-50 tracking-tight mb-2">Facebook Messenger</h3>
                  <p className="text-base text-emerald-900/40 font-medium leading-relaxed max-w-md">
                    Synchronize your Facebook Page. Turn every interaction into a seamless conversational commerce opportunity.
                  </p>
                </div>
              </div>
              <div className="flex items-center">
                <Badge 
                  variant={facebookConnection.connected ? 'success' : 'outline'}
                  className={`font-black uppercase tracking-[0.2em] text-[10px] px-6 py-2 rounded-2xl border shadow-2xl transition-all duration-500 ${
                    facebookConnection.connected 
                      ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' 
                      : 'bg-[#111] text-zinc-500 border-white/5'
                  }`}
                >
                  {facebookConnection.connected ? 'Operational' : 'Disconnected'}
                </Badge>
              </div>
            </div>

            {/* Error Alert */}
            {facebookError && (
              <div className="mt-10 p-6 bg-red-500/5 border border-red-500/10 rounded-3xl animate-in shake duration-700 backdrop-blur-md">
                <div className="flex items-center gap-3 text-red-400 mb-2">
                  <div className="w-2 h-2 rounded-full bg-red-500 shadow-[0_0_10px_rgba(239,68,68,0.8)]" />
                  <p className="text-[10px] font-black uppercase tracking-[0.3em]">Integrity Fault Detected</p>
                </div>
                <p className="text-sm text-red-400/80 font-medium leading-relaxed ml-5">{facebookError}</p>
              </div>
            )}

            {/* Connected State */}
            {facebookConnection.connected ? (
              <div className="mt-10 pt-10 border-t border-emerald-500/10 relative z-10">
                <div className="flex items-center justify-between bg-white/[0.02] p-6 rounded-3xl border border-white/5">
                  <div className="flex items-center gap-5">
                    {facebookConnection.pagePictureUrl && (
                      <div className="relative">
                        <img
                          src={facebookConnection.pagePictureUrl}
                          alt={facebookConnection.pageName}
                          className="w-14 h-14 rounded-2xl border-2 border-emerald-500/20 shadow-xl"
                        />
                        <div className="absolute -bottom-1 -right-1 w-5 h-5 bg-emerald-500 rounded-full border-4 border-[#0a0a0a] flex items-center justify-center text-[8px] text-white font-bold">✓</div>
                      </div>
                    )}
                    <div>
                      <p className="text-lg font-bold text-emerald-50 tracking-tight">{facebookConnection.pageName}</p>
                      <p className="text-xs font-mono text-emerald-900/40 uppercase tracking-tighter mt-1">Page ID: {facebookConnection.pageId}</p>
                    </div>
                  </div>
                  <Button
                    variant="outline"
                    onClick={handleFacebookDisconnect}
                    disabled={facebookStatus === 'connecting'}
                    className="border-red-500/20 text-red-400 hover:bg-red-500/10 hover:border-red-500/30 rounded-2xl font-bold uppercase tracking-widest text-[10px] px-6 py-2 transition-all"
                  >
                    Disconnect
                  </Button>
                </div>
              </div>
            ) : (
              <div className="mt-8 pt-8 border-t border-white/5 relative z-10">
                <Button
                  onClick={handleFacebookConnect}
                  disabled={facebookStatus === 'connecting'}
                  className="bg-blue-600 hover:bg-blue-500 text-white font-bold px-8 shadow-[0_0_20px_rgba(37,99,235,0.3)] transition-all hover:shadow-[0_0_30px_rgba(37,99,235,0.5)]"
                >
                  {facebookStatus === 'connecting' ? 'Connecting...' : 'Connect Page'}
                </Button>

                {/* Advanced Configuration */}
                <div className="mt-8 border border-white/5 rounded-[32px] overflow-hidden bg-white/[0.02] backdrop-blur-xl transition-all duration-500 hover:border-blue-500/20 shadow-inner">
                  <button
                    onClick={() => setShowFacebookConfig(!showFacebookConfig)}
                    className="w-full flex items-center justify-between p-6 bg-white/[0.03] hover:bg-white/[0.05] transition-all group/btn"
                  >
                    <span className="text-[10px] font-bold text-emerald-900/60 uppercase tracking-[0.2em]">
                      Advanced Config: Meta App Credentials
                    </span>
                    <div className={`p-2 rounded-xl transition-all duration-500 ${showFacebookConfig ? 'bg-blue-500/20 text-blue-400 rotate-180' : 'bg-white/5 text-emerald-900/40 group-hover/btn:bg-white/10'}`}>
                      <ChevronDown size={16} />
                    </div>
                  </button>

                  {showFacebookConfig && (
                    <div className="p-8 border-t border-white/5 space-y-8 animate-in slide-in-from-top-4 duration-500">
                      {/* Instructions */}
                      <div className="p-6 bg-blue-500/5 rounded-[24px] border border-blue-500/10 space-y-4">
                        <h4 className="text-sm font-bold text-blue-400 uppercase tracking-widest flex items-center gap-2">
                          <Code size={16} />
                          Meta Developers Setup
                        </h4>
                        <ol className="text-xs text-emerald-900/60 space-y-3 font-medium leading-relaxed list-decimal list-inside marker:text-blue-500/50">
                          <li>
                            Access the{' '}
                            <a
                              href="https://developers.facebook.com/apps/"
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-blue-400 underline decoration-blue-500/30 hover:decoration-blue-400 transition-all font-bold"
                            >
                              Meta Developers Dashboard
                              <ExternalLink size={10} className="inline ml-1" />
                            </a>
                          </li>
                          <li>
                            Create a **Business** app type &rarr; App Settings &rarr; Basic &rarr; Add **Website** platform &rarr; Site URL: <code className="bg-white/5 px-2 py-0.5 rounded text-blue-400 border border-white/10">{window.location.origin}</code>
                          </li>
                          <li>
                            Add **Messenger** product &rarr; Generate/Link your Page Access Token.
                          </li>
                          <li>
                            Copy **App ID** and **App Secret** into the fields below.
                          </li>
                          <li>
                            Add <span className="text-emerald-50 bg-white/5 px-2 py-0.5 rounded border border-white/10 font-mono text-[10px]">{window.location.origin}/api/integrations/facebook/callback</span> to **Valid OAuth Redirect URIs**.
                          </li>
                        </ol>
                      </div>

                      <form onSubmit={handleSaveFacebookCredentials} className="space-y-6">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                          <div className="space-y-2">
                            <Label htmlFor="facebook-app-id" className="text-[10px] uppercase tracking-widest text-emerald-900/40 font-bold ml-1">App ID</Label>
                            <Input
                              id="facebook-app-id"
                              value={facebookAppId}
                              onChange={(e) => setFacebookAppId(e.target.value)}
                              placeholder="e.g., 123456789012345"
                              className="bg-white/5 border-white/10 text-emerald-50 rounded-2xl h-12 focus:ring-blue-500/20 focus:border-blue-500/50 transition-all"
                            />
                          </div>
                          <div className="space-y-2">
                            <Label htmlFor="facebook-app-secret" className="text-[10px] uppercase tracking-widest text-emerald-900/40 font-bold ml-1">App Secret</Label>
                            <Input
                              id="facebook-app-secret"
                              type="password"
                              value={facebookAppSecret}
                              onChange={(e) => setFacebookAppSecret(e.target.value)}
                              placeholder="••••••••••••••••"
                              className="bg-white/5 border-white/10 text-emerald-50 rounded-2xl h-12 focus:ring-blue-500/20 focus:border-blue-500/50 transition-all"
                            />
                          </div>
                        </div>

                        <Button
                          type="submit"
                          disabled={isSavingFacebook || !facebookAppId || !facebookAppSecret}
                          className="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold h-12 rounded-2xl shadow-[0_0_20px_rgba(37,99,235,0.2)] transition-all"
                        >
                          {isSavingFacebook ? 'Processing...' : 'Secure & Connect'}
                        </Button>
                      </form>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Shopify */}
          <div className="bg-[#0a0a0a]/60 backdrop-blur-2xl border border-emerald-500/10 p-10 rounded-[40px] shadow-2xl relative overflow-hidden group transition-all duration-500 hover:border-emerald-500/20">
            <div className="absolute top-0 right-0 w-80 h-80 bg-emerald-500/5 rounded-full -mr-40 -mt-40 blur-[120px] transition-all duration-700 group-hover:bg-emerald-500/10" />
            
            <div className="flex flex-col md:flex-row md:items-start justify-between gap-10 relative z-10">
              <div className="flex items-start space-x-8">
                <div className="p-6 bg-emerald-500/10 rounded-3xl text-emerald-400 border border-emerald-500/20 shadow-[0_0_30px_rgba(16,185,129,0.1)] backdrop-blur-md transition-all duration-700 group-hover:scale-105 group-hover:-rotate-3">
                  <ShoppingBag size={36} />
                </div>
                <div>
                  <h3 className="text-3xl font-black text-emerald-50 tracking-tight mb-2">Shopify Core</h3>
                  <p className="text-base text-emerald-900/40 font-medium leading-relaxed max-w-md">
                    Bridge your inventory and orders. Empower your and agent with real-time shop intelligence.
                  </p>
                </div>
              </div>
              <div className="flex items-center">
                <Badge 
                  variant={shopifyConnection.connected ? 'success' : 'outline'}
                  className={`font-black uppercase tracking-[0.2em] text-[10px] px-6 py-2 rounded-2xl border shadow-2xl transition-all duration-500 ${
                    shopifyConnection.connected 
                      ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' 
                      : 'bg-[#111] text-zinc-500 border-white/5'
                  }`}
                >
                  {shopifyConnection.connected ? 'Synchronized' : 'Disconnected'}
                </Badge>
              </div>
            </div>

            {shopifyError && (
              <div className="mt-10 p-6 bg-red-500/5 border border-red-500/10 rounded-3xl animate-in shake duration-700 backdrop-blur-md">
                <div className="flex items-center gap-3 text-red-400 mb-2">
                  <div className="w-2 h-2 rounded-full bg-red-500 shadow-[0_0_10px_rgba(239,68,68,0.8)]" />
                  <p className="text-[10px] font-black uppercase tracking-[0.3em]">Logic Fault Detected</p>
                </div>
                <p className="text-sm text-red-400/80 font-medium leading-relaxed ml-5">{shopifyError}</p>
              </div>
            )}

            {shopifyConnection.connected ? (
              <div className="mt-10 pt-10 border-t border-emerald-500/10 relative z-10">
                <div className="flex items-center justify-between bg-white/[0.02] p-8 rounded-[32px] border border-white/5 shadow-inner backdrop-blur-sm group/store">
                  <div className="flex items-center gap-6">
                    <div className="w-16 h-16 bg-emerald-500/10 rounded-[22px] flex items-center justify-center border border-emerald-500/20 shadow-xl transition-all duration-500 group-hover/store:bg-emerald-500/20">
                      <ShoppingBag size={28} className="text-emerald-500 shadow-glow" />
                    </div>
                    <div>
                      <p className="text-xl font-black text-emerald-50 tracking-tight">{shopifyConnection.shopName || 'Shopify Store'}</p>
                      <p className="text-xs font-mono text-emerald-900/40 uppercase tracking-[0.1em] mt-1">{shopifyConnection.shopDomain}</p>
                    </div>
                  </div>
                  <Button
                    variant="outline"
                    onClick={handleShopifyDisconnect}
                    disabled={shopifyStatus === 'connecting'}
                    className="border-red-500/20 text-red-400 hover:bg-red-500/10 hover:border-red-500/30 rounded-2xl font-black uppercase tracking-[0.15em] text-[10px] px-8 py-3 transition-all h-auto"
                  >
                    Disconnect
                  </Button>
                </div>

                <div className="mt-6 border border-gray-200 rounded-lg overflow-hidden">
                  <div className="flex items-center justify-between p-6 bg-white/[0.02]">
                    <div className="flex items-center gap-4">
                      <Webhook size={24} className="text-emerald-400" />
                      <div>
                        <p className="font-bold text-slate-100 uppercase tracking-widest text-xs">Webhook Configuration</p>
                        <p className="text-xs text-slate-500 font-medium mt-0.5">Required for order sync and inventory updates</p>
                      </div>
                    </div>
                    <Badge variant={shopifyConnection.webhookSubscribed ? 'success' : 'outline'} className="font-bold uppercase tracking-tighter shadow-lg">
                      {shopifyConnection.webhookSubscribed ? 'Auto-Configured' : 'Manual Setup Required'}
                    </Badge>
                  </div>

                  <div className="p-4 border-t border-gray-200">
                    {shopifyConnection.webhookSubscribed ? (
                      <div className="text-sm text-gray-600">
                        <p className="text-slate-400 font-medium font-medium mb-2">Webhooks are automatically configured!</p>
                        <p>
                          When you connected your store, we automatically registered webhooks for orders, inventory, and product updates.
                          No manual configuration needed.
                        </p>
                      </div>
                    ) : (
                      <div className="space-y-4">
                        <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg">
                          <p className="text-sm text-amber-400 font-medium">
                            <strong className="text-amber-300">Manual webhook setup required.</strong> If webhooks weren&apos;t auto-configured during connection,
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
                                Shopify Admin &rarr; Settings &rarr; Notifications &rarr; Webhooks
                                <ExternalLink size={12} />
                              </a>
                            </li>
                            <li>
                              Click <strong>&quot;Create webhook&quot;</strong>
                            </li>
                            <li>
                                 Add the following webhooks using this URL:
                                <div className="mt-4 p-4 bg-white/10 rounded-2xl font-mono text-xs overflow-x-auto text-emerald-400 border border-white/10 shadow-inner">
                                  {window.location.origin}/api/webhooks/shopify
                                </div>
                              </li>
                            </ol>

                            <div className="mt-4">
                              <h5 className="font-medium text-gray-900 mb-2">Required Webhooks</h5>
                              <p className="text-xs text-gray-500 mb-2">
                                For each webhook below, select:
                                <br />&bull; <strong>Event:</strong> (as listed)
                                <br />&bull; <strong>Format:</strong> JSON
                                <br />&bull; <strong>URL:</strong> (the URL above)
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
                                <p className="text-sm font-mono">inventory_items/update</p>
                                <p className="text-sm font-mono">customers/create</p>
                                <p className="text-sm font-mono">checkouts/create</p>
                                <p className="text-sm font-mono">checkouts/update</p>
                              </div>
                          <div className="mt-8 p-6 bg-amber-500/5 border border-amber-500/10 rounded-2xl backdrop-blur-md">
                            <p className="text-sm text-amber-400 font-medium">
                              <strong className="text-amber-300">Note:</strong> <code className="bg-white/5 border border-white/10 px-1 rounded text-emerald-400">disputes/create</code> is optional &mdash; only for stores using Shopify Payments.
                            </p>
                          </div>
                                                  <div className="mt-8 p-6 bg-blue-500/5 border border-blue-500/10 rounded-2xl backdrop-blur-md">
                            <p className="text-sm text-blue-400 font-medium">
                              <strong className="text-blue-300">Tip:</strong> After creating each webhook, Shopify will show a <strong>Signing secret</strong>.
                              Keep this secret safe &mdash; it&apos;s used to verify webhook authenticity.
                            </p>
                          </div>
                           <div className="mt-6 p-6 bg-emerald-500/5 border border-emerald-500/10 rounded-2xl backdrop-blur-md">
                            <p className="text-sm text-emerald-400 font-medium">
                              <strong className="text-emerald-300">Storefront API:</strong> To enable the chat widget on external websites, enable the 
                              Storefront API in your Shopify Admin under <strong>Apps &rarr; App development</strong> &rarr; 
                              select your app &rarr; <strong>Configuration &rarr; API credentials &rarr; Storefront API</strong>.
                            </p>
                          </div>
               </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ) : (
              <div className="mt-8 pt-8 border-t border-white/5 relative z-10">
                <div className="flex max-w-md gap-2">
                  <Input
                    type="text"
                    placeholder="your-store.myshopify.com"
                    value={shopDomain}
                    onChange={(e) => setShopDomain(e.target.value)}
                    className="flex-1 bg-white/5 border-white/10 text-slate-100 placeholder:text-slate-500 rounded-xl focus:ring-emerald-500/20 focus:border-emerald-500"
                  />
                  <Button
                    onClick={handleShopifyConnect}
                    disabled={shopifyStatus === 'connecting' || !shopDomain.trim()}
                    className="bg-emerald-600 hover:bg-emerald-500 text-white font-bold px-6 shadow-[0_0_20px_rgba(16,185,129,0.3)] transition-all hover:shadow-[0_0_30px_rgba(16,185,129,0.5)]"
                  >
                    {shopifyStatus === 'connecting' ? 'Connecting...' : 'Connect'}
                  </Button>
                </div>

                <div className="mt-8 border border-white/5 rounded-[32px] overflow-hidden bg-white/[0.02] backdrop-blur-xl transition-all duration-500 hover:border-emerald-500/20 shadow-inner">
                  <button
                    onClick={() => setShowShopifyConfig(!showShopifyConfig)}
                    className="w-full flex items-center justify-between p-6 bg-white/[0.03] hover:bg-white/[0.05] transition-all group/btn"
                  >
                    <span className="text-[10px] font-bold text-emerald-900/60 uppercase tracking-[0.2em]">
                      Advanced Config: Shopify API Credentials
                    </span>
                    <div className={`p-2 rounded-xl transition-all duration-500 ${showShopifyConfig ? 'bg-emerald-500/20 text-emerald-400 rotate-180' : 'bg-white/5 text-emerald-900/40 group-hover/btn:bg-white/10'}`}>
                      <ChevronDown size={16} />
                    </div>
                  </button>

                  {showShopifyConfig && (
                    <div className="p-8 border-t border-white/5 space-y-8 animate-in slide-in-from-top-4 duration-500">
                      <div className="p-6 bg-emerald-500/5 rounded-[24px] border border-emerald-500/10 space-y-4">
                        <h4 className="text-sm font-bold text-emerald-400 uppercase tracking-widest flex items-center gap-2">
                          <ShoppingBag size={16} />
                          Shopify Partner Setup
                        </h4>
                        <ol className="text-xs text-emerald-900/60 space-y-4 font-medium leading-relaxed list-decimal list-inside marker:text-emerald-500/50">
                          <li>
                            **Create App** in Shopify Admin &rarr; Apps &rarr; App development.
                          </li>
                          <li>
                            Set App URL to <code className="bg-white/5 px-2 py-0.5 rounded text-emerald-400 border border-white/10">{window.location.origin}</code>
                          </li>
                          <li>
                            Add Redirection URL: <span className="text-emerald-50 bg-white/5 px-2 py-0.5 rounded border border-white/10 font-mono text-[10px]">{window.location.origin}/api/integrations/shopify/callback</span>
                          </li>
                          <li>
                            **Permissions**: Enable all required scopes (`products`, `orders`, `customers`, etc).
                          </li>
                          <li>
                            Copy **Client ID** and **Client Secret** (API Key/Secret).
                          </li>
                        </ol>
                      </div>

                      <form onSubmit={handleSaveShopifyCredentials} className="space-y-6">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                          <div className="space-y-2">
                            <Label htmlFor="shopify-api-key" className="text-[10px] uppercase tracking-widest text-emerald-900/40 font-bold ml-1">Client ID</Label>
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
                              placeholder="e.g., abc123def..."
                              className="bg-white/5 border-white/10 text-emerald-50 rounded-2xl h-12 focus:ring-emerald-500/20 focus:border-emerald-500/50 transition-all"
                            />
                          </div>
                          <div className="space-y-2">
                            <Label htmlFor="shopify-api-secret" className="text-[10px] uppercase tracking-widest text-emerald-900/40 font-bold ml-1">Client Secret</Label>
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
                              placeholder="shpss_••••••••"
                              className="bg-white/5 border-white/10 text-emerald-50 rounded-2xl h-12 focus:ring-emerald-500/20 focus:border-emerald-500/50 transition-all"
                            />
                          </div>
                        </div>

                        <Button
                          type="submit"
                          disabled={isSavingShopify || !shopifyApiKey || !shopifyApiSecret}
                          className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold h-12 rounded-2xl shadow-[0_0_20px_rgba(16,185,129,0.2)] transition-all"
                        >
                          {isSavingShopify ? 'Saving...' : 'Authorize Shopify Access'}
                        </Button>

                        {shopifyCredentialsStatus === 'success' && (
                          <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-2xl animate-in fade-in duration-500">
                            <p className="text-sm text-emerald-400 font-bold flex items-center gap-2 italic">
                              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                              {shopifyCredentialsMessage}
                            </p>
                          </div>
                        )}

                        {shopifyCredentialsStatus === 'error' && (
                          <div className="p-4 bg-red-500/5 border border-red-500/10 rounded-2xl animate-in shake duration-500">
                            <p className="text-xs font-bold text-red-400 uppercase tracking-widest">Update Failed</p>
                            <p className="text-sm text-red-400 mt-1 font-medium">{shopifyCredentialsMessage}</p>
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
      {activeTab === 'shipping' && (
        <div className="space-y-10 max-w-4xl animate-in fade-in duration-1000">
          <div className="bg-[#0a0a0a]/60 backdrop-blur-2xl border border-emerald-500/10 p-10 rounded-[40px] shadow-2xl relative overflow-hidden group hover:border-emerald-500/20 transition-all duration-500">
            <div className="absolute top-0 right-0 w-48 h-48 bg-emerald-500/5 rounded-full -mr-24 -mt-24 blur-3xl transition-all duration-700 group-hover:bg-emerald-500/10" />
            
            <div className="flex items-start justify-between relative z-10">
              <div className="flex items-start space-x-8">
                <div className="p-6 bg-emerald-500/10 rounded-3xl text-emerald-400 border border-emerald-500/20 shadow-2xl backdrop-blur-md transition-all duration-700 group-hover:scale-105 group-hover:rotate-6">
                  <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 18V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v11a1 1 0 0 0 1 1h2"/><path d="M15 18H9"/><path d="M19 18h2a1 1 0 0 0 1-1v-3.65a1 1 0 0 0-.22-.624l-3.48-4.35A1 1 0 0 0 17.52 8H14"/><circle cx="17" cy="18" r="2"/><circle cx="7" cy="18" r="2"/></svg>
                </div>
                <div>
                  <h3 className="text-3xl font-black text-emerald-50 tracking-tight mb-2">Shipping Logistics</h3>
                  <p className="text-base text-emerald-900/40 font-medium leading-relaxed max-w-md">
                    Orchestrate custom carriers for dynamic order tracking. Streamline fulfillment transparency.
                  </p>
                </div>
              </div>
            </div>
            <div className="mt-10 pt-10 border-t border-white/5 relative z-10">
              <Link
                to="/settings/shipping"
                className="inline-flex items-center gap-3 px-10 py-4 text-[11px] font-black uppercase tracking-[0.2em] text-white bg-emerald-600 border border-transparent rounded-2xl hover:bg-emerald-500 transition-all shadow-2xl hover:shadow-emerald-500/40"
              >
                Enter Logistics Control
              </Link>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'general' && (
        <div className="space-y-10 max-w-4xl animate-in fade-in duration-1000">
          {/* Mode Toggle Section (Story 8.7) */}
          <div className="bg-[#0a0a0a]/60 backdrop-blur-2xl border border-indigo-500/10 p-10 rounded-[40px] shadow-2xl relative overflow-hidden group hover:border-indigo-500/20 transition-all duration-500">
            <div className="absolute top-0 right-0 w-48 h-48 bg-indigo-500/5 rounded-full -mr-24 -mt-24 blur-3xl transition-all duration-700 group-hover:bg-indigo-500/10" />
            
            <div className="flex items-start space-x-8 relative z-10">
              <div className="p-6 bg-indigo-500/10 rounded-3xl text-indigo-400 border border-indigo-500/20 shadow-2xl backdrop-blur-md transition-all duration-700 group-hover:scale-110">
                <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/></svg>
              </div>
              <div className="flex-1">
                <h3 className="text-3xl font-black text-emerald-50 tracking-tight mb-2">Neural Operating Mode</h3>
                <p className="text-base text-emerald-900/40 font-medium leading-relaxed max-w-md">
                  Toggle between general-purpose conversational logic and e-commerce specialized reasoning hooks.
                </p>
                <div className="mt-10 bg-white/5 p-8 rounded-[32px] border border-white/5 shadow-inner">
                  <ModeToggle
                    currentMode={currentMode}
                    onModeChange={handleModeChangeRequest}
                    loading={modeLoading}
                    fetching={modeFetching}
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Data Export Section */}
          <div className="bg-[#0a0a0a]/60 backdrop-blur-2xl border border-purple-500/10 p-10 rounded-[40px] shadow-2xl relative overflow-hidden group hover:border-purple-500/20 transition-all duration-500">
            <div className="absolute top-0 right-0 w-48 h-48 bg-purple-500/5 rounded-full -mr-24 -mt-24 blur-3xl transition-all duration-700 group-hover:bg-purple-500/10" />
            
            <div className="flex items-start space-x-8 relative z-10">
              <div className="p-6 bg-purple-500/10 rounded-3xl text-purple-400 border border-purple-500/20 shadow-2xl backdrop-blur-md transition-all duration-700 group-hover:scale-105 group-hover:-rotate-3">
                <Download size={32} />
              </div>
              <div className="flex-1">
                <h3 className="text-3xl font-black text-emerald-50 tracking-tight mb-2">Data Integrity & Export</h3>
                <p className="text-sm text-emerald-900/40 font-medium leading-relaxed max-w-md">
                  Archive and secure your information. Full GDPR/CCPA compliant data synchronization and export facility.
                </p>
                <div className="mt-10">
                  {merchant?.id ? (
                    <ExportButton merchantId={merchant.id} />
                  ) : (
                    <div className="bg-red-500/5 border border-red-500/10 rounded-2xl p-6 text-center">
                      <p className="text-[10px] font-black uppercase tracking-[0.3em] text-red-400">Authentication Required</p>
                      <p className="text-xs text-red-400/60 font-medium mt-1 italic">Please log in to initiate data extraction protocols.</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'billing' && (
        <div className="flex flex-col items-center justify-center py-24 animate-in fade-in slide-in-from-bottom-8 duration-1000">
          <div className="bg-[#0a0a0a]/80 backdrop-blur-3xl border border-blue-500/20 p-16 rounded-[48px] shadow-2xl text-center max-w-2xl relative group overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-blue-600/5 via-transparent to-transparent opacity-50" />
            <div className="bg-blue-500/10 w-24 h-24 rounded-[32px] flex items-center justify-center mx-auto mb-10 border border-blue-500/20 shadow-2xl backdrop-blur-md transition-all duration-700 group-hover:scale-110">
              <Webhook size={48} className="text-blue-400 animate-pulse" />
            </div>
            <h3 className="text-4xl font-black text-emerald-50 tracking-tight mb-4 mantis-glow-text underline underline-offset-8 decoration-blue-500/30">Finance Module</h3>
            <p className="text-emerald-900/40 font-black uppercase tracking-[0.4em] text-[10px] mb-4">Core Systems Off-line</p>
            <p className="text-emerald-900/60 font-medium leading-relaxed">
              The billing infrastructure is undergoing primary initialization. Commercial hook-ins will be deployed in the next update cycle.
            </p>
          </div>
        </div>
      )}

      {activeTab === 'widget' && (
        <div className="space-y-10 max-w-4xl animate-in fade-in duration-1000">
          <div className="bg-[#0a0a0a]/60 backdrop-blur-2xl border border-indigo-500/10 p-10 rounded-[40px] shadow-2xl relative overflow-hidden group hover:border-indigo-500/20 transition-all duration-500">
            <div className="absolute top-0 right-0 w-48 h-48 bg-indigo-500/5 rounded-full -mr-24 -mt-24 blur-3xl transition-all duration-700 group-hover:bg-indigo-500/10" />
            
            <div className="flex items-start justify-between relative z-10">
              <div className="flex items-start space-x-8">
                <div className="p-6 bg-indigo-500/10 rounded-3xl text-indigo-400 border border-indigo-500/20 shadow-2xl backdrop-blur-md transition-all duration-700 group-hover:scale-105 group-hover:rotate-6">
                  <MessageSquare size={32} />
                </div>
                <div>
                  <h3 className="text-3xl font-black text-emerald-50 tracking-tight mb-2">Widget Interface</h3>
                  <p className="text-base text-emerald-900/40 font-medium leading-relaxed max-w-md">
                    Customize the visual DNA of your embedded chat experience. Control brand alignment and interaction logic.
                  </p>
                </div>
              </div>
            </div>
            <div className="mt-10 pt-10 border-t border-white/5 relative z-10">
              <Link
                to="/settings/widget"
                className="inline-flex items-center gap-3 px-10 py-4 text-[11px] font-black uppercase tracking-[0.2em] text-white bg-indigo-600 border border-transparent rounded-2xl hover:bg-indigo-500 transition-all shadow-2xl hover:shadow-indigo-500/40"
              >
                Modify Interface DNA
              </Link>
            </div>
          </div>
        </div>
      )}
      
      {/* Mode Change Dialog (Story 8.7) */}
      {targetMode && (
        <ModeChangeDialog
          isOpen={modeDialogOpen}
          onClose={() => {
            setModeDialogOpen(false);
            setTargetMode(null);
          }}
          onConfirm={handleModeChangeConfirm}
          currentMode={currentMode}
          targetMode={targetMode}
          loading={modeLoading}
        />
      )}
    </div>
  );
};

export default Settings;
