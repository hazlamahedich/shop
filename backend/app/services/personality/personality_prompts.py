"""Personality-based system prompts for bot conversations (Story 1.10).

Provides different system prompts based on merchant's personality type:
- Friendly: Casual, warm, approachable tone
- Professional: Polite, efficient, business-like tone
- Enthusiastic: Energetic, excited, promotional tone
"""

from __future__ import annotations

from typing import Optional

from app.models.merchant import PersonalityType


# Base system prompt template
BASE_SYSTEM_PROMPT = """You are a helpful shopping assistant for an e-commerce store.
Your task is to help customers find products, answer questions about the store,
and assist with their shopping experience.

Key capabilities:
- Product search and recommendations
- Answering questions about products, shipping, returns, and store policies
- Cart management
- Checkout assistance
- Order tracking

IMPORTANT - Stay On Topic:
You are a SHOPPING ASSISTANT for this specific store. If a customer asks about
topics unrelated to shopping, products, or this store (e.g., general knowledge
questions, current events, other websites), politely redirect them back to how
you can help with their shopping needs.

IMPORTANT - Reference Store Products:
When redirecting or answering general questions, mention what your store
actually sells based on the "STORE PRODUCTS" section below. This helps customers
understand what you offer.

Example redirects that reference store products:
- "I don't serve coffee, but I can help you find [mention product types]!"
- "I'm here to help with [mention product categories]! What would you like?"
- "That's not something we offer, but check out our [mention key products]!"

Always be helpful, accurate, and concise in your responses.
"""


# Personality-specific prompts
FRIENDLY_SYSTEM_PROMPT = """You are a friendly shopping assistant who creates a warm, welcoming experience.

Tone guidelines:
- Use casual, conversational language (contractions, informal phrases)
- Be warm and approachable (use occasional emojis like 👋, 😊, 🎉)
- Show genuine interest in helping the customer
- Use phrases like "Sure thing!", "No problem!", "Happy to help!"
- Keep things light and fun while being helpful

Example friendly phrases:
- "Hey there! 👋 How can I help you today?"
- "Awesome choice! Let me find that for you."
- "Sure thing! Here's what I found..."
- "No worries at all! Is there anything else I can help with?"
"""

PROFESSIONAL_SYSTEM_PROMPT = """You are a professional shopping assistant who provides efficient, courteous service.

Tone guidelines:
- Use polite, formal language (complete sentences, proper grammar)
- Be efficient and business-like
- Focus on accuracy and helpfulness
- Use phrases like "Certainly", "I would be happy to assist", "Thank you for your inquiry"
- Maintain a respectful, professional distance

Example professional phrases:
- "Good day. How may I assist you with your shopping needs?"
- "Excellent choice. Allow me to locate that item for you."
- "Certainly. Here are the available options."
- "Thank you for your patience. Is there anything else you require assistance with?"
"""

ENTHUSIASTIC_SYSTEM_PROMPT = (
    """You are an enthusiastic shopping assistant who brings energetic excitement to shopping.

Tone guidelines:
- Use high-energy, expressive language
- Be excited about products and recommendations
- Use enthusiastic punctuation (!!!, ¡)
- Use phrases like "Amazing!", "You'll love this!", "Fantastic choice!"
- Create excitement about deals and products
- Use more emojis like ✨, 🔥, 🛍️, 💫

Example enthusiastic phrases:
- "Hey there! 🎉 So excited to help you find something amazing today!!!"
- "OH WOW, fantastic choice!!! ✨ You're going to LOVE this!"
- "Here's what I found - get ready, these are AMAZING!!! 🔥"
- "YAY! So glad I could help! ✨ Let me know if you need anything else! 💫" """
    ""
)


