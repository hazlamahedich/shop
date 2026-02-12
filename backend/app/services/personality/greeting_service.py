"""Greeting template service (Story 1.14).

Provides personality-based default greeting templates with variable
substitution for bot's first message to customers.

Key Features:
- Default greetings for each personality type (Friendly, Professional, Enthusiastic)
- Variable substitution: {bot_name}, {business_name}, {business_hours}
- Custom greeting support with fallback to personality defaults
"""

from __future__ import annotations

import re
from typing import Optional

from app.models.merchant import PersonalityType


# Default greeting templates for each personality type
# These match the AC specifications exactly
DEFAULT_GREETINGS = {
    PersonalityType.FRIENDLY: (
        "Hey there! 👋 I'm {bot_name} from {business_name}. How can I help you today?"
    ),
    PersonalityType.PROFESSIONAL: (
        "Good day. I am {bot_name} from {business_name}. How may I assist you today?"
    ),
    PersonalityType.ENTHUSIASTIC: (
        "Hello! 🎉 I'm {bot_name} from {business_name}. How can I help you find exactly what you need!!! ✨ What can I help you with today?"
    ),
}


def get_default_greeting(personality: PersonalityType) -> str:
    """Get default greeting template for a personality type.

    Args:
        personality: The merchant's selected personality type

    Returns:
        Default greeting template with placeholder variables

    Examples:
        >>> get_default_greeting(PersonalityType.FRIENDLY)
        "Hey there! 👋 I'm {bot_name} from {business_name}. How can I help you today?"
    """
    # Return personality-based greeting or fallback to friendly
    return DEFAULT_GREETINGS.get(personality, DEFAULT_GREETINGS[PersonalityType.FRIENDLY])


def substitute_greeting_variables(
    template: str,
    merchant_config: dict[str, Optional[str]],
) -> str:
    """Substitute placeholder variables in greeting template.

    CRITICAL: Supports {bot_name}, {business_name}, AND {business_hours}
    as specified in Story 1.14 AC3 and AC6.

    Leaves missing placeholders as-is (e.g., {business_name} when value not provided).
    Substitutes with defaults for bot_name and business_name when empty/None.
    Handles {business_hours} by leaving placeholder as-is or using "hours" default when empty.

    Args:
        template: Greeting template with placeholder variables
        merchant_config: Dictionary containing merchant configuration values
            - bot_name: Optional[str] - Custom bot name (Story 1.12)
            - business_name: Optional[str] - Business name (Story 1.11)
            - business_hours: Optional[str] - Business hours (Story 1.11)

    Returns:
        Greeting template with variables substituted

    Examples:
        >>> substitute_greeting_variables(
        ...     "Hi! I'm {bot_name} from {business_name}.",
        ...     {"bot_name": "GearBot", "business_name": "Alex's Gear"}
        ... )
        "Hi! I'm GearBot from Alex's Gear."

        >>> # Partial substitution - missing business_name
        >>> substitute_greeting_variables(
        ...     "Hi! I'm {bot_name} from {business_name}.",
        ...     {"bot_name": "GearBot"}
        ... )
        "Hi! I'm GearBot from {business_name}."  # Unsubstituted variable remains
    """
    # Build substitution map
    # Rules:
    # - If config is completely empty: use defaults for bot_name/business_name
    # - If config has some keys: only substitute keys that exist (use default if empty)
    # - business_hours: only substitute if key exists (leave placeholder if missing)
    substitutions = {}
    is_config_empty = not merchant_config or len(merchant_config) == 0

    # bot_name: substitute if key in config OR config is empty
    if is_config_empty or "bot_name" in merchant_config:
        if is_config_empty:
            substitutions["bot_name"] = "your shopping assistant"
        elif "bot_name" in merchant_config:
            bot_name_value = merchant_config["bot_name"]
            if bot_name_value is None or bot_name_value.strip() == "":
                substitutions["bot_name"] = "your shopping assistant"
            else:
                substitutions["bot_name"] = bot_name_value

    # business_name: substitute if key in config OR config is empty
    if is_config_empty or "business_name" in merchant_config:
        if is_config_empty:
            substitutions["business_name"] = "the store"
        elif "business_name" in merchant_config:
            business_name_value = merchant_config["business_name"]
            if business_name_value is None or business_name_value.strip() == "":
                substitutions["business_name"] = "the store"
            else:
                substitutions["business_name"] = business_name_value

    # business_hours: only substitute if key exists in config (optional)
    if "business_hours" in merchant_config:
        business_hours_value = merchant_config["business_hours"]
        substitutions["business_hours"] = business_hours_value or ""

    # Manual string substitution - only replaces keys that are in substitutions map
    # Placeholders for keys NOT in map remain unchanged
    result = template
    for key, value in substitutions.items():
        # Use regex to replace all occurrences of {key} with value
        result = re.sub(rf'\{{{re.escape(key)}\}}', value, result)

    return result


def get_effective_greeting(merchant_config: dict[str, Optional[str]]) -> str:
    """Get the effective greeting for a merchant.

    Returns custom greeting if use_custom_greeting is True and
    custom greeting is non-empty. Otherwise returns personality-based
    default greeting with variable substitution.

    Args:
        merchant_config: Dictionary containing:
            - personality: Personality type enum
            - custom_greeting: Optional custom greeting template
            - use_custom_greeting: Boolean flag for custom greeting
            - bot_name: Optional bot name
            - business_name: Optional business name
            - business_hours: Optional business hours

    Returns:
        The effective greeting message for the bot

    Examples:
        >>> # Custom greeting enabled
        >>> get_effective_greeting({
        ...     "use_custom_greeting": True,
        ...     "custom_greeting": "Welcome!",
        ... })
        "Welcome!"

        >>> # Custom greeting disabled, use personality default
        >>> get_effective_greeting({
        ...     "personality": PersonalityType.FRIENDLY,
        ...     "use_custom_greeting": False,
        ...     "bot_name": "GearBot",
        ...     "business_name": "Alex's Gear",
        ... })
        "Hey there! 👋 I'm GearBot from Alex's Gear. How can I help you today?"
    """
    use_custom = merchant_config.get("use_custom_greeting", False)
    # Handle personality value which could be PersonalityType, str, or None
    personality_raw = merchant_config.get("personality", PersonalityType.FRIENDLY)
    if isinstance(personality_raw, PersonalityType):
        personality = personality_raw
    else:
        # Default to FRIENDLY for any invalid/unknown personality value
        personality = PersonalityType.FRIENDLY

    # Check if custom greeting should be used
    if use_custom:
        custom_greeting = merchant_config.get("custom_greeting", "")
        # Use custom if non-empty after stripping
        if custom_greeting and custom_greeting.strip():
            return custom_greeting

    # Fall back to personality-based default with variable substitution
    default_template = get_default_greeting(personality)
    return substitute_greeting_variables(default_template, merchant_config)
