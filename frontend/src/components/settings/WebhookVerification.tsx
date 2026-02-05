import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Alert } from '@/components/ui/Alert';
import { Badge } from '@/components/ui/Badge';
import { CheckCircle2, AlertCircle, RefreshCw, Loader2 } from 'lucide-react';
import { useWebhookVerificationStore } from '@/stores/webhookVerificationStore';
import { WebhookStatusCard } from './WebhookStatusCard';

// Default merchant ID - in production this would come from auth context
// TODO: Get from auth context when authentication is implemented
const DEFAULT_MERCHANT_ID = 1;

export function WebhookVerification() {
  const {
    status,
    isTestingFacebook,
    isTestingShopify,
    isResubscribingFacebook,
    isResubscribingShopify,
    error,
    lastTestResult,
    lastResubscribeResult,
    getStatus,
    testFacebookWebhook,
    testShopifyWebhook,
    resubscribeFacebookWebhook,
    resubscribeShopifyWebhook,
    clearError,
  } = useWebhookVerificationStore();

  const [isRefreshing, setIsRefreshing] = useState(false);

  useEffect(() => {
    loadStatus();
  }, []);

  const loadStatus = async () => {
    setIsRefreshing(true);
    try {
      await getStatus(DEFAULT_MERCHANT_ID);
    } catch (err) {
      // Error is handled by store
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleTestFacebook = async () => {
    try {
      await testFacebookWebhook(DEFAULT_MERCHANT_ID);
      // Refresh status after test
      await loadStatus();
    } catch (err) {
      // Error is handled by store
    }
  };

  const handleTestShopify = async () => {
    try {
      await testShopifyWebhook(DEFAULT_MERCHANT_ID);
      // Refresh status after test
      await loadStatus();
    } catch (err) {
      // Error is handled by store
    }
  };

  const handleResubscribeFacebook = async () => {
    if (
      !confirm(
        'Re-subscribe to Facebook webhooks? This will re-establish the webhook subscription.'
      )
    ) {
      return;
    }
    try {
      await resubscribeFacebookWebhook(DEFAULT_MERCHANT_ID);
    } catch (err) {
      // Error is handled by store
    }
  };

  const handleResubscribeShopify = async () => {
    if (
      !confirm(
        'Re-subscribe to Shopify webhooks? This will re-establish the webhook subscriptions.'
      )
    ) {
      return;
    }
    try {
      await resubscribeShopifyWebhook(DEFAULT_MERCHANT_ID);
    } catch (err) {
      // Error is handled by store
    }
  };

  const getOverallStatusBadge = () => {
    if (!status) {
      return (
        <Badge variant="outline" className="bg-gray-50 text-gray-700 border-gray-200">
          Unknown
        </Badge>
      );
    }

    switch (status.overallStatus) {
      case 'ready':
        return (
          <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200 gap-1">
            <CheckCircle2 className="h-3 w-3" />
            Ready to Go Live
          </Badge>
        );
      case 'partial':
        return (
          <Badge variant="outline" className="bg-yellow-50 text-yellow-700 border-yellow-200 gap-1">
            <AlertCircle className="h-3 w-3" />
            Partial Setup
          </Badge>
        );
      case 'not_connected':
        return (
          <Badge variant="outline" className="bg-red-50 text-red-700 border-red-200 gap-1">
            <AlertCircle className="h-3 w-3" />
            Not Connected
          </Badge>
        );
      default:
        return (
          <Badge variant="outline" className="bg-gray-50 text-gray-700 border-gray-200">
            Unknown
          </Badge>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Webhook Verification</CardTitle>
              <CardDescription>
                Verify and test webhook connections for Facebook Messenger and Shopify
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              {getOverallStatusBadge()}
              <Button onClick={loadStatus} disabled={isRefreshing} variant="outline" size="sm">
                <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
              </Button>
            </div>
          </div>
        </CardHeader>
        {status?.canGoLive && (
          <CardContent className="pt-0">
            <Alert className="bg-green-50 text-green-800 border-green-200">
              <CheckCircle2 className="h-4 w-4" />
              All webhooks are verified and working! Your bot is ready to accept customers.
            </Alert>
          </CardContent>
        )}
      </Card>

      {/* Error Message */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          {error}
          <Button onClick={clearError} variant="ghost" size="sm" className="ml-auto">
            Dismiss
          </Button>
        </Alert>
      )}

      {/* Loading State */}
      {!status && !error && (
        <Card>
          <CardContent className="flex items-center justify-center py-12">
            <div className="flex items-center gap-2 text-slate-500">
              <Loader2 className="h-5 w-5 animate-spin" />
              Loading webhook status...
            </div>
          </CardContent>
        </Card>
      )}

      {/* Webhook Status Cards */}
      {status && status.facebook && status.shopify && (
        <div className="grid gap-6 md:grid-cols-2">
          <WebhookStatusCard
            platform="facebook"
            status={status.facebook}
            isLoading={isTestingFacebook || isResubscribingFacebook}
            onTest={handleTestFacebook}
            onResubscribe={handleResubscribeFacebook}
            lastTestResult={lastTestResult?.pageId ? (lastTestResult as any) : undefined}
            lastResubscribeResult={
              lastResubscribeResult?.platform === 'facebook'
                ? (lastResubscribeResult as any)
                : undefined
            }
          />
          <WebhookStatusCard
            platform="shopify"
            status={status.shopify}
            isLoading={isTestingShopify || isResubscribingShopify}
            onTest={handleTestShopify}
            onResubscribe={handleResubscribeShopify}
            lastTestResult={lastTestResult?.shopDomain ? (lastTestResult as any) : undefined}
            lastResubscribeResult={
              lastResubscribeResult?.platform === 'shopify'
                ? (lastResubscribeResult as any)
                : undefined
            }
          />
        </div>
      )}

      {/* Help Section */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Troubleshooting</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-slate-600">
          <p>
            <strong>Webhook not connected?</strong> Make sure you've completed the Facebook Page and
            Shopify store connection steps in the onboarding process.
          </p>
          <p>
            <strong>Test webhook failing?</strong> Try clicking "Resubscribe" to re-establish the
            webhook subscription. If that doesn't work, check your platform's developer dashboard
            for webhook settings.
          </p>
          <p>
            <strong>Need help?</strong> Consult the{' '}
            <a
              href="https://developers.facebook.com/docs/messenger-platform/webhooks"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:underline"
            >
              Facebook webhook documentation
            </a>{' '}
            or{' '}
            <a
              href="https://shopify.dev/docs/api/admin-rest/latest/resources/webhook"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:underline"
            >
              Shopify webhook documentation
            </a>
            .
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
