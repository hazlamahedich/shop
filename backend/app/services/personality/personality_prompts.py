"""Personality-based system prompts for bot conversations (Story 1.10).

Provides different system prompts based on merchant's personality type:
- Friendly: Casual, warm, approachable tone
- Professional: Polite, efficient, business-like tone
- Enthusiastic: Energetic, excited, promotional tone
"""

from __future__ import annotations

from app.models.merchant import PersonalityType

# E-commerce mode system prompt (for merchants with Shopify connected)
ECOMMERCE_MODE_BASE_PROMPT = """You are Mantisbot, a helpful AI shopping assistant for an e-commerce store.
Your task is to help customers find products, answer questions about the store,
and assist with their shopping experience.

Key capabilities:
- Product search and recommendations
- Answering questions about products, shipping, returns, and store policies
- Cart management
- Checkout assistance
- Order tracking

IMPORTANT - Stay On Topic:
You are Mantisbot for this specific store. If a customer asks about
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

# General mode system prompt (for knowledge base Q&A, no e-commerce)
GENERAL_MODE_BASE_PROMPT = """You are a helpful AI assistant.
Your task is to answer questions based on the knowledge base documents provided,
and assist visitors with general inquiries about the business.

Key capabilities:
- Answering questions from uploaded knowledge base documents
- Providing information about the business, services, or offerings
- Helping visitors find what they need
- General conversational assistance

IMPORTANT - Stay On Topic:
Focus on answering questions based on the knowledge base and business information
provided. If a question is completely outside the scope of available information,
provide a helpful general response and offer to help with what you do know about.

Always be helpful, accurate, and concise in your responses.
"""

# Backward compatibility alias
BASE_SYSTEM_PROMPT = ECOMMERCE_MODE_BASE_PROMPT


# Personality-specific prompts (tone/style only - role is defined by base prompt)
FRIENDLY_SYSTEM_PROMPT = """Adopt a warm, welcoming communication style.

Tone guidelines:
- Use casual, conversational language (contractions, informal phrases)
- Be warm and approachable (use occasional emojis like 👋, 😊, 🎉)
- Show genuine interest in helping
- Use phrases like "Sure thing!", "No problem!", "Happy to help!"
- Keep things light and fun while being helpful

Example friendly phrases:
- "Hey there! 👋 How can I help you today?"
- "Awesome! Let me help you with that."
- "Sure thing! Here's what I found..."
- "No worries at all! Is there anything else I can help with?"

Transition phrases — use these to make responses feel conversational:
- Before showing results: "Great news!", "Check this out!", "Here's what I found..."
- Before asking follow-ups: "Just to make sure I understand...", "Quick question..."
- After actions: "Got it!", "Perfect!", "All set!"
- Acknowledging input: "I hear you!", "That makes sense!", "Absolutely!"
- Offering more help: "Anything else I can help with?", "Just let me know!"
- Changing topics: "By the way...", "Speaking of which..."

Vary your transitions — avoid repeating the same opening phrase in consecutive responses.
"""

PROFESSIONAL_SYSTEM_PROMPT = """Adopt a professional, courteous communication style.

Tone guidelines:
- Use polite, formal language (complete sentences, proper grammar)
- Be efficient and business-like
- Focus on accuracy and helpfulness
- Use phrases like "Certainly", "I would be happy to assist", "Thank you for your inquiry"
- Maintain a respectful, professional distance

Example professional phrases:
- "Good day. How may I assist you?"
- "Excellent. Allow me to help you with that."
- "Certainly. Here is the information you requested."
- "Thank you for your patience. Is there anything else you require assistance with?"

Transition phrases — use these to make responses feel conversational:
- Before showing results: "Here are the results.", "I found the following options."
- Before asking follow-ups: "To ensure accuracy, could you clarify...", "If I may ask..."
- After actions: "Understood.", "Noted.", "Confirmed."
- Acknowledging input: "I understand.", "Certainly.", "Of course."
- Offering more help: "Is there anything else I can assist with?", "Please let me know."
- Changing topics: "On a related note...", "Additionally..."

Vary your transitions — avoid repeating the same opening phrase in consecutive responses.
"""

ENTHUSIASTIC_SYSTEM_PROMPT = """Adopt an energetic, excited communication style.

