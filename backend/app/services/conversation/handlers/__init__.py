"""Handlers for unified conversation processing.

Story 5-10: Widget Full App Integration
Task 1: Create UnifiedConversationService
Task 16: ClarificationHandler

Story 5-10 Code Review Fix (C9): Added HandoffHandler

Story 6-1: Opt-In Consent Flow
Task 3.3: Added ForgetPreferencesHandler

Story 11-6: Contextual Product Recommendations
Added RecommendationHandler
"""

from app.services.conversation.handlers.base_handler import BaseHandler
from app.services.conversation.handlers.cart_handler import CartHandler
from app.services.conversation.handlers.check_consent_handler import CheckConsentHandler
from app.services.conversation.handlers.checkout_handler import CheckoutHandler
from app.services.conversation.handlers.clarification_handler import ClarificationHandler
from app.services.conversation.handlers.forget_preferences_handler import ForgetPreferencesHandler
from app.services.conversation.handlers.greeting_handler import GreetingHandler
from app.services.conversation.handlers.handoff_handler import HandoffHandler
from app.services.conversation.handlers.llm_handler import LLMHandler
from app.services.conversation.handlers.order_handler import OrderHandler
from app.services.conversation.handlers.recommendation_handler import RecommendationHandler
from app.services.conversation.handlers.search_handler import SearchHandler
from app.services.conversation.handlers.summarize_handler import SummarizeHandler

__all__ = [
    "BaseHandler",
    "CartHandler",
    "CheckConsentHandler",
    "CheckoutHandler",
    "ClarificationHandler",
    "ForgetPreferencesHandler",
    "GreetingHandler",
    "HandoffHandler",
    "LLMHandler",
    "OrderHandler",
    "RecommendationHandler",
    "SearchHandler",
    "SummarizeHandler",
]
