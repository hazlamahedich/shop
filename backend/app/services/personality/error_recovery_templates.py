"""Error recovery personality templates for natural error handling (Story 11-7).

Context-aware suggestion templates used by NaturalErrorRecoveryService.
These provide actionable next steps after errors, using conversation state.

Registered via PersonalityAwareResponseFormatter.register_response_type().
All 3 personality variants must be defined for each key to prevent KeyError.
"""

from app.models.merchant import PersonalityType
from app.services.personality.response_formatter import PersonalityAwareResponseFormatter

ERROR_RECOVERY_TEMPLATES = {
    PersonalityType.FRIENDLY: {
        "search_retry_with_last_query": (
            "Want to try searching for '{last_query}' again? I'm happy to look! 😊"
        ),
        "search_browse_viewed": (
            "We could also browse those products you were looking at earlier! Want me to show them? 😊"
        ),
        "cart_retry_viewed_product": ("Want me to try adding that product to your cart again? 😊"),
        "checkout_retry_with_cart": ("Your cart is still ready! Want to try checkout again? 😊"),
        "order_lookup_retry": (
            "Try sharing your order number or email and I'll look it up for you! 😊"
        ),
        "llm_timeout_with_last_query": (
            "Want me to search for '{last_query}' instead? I can help with that! 😊"
        ),
        "llm_timeout_generic": (
            "Ask me about products, your cart, or an order — I'm here to help! 😊"
        ),
        "context_lost_suggestion": (
            "Let's start fresh! Ask me anything — products, cart, orders — I'm ready! 😊"
        ),
    },
    PersonalityType.PROFESSIONAL: {
        "search_retry_with_last_query": ("Would you like me to search for '{last_query}' again?"),
        "search_browse_viewed": (
            "Alternatively, I can show you the products you were viewing earlier."
        ),
        "cart_retry_viewed_product": (
            "Would you like me to attempt adding that product to your cart again?"
        ),
        "checkout_retry_with_cart": (
            "Your cart is still available. Would you like to retry checkout?"
        ),
        "order_lookup_retry": (
            "Please provide your order number or email address and I will look it up."
        ),
        "llm_timeout_with_last_query": ("Would you like me to search for '{last_query}' instead?"),
        "llm_timeout_generic": (
            "I can help with products, cart, or order inquiries. What would you like?"
        ),
        "context_lost_suggestion": ("Let's start over. How can I assist you today?"),
    },
    PersonalityType.ENTHUSIASTIC: {
        "search_retry_with_last_query": (
            "Let's try searching for '{last_query}' again — I'm ON it! 🔍"
        ),
        "search_browse_viewed": (
            "OR I can show you those AWESOME products you were checking out earlier! 😍"
        ),
        "cart_retry_viewed_product": (
            "Want me to pop that product into your cart?! Let's DO this! 🛒"
        ),
        "checkout_retry_with_cart": (
            "Your cart is still ready and waiting — let's try checkout AGAIN! 🛒✨"
        ),
        "order_lookup_retry": ("Try your order number or email — I'll find it for you! 🔍"),
        "llm_timeout_with_last_query": (
            "Want me to search for '{last_query}' instead?! I'm ON it! 🔍"
        ),
        "llm_timeout_generic": ("Ask me about products, your cart, or an order — I'm READY! 💪"),
        "context_lost_suggestion": (
            "Fresh start! Ask me ANYTHING — products, cart, orders — I'm SO ready! 🎉"
        ),
    },
}


def register_error_recovery_templates() -> None:
    """Register error recovery personality templates with the formatter."""
    PersonalityAwareResponseFormatter.register_response_type(
        "error_recovery", ERROR_RECOVERY_TEMPLATES
    )
