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

// ==================== Personality Configuration Enums ====================
// Story 1.10: Bot Personality Configuration

export type PersonalityType = "friendly" | "professional" | "enthusiastic";

export const PersonalityDisplay: Record<PersonalityType, string> = {
  friendly: "Friendly",
  professional: "Professional",
  enthusiastic: "Enthusiastic",
};

export const PersonalityDescriptions: Record<PersonalityType, string> = {
  friendly: "Casual, warm tone with emojis (e.g., \"Hey! 👋 How can I help?\")",
  professional: "Direct, helpful tone with minimal emojis (e.g., \"Hello. How may I assist you?\")",
  enthusiastic: "High-energy tone with exclamation marks (e.g., \"Hi there! Welcome! What can I help you find today?\")",
};

export const PersonalityDefaultGreetings: Record<PersonalityType, string> = {
  friendly: "Hey there! 👋 I'm {bot_name} from {business_name}. How can I help you today?",
  professional: "Good day. I am {bot_name} from {business_name}. How may I assist you today?",
  enthusiastic: "Hello! 🎉 I'm {bot_name} from {business_name}. How can I help you find exactly what you need!!! ✨ What can I help you with today?",
};

export const PersonalitySystemPrompts: Record<PersonalityType, string> = {
  friendly: "You are a friendly and helpful shopping assistant. Your tone should be casual, warm, and conversational. Use appropriate emojis to enhance friendliness. Be helpful and enthusiastic about helping customers find products. Keep responses concise but warm. Make customers feel welcome and valued.",
  professional: "You are a professional and efficient shopping assistant. Your tone should be direct, helpful, and respectful. Use minimal emojis, only when necessary for clarity. Focus on providing accurate information and helping customers efficiently. Keep responses concise and professional. Maintain a helpful but business-like demeanor.",
  enthusiastic: "You are an enthusiastic and exciting shopping assistant! Your tone should be high-energy, positive, and exciting! Use frequent emojis to express enthusiasm. Show genuine excitement about helping customers find amazing products. Make shopping feel fun and engaging. Use exclamation marks (sparingly but effectively) to convey energy. Create an upbeat and positive shopping experience!",
};
