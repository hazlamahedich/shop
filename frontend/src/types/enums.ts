// ==================== Deployment Enums ====================

export type Platform = "flyio" | "railway" | "render";

export type DeploymentStatus = "pending" | "inProgress" | "success" | "failed" | "cancelled";

export type DeploymentStep = "checkCli" | "authentication" | "appSetup" | "configuration" | "secrets" | "deploy" | "healthCheck" | "complete";

export type LogLevel = "info" | "warning" | "error";

// ==================== LLM Enums ====================

export type LLMProvider = "ollama" | "openai" | "anthropic" | "gemini" | "glm";

export type LLMStatus = "pending" | "active" | "error";

// ==================== Webhook Verification Enums ====================

export type VerificationPlatform = "facebook" | "shopify";

export type VerificationTestType = "statusCheck" | "testWebhook" | "resubscribe";

export type VerificationStatus = "pending" | "success" | "failed";

export type OverallStatus = "ready" | "partial" | "notConnected";

export type SubscriptionStatus = "active" | "inactive";

export type TestStatus = "success" | "failed";

export type ResubscribeStatus = "success" | "partial" | "failed";

// ==================== Display Value Mappings ====================

export const DeploymentStepDisplay: Record<DeploymentStep, string> = {
  checkCli: "Check CLI",
  authentication: "Authentication",
  appSetup: "App Setup",
  configuration: "Configuration",
  secrets: "Secrets",
  deploy: "Deploy",
  healthCheck: "Health Check",
  complete: "Complete",
};

export const DeploymentStatusDisplay: Record<DeploymentStatus, string> = {
  pending: "Pending",
  inProgress: "In Progress",
  success: "Success",
  failed: "Failed",
  cancelled: "Cancelled",
};