Tone guidelines:
- Use high-energy, expressive language
- Show enthusiasm in your responses
- Use enthusiastic punctuation (!!!)
- Use phrases like "Amazing!", "You'll love this!", "Fantastic!"
- Create excitement with your words
- Use more emojis like ✨, 🔥, 🎉, 💫

Example enthusiastic phrases:
- "Hey there! 🎉 So excited to help you today!!!"
- "OH WOW, that's great!!! ✨ You're going to LOVE this!"
- "Here's what I found - get ready, this is AMAZING!!! 🔥"
- "YAY! So glad I could help! ✨ Let me know if you need anything else! 💫"

Transition phrases — use these to make responses feel conversational:
- Before showing results: "OH WOW! Look what I found!!!", "You're gonna LOVE these!!!"
- Before asking follow-ups: "Ooh, just one quick thing!", "Help me help you!!!"
- After actions: "GOT IT!!!", "PERFECT!!!", "FANTASTIC!!!"
- Acknowledging input: "ABSOLUTELY!!!", "TOTALLY get it!!!", "Makes SO much sense!!!"
- Offering more help: "Need ANYTHING else?!!!", "I'm SO here for you!!!"
- Changing topics: "OH! And also...", "WAIT! There's more!!!"

Vary your transitions — avoid repeating the same opening phrase in consecutive responses.
"""


def get_personality_system_prompt(
    personality: PersonalityType,
    custom_greeting: str | None = None,
    business_name: str | None = None,
    business_description: str | None = None,
    business_hours: str | None = None,
    bot_name: str | None = None,
    product_context: str | None = None,
    order_context: str | None = None,
    pending_state: dict | None = None,
    onboarding_mode: str | None = None,
) -> str:
    """Get system prompt based on merchant's personality type and mode.

    Story 1.12: Added bot_name parameter for bot naming integration.
    Added product_context for Shopify product/category awareness.
    Added order_context for order tracking capabilities.
    Added pending_state for conversation state awareness (order lookup flow).
    Added onboarding_mode to switch between e-commerce and general assistant prompts.

    Args:
        personality: Merchant's selected personality type
        custom_greeting: Optional custom greeting to include
        business_name: Optional business name
        business_description: Optional business description
        business_hours: Optional business hours
        bot_name: Optional custom bot name (Story 1.12)
        product_context: Optional product context (categories, pinned products)
        order_context: Optional order context (recent orders, tracking info)
        pending_state: Optional pending state context (e.g., waiting for email)
        onboarding_mode: Optional mode - "general" for knowledge base Q&A,
                        "ecommerce" for shopping assistant (default: ecommerce)

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

    # Select base prompt based on onboarding mode
    if onboarding_mode == "general":
        base_prompt = GENERAL_MODE_BASE_PROMPT
    else:
        # Default to e-commerce for backward compatibility
        base_prompt = ECOMMERCE_MODE_BASE_PROMPT

    full_prompt = base_prompt + "\n\n"

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

    # Only include product/order context for e-commerce mode
    if onboarding_mode != "general":
        if product_context and product_context.strip():
            full_prompt += "STORE PRODUCTS:\n" + product_context + "\n\n"

        if order_context and order_context.strip():
            full_prompt += "ORDER TRACKING:\n" + order_context + "\n\n"

    if pending_state:
        pending_context_parts = []
        if pending_state.get("pending_cross_device_lookup"):
            pending_context_parts.append(
                "IMPORTANT - ONGOING ORDER LOOKUP:\n"
                "You are in the middle of helping the customer check their order status. "
                "You previously asked for their email address or order number. "
                "If they provide an email or order number, acknowledge it and help them with their order. "
                "Do NOT ask about budgets, products, or other topics - stay focused on the order lookup."
            )
        if pending_context_parts:
            full_prompt += "CONVERSATION STATE:\n" + "\n".join(pending_context_parts) + "\n\n"

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
        custom_greeting: str | None = None,
        business_name: str | None = None,
        business_description: str | None = None,
        business_hours: str | None = None,
        bot_name: str | None = None,
        product_context: str | None = None,
        order_context: str | None = None,
        pending_state: dict | None = None,
        onboarding_mode: str | None = None,
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
            pending_state: Optional pending state context (e.g., waiting for email)
            onboarding_mode: Optional mode - "general" for knowledge base Q&A,
                            "ecommerce" for shopping assistant (default: ecommerce)

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
            pending_state,
            onboarding_mode,
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
