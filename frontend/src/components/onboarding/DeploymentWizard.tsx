/** Deployment Wizard Component.
 *
 * One-click deployment wizard for deploying the bot to cloud platforms.
 * Features:
 * - Platform selector (Fly.io, Railway, Render)
 * - Real-time deployment progress tracking
 * - Live deployment logs with auto-scroll
 * - Success/error messages with next steps
 * - WCAG AA accessibility compliance
 */

import * as React from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../ui/Card';
import { Button } from '../ui/Button';
import { Select } from '../ui/Select';
import { Progress } from '../ui/Progress';
import { Input } from '../ui/input';
import { Alert } from '../ui/Alert';
import { Badge } from '../ui/Badge';
import { ScrollArea } from '../ui/ScrollArea';
import { useDeploymentStore, Platform } from '../../stores/deploymentStore';
import { onboardingStore } from '../../stores/onboardingStore';
import { cn } from '../../lib/utils';

const PLATFORM_OPTIONS = [
  { value: 'flyio' as Platform, label: 'Fly.io (Recommended)' },
  { value: 'railway' as Platform, label: 'Railway' },
  { value: 'render' as Platform, label: 'Render' },
];

const PLATFORM_INFO: Record<Platform, { name: string; description: string; docsUrl: string }> = {
  flyio: {
    name: 'Fly.io',
    description: 'Fastest deploy experience, free tier available',
    docsUrl: 'https://fly.io/docs/hands-on/start/',
  },
  railway: {
    name: 'Railway',
    description: 'Simple deployment with $5 free credit monthly',
    docsUrl: 'https://docs.railway.app/',
  },
  render: {
    name: 'Render',
    description: 'Free tier with 750 hours/month',
    docsUrl: 'https://render.com/docs/deploy-command',
  },
};

