import { Store, RefreshCw } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { Card } from '../components/ui/Card';
import { TutorialPrompt } from '../components/onboarding/TutorialPrompt';
import { useHasStoreConnected } from '../stores/authStore';
import { RetentionJobStatus } from '../components/retention/RetentionJobStatus';

// Dashboard widgets
import { RevenueWidget } from '../components/dashboard/RevenueWidget';
import { ConversationOverviewWidget } from '../components/dashboard/ConversationOverviewWidget';
import { HandoffQueueWidget } from '../components/dashboard/HandoffQueueWidget';
import { AICostWidget } from '../components/dashboard/AICostWidget';
import { GeographicSnapshotWidget } from '../components/dashboard/GeographicSnapshotWidget';
import { TopProductsWidget } from '../components/dashboard/TopProductsWidget';
import { analyticsService } from '../services/analyticsService';

function LastUpdatedBadge() {
  // Rerender every minute to show a live "Last updated" time
  const { dataUpdatedAt } = useQuery({ 
    queryKey: ['analytics', 'summary'], 
    queryFn: () => analyticsService.getSummary(),
    enabled: false 
  });

  const label = dataUpdatedAt
    ? new Date(dataUpdatedAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    : 'loading…';

  return (
    <span className="flex items-center gap-1.5 text-xs text-gray-400">
      <RefreshCw size={11} className="animate-spin-slow opacity-60" />
      Updated at {label} · auto-refreshes every minute
    </span>
  );
}

const Dashboard = () => {
  const hasStoreConnected = useHasStoreConnected();

  return (
    <>
      {/* Tutorial Prompt Banner */}
      <TutorialPrompt />

      <div data-testid="dashboard-content" className="space-y-6">
        {/* ── Page Header ──────────────────────────────────────── */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 tracking-tight">Dashboard</h2>
            <p className="text-sm text-gray-500 mt-0.5">
              Your store at a glance — live data from Shopify.
            </p>
          </div>
          <LastUpdatedBadge />
        </div>

        {/* ── No store warning ─────────────────────────────────── */}
        {!hasStoreConnected && (
          <Card>
            <div style={{ padding: 'var(--card-padding)' }}>
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-amber-100 text-amber-600">
                  <Store size={18} />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-semibold text-amber-800">No e-commerce store connected</p>
                  <p className="text-xs text-amber-700 mt-0.5">
                    Revenue and order stats will appear once you{' '}
                    <a href="/bot-config" className="underline font-medium hover:text-amber-900">
                      connect a Shopify store
                    </a>
                    .
                  </p>
                </div>
              </div>
            </div>
          </Card>
        )}

        {/* ── Row 1: Revenue (wide) + AI Cost ──────────────────── */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          {/* Revenue spans 2 of 3 columns on large screens */}
          <div className="lg:col-span-2" data-testid="revenue-widget-container">
            <RevenueWidget />
          </div>

          {/* AI Cost */}
          <div data-testid="ai-cost-widget-container">
            <AICostWidget />
          </div>
        </div>

        {/* ── Row 2: Conversations + Handoff Queue (wide) ───────── */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          {/* Conversation overview */}
          <div data-testid="conversation-overview-widget-container">
            <ConversationOverviewWidget />
          </div>

          {/* Handoff queue spans 2 columns */}
          <div className="lg:col-span-2" data-testid="handoff-queue-widget-container">
            <HandoffQueueWidget />
          </div>
        </div>

        {/* ── Row 3: Top Products + Geographic Snapshot ─────────── */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          <div className="lg:col-span-2" data-testid="top-products-widget-container">
            <TopProductsWidget />
          </div>

          <div data-testid="geographic-widget-container">
            <GeographicSnapshotWidget />
          </div>
        </div>

        {/* ── GDPR / Data Retention Status ─────────────────────── */}
        <div>
          <RetentionJobStatus />
        </div>
      </div>
    </>
  );
};

export default Dashboard;
