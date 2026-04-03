"""Conversation-level personality templates for unified conversation service handlers (Story 11-5, AC8, AC10).

These templates are used by:
- unified_conversation_service.py
- clarification_handler.py
- check_consent_handler.py
- forget_preferences_handler.py
- llm_handler.py

Registered via PersonalityAwareResponseFormatter.register_response_type().
All 3 personality variants must be defined for each key to prevent KeyError.
"""

from app.models.merchant import PersonalityType
from app.services.personality.response_formatter import PersonalityAwareResponseFormatter

CONVERSATION_TEMPLATES = {
    PersonalityType.FRIENDLY: {
        "welcome_back_fallback": "Welcome back! Is there anything else I can help you with? 😊",
        "bot_paused": "I'm currently unavailable. Please try again later or contact support! 🙏",
        "clarification_fallback": "I'm not sure what you're looking for. 😅 Could you tell me more?",
        "consent_check_error": "I couldn't check your preferences right now. Please try again later! 😅",
        "forget_rate_limited": "You've already requested data deletion recently. Please wait a bit before trying again! 😊",
        "forget_error": "I had trouble deleting your preferences. 😅 Please try again later!",
        "forget_unexpected_error": "Oops, something unexpected happened! 😅 Please try again later.",
        "llm_classification_leak": "I'd be happy to help you with that! 😊 Could you tell me a bit more?",
        "llm_fallback": "I'm here to help you shop at {business_name}! 😊 You can ask me about products, check your cart, or place an order.",
    },
    PersonalityType.PROFESSIONAL: {
        "welcome_back_fallback": "Welcome back. Is there anything else I can assist you with?",
        "bot_paused": "I am currently unavailable. Please contact support or try again later.",
        "clarification_fallback": "I am not certain what you are looking for. Could you provide additional details?",
        "consent_check_error": "I was unable to check your preferences at this time. Please try again later.",
        "forget_rate_limited": "You have already requested data deletion recently. Please wait before trying again.",
        "forget_error": "An error occurred while attempting to delete your preferences. Please try again later.",
        "forget_unexpected_error": "An unexpected error occurred. Please try again later.",
        "llm_classification_leak": "I would be happy to assist you. Could you provide additional details?",
        "llm_fallback": "I am here to help you shop at {business_name}. You can inquire about products, check your cart, or place an order.",
    },
    PersonalityType.ENTHUSIASTIC: {
        "welcome_back_fallback": "WELCOME BACK!!! 🎉 Is there anything else I can help you with?! ✨",
        "bot_paused": "I'm taking a tiny break right now! 😊 Please try again in just a moment or contact support! ✨",
        "clarification_fallback": "Hmm, I'm not quite sure what you're looking for! 🤔 Could you tell me more? I'm SO here to help!!!",
        "consent_check_error": "Oops! I couldn't check your preferences right now! 😅 Let's try again later! 💪",
        "forget_rate_limited": "You just requested data deletion! 😊 Please wait a tiny bit before trying again! ✨",
        "forget_error": "Oopsie! I had trouble deleting your preferences! 😅 Let's try again later! 💪",
        "forget_unexpected_error": "Oh no! Something unexpected happened! 😅 Let's try again! 💪",
        "llm_classification_leak": "I'd LOVE to help you with that! 😊 Could you tell me a bit more?! 🎉",
        "llm_fallback": "I'm SO here to help you shop at {business_name}! 🎉 Ask me about products, check your cart, or place an order!!! ✨",
    },
}


def register_conversation_templates() -> None:
    """Register conversation personality templates with the formatter."""
    PersonalityAwareResponseFormatter.register_response_type("conversation", CONVERSATION_TEMPLATES)