export function DeploymentWizard(): React.ReactElement {
  /* eslint-enable @typescript-eslint/no-unused-vars */

  const [renderApiKey, setRenderApiKey] = React.useState('');
  const [flyApiToken, setFlyApiToken] = React.useState('');
  const [railwayToken, setRailwayToken] = React.useState('');

  const {
    platform,
    status,
    progress,
    logs,
    currentStep,
    errorMessage,
    troubleshootingUrl,
    merchantKey,
    startDeployment,
    cancelDeployment,
    skipDeployment,
    reset,
    setPlatform,
  } = useDeploymentStore();

  const { isComplete: prerequisitesComplete } = onboardingStore();

  // Only "inProgress" means actively deploying. "pending" means ready to start.
  const isDeploying = status === 'inProgress';
  const isComplete = status === 'success';
  const hasFailed = status === 'failed';
  const isCancelled = status === 'cancelled';

  const handleDeploy = async () => {
    if (!platform) return;

    const config: Record<string, string> = {};
    if (platform === 'render' && renderApiKey) {
      config['RENDER_API_KEY'] = renderApiKey;
    } else if (platform === 'flyio' && flyApiToken) {
      config['FLY_API_TOKEN'] = flyApiToken;
    } else if (platform === 'railway' && railwayToken) {
      config['RAILWAY_TOKEN'] = railwayToken;
    }

    await startDeployment(platform, config);
  };

  const handleCancel = async () => {
    await cancelDeployment();
  };

  const handleReset = () => {
    reset();
  };

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  return (
    <div
      className="w-full max-w-3xl mx-auto p-4"
      data-theme="onboarding"
      data-testid="deployment-wizard"
    >
      <Card>
        <CardHeader>
          <CardTitle>Deploy Your Bot</CardTitle>
          <CardDescription>
            Choose your cloud platform and deploy with one click.{' '}
            <strong>Estimated time: {formatTime(900)} (15 minutes)</strong>
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* Platform Selection */}
          {status === 'pending' && !isDeploying && (
            <div>
              <Select
                label="Select Deployment Platform"
                options={PLATFORM_OPTIONS}
                value={platform || undefined}
                onChange={(e) => setPlatform(e.target.value as Platform)}
                disabled={isDeploying}
                aria-label="Select deployment platform"
              />
              {platform && (
                <div className="mt-4 space-y-4">
                  <div className="p-3 bg-slate-50 rounded-md">
                    <p className="text-sm text-slate-700">{PLATFORM_INFO[platform].description}</p>
                    <a
                      href={PLATFORM_INFO[platform].docsUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-block mt-2 text-sm text-blue-600 hover:text-blue-700 underline"
                    >
                      View {PLATFORM_INFO[platform].name} documentation →
                    </a>
                  </div>

                  {platform === 'render' && (
                    <Input
                      label="Render API Key (Recommended)"
                      type="password"
                      placeholder="rnd_xxxxxxxxxxxxxxxxxxxxxxxx"
                      value={renderApiKey}
                      onChange={(e) => setRenderApiKey(e.target.value)}
                      error={undefined}
                    />
                  )}
                  {platform === 'flyio' && (
                    <Input
                      label="Fly.io Access Token (Recommended)"
                      type="password"
                      placeholder="fo1_xxxxxxxxxxxxxxxxxxxxxxxx"
                      value={flyApiToken}
                      onChange={(e) => setFlyApiToken(e.target.value)}
                      error={undefined}
                    />
                  )}
                  {platform === 'railway' && (
                    <Input
                      label="Railway Project Token (Recommended)"
                      type="password"
                      placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
                      value={railwayToken}
                      onChange={(e) => setRailwayToken(e.target.value)}
                      error={undefined}
                    />
                  )}
                </div>
              )}
            </div>
          )}

          {/* Progress Section */}
          {(isDeploying || isComplete || hasFailed || isCancelled) && (
            <div className="space-y-4">
              {/* Status Badge */}
              <div className="flex items-center justify-between" data-testid="deployment-status">
                <div className="flex items-center gap-2">
                  <Badge variant={isComplete ? 'success' : hasFailed ? 'destructive' : 'default'}>
                    {status === 'inProgress' && currentStep
                      ? `Deploying: ${currentStep}`
                      : status === 'inProgress'
                        ? 'Deploying...'
                        : status === 'success'
                          ? 'Deployment Complete'
                          : status === 'failed'
                            ? 'Deployment Failed'
                            : 'Deployment Cancelled'}
                  </Badge>
                  {platform && (
                    <span className="text-sm text-slate-600">
                      on {PLATFORM_INFO[platform].name}
                    </span>
                  )}
                </div>
                {isDeploying && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleCancel}
                    disabled={!isDeploying}
                  >
                    Cancel
                  </Button>
                )}
              </div>

              {/* Progress Bar */}
              <div data-testid="deployment-progress">
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-slate-600">Deployment Progress</span>
                  <span className="font-medium">{progress}%</span>
                </div>
                <Progress value={progress} max={100} />
              </div>

              {/* Deployment Logs */}
              {logs.length > 0 && (
                <div>
                  <h3
                    className="text-sm font-medium text-slate-700 mb-2"
                    id="deployment-logs-title"
                  >
                    Deployment Logs
                  </h3>
                  <ScrollArea className="h-48 w-full rounded-md border border-slate-200">
                    <div
                      className="p-3 space-y-1 font-mono text-xs"
                      role="log"
                      aria-live="polite"
                      aria-atomic="true"
                      aria-labelledby="deployment-logs-title"
                    >
                      {logs.map((log, index) => (
                        <div
                          key={index}
                          className={cn(
                            'flex gap-2',
                            log.level === 'error' && 'text-red-600',
                            log.level === 'warning' && 'text-yellow-600',
                            log.level === 'info' && 'text-slate-700'
                          )}
                        >
                          <span className="text-slate-400 shrink-0">
                            [{new Date(log.timestamp).toLocaleTimeString()}]
                          </span>
                          <span className="flex-1">{log.message}</span>
                        </div>
                      ))}
                    </div>
                  </ScrollArea>
                </div>
              )}

              {/* Error Message */}
              {hasFailed && errorMessage && (
                <Alert variant="destructive" title="Deployment Failed">
                  <p className="mb-2">{errorMessage}</p>
                  {troubleshootingUrl && (
                    <a
                      href={troubleshootingUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="underline"
                    >
                      View troubleshooting guide →
                    </a>
                  )}
                </Alert>
              )}

              {/* Success Message */}
              {isComplete && merchantKey && (
                <Alert variant="default" title="Deployment Successful!">
                  <p className="mb-3">
                    Your bot has been deployed successfully. Your merchant key is{' '}
                    <code className="px-1 py-0.5 bg-slate-100 rounded text-sm">{merchantKey}</code>
                  </p>
                  <p className="font-medium mb-2">Next Steps:</p>
                  <ol
                    className="list-decimal list-inside space-y-1 text-sm"
                    aria-label="Next steps after deployment"
                  >
                    <li>Connect your Facebook Page (Story 1.3)</li>
                    <li>Connect your Shopify Store (Story 1.4)</li>
                    <li>Configure your LLM Provider (Story 1.5)</li>
                  </ol>
                </Alert>
              )}
            </div>
          )}
        </CardContent>

        <CardFooter className="flex flex-col gap-3">
          {status === 'pending' && !isDeploying && (
            <div className="w-full space-y-3">
              <Button
                variant="default"
                size="lg"
                onClick={handleDeploy}
                disabled={!platform || !prerequisitesComplete()}
                className="w-full"
              >
                {!platform
                  ? 'Select a platform to deploy'
                  : !prerequisitesComplete()
                    ? 'Complete all prerequisites first'
                    : `Deploy to ${PLATFORM_INFO[platform].name}`}
              </Button>

              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  skipDeployment();
                }}
                className="w-full text-slate-500"
              >
                Skip / Use Localhost (Development)
              </Button>
            </div>
          )}

          {(isComplete || hasFailed || isCancelled) && (
            <Button variant="outline" size="lg" onClick={handleReset} className="w-full">
              Deploy Again
            </Button>
          )}

          {!prerequisitesComplete() && (
            <p className="text-sm text-slate-500 text-center">
              Complete all prerequisites before deploying
            </p>
          )}
        </CardFooter>
      </Card>
    </div>
  );
}
