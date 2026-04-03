"""Personality-aware response formatter (Story 5-12).

Provides personality-based templates for all bot response types,
ensuring consistent tone and style across all interactions.

Key Features:
- Templates for all response types: product_search, cart, checkout, order_tracking, handoff, error
- Three personality variants: Friendly, Professional, Enthusiastic
- Extensibility via register_response_type() class method
- Fallback to neutral templates when personality/template not found
"""

from __future__ import annotations

from typing import Any, ClassVar

import structlog

from app.models.merchant import PersonalityType
from app.services.personality.transition_phrases import (
    RESPONSE_TYPE_TO_TRANSITION,
    TEMPLATES_WITH_OPENINGS,
    TransitionCategory,
)
from app.services.personality.transition_selector import get_transition_selector

logger = structlog.get_logger(__name__)


class PersonalityAwareResponseFormatter:
    """Formats bot responses based on merchant personality type.

    This class provides personality-aware templates for all response types,
    ensuring consistent tone across the entire bot experience.

    Story 5-12: Bot Personality Consistency
    """

    TEMPLATES: ClassVar[dict[str, dict[PersonalityType, dict[str, str]]]] = {
        "product_search": {
            PersonalityType.FRIENDLY: {
                "found_single": "I found this for you at {business_name}! 😊\n\n• {title}{price}",
                "found_multiple": "Sure thing! Here's what I found at {business_name}! 👋\n\n{products}\n\nWould you like more details on any of these?",
                "no_results": "Hmm, I couldn't find anything matching '{query}'. Want to try a different search? 🤔",
                "fallback": "I don't have {query} at {business_name}, but here are some popular items:\n\n{products}\n\nInterested in any of these?",
                "recommendation_single": "My top pick at {business_name}:\n\n• {title}{price}",
                "recommendation_multiple": "Here are my recommendations from {business_name}:\n\n{products}\n{more_options}",
                "more_options": "\nWant to see more options?",
            },
            PersonalityType.PROFESSIONAL: {
                "found_single": "Here is the product available at {business_name}.\n\n• {title}{price}",
                "found_multiple": "Here are the available products at {business_name}.\n\n{products}\n\nWould you like additional information on any item?",
                "no_results": "I was unable to find any products matching '{query}' at {business_name}. Please try a different search term.",
                "fallback": "We do not have {query} at {business_name}, but here are some popular items:\n\n{products}\n\nWould you like more information on any of these?",
                "recommendation_single": "Our top recommendation at {business_name}:\n\n• {title}{price}",
                "recommendation_multiple": "Here are our recommendations from {business_name}:\n\n{products}\n{more_options}",
                "more_options": "\nWould you like to see additional options?",
            },
            PersonalityType.ENTHUSIASTIC: {
                "found_single": "YAY! Look what I found at {business_name}! ✨\n\n• {title}{price}",
                "found_multiple": "WOW!!! Check out these AMAZING finds at {business_name}! 🔥\n\n{products}\n\nWhich one catches your eye?! I'm SO excited to help you pick! 🎉",
                "no_results": "Oh no! I couldn't find anything matching '{query}'! 😢 But don't worry - let's try another search and find something AWESOME! 💪",
                "fallback": "Hmm, we don't have {query} at {business_name}, BUT check out these AMAZING popular items!!!\n\n{products}\n\nI bet you'll find something you LOVE! 💫",
                "recommendation_single": "My absolute FAVORITE pick at {business_name}!!! ⭐\n\n• {title}{price}",
                "recommendation_multiple": "Here are my TOP recommendations from {business_name} - you're gonna LOVE these!!! 💖\n\n{products}\n{more_options}",
                "more_options": "\nWant to see MORE awesome options?!",
            },
        },
        "cart": {
            PersonalityType.FRIENDLY: {
                "view_empty": "Your cart is empty. Would you like to browse our products? 😊",
                "view_items": "Here's what's in your cart:\n\n{items}\n\nSubtotal: {subtotal}",
                "add_success": "Added {title} to your cart! 🛒 Want to keep shopping or checkout?",
                "add_needs_selection": "I need to know which product to add. Which one would you like? 😊",
                "remove_success": "Item removed from your cart. Anything else I can help with?",
                "remove_needs_selection": "Which item would you like to remove from your cart?",
                "clear_success": "Your cart has been emptied. Would you like to browse our products?",
                "no_items_to_remove": "Your cart is already empty!",
                "item_not_found": "I couldn't find that item in your cart. Want me to show you what's in there? 🤔",
            },
            PersonalityType.PROFESSIONAL: {
                "view_empty": "Your cart is currently empty. Would you like to browse our products?",
                "view_items": "Current cart contents:\n\n{items}\n\nSubtotal: {subtotal}",
                "add_success": "{title} has been added to your cart. Would you like to continue shopping or proceed to checkout?",
                "add_needs_selection": "Please specify which product you would like to add to your cart.",
                "remove_success": "The item has been removed from your cart. Is there anything else I can assist with?",
                "remove_needs_selection": "Please specify which item you would like to remove from your cart.",
                "clear_success": "Your cart has been cleared. Would you like to browse our products?",
                "no_items_to_remove": "Your cart is already empty.",
                "item_not_found": "I was unable to locate that item in your cart. Would you like me to display your current cart contents?",
            },
            PersonalityType.ENTHUSIASTIC: {
                "view_empty": "Your cart is empty! Let's fill it up with something AWESOME! 🛍️",
                "view_items": "Here's what's in your cart - looking GREAT! 😍\n\n{items}\n\nSubtotal: {subtotal}",
                "add_success": "WOOHOO! {title} is now in your cart!!! 🛒 Ready for more or shall we checkout?!",
                "add_needs_selection": "I need to know which AWESOME product you want! Which one?! 🤩",
                "remove_success": "Item removed! Your cart is ready for more great finds! ✨",
                "remove_needs_selection": "Which item should I remove? Just let me know! 👍",
                "clear_success": "Cart cleared! Time for a fresh start - let's find something AMAZING! 🎉",
                "no_items_to_remove": "Your cart is already empty - let's fill it with something FANTASTIC! 💫",
                "item_not_found": "Hmm, I couldn't find that one in your cart! Want to see what's in there? 🔍",
            },
        },
        "checkout": {
            PersonalityType.FRIENDLY: {
                "empty_cart": "Your cart is empty! Add some items first before checking out. 😊",
                "ready": "Ready to checkout! 🛒 Click here to complete your order:\n\n{checkout_url}",
                "fallback": "I had trouble starting checkout. You can also checkout directly on our website!",
                "circuit_open": "I'm having trouble connecting to the store right now. Please try again in a moment! 🙏",
            },
            PersonalityType.PROFESSIONAL: {
                "empty_cart": "Your cart is currently empty. Please add items before proceeding to checkout.",
                "ready": "Ready for checkout. Please click the following link to complete your order:\n\n{checkout_url}",
                "fallback": "There was an issue initiating checkout. You may also checkout directly through our website.",
                "circuit_open": "We are currently experiencing connectivity issues. Please try again shortly.",
            },
            PersonalityType.ENTHUSIASTIC: {
                "empty_cart": "Oops! Your cart is empty! Let's fill it up with something AWESOME first! 🛍️",
                "ready": "LET'S DO THIS!!! 🎉 Ready to checkout - click here to complete your order:\n\n{checkout_url}\n\nYou're gonna LOVE your purchase! ✨",
                "fallback": "Hmm, I had a little trouble with checkout! But don't worry - you can checkout directly on our website too! 💪",
                "circuit_open": "We're having a tiny hiccup connecting to the store! Please try again in just a moment - thanks for your patience! 🙏",
            },
        },
        "order_tracking": {
            PersonalityType.FRIENDLY: {
                "not_found": "I couldn't find an order with that information. 😕 Want to try again with your order number or email?",
                "found": "Great news! Here's your order status! 📦\n\n{order_details}",
                "found_shipped": "Your order is on its way! 🚚\n\n{order_details}\n\n{tracking_info}",
                "found_delivered": "Your order has been delivered! 🎉\n\n{order_details}",
                "found_processing": "Your order is being prepared! 📦\n\n{order_details}",
                "tracking_info": "Tracking: {tracking_number}\nCarrier: {carrier}",
                "prompt_email": "I couldn't find orders on this device. 😊 I can look it up! What's your email address?",
                "prompt_order_number": "I couldn't find orders on this device. 😊 What's your order number?",
                "device_linked": "Found you, {customer_name}! 🎉 This device is now linked to your account!",
                "welcome_back": "Welcome back, {customer_name}! 👋",
            },
            PersonalityType.PROFESSIONAL: {
                "not_found": "I was unable to locate an order matching that information. Please try again with your order number or email address.",
                "found": "Order Status:\n\n{order_details}",
                "found_shipped": "Your order has been shipped.\n\n{order_details}\n\n{tracking_info}",
                "found_delivered": "Your order has been delivered.\n\n{order_details}",
                "found_processing": "Your order is currently being processed.\n\n{order_details}",
                "tracking_info": "Tracking Number: {tracking_number}\nCarrier: {carrier}",
                "prompt_email": "I was unable to locate orders on this device. Please provide your email address to look up your orders.",
                "prompt_order_number": "I was unable to locate orders on this device. Please provide your order number.",
                "device_linked": "Your device has been linked to your account, {customer_name}.",
                "welcome_back": "Welcome back, {customer_name}.",
            },
            PersonalityType.ENTHUSIASTIC: {
                "not_found": "Oh no! I couldn't find that order! 😢 Let's try again - what's your order number or email?!",
                "found": "YAY! Found your order!!! 🎉\n\n{order_details}",
                "found_shipped": "Your order is ON ITS WAY!!! 🚚💨\n\n{order_details}\n\n{tracking_info}",
                "found_delivered": "IT'S HERE!!! Your order has been delivered! 🎉🎉🎉\n\n{order_details}",
                "found_processing": "Your order is being prepared with care! 📦✨\n\n{order_details}",
                "tracking_info": "Tracking: {tracking_number}\nCarrier: {carrier}",
                "prompt_email": "I couldn't find orders on this device! Let me look it up for you! 😊 What's your email address?",
                "prompt_order_number": "I couldn't find orders on this device! What's your order number?! 🔍",
                "device_linked": "Found you, {customer_name}! 🎉 This device is now linked to your account - SO exciting! ✨",
                "welcome_back": "WELCOME BACK, {customer_name}!!! 👋🎉 So great to see you again! 💖",
            },
        },
        "handoff": {
            PersonalityType.FRIENDLY: {
                "standard": "I'm connecting you with a human agent who can help! 😊 They'll be with you shortly.",
                "after_hours": "Our team is currently offline. 😊 Leave a message and they'll get back to you during business hours!\n\nBusiness hours: {business_hours}",
                "queue_position": "You're #{position} in the queue. A human agent will be with you soon! ⏳",
                "resolved": "Glad I could help! Is there anything else you need? 😊",
            },
            PersonalityType.PROFESSIONAL: {
                "standard": "I am connecting you with a human agent who can assist you further. They will be with you shortly.",
                "after_hours": "Our team is currently unavailable. Please leave a message and they will respond during business hours.\n\nBusiness hours: {business_hours}",
                "queue_position": "You are #{position} in the queue. A human agent will assist you shortly.",
                "resolved": "I am glad I could assist. Is there anything else you require?",
            },
            PersonalityType.ENTHUSIASTIC: {
                "standard": "I'm connecting you with a SUPER helpful human agent right now! 😊 They'll be with you in a flash! ✨",
                "after_hours": "Our team is offline right now, but don't worry! 😊 Leave a message and they'll get back to you super soon!\n\nBusiness hours: {business_hours}",
                "queue_position": "You're #{position} in the queue - almost there! 🎉 A friendly human agent will be with you soon! ⏳✨",
                "resolved": "YAY! So glad I could help! 💖 Is there anything else you need?!",
            },
        },
        "error": {
            PersonalityType.FRIENDLY: {
                "general": "Oops, something went wrong! 😅 Please try again.",
                "search_failed": "I had trouble searching for products. Please try again! 🤔",
                "cart_failed": "I had trouble with your cart. Please try again!",
                "checkout_failed": "I had trouble with checkout. Please try again!",
                "order_lookup_failed": "I had trouble finding your order. Please try again!",
            },
            PersonalityType.PROFESSIONAL: {
                "general": "An error occurred. Please try your request again.",
                "search_failed": "Unable to complete product search. Please try again.",
                "cart_failed": "Unable to process cart request. Please try again.",
                "checkout_failed": "Unable to process checkout request. Please try again.",
                "order_lookup_failed": "Unable to locate order. Please try again.",
            },
            PersonalityType.ENTHUSIASTIC: {
                "general": "Oopsie! Something went a little wonky! 😅 Let's try again - it'll work this time! 💪",
                "search_failed": "Hmm, the search gremlins are acting up! 😅 Let's try again! 🔍",
                "cart_failed": "Oops! The cart is being a little shy! 😅 Let's give it another try! 🛒",
                "checkout_failed": "Eek! Checkout hit a tiny bump! 😅 Let's try again - you're SO close! ✨",
                "order_lookup_failed": "Hmm, I couldn't quite find that order! 😅 Let's try again! 🔍",
            },
        },
        "order_confirmation": {
            PersonalityType.FRIENDLY: {
                "confirmed": 'Great news! Your order #{order_number} is confirmed! 🎉\n\nEst. delivery: {delivery_date}\n\nTrack your order: Type "Where\'s my order?"',
            },
            PersonalityType.PROFESSIONAL: {
                "confirmed": 'Order Confirmation\n\nOrder #{order_number}\n\nEstimated delivery: {delivery_date}\n\nTo track your order, type "Where\'s my order?"',
            },
            PersonalityType.ENTHUSIASTIC: {
                "confirmed": 'OMG YOUR ORDER IS CONFIRMED!!! 🎉🎉🎉\n\nOrder #{order_number}\nEst. delivery: {delivery_date}\n\nWant to track it?! Just type "Where\'s my order?" anytime! ✨',
            },
        },
        "general_mode_fallback": {
            PersonalityType.FRIENDLY: {
                "ecommerce_not_supported": "I'm a general assistant right now! 😊 For product search, cart, and orders, please connect a Shopify store in Settings. I'm still here to help with general questions!",
            },
            PersonalityType.PROFESSIONAL: {
                "ecommerce_not_supported": "I'm currently operating in general assistant mode. For product search, cart management, and order tracking, please connect a Shopify store via Settings. I'm available to assist with general inquiries.",
            },
            PersonalityType.ENTHUSIASTIC: {
                "ecommerce_not_supported": "I'm your general AI assistant! ✨ For shopping features like product search and orders, connect a Shopify store in Settings. I'm super excited to help with any other questions!",
            },
        },
    }

    _custom_templates: ClassVar[dict[str, dict[PersonalityType, dict[str, str]]]] = {}

    @classmethod
    def register_response_type(
        cls,
        response_type: str,
        templates: dict[PersonalityType, dict[str, str]],
    ) -> None:
        """Register custom templates for a response type.

        Allows extension of the formatter with new response types
        without modifying the base class.

        Args:
            response_type: Unique identifier for the response type
            templates: Dictionary mapping personality types to message templates
        """
        cls._custom_templates[response_type] = templates
        logger.info(
            "custom_templates_registered",
            response_type=response_type,
            personalities=list(templates.keys()),
        )

    @classmethod
    def format_response(
        cls,
        response_type: str,
        message_key: str,
        personality: PersonalityType,
        include_transition: bool = False,
        conversation_id: str | None = None,
        mode: str = "ecommerce",
        validate: bool = False,
        **kwargs: Any,
    ) -> str:
        """Format a response using personality-appropriate template.

        Story 11-4: Added include_transition for transition phrase prefixing.
        Story 11-5: Added validate for optional personality validation logging.

        Args:
            response_type: Type of response (e.g., "product_search", "cart")
            message_key: Specific message template key (e.g., "found_single")
            personality: Merchant's personality type
            include_transition: Whether to prepend a transition phrase
            conversation_id: Conversation ID for anti-repetition tracking
            mode: "ecommerce" or "general" for mode-specific transitions
            validate: If True, run personality validation and log violations
            **kwargs: Variables to substitute in template

        Returns:
            Formatted message string
        """
        template = cls._get_template(response_type, message_key, personality)

        if template is None:
            logger.warning(
                "template_not_found",
                response_type=response_type,
                message_key=message_key,
                personality=personality.value,
            )
            return cls._format_neutral_fallback(response_type, message_key, **kwargs)

        try:
            formatted = template.format(**kwargs)
        except KeyError as e:
            logger.warning(
                "template_substitution_failed",
                response_type=response_type,
                message_key=message_key,
                missing_key=str(e),
            )
            return template

        if include_transition and response_type in RESPONSE_TYPE_TO_TRANSITION:
            if message_key in TEMPLATES_WITH_OPENINGS.get(response_type, set()):
                if validate:
                    cls._run_validation(formatted, personality, response_type, message_key)
                return formatted
            category = RESPONSE_TYPE_TO_TRANSITION[response_type]
            selector = get_transition_selector()
            transition = selector.select(category, personality, conversation_id, mode)
            result = f"{transition} {formatted}"
            if validate:
                cls._run_validation(result, personality, response_type, message_key)
            return result

        if validate:
            cls._run_validation(formatted, personality, response_type, message_key)
        return formatted

    @classmethod
    def _run_validation(
        cls,
        text: str,
        personality: PersonalityType,
        response_type: str,
        message_key: str,
    ) -> None:
        """Run personality validation on formatted text (advisory only).

        Logs violations as warnings but never blocks the response.
        """
        from app.services.personality.personality_validator import validate_personality

        result = validate_personality(text, personality)
        if not result.passed:
            logger.warning(
                "personality_validation_violation",
                response_type=response_type,
                message_key=message_key,
                personality=personality.value,
                violations=result.violations,
                severity=result.severity,
            )

    @classmethod
    def _get_template(
        cls,
        response_type: str,
        message_key: str,
        personality: PersonalityType,
    ) -> str | None:
        """Get template string for the given parameters.

        Checks custom templates first, then built-in templates.

        Args:
            response_type: Type of response
            message_key: Specific message template key
            personality: Merchant's personality type

        Returns:
            Template string or None if not found
        """
        if response_type in cls._custom_templates:
            personality_templates = cls._custom_templates[response_type].get(personality)
            if personality_templates and message_key in personality_templates:
                return personality_templates[message_key]

        if response_type in cls.TEMPLATES:
            personality_templates = cls.TEMPLATES[response_type].get(personality)
            if personality_templates and message_key in personality_templates:
                return personality_templates[message_key]

        return None

    @classmethod
    def _format_neutral_fallback(
        cls,
        response_type: str,
        message_key: str,
        **kwargs: Any,
    ) -> str:
        """Generate a neutral fallback message when template not found.

        Provides basic, personality-agnostic message for graceful degradation.

        Args:
            response_type: Type of response
            message_key: Specific message template key
            **kwargs: Variables that might be useful

        Returns:
            Neutral fallback message
        """
        fallbacks = {
            ("product_search", "found_single"): "Found: {title}",
            ("product_search", "found_multiple"): "Products found.",
            ("product_search", "no_results"): "No products found.",
            ("product_search", "fallback"): "Here are some products.",
            ("cart", "view_empty"): "Your cart is empty.",
            ("cart", "view_items"): "Cart contents: {items}",
            ("cart", "add_success"): "Added {title} to cart.",
            ("cart", "remove_success"): "Item removed from cart.",
            ("cart", "clear_success"): "Cart cleared.",
            ("checkout", "empty_cart"): "Cart is empty.",
            ("checkout", "ready"): "Ready for checkout: {checkout_url}",
            ("order_tracking", "not_found"): "Order not found.",
            ("order_tracking", "found"): "Order found.",
            ("handoff", "standard"): "Connecting to human agent.",
            ("error", "general"): "An error occurred.",
        }

        key = (response_type, message_key)
        if key in fallbacks:
            try:
                return fallbacks[key].format(**kwargs)
            except KeyError:
                return fallbacks[key]

        return "I'm here to help."
