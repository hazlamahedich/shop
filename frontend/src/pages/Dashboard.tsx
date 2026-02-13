import React from 'react';
import { DollarSign, MessageSquare, TrendingUp, ArrowRight, Store } from 'lucide-react';
import { Card } from '../components/ui/Card';
import { TutorialPrompt } from '../components/onboarding/TutorialPrompt';
import { InteractiveTutorial } from '../components/onboarding/InteractiveTutorial';
import { useTutorialStore } from '../stores/tutorialStore';
import { useHasStoreConnected, useStoreProvider } from '../stores/authStore';

const Dashboard = () => {
  const { isStarted: isTutorialStarted } = useTutorialStore();
  const hasStoreConnected = useHasStoreConnected();
  const storeProvider = useStoreProvider();

  return (
    <>
      {/* Interactive Tutorial Modal - shown when tutorial is active */}
      {isTutorialStarted && <InteractiveTutorial />}

      <div className="space-y-8">
        {/* Tutorial Prompt Banner */}
        <TutorialPrompt />

        {/* Welcome Card with Tutorial Entry */}
        <Card>
          <div style={{ padding: 'var(--card-padding)' }}>
            <div className="flex items-start gap-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-blue-100 text-blue-600">
                <span className="text-2xl font-bold">Welcome!</span>
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-gray-900 mb-1">
                  Welcome to your Bot Dashboard
                </h3>
                <p className="text-sm text-gray-600 mb-3">
                  You've completed initial setup. Continue with the interactive tutorial to
                  learn how to use all features and configure your bot completely.
                </p>
                {/* Sprint Change 2026-02-13: Store status indicator */}
                {!hasStoreConnected && (
                  <div className="mt-2 p-2 bg-amber-50 border border-amber-200 rounded-lg flex items-center gap-2">
                    <Store size={16} className="text-amber-600" />
                    <span className="text-sm text-amber-700">
                      No e-commerce store connected.{' '}
                      <a href="/bot-config" className="underline font-medium hover:text-amber-800">
                        Connect a store
                      </a>{' '}
                      to enable product and order features.
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </Card>

        <div className="flex justify-between items-center">
          <h2 className="text-3xl font-bold text-gray-900">Dashboard</h2>
          <span className="text-sm text-gray-500">Last updated: Just now</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Cost Tracking Widget */}
          <Card>
            <div style={{ padding: 'var(--card-padding)' }}>
              <div className="flex justify-between items-start mb-4">
                <div>
                  <p className="text-sm font-medium text-gray-500">Today's Cost</p>
                  <h3 className="text-3xl font-bold text-gray-900 mt-1">$1.23</h3>
                </div>
                <div className="p-2 bg-blue-50 rounded-lg text-primary">
                  <DollarSign size={20} />
                </div>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Monthly Budget</span>
                  <span className="font-medium text-gray-900">$18.45 / $50.00</span>
                </div>
                <div className="w-full bg-gray-100 rounded-full h-2">
                  <div className="bg-accent h-2 rounded-full" style={{ width: '37%' }}></div>
                </div>
              </div>
            </div>
          </Card>

          {/* Active Conversations Widget */}
          <Card>
            <div style={{ padding: 'var(--card-padding)' }}>
              <div className="flex justify-between items-start mb-4">
                <div>
                  <p className="text-sm font-medium text-gray-500">Active Chats</p>
                  <h3 className="text-3xl font-bold text-gray-900 mt-1">24</h3>
                </div>
                <div className="p-2 bg-green-50 rounded-lg text-success">
                  <MessageSquare size={20} />
                </div>
              </div>
              <div className="space-y-4">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center text-xs font-medium">
                    JD
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">John Doe</p>
                    <p className="text-xs text-gray-500 truncate">I'm looking for running shoes...</p>
                  </div>
                  <span className="text-xs text-gray-400">2m</span>
                </div>
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center text-xs font-medium">
                    AS
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">Alice Smith</p>
                    <p className="text-xs text-gray-500 truncate">Is this available in red?</p>
                  </div>
                  <span className="text-xs text-gray-400">5m</span>
                </div>
              </div>
            </div>
          </Card>

          {/* Sales Summary Widget - Sprint Change 2026-02-13: Conditional rendering */}
          {hasStoreConnected ? (
            <Card>
              <div style={{ padding: 'var(--card-padding)' }}>
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <p className="text-sm font-medium text-gray-500">Total Sales</p>
                    <h3 className="text-3xl font-bold text-gray-900 mt-1">$459.00</h3>
                  </div>
                  <div className="p-2 bg-purple-50 rounded-lg text-accent">
                    <TrendingUp size={20} />
                  </div>
                </div>
                <div className="space-y-3">
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-gray-500">Today</span>
                    <span className="font-medium text-success">+$124.00</span>
                  </div>
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-gray-500">This Week</span>
                    <span className="font-medium text-gray-900">$1,240.00</span>
                  </div>
                  <button className="text-primary text-sm font-medium hover:underline flex items-center mt-2">
                    View Report <ArrowRight size={14} className="ml-1" />
                  </button>
                </div>
              </div>
            </Card>
          ) : (
            /* Connect Store Card - shown when no store connected */
            <Card>
              <div style={{ padding: 'var(--card-padding)' }}>
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <p className="text-sm font-medium text-gray-500">Sales</p>
                    <h3 className="text-xl font-semibold text-gray-500 mt-1">Connect Store</h3>
                  </div>
                  <div className="p-2 bg-gray-100 rounded-lg text-gray-400">
                    <Store size={20} />
                  </div>
                </div>
                <div className="space-y-3">
                  <p className="text-sm text-gray-500">
                    Connect an e-commerce store to track sales and orders.
                  </p>
                  <a
                    href="/bot-config"
                    className="inline-flex items-center text-primary text-sm font-medium hover:underline"
                  >
                    Connect Store <ArrowRight size={14} className="ml-1" />
                  </a>
                </div>
              </div>
            </Card>
          )}
        </div>
      </div>
    </>
  );
};

export default Dashboard;