def get_personality_system_prompt(
    personality: PersonalityType,
    custom_greeting: Optional[str] = None,
    business_name: Optional[str] = None,
    business_description: Optional[str] = None,
    business_hours: Optional[str] = None,
    bot_name: Optional[str] = None,
    product_context: Optional[str] = None,
    order_context: Optional[str] = None,
) -> str:
    """Get system prompt based on merchant's personality type.

    Story 1.12: Added bot_name parameter for bot naming integration.
    Added product_context for Shopify product/category awareness.
    Added order_context for order tracking capabilities.

    Args:
        personality: Merchant's selected personality type
        custom_greeting: Optional custom greeting to include
        business_name: Optional business name
        business_description: Optional business description
        business_hours: Optional business hours
        bot_name: Optional custom bot name (Story 1.12)
        product_context: Optional product context (categories, pinned products)
        order_context: Optional order context (recent orders, tracking info)

    Returns:
        System prompt string with personality-appropriate tone

    Examples:
        >>> get_personality_system_prompt(PersonalityType.FRIENDLY)
        'You are a friendly shopping assistant...'
    """
    if personality == PersonalityType.FRIENDLY:
        personality_prompt = FRIENDLY_SYSTEM_PROMPT
    elif personality == PersonalityType.PROFESSIONAL:
        personality_prompt = PROFESSIONAL_SYSTEM_PROMPT
    elif personality == PersonalityType.ENTHUSIASTIC:
        personality_prompt = ENTHUSIASTIC_SYSTEM_PROMPT
    else:
        personality_prompt = FRIENDLY_SYSTEM_PROMPT

    full_prompt = BASE_SYSTEM_PROMPT + "\n\n"

    if bot_name and bot_name.strip():
        full_prompt += f'Your name is {bot_name}. When introducing yourself, use phrases like "I\'m {bot_name}" or "This is {bot_name}".\n\n'

    business_info_parts = []
    if business_name:
        business_info_parts.append(f"Business Name: {business_name}")
    if business_description:
        business_info_parts.append(f"Description: {business_description}")
    if business_hours:
        business_info_parts.append(f"Hours: {business_hours}")

    if business_info_parts:
        full_prompt += "BUSINESS INFORMATION:\n" + "\n".join(business_info_parts) + "\n\n"

    if product_context and product_context.strip():
        full_prompt += "STORE PRODUCTS:\n" + product_context + "\n\n"

    if order_context and order_context.strip():
        full_prompt += "ORDER TRACKING:\n" + order_context + "\n\n"

    full_prompt += f"COMMUNICATION STYLE:\n{personality_prompt}"

    return full_prompt


class PersonalityPromptService:
    """Service for generating personality-based system prompts.

    This service provides system prompts that adapt the bot's communication
    style based on the merchant's selected personality type.

    Story 1.10: Bot Personality Configuration
    """

    def __init__(self) -> None:
        """Initialize the personality prompt service."""
        pass

    def get_system_prompt(
        self,
        personality: PersonalityType,
        custom_greeting: Optional[str] = None,
        business_name: Optional[str] = None,
        business_description: Optional[str] = None,
        business_hours: Optional[str] = None,
        bot_name: Optional[str] = None,
        product_context: Optional[str] = None,
        order_context: Optional[str] = None,
    ) -> str:
        """Get system prompt for the given personality.

        Args:
            personality: Merchant's personality type
            custom_greeting: Optional custom greeting message
            business_name: Optional business name
            business_description: Optional business description
            business_hours: Optional business hours
            bot_name: Optional custom bot name (Story 1.12)
            product_context: Optional product context (categories, pinned products)
            order_context: Optional order context (recent orders, tracking info)

        Returns:
            System prompt string with personality-appropriate tone
        """
        return get_personality_system_prompt(
            personality,
            custom_greeting,
            business_name,
            business_description,
            business_hours,
            bot_name,
            product_context,
            order_context,
        )

    def get_prompt_description(self, personality: PersonalityType) -> str:
        """Get human-readable description of a personality type.

        Args:
            personality: Personality type to describe

        Returns:
            Description string for UI display
        """
        descriptions = {
            PersonalityType.FRIENDLY: "Warm and casual - creates a friendly, approachable experience",
            PersonalityType.PROFESSIONAL: "Polite, professional, and efficient - provides courteous, business-like service",
            PersonalityType.ENTHUSIASTIC: "Enthusiastic, energetic, and excited - brings high energy to shopping",
        }
        return descriptions.get(personality, descriptions[PersonalityType.FRIENDLY])
