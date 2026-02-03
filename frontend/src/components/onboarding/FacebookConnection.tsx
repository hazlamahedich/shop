/**
 * Facebook Connection Component
 * Handles Facebook Page OAuth connection with status display
 */

import { useEffect } from 'react';
import { useIntegrationsStore } from '../../stores/integrationsStore';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import { Alert } from '../ui/Alert';
import { Avatar, AvatarImage } from '../ui/Avatar';

export interface FacebookConnectionProps {
  /** Whether to show in compact mode */
  compact?: boolean;
  /** Callback when connection status changes */
  onConnectionChange?: (connected: boolean) => void;
}

/**
 * FacebookConnection component for OAuth flow and status display
 */
export function FacebookConnection({
  compact = false,
  onConnectionChange,
}: FacebookConnectionProps) {
  const {
    facebookStatus,
    facebookConnection,
    facebookError,
    initiateFacebookOAuth,
    checkFacebookStatus,
    disconnectFacebook,
    clearError,
  } = useIntegrationsStore();

  // Check status on mount
  useEffect(() => {
    checkFacebookStatus();
  }, [checkFacebookStatus]);

  // Notify parent of connection changes
  useEffect(() => {
    onConnectionChange?.(facebookConnection.connected);
  }, [facebookConnection.connected, onConnectionChange]);

  // Handle connect/disconnect actions
  const handleConnect = () => {
    clearError();
    initiateFacebookOAuth();
  };

  const handleDisconnect = async () => {
    clearError();
    await disconnectFacebook();
  };

  // Render compact version
  if (compact) {
    return (
      <div className="flex items-center justify-between p-4 border rounded-lg">
        <div className="flex items-center gap-3">
          {facebookConnection.connected && facebookConnection.pagePictureUrl && (
            <Avatar className="w-10 h-10">
              <AvatarImage src={facebookConnection.pagePictureUrl} alt={facebookConnection.pageName} />
            </Avatar>
          )}
          <div>
            <p className="text-sm font-medium">
              {facebookConnection.connected
                ? facebookConnection.pageName || 'Facebook Page'
                : 'Connect Facebook Page'}
            </p>
            <StatusBadge status={facebookStatus} connected={facebookConnection.connected} />
          </div>
        </div>
        {facebookConnection.connected ? (
          <Button variant="outline" size="sm" onClick={handleDisconnect} disabled={facebookStatus === 'connecting'}>
            Disconnect
          </Button>
        ) : (
          <Button size="sm" onClick={handleConnect} disabled={facebookStatus === 'connecting'}>
            Connect
          </Button>
        )}
      </div>
    );
  }

  // Full version
  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">Facebook Page Connection</h3>
          <p className="text-sm text-muted-foreground">
            Connect your Facebook Page to enable Messenger bot functionality
          </p>
        </div>
        <StatusBadge status={facebookStatus} connected={facebookConnection.connected} />
      </div>

      {/* Error Alert */}
      {facebookError && (
        <Alert variant="destructive" dismissible onDismiss={clearError}>
          <p className="font-medium">Connection Error</p>
          <p className="text-sm">{facebookError}</p>
          <p className="text-sm mt-2">
            <strong>Troubleshooting:</strong>
            <ul className="list-disc list-inside mt-1">
              <li>Make sure you have admin access to the Facebook Page</li>
              <li>Grant all required permissions (pages_messaging, pages_manage_metadata)</li>
              <li>Check that your Facebook App is properly configured</li>
            </ul>
          </p>
        </Alert>
      )}

      {/* Connected State */}
      {facebookConnection.connected ? (
        <div className="border rounded-lg p-6 space-y-4">
          <div className="flex items-start gap-4">
            {facebookConnection.pagePictureUrl && (
              <Avatar className="w-16 h-16">
                <AvatarImage src={facebookConnection.pagePictureUrl} alt={facebookConnection.pageName} />
              </Avatar>
            )}
            <div className="flex-1">
              <h4 className="font-semibold text-lg">{facebookConnection.pageName || 'Facebook Page'}</h4>
              <p className="text-sm text-muted-foreground">Page ID: {facebookConnection.pageId}</p>
              {facebookConnection.connectedAt && (
                <p className="text-xs text-muted-foreground mt-1">
                  Connected: {new Date(facebookConnection.connectedAt).toLocaleDateString()}
                </p>
              )}
            </div>
          </div>

          {/* Webhook Status */}
          <div className="flex items-center justify-between pt-4 border-t">
            <div>
              <p className="text-sm font-medium">Webhook Status</p>
              <Badge variant={facebookConnection.webhookVerified ? 'default' : 'secondary'}>
                {facebookConnection.webhookVerified ? 'Verified' : 'Pending'}
              </Badge>
            </div>
            <Button variant="outline" onClick={handleDisconnect} disabled={facebookStatus === 'connecting'}>
              Disconnect Page
            </Button>
          </div>
        </div>
      ) : (
        /* Not Connected State */
        <div className="border rounded-lg p-6">
          <div className="text-center space-y-4">
            <div className="w-16 h-16 mx-auto bg-blue-100 rounded-full flex items-center justify-center">
              <svg className="w-8 h-8 text-blue-600" fill="currentColor" viewBox="0 0 24 24">
                <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
              </svg>
            </div>
            <div>
              <h4 className="font-semibold text-lg">Connect Your Facebook Page</h4>
              <p className="text-sm text-muted-foreground max-w-md mx-auto">
                Click the button below to authorize the bot to send and receive messages
                through your Facebook Page.
              </p>
            </div>
            <Button onClick={handleConnect} disabled={facebookStatus === 'connecting'} size="lg">
              {facebookStatus === 'connecting' ? 'Connecting...' : 'Connect Facebook Page'}
            </Button>
            <p className="text-xs text-muted-foreground">
              Required permissions: pages_messaging, pages_manage_metadata
            </p>
          </div>
        </div>
      )}

      {/* Loading State */}
      {facebookStatus === 'connecting' && !facebookConnection.connected && (
        <div className="text-center py-4">
          <div className="inline-block w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
          <p className="text-sm text-muted-foreground mt-2">Connecting to Facebook...</p>
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
