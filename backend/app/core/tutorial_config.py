"""Tutorial Steps Configuration.

Defines the tutorial step content for the interactive tutorial.
Expanded from 4 steps to 8 steps to cover bot configuration features.

Steps Overview:
1. Dashboard Overview - Show conversation list, search, filters
2. Cost Tracking - Real-time costs, budget configuration
3. LLM Provider Switching - How to change providers
4. Bot Testing - Messenger preview pane with test message
5. Bot Personality Selection - Choose bot personality (Friendly/Professional/Enthusiastic)
6. Business Info & FAQ Configuration - Business name, description, hours, FAQ
7. Bot Naming - Custom bot name with preview
8. Smart Greetings & Product Pins - Greeting templates and product highlight pins
"""

from typing import Dict, Any

# Tutorial step definitions with content and actions
TUTORIAL_STEPS: Dict[str, Dict[str, Any]] = {
    "1": {
        "step": 1,
        "title": "Dashboard Overview",
        "description": "Learn how to navigate to dashboard and view customer conversations",
        "component": "ConversationList",
        "action": "View Conversation List",
        "content": """
        <div className="space-y-4">
          <p className="text-slate-700">
            Your dashboard displays all customer conversations in one place. You can search, filter, and respond to messages directly.
          </p>
          <div className="rounded-md bg-slate-100 p-4">
            <h4 className="mb-2 font-semibold text-slate-900">Key Features:</h4>
            <ul className="space-y-1 text-sm text-slate-700">
              <li>• View all customer conversations</li>
              <li>• Search by customer name or message content</li>
              <li>• Filter by date or status</li>
              <li>• Real-time message updates</li>
            </ul>
          </div>
        </div>
        """,
    },
    "2": {
        "step": 2,
        "title": "Cost Tracking",
        "description": "Understand your LLM costs in real-time and set budget caps",
        "component": "CostTracking",
        "action": "View Cost Tracking Panel",
        "content": """
        <div className="space-y-4">
          <p className="text-slate-700">
            Monitor your LLM usage and costs in real-time. Set budget caps to avoid surprise bills.
          </p>
          <div className="rounded-md bg-slate-100 p-4">
            <h4 className="mb-2 font-semibold text-slate-900">Cost Features:</h4>
            <ul className="space-y-1 text-sm text-slate-700">
              <li>• Real-time token usage tracking</li>
              <li>• Cost estimation per conversation</li>
              <li>• Budget cap configuration</li>
              <li>• Usage alerts and notifications</li>
            </ul>
          </div>
        </div>
        """,
    },
    "3": {
        "step": 3,
        "title": "LLM Provider Switching",
        "description": "Learn how to switch between LLM providers (Ollama, OpenAI, etc.)",
        "component": "LLMSettings",
        "action": "View Provider Settings",
        "content": """
        <div className="space-y-4">
          <p className="text-slate-700">
            You can switch between different LLM providers at any time. Choose the one that best fits your needs and budget.
          </p>
          <div className="rounded-md bg-slate-100 p-4">
            <h4 className="mb-2 font-semibold text-slate-900">Supported Providers:</h4>
            <ul className="space-y-1 text-sm text-slate-700">
              <li>• <strong>Ollama:</strong> Free, local LLM hosting</li>
              <li>• <strong>OpenAI:</strong> GPT models with excellent quality</li>
              <li>• <strong>Anthropic:</strong> Claude models for nuanced responses</li>
              <li>• <strong>Gemini:</strong> Google's powerful AI models</li>
            </ul>
          </div>
        </div>
        """,
    },
    "4": {
        "step": 4,
        "title": "Test Your Bot",
        "description": "Send a test message to your bot and see how it responds",
        "component": "BotPreview",
        "action": "Test Bot with Preview Pane",
        "content": """
        <div className="space-y-4">
          <p className="text-slate-700">
            Send a test message to your bot and see how it responds. This helps you verify everything is working before going live.
          </p>
        </div>
        """,
    },
    # New steps for bot configuration features
    "5": {
        "step": 5,
        "title": "Bot Personality Selection",
        "description": "Choose how your bot should interact with customers (Friendly, Professional, or Enthusiastic)",
        "component": "PersonalityConfig",
        "action": "Select Bot Personality",
        "content": """
        <div className="space-y-4">
          <p className="text-slate-700">
            Choose the personality that best fits your brand. Your bot will use this tone in all responses.
          </p>
          <div className="rounded-md bg-slate-100 p-4">
            <h4 className="mb-2 font-semibold text-slate-900">Available Personalities:</h4>
            <ul className="space-y-1 text-sm text-slate-700">
              <li>• <strong>Friendly:</strong> Casual and warm tone</li>
              <li>• <strong>Professional:</strong> Formal and direct tone</li>
              <li>• <strong>Enthusiastic:</strong> Excited and energetic tone</li>
            </ul>
          </div>
        </div>
        """,
    },
    "6": {
        "step": 6,
        "title": "Business Info & FAQ Configuration",
        "description": "Add your business information and create frequently asked questions (FAQ)",
        "component": "BusinessInfoConfig",
        "action": "Configure Business Info & FAQ",
        "content": """
        <div className="space-y-4">
          <p className="text-slate-700">
            Add your business name, description, and operating hours. Also create FAQ entries for common customer questions.
          </p>
          <div className="rounded-md bg-slate-100 p-4">
            <h4 className="mb-2 font-semibold text-slate-900">Business Info Fields:</h4>
            <ul className="space-y-1 text-sm text-slate-700">
              <li>• Business Name</li>
              <li>• Business Description</li>
              <li>• Business Hours</li>
            </ul>
            <h4 className="mt-4 mb-2 font-semibold text-slate-900">FAQ Management:</h4>
            <ul className="space-y-1 text-sm text-slate-700">
              <li>• Add question-answer pairs</li>
              <li>• Edit or delete existing FAQs</li>
              <li>• Reorder FAQ display order</li>
            </ul>
          </div>
        </div>
        """,
    },
    "7": {
        "step": 7,
        "title": "Bot Naming",
        "description": "Give your bot a custom name that customers will see",
        "component": "BotNamingConfig",
        "action": "Set Bot Name",
        "content": """
        <div className="space-y-4">
          <p className="text-slate-700">
            Give your bot a custom name. This name will appear in messages and helps customers identify your business.
          </p>
          <div className="rounded-md bg-slate-100 p-4">
            <h4 className="mb-2 font-semibold text-slate-900">Tips:</h4>
            <ul className="space-y-1 text-sm text-slate-700">
              <li>• Keep it short (under 30 characters)</li>
              <li>• Make it memorable and relevant to your business</li>
              <li>• Preview how it looks in messages</li>
            </ul>
          </div>
        </div>
        """,
    },
    "8": {
        "step": 8,
        "title": "Smart Greetings & Product Pins",
        "description": "Configure personalized greeting templates and highlight products for customers",
        "component": "GreetingsConfig",
        "action": "Configure Greetings & Pins",
        "content": """
        <div className="space-y-4">
          <p className="text-slate-700">
            Set up personalized greeting templates based on your bot personality. Also pin important products that will be highlighted to customers.
          </p>
          <div className="rounded-md bg-slate-100 p-4">
            <h4 className="mb-2 font-semibold text-slate-900">Greeting Features:</h4>
            <ul className="space-y-1 text-sm text-slate-700">
              <li>• Personality-based templates</li>
              <li>• Custom greeting messages</li>
              <li>• Time-sensitive greetings</li>
            </ul>
            <h4 className="mt-4 mb-2 font-semibold text-slate-900">Product Pins:</h4>
            <ul className="space-y-1 text-sm text-slate-700">
              <li>• Highlight up to 8 products</li>
              <li>• Set pin order/priority</li>
              <li>• Show pinned products first</li>
            </ul>
          </div>
        </div>
        """,
    },
}


def get_tutorial_step_content(step: int) -> str:
    """Get the HTML content for a given tutorial step.

    Args:
        step: Step number (1-8)

    Returns:
        HTML content string for the step
    """
    step_config = TUTORIAL_STEPS.get(str(step))
    if not step_config:
        return "<p>Step content not found.</p>"
    return step_config.get("content", "<p>Step content not available.</p>")


def get_all_steps() -> list[Dict[str, Any]]:
    """Get all tutorial step configurations.

    Returns:
        List of all step configs sorted by step number
    """
    return [TUTORIAL_STEPS[key] for key in sorted(TUTORIAL_STEPS.keys())]
