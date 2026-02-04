import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Alert } from '@/components/ui/Alert';
import { CheckCircle2, XCircle, AlertCircle, Loader2, RefreshCw } from 'lucide-react';
import type { WebhookStatus } from '@/stores/webhookVerificationStore';

interface WebhookStatusCardProps {
  platform: 'facebook' | 'shopify';
  status: WebhookStatus;
  isLoading: boolean;
  onTest: () => void;
  onResubscribe: () => void;
  lastTestResult?: {
    status: 'success' | 'failed';
    message: string;
  };
  lastResubscribeResult?: {
    status: 'success' | 'partial' | 'failed';
    message: string;
  };
}

const PLATFORM_CONFIG = {
  facebook: {
    title: 'Facebook Messenger',
    description: 'Webhook for receiving customer messages from Facebook',
    color: 'blue',
  },
  shopify: {
    title: 'Shopify',
    description: 'Webhook for receiving order updates from Shopify',
    color: 'green',
  },
} as const;

export function WebhookStatusCard({
  platform,
  status,
  isLoading,
  onTest,
  onResubscribe,
  lastTestResult,
  lastResubscribeResult,
}: WebhookStatusCardProps) {
  const config = PLATFORM_CONFIG[platform];

  const getStatusIcon = () => {
    if (isLoading) {
      return <Loader2 className="h-4 w-4 animate-spin" />;
    }
    if (status.connected) {
      return <CheckCircle2 className="h-4 w-4 text-green-600" />;
    }
    return <XCircle className="h-4 w-4 text-red-600" />;
  };

  const getStatusBadge = () => {
    if (isLoading) {
      return (
        <Badge variant="outline" className="gap-1">
          <Loader2 className="h-3 w-3 animate-spin" />
          Testing...
        </Badge>
      );
    }
    if (status.connected) {
      return (
        <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200 gap-1">
          <CheckCircle2 className="h-3 w-3" />
          Connected
        </Badge>
      );
    }
    return (
      <Badge variant="outline" className="bg-red-50 text-red-700 border-red-200 gap-1">
        <XCircle className="h-3 w-3" />
        Not Connected
      </Badge>
    );
  };

  const getSubscriptionStatusBadge = () => {
    if (status.subscriptionStatus === 'active') {
      return (
        <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
          Active
        </Badge>
      );
    }
    return (
      <Badge variant="outline" className="bg-gray-50 text-gray-700 border-gray-200">
        Inactive
      </Badge>
    );
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              {getStatusIcon()}
              {config.title}
            </CardTitle>
            <CardDescription>{config.description}</CardDescription>
          </div>
          {getStatusBadge()}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Error Message */}
        {status.error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            {status.error}
          </Alert>
        )}

        {/* Last Test Result */}
        {lastTestResult && (
          <Alert
            variant={lastTestResult.status === 'success' ? 'default' : 'destructive'}
            className={
              lastTestResult.status === 'success'
                ? 'bg-green-50 text-green-800 border-green-200'
                : undefined
            }
          >
            {lastTestResult.status === 'success' ? (
              <CheckCircle2 className="h-4 w-4" />
            ) : (
              <XCircle className="h-4 w-4" />
            )}
            {lastTestResult.message}
          </Alert>
        )}

        {/* Re-subscribe Result */}
        {lastResubscribeResult && (
          <Alert
            variant={lastResubscribeResult.status === 'success' ? 'default' : 'destructive'}
            className={
              lastResubscribeResult.status === 'success'
                ? 'bg-green-50 text-green-800 border-green-200'
                : undefined
            }
          >
            {lastResubscribeResult.status === 'success' ? (
              <CheckCircle2 className="h-4 w-4" />
            ) : (
              <XCircle className="h-4 w-4" />
            )}
            {lastResubscribeResult.message}
          </Alert>
        )}

        {/* Status Details */}
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-slate-500">Subscription:</span>
            <span className="ml-2">{getSubscriptionStatusBadge()}</span>
          </div>
          <div>
            <span className="text-slate-500">Topics:</span>
            <span className="ml-2">{status.topics.length} subscribed</span>
          </div>
          {status.lastWebhookAt && (
            <div className="col-span-2">
              <span className="text-slate-500">Last webhook:</span>
              <span className="ml-2">{new Date(status.lastWebhookAt).toLocaleString()}</span>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex gap-2 pt-2">
          <Button
            onClick={onTest}
            disabled={isLoading}
            variant="outline"
            className="flex-1"
          >
            {isLoading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Testing...
              </>
            ) : (
              'Test Webhook'
            )}
          </Button>
          <Button
            onClick={onResubscribe}
            disabled={isLoading}
            variant="outline"
            className="flex-1"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Resubscribe
          </Button>
        </div>

        {/* Webhook URL */}
        <div className="pt-2 border-t">
          <p className="text-xs text-slate-500 mb-1">Webhook URL:</p>
          <code className="text-xs bg-slate-100 px-2 py-1 rounded block break-all">
            {status.webhookUrl}
          </code>
        </div>
      </CardContent>
    </Card>
  );
}
