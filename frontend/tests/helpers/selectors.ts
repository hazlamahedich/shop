/**
 * Enhanced Selectors - PageObjects Pattern
 *
 * Centralized selector management following the PageObjects pattern.
 * Provides type-safe, maintainable selector definitions.
 *
 * Benefits:
 * - Single source of truth for selectors
 * - Easy to update when UI changes
 * - Type-safe selector access
 * - Consistent naming conventions
 */

/**
 * PageObject for Prerequisite Checklist
 */
export const PrerequisiteChecklist = {
  container: '[data-testid="prerequisite-checklist"]',
  title: '[data-testid="prerequisite-title"]',

  // Checkboxes
  checkboxes: {
    cloudAccount: '[data-testid="checkbox-cloudAccount"]',
    facebookAccount: '[data-testid="checkbox-facebookAccount"]',
    shopifyAccess: '[data-testid="checkbox-shopifyAccess"]',
    llmProvider: '[data-testid="checkbox-llmProviderChoice"]',
  },

  // Help sections
  helpButtons: {
    cloudAccount: '[data-testid="help-button-cloudAccount"]',
    facebookAccount: '[data-testid="help-button-facebookAccount"]',
    shopifyAccess: '[data-testid="help-button-shopifyAccess"]',
    llmProvider: '[data-testid="help-button-llmProviderChoice"]',
  },

  helpSections: {
    cloudAccount: '[data-testid="help-section-cloudAccount"]',
    facebookAccount: '[data-testid="help-section-facebookAccount"]',
    shopifyAccess: '[data-testid="help-section-shopifyAccess"]',
    llmProvider: '[data-testid="help-section-llmProviderChoice"]',
  },

  // Progress indicator
  progressText: '[data-testid="progress-text"]',
  progressBar: '[data-testid="progress-bar"]',

  // Deploy button
  deployButton: '[data-testid="deploy-button"]',
} as const;

/**
 * PageObject for Deployment Wizard
 */
export const DeploymentWizard = {
  container: '[data-testid="deployment-wizard"]',
  title: '[data-testid="deployment-title"]',

  // Platform selector
  platformSelector: '[aria-label="Select deployment platform"]',
  platformLabel: 'label:has-text("Select Deployment Platform")',

  // Documentation links
  docsLinks: {
    flyio: 'a[href*="fly.io"]',
    railway: 'a[href*="railway.app"]',
    render: 'a[href*="render.com"]',
  },

  // Deployment progress
  progressSection: '[data-testid="deployment-progress"]',
  statusIndicator: '[data-testid="deployment-status"]',
  stepProgress: '[data-testid="step-progress"]',

  // Time estimate
  timeEstimate: '[data-testid="time-estimate"]',

  // Deployment button
  deployButton: '[data-testid="start-deployment-button"]',
} as const;

/**
 * PageObject for Facebook Connection
 */
export const FacebookConnection = {
  container: '[data-testid="facebook-connection"]',
  statusIndicator: '[data-testid="facebook-connection-status"]',

  // Connection button
  connectButton: '[data-testid="facebook-connect-button"]',

  // Webhook verification
  webhookStatus: '[data-testid="facebook-webhook-status"]',
  verifyToken: '[data-testid="facebook-verify-token"]',

  // Page info
  pageName: '[data-testid="facebook-page-name"]',
  pageId: '[data-testid="facebook-page-id"]',
} as const;

/**
 * PageObject for Shopify Connection
 */
export const ShopifyConnection = {
  container: '[data-testid="shopify-connection"]',
  statusIndicator: '[data-testid="shopify-connection-status"]',

  // Connection button
  connectButton: '[data-testid="shopify-connect-button"]',

  // Store info
  storeUrl: '[data-testid="shopify-store-url"]',
  storeDomain: '[data-testid="shopify-store-domain"]',
} as const;

/**
 * PageObject for LLM Configuration
 */
export const LLMConfiguration = {
  container: '[data-testid="llm-configuration"]',

  // Provider options
  ollamaOption: '[data-testid="ollama-option"]',
  cloudOption: '[data-testid="cloud-option"]',

  // Connection testing
  testConnectionButton: '[data-testid="test-connection-button"]',
  connectionStatus: '[data-testid="connection-status"]',

  // Model selection (Ollama)
  modelSelector: '[data-testid="model-selector"]',
  availableModels: '[data-testid="available-models"]',
} as const;

/**
 * PageObject for Webhook Verification
 */
export const WebhookVerification = {
  container: '[data-testid="webhook-verification"]',
  title: 'text=Webhook Verification',

  // Platform status cards
  facebookStatus: '[data-testid="webhook-status-facebook"]',
  shopifyStatus: '[data-testid="webhook-status-shopify"]',

  // Action buttons
  testWebhooksButton: '[data-testid="test-webhooks-button"]',
  resubscribeButton: '[data-testid="resubscribe-webhooks-button"]',
  refreshButton: '[data-testid="refresh-webhooks-button"]',

  // Troubleshooting
  troubleshootingSection: '[data-testid="troubleshooting-section"]',
  troubleshootingDocs: 'a[href*="developers.facebook.com"], a[href*="shopify.dev"]',
} as const;

/**
 * PageObject for Navigation
 */
export const Navigation = {
  mainMenu: '[data-testid="main-menu"]',
  homeLink: 'a[href="/"]',
  settingsLink: 'a[href="/settings"]',
  integrationsLink: 'a[href="/integrations"]',

  // Breadcrumb
  breadcrumb: '[data-testid="breadcrumb"]',
} as const;

/**
 * Re-export legacy selectors for backward compatibility
 * @deprecated Use new PageObjects instead
 */
export const mockSelectors = {
  prerequisiteChecklist: PrerequisiteChecklist.container,
  cloudAccountCheckbox: PrerequisiteChecklist.checkboxes.cloudAccount,
  facebookAccountCheckbox: PrerequisiteChecklist.checkboxes.facebookAccount,
  shopifyAccessCheckbox: PrerequisiteChecklist.checkboxes.shopifyAccess,
  llmProviderCheckbox: PrerequisiteChecklist.checkboxes.llmProvider,
  deployButton: PrerequisiteChecklist.deployButton,
  deploymentWizard: DeploymentWizard.container,
  deploymentStatus: DeploymentWizard.statusIndicator,
  facebookConnection: FacebookConnection.container,
  facebookStatus: FacebookConnection.statusIndicator,
  shopifyConnection: ShopifyConnection.container,
  shopifyStatus: ShopifyConnection.statusIndicator,
  llmConfiguration: LLMConfiguration.container,
  ollamaOption: LLMConfiguration.ollamaOption,
  cloudOption: LLMConfiguration.cloudOption,
  testConnectionButton: LLMConfiguration.testConnectionButton,
};
