import React, { useState } from 'react';
import { Facebook, ShoppingBag, Bot, Eye, EyeOff } from 'lucide-react';

const Settings = () => {
  const [activeTab, setActiveTab] = useState('integrations');
  const [showApiKey, setShowApiKey] = useState(false);

  return (
    <div className="space-y-6">
      <h2 className="text-3xl font-bold text-gray-900">Settings</h2>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {['General', 'Integrations', 'Billing'].map((tab) => (
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
              <button className="px-4 py-2 bg-primary text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors">
                Connect Page
              </button>
            </div>
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

          {/* LLM Settings */}
          <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
            <div className="flex items-start space-x-4">
              <div className="p-3 bg-purple-50 rounded-lg text-accent">
                <Bot size={24} />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-medium text-gray-900">LLM Settings</h3>
                <p className="text-sm text-gray-500 mt-1">Configure your AI provider.</p>

                <div className="mt-4 space-y-4 max-w-md">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Provider</label>
                    <select className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary">
                      <option>OpenAI (GPT-4)</option>
                      <option>Anthropic (Claude 3)</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">API Key</label>
                    <div className="relative">
                      <input
                        type={showApiKey ? 'text' : 'password'}
                        defaultValue="sk-........................"
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
                      />
                      <button
                        onClick={() => setShowApiKey(!showApiKey)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                      >
                        {showApiKey ? <EyeOff size={16} /> : <Eye size={16} />}
                      </button>
                    </div>
                  </div>
                  <div className="pt-2">
                    <button className="px-4 py-2 bg-primary text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors">
                      Save Configuration
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Placeholder for other tabs */}
      {(activeTab === 'general' || activeTab === 'billing') && (
        <div className="bg-white p-8 rounded-xl border border-gray-200 text-center">
          <p className="text-gray-500">Settings for {activeTab} coming soon.</p>
        </div>
      )}
    </div>
  );
};

export default Settings;
