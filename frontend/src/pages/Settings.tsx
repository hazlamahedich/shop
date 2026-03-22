import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Facebook, ShoppingBag, ChevronDown, ExternalLink, MessageSquare, Webhook, Download, Code, ShieldCheck, ToggleRight, Loader2 } from 'lucide-react';
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
  
  // Mode toggle state
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

  useEffect(() => {
    const loadMode = async () => {
      setModeFetching(true);
      try {
        const response = await merchantApi.getMerchantMode();
        setCurrentMode(response.onboardingMode);
      } catch (error) {
        console.error('Failed to load merchant mode:', error);
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
      setTimeout(() => {
        window.location.reload();
      }, 500);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to update mode.';
      toast(errorMessage, 'error');
    } finally {
      setModeLoading(false);
    }
  };

  const handleFacebookConnect = () => { clearError(); initiateFacebookOAuth(); };
  const handleFacebookDisconnect = async () => { clearError(); await disconnectFacebook(); };
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
    clearShopifyError(); await disconnectShopify(); setShopDomain('');
  };
  const handleSaveShopifyCredentials = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!shopifyApiKey || !shopifyApiSecret) return;
    setIsSavingShopify(true);
    setShopifyCredentialsStatus('idle'); setShopifyCredentialsMessage('');
    try {
      await saveShopifyCredentials(shopifyApiKey, shopifyApiSecret);
      setShopifyCredentialsStatus('success');
      setShopifyCredentialsMessage('Credentials saved successfully! You can now connect your store.');
    } catch (error) {
      setShopifyCredentialsStatus('error');
      setShopifyCredentialsMessage(error instanceof Error ? error.message : 'Failed to save credentials.');
    } finally {
      setIsSavingShopify(false);
    }
  };

  return (
    <div className="animate-in fade-in slide-in-from-bottom-8 duration-1000 max-w-6xl mx-auto pb-20 font-body text-on-surface">
      {/* Page Header */}
      <div className="mb-10 flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div>
          <h1 className="font-headline text-5xl font-bold tracking-tighter mb-2 text-on-surface">
            Control <span className="text-primary-container">Center</span>
          </h1>
          <p className="text-on-surface-variant max-w-lg">
            Master your shop configuration. Orchestrate integrations, manage intelligent fulfillment, and fine-tune your autonomous agent.
          </p>
        </div>

        {/* Segmented Tabs */}
        <div className="glass-panel p-1 rounded-xl flex gap-1 overflow-x-auto max-w-full">
          {['General', 'Integrations', 'Shipping', 'Billing', 'Widget'].map((tab) => {
            const tabId = tab.toLowerCase().replace(' ', '-');
            const isActive = activeTab === tabId;
            return (
              <button
                key={tab}
                onClick={() => setActiveTab(tabId)}
                className={`px-6 py-2 rounded-lg text-sm font-semibold transition-all whitespace-nowrap ${
                  isActive
                    ? 'bg-primary-container text-on-primary-container shadow-lg'
                    : 'text-on-surface-variant hover:text-on-surface hover:bg-surface-container'
                }`}
              >
                {tab}
              </button>
            );
          })}
        </div>
      </div>

      {/* Profile Summary Card */}
      <div className="glass-panel rounded-2xl p-8 mb-10 flex items-center justify-between overflow-hidden relative group">
        <div className="absolute top-0 right-0 w-64 h-64 bg-primary-container/5 rounded-full blur-[80px] -translate-y-1/2 translate-x-1/2 group-hover:bg-primary-container/10 transition-colors duration-500" />
        <div className="flex items-center gap-8 relative z-10">
          <div className="relative">
            <div className="w-24 h-24 rounded-full border-2 border-primary-container/30 glow-primary flex items-center justify-center bg-surface-container text-primary-container text-3xl font-headline font-bold">
              {merchant?.businessName ? merchant.businessName.charAt(0).toUpperCase() : 'M'}
            </div>
            <div className="absolute bottom-0 right-0 w-6 h-6 bg-primary-fixed rounded-full border-4 border-surface-dim" />
          </div>
          <div>
            <h2 className="text-2xl font-bold font-headline mb-1 tracking-tight text-[#d7fff3]">{merchant?.businessName || 'Merchant'}</h2>
            <div className="flex items-center gap-2">
              <ShieldCheck size={16} className="text-primary-container" />
              <span className="text-sm font-medium text-on-surface-variant">Enterprise Plan</span>
            </div>
          </div>
        </div>
      </div>

      {/* Content - Showing Integrations */}
      {activeTab === 'integrations' && (
        <div className="space-y-8 animate-in fade-in duration-700">
          <div className="mb-6">
            <h3 className="font-headline text-2xl font-bold text-[#d7fff3] mb-2 tracking-tight">Active Uplinks</h3>
            <p className="text-sm text-on-surface-variant">Manage your connected channels and external data bridges.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Facebook Messenger Card */}
            <div className="glass-panel rounded-2xl p-6 flex flex-col justify-between group hover:border-blue-500/30 transition-all duration-300 relative overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
              <div className="relative z-10">
                <div className="flex justify-between items-start mb-6">
                  <div className="w-14 h-14 rounded-xl bg-blue-500/10 flex items-center justify-center border border-blue-500/20 group-hover:scale-105 transition-transform">
                    <Facebook size={28} className="text-blue-400" />
                  </div>
                  <Badge 
                    variant={facebookConnection.connected ? 'success' : 'outline'}
                    className={`font-bold px-3 py-1 rounded-full text-xs ${
                      facebookConnection.connected 
                        ? 'bg-blue-500/20 text-blue-300 border-blue-500/30 glow-primary' 
                        : 'bg-surface-container text-on-surface-variant border-outline-variant'
                    }`}
                  >
                    {facebookConnection.connected ? 'Synchronized' : 'Disconnected'}
                  </Badge>
                </div>
                <h4 className="text-lg font-bold font-headline text-[#d7fff3] mb-2">Facebook Messenger</h4>
                <p className="text-sm text-on-surface-variant mb-6 leading-relaxed">
                  Turn every interaction into a seamless conversational commerce opportunity.
                </p>

                {facebookError && (
                  <div className="mb-6 p-4 bg-error-container/20 border border-error/20 rounded-xl text-error text-xs font-medium">
                    {facebookError}
                  </div>
                )}
                
                {facebookConnection.connected ? (
                  <div className="pt-6 border-t border-outline-variant/30 flex justify-between items-center">
                    <p className="text-sm font-medium text-blue-300 truncate pr-4">{facebookConnection.pageName}</p>
                    <Button
                      variant="outline"
                      onClick={handleFacebookDisconnect}
                      disabled={facebookStatus === 'connecting'}
                      className="text-xs font-semibold px-4 border-outline-variant hover:bg-error-container/20 hover:text-error hover:border-error/30"
                    >
                      Disconnect
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <Button
                      onClick={handleFacebookConnect}
                      disabled={facebookStatus === 'connecting'}
                      className="w-full bg-blue-600 hover:bg-blue-500 text-white font-semibold"
                    >
                      {facebookStatus === 'connecting' ? 'Connecting...' : 'Connect Page'}
                    </Button>
                    <button
                      onClick={() => setShowFacebookConfig(!showFacebookConfig)}
                      className="w-full text-xs flex items-center justify-center gap-2 text-on-surface-variant hover:text-blue-300 transition-colors"
                    >
                      Advanced App Configuration <ChevronDown size={14} className={showFacebookConfig ? 'rotate-180 transition-transform' : 'transition-transform'} />
                    </button>
                  </div>
                )}
              </div>
            </div>

            {/* Shopify Store Card */}
            <div className="glass-panel rounded-2xl p-6 flex flex-col justify-between group hover:border-primary-container/30 transition-all duration-300 relative overflow-hidden">
               <div className="absolute inset-0 bg-gradient-to-br from-primary-container/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
               <div className="relative z-10">
                <div className="flex justify-between items-start mb-6">
                  <div className="w-14 h-14 rounded-xl bg-primary-container/10 flex items-center justify-center border border-primary-container/20 group-hover:scale-105 transition-transform">
                    <ShoppingBag size={28} className="text-primary-container" />
                  </div>
                  <Badge 
                    variant={shopifyConnection.connected ? 'success' : 'outline'}
                    className={`font-bold px-3 py-1 rounded-full text-xs ${
                      shopifyConnection.connected 
                        ? 'bg-primary-container/20 text-primary-container border-primary-container/30 glow-primary' 
                        : 'bg-surface-container text-on-surface-variant border-outline-variant'
                    }`}
                  >
                    {shopifyConnection.connected ? 'Active Sync' : 'Disconnected'}
                  </Badge>
                </div>
                <h4 className="text-lg font-bold font-headline text-[#d7fff3] mb-2">Shopify Store</h4>
                <p className="text-sm text-on-surface-variant mb-6 leading-relaxed">
                  Bridge your inventory and orders. Empower your agent with real-time shop intelligence.
                </p>

                {shopifyError && (
                  <div className="mb-6 p-4 bg-error-container/20 border border-error/20 rounded-xl text-error text-xs font-medium">
                    {shopifyError}
                  </div>
                )}
                
                {shopifyConnection.connected ? (
                  <div className="pt-6 border-t border-outline-variant/30 flex justify-between items-center">
                    <div>
                      <p className="text-sm font-medium text-primary-container truncate">{shopifyConnection.shopName}</p>
                      <p className="text-[10px] text-on-surface-variant truncate opacity-70">{shopifyConnection.shopDomain}</p>
                    </div>
                    <Button
                      variant="outline"
                      onClick={handleShopifyDisconnect}
                      disabled={shopifyStatus === 'connecting'}
                      className="text-xs font-semibold px-4 border-outline-variant hover:bg-error-container/20 hover:text-error hover:border-error/30"
                    >
                      Disconnect
                    </Button>
                  </div>
                ) : (
                   <div className="space-y-4">
                    <div className="flex gap-2">
                       <Input
                        type="text"
                        placeholder="your-store.myshopify.com"
                        value={shopDomain}
                        onChange={(e) => setShopDomain(e.target.value)}
                        className="flex-1 bg-surface-container border-outline-variant text-[#e4e1e9] placeholder:text-on-surface-variant/50 focus:ring-primary-container/30 focus:border-primary-container"
                      />
                      <Button
                        onClick={handleShopifyConnect}
                        disabled={shopifyStatus === 'connecting' || !shopDomain.trim()}
                        className="bg-primary-container hover:bg-primary-fixed text-on-primary-container font-semibold whitespace-nowrap"
                      >
                        {shopifyStatus === 'connecting' ? 'Connecting...' : 'Connect'}
                      </Button>
                    </div>
                    <button
                      onClick={() => setShowShopifyConfig(!showShopifyConfig)}
                      className="w-full text-xs flex items-center justify-center gap-2 text-on-surface-variant hover:text-primary-container transition-colors mt-2"
                    >
                      Advanced API Configuration <ChevronDown size={14} className={showShopifyConfig ? 'rotate-180 transition-transform' : 'transition-transform'} />
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
          
          {/* Advanced config flyouts (renders below grid if toggled) */}
          {(showFacebookConfig || showShopifyConfig) && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
              {showFacebookConfig && !facebookConnection.connected && (
                  <div className="glass-panel rounded-2xl p-6 border-blue-500/20 animate-in fade-in slide-in-from-top-4">
                    <form onSubmit={handleSaveFacebookCredentials} className="space-y-4">
                      <div>
                        <Label htmlFor="facebook-app-id" className="text-xs text-on-surface-variant">Meta App ID</Label>
                        <Input
                          id="facebook-app-id"
                          value={facebookAppId}
                          onChange={(e) => setFacebookAppId(e.target.value)}
                          className="bg-surface-container border-outline-variant text-[#e4e1e9] mt-1"
                        />
                      </div>
                      <div>
                        <Label htmlFor="facebook-app-secret" className="text-xs text-on-surface-variant">Meta App Secret</Label>
                        <Input
                          id="facebook-app-secret"
                          type="password"
                          value={facebookAppSecret}
                          onChange={(e) => setFacebookAppSecret(e.target.value)}
                          className="bg-surface-container border-outline-variant text-[#e4e1e9] mt-1"
                        />
                      </div>
                      <Button type="submit" disabled={isSavingFacebook || !facebookAppId || !facebookAppSecret} className="w-full bg-blue-600 hover:bg-blue-500">
                        {isSavingFacebook ? 'Processing...' : 'Secure & Connect Meta App'}
                      </Button>
                    </form>
                  </div>
              )}
              {showShopifyConfig && !shopifyConnection.connected && (
                  <div className="glass-panel rounded-2xl p-6 border-primary-container/20 animate-in fade-in slide-in-from-top-4">
                    <form onSubmit={handleSaveShopifyCredentials} className="space-y-4">
                      <div>
                        <Label htmlFor="shopify-api-key" className="text-xs text-on-surface-variant">Shopify Client ID</Label>
                        <Input
                          id="shopify-api-key"
                          value={shopifyApiKey}
                          onChange={(e) => setShopifyApiKey(e.target.value)}
                          className="bg-surface-container border-outline-variant text-[#e4e1e9] mt-1"
                        />
                      </div>
                      <div>
                        <Label htmlFor="shopify-api-secret" className="text-xs text-on-surface-variant">Shopify Client Secret</Label>
                        <Input
                          id="shopify-api-secret"
                          type="password"
                          value={shopifyApiSecret}
                          onChange={(e) => setShopifyApiSecret(e.target.value)}
                          className="bg-surface-container border-outline-variant text-[#e4e1e9] mt-1"
                        />
                      </div>
                      <Button type="submit" disabled={isSavingShopify || !shopifyApiKey || !shopifyApiSecret} className="w-full bg-primary-container hover:bg-primary-fixed text-on-primary-container">
                        {isSavingShopify ? 'Saving...' : 'Authorize Shopify Access'}
                      </Button>
                      {shopifyCredentialsStatus === 'success' && <p className="text-xs text-primary-fixed-dim mt-2">{shopifyCredentialsMessage}</p>}
                      {shopifyCredentialsStatus === 'error' && <p className="text-xs text-error mt-2">{shopifyCredentialsMessage}</p>}
                    </form>
                  </div>
              )}
            </div>
          )}
        </div>
      )}

      {activeTab === 'general' && (
        <div className="space-y-8 animate-in fade-in duration-700">
          <div className="mb-6">
            <h3 className="font-headline text-2xl font-bold text-[#d7fff3] mb-2 tracking-tight">System Protocol</h3>
            <p className="text-sm text-on-surface-variant">Configure fundamental operational rules and privacy compliance mechanisms.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Mode Toggle Section */}
            <div className="glass-panel p-6 rounded-2xl flex flex-col justify-between group hover:border-indigo-500/30 transition-all">
              <div>
                <div className="w-12 h-12 rounded-xl bg-indigo-500/10 flex items-center justify-center border border-indigo-500/20 mb-6">
                  <ToggleRight size={24} className="text-indigo-400" />
                </div>
                <h4 className="text-lg font-bold font-headline text-[#d7fff3] mb-2">Bot Operating Mode</h4>
                <p className="text-sm text-on-surface-variant mb-6">Toggle between general-purpose conversational logic and e-commerce specialized reasoning hooks.</p>
              </div>
              <div className="bg-surface-container/50 border border-outline-variant/30 p-4 rounded-xl">
                 <ModeToggle
                    currentMode={currentMode}
                    onModeChange={handleModeChangeRequest}
                    loading={modeLoading}
                    fetching={modeFetching}
                  />
              </div>
            </div>

            {/* Privacy Section */}
            <div className="glass-panel p-6 rounded-2xl flex flex-col justify-between group hover:border-purple-500/30 transition-all">
              <div>
                <div className="w-12 h-12 rounded-xl bg-purple-500/10 flex items-center justify-center border border-purple-500/20 mb-6">
                  <Download size={24} className="text-purple-400" />
                </div>
                <h4 className="text-lg font-bold font-headline text-[#d7fff3] mb-2">Privacy & Compliance</h4>
                <p className="text-sm text-on-surface-variant mb-6">Archive and secure your information. Full GDPR/CCPA compliant data synchronization and export facility.</p>
              </div>
              <div>
                {merchant?.id ? (
                  <ExportButton merchantId={merchant.id} />
                ) : (
                  <div className="bg-error-container/10 border border-error/20 p-4 rounded-xl text-error text-center text-sm">
                    Authentication required to initiate data extraction.
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Placeholders for other tabs */}
      {activeTab === 'shipping' && (
        <div className="glass-panel p-10 rounded-2xl flex flex-col items-center justify-center text-center animate-in fade-in duration-700">
           <div className="w-16 h-16 rounded-2xl bg-surface-container flex items-center justify-center border border-outline-variant mb-6">
              <span className="material-symbols-outlined text-outline text-3xl">local_shipping</span>
           </div>
           <h3 className="text-2xl font-bold font-headline text-[#d7fff3] mb-3">Shipping Logistics</h3>
           <p className="text-on-surface-variant max-w-sm mb-8">Orchestrate custom carriers for dynamic order tracking. Streamline fulfillment transparency.</p>
           <Link to="/settings/shipping" className="bg-surface-bright text-on-surface hover:bg-outline-variant px-6 py-3 rounded-xl font-semibold transition-colors">
              Enter Logistics Control
           </Link>
        </div>
      )}

      {activeTab === 'billing' && (
        <div className="glass-panel p-10 rounded-2xl flex flex-col items-center justify-center text-center animate-in fade-in duration-700">
           <div className="w-16 h-16 rounded-2xl bg-surface-container flex items-center justify-center border border-outline-variant mb-6">
              <span className="material-symbols-outlined text-outline text-3xl">payments</span>
           </div>
           <h3 className="text-2xl font-bold font-headline text-[#d7fff3] mb-3">Finance Module</h3>
           <Badge variant="outline" className="mb-4">Core Systems Off-line</Badge>
           <p className="text-on-surface-variant max-w-sm">The billing infrastructure is undergoing primary initialization. Commercial hook-ins will be deployed in the next update cycle.</p>
        </div>
      )}

      {activeTab === 'widget' && (
        <div className="glass-panel p-10 rounded-2xl flex flex-col items-center justify-center text-center animate-in fade-in duration-700">
           <div className="w-16 h-16 rounded-2xl bg-surface-container flex items-center justify-center border border-outline-variant mb-6">
              <MessageSquare size={32} className="text-outline" />
           </div>
           <h3 className="text-2xl font-bold font-headline text-[#d7fff3] mb-3">Widget Interface</h3>
           <p className="text-on-surface-variant max-w-sm mb-8">Customize the visual DNA of your embedded chat experience. Control brand alignment and interaction logic.</p>
           <Link to="/settings/widget" className="bg-surface-bright text-on-surface hover:bg-outline-variant px-6 py-3 rounded-xl font-semibold transition-colors">
              Modify Interface DNA
           </Link>
        </div>
      )}

      {/* Dialogs */}
      {targetMode && (
        <ModeChangeDialog
          isOpen={modeDialogOpen}
          onClose={() => { setModeDialogOpen(false); setTargetMode(null); }}
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
