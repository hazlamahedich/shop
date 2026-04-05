"""Transition phrase library for conversational responses (Story 11-4).

Provides categorized transition phrases with personality variants
for natural conversational flow between bot responses.

Categories:
- SHOWING_RESULTS: Phrases before presenting search/tracking results
- CLARIFYING: Phrases before asking follow-up questions
- CONFIRMING: Phrases acknowledging user actions (cart add, etc.)
- ACKNOWLEDGING: Phrases acknowledging user input/situations
- TRANSITIONING_TOPICS: Phrases for topic changes
- OFFERING_HELP: Phrases offering further assistance
"""

from __future__ import annotations

from enum import Enum

from app.models.merchant import PersonalityType


class TransitionCategory(str, Enum):
    SHOWING_RESULTS = "showing_results"
    CLARIFYING = "clarifying"
    CONFIRMING = "confirming"
    ACKNOWLEDGING = "acknowledging"
    TRANSITIONING_TOPICS = "transitioning_topics"
    OFFERING_HELP = "offering_help"


TRANSITION_PHRASES: dict[TransitionCategory, dict[PersonalityType, list[str]]] = {
    TransitionCategory.SHOWING_RESULTS: {
        PersonalityType.FRIENDLY: [
            "Great news! I found...",
            "Check this out!",
            "Here's what I discovered...",
            "Look what I found for you!",
            "Good news!...",
            "Nice! Here's what came up...",
            "Oh nice, check these out...",
        ],
        PersonalityType.PROFESSIONAL: [
            "Here are the results.",
            "I found the following options.",
            "Based on your criteria, these are available.",
            "The search returned these matches.",
            "Available options are as follows.",
            "Here are the matching results.",
            "The following items meet your requirements.",
        ],
        PersonalityType.ENTHUSIASTIC: [
            "OH WOW! Look what I found!!!",
            "AMAZING news!!! Check these out!!!",
            "You're gonna LOVE these!!!",
            "SO EXCITING! Here they are!!!",
            "GET READY!!! Found some gems!!!",
            "OH MY GOSH!!! These are PERFECT!!!",
            "LOOK AT THESE INCREDIBLE FINDS!!!",
        ],
    },
    TransitionCategory.CLARIFYING: {
        PersonalityType.FRIENDLY: [
            "Just to make sure I understand...",
            "Quick question...",
            "Help me narrow this down...",
            "So I can find the perfect match...",
            "Let me get this right...",
            "Just one thing...",
            "So I can point you in the right direction...",
        ],
        PersonalityType.PROFESSIONAL: [
            "To ensure accuracy, could you clarify...",
            "For the best results, please specify...",
            "To assist you better, I need one more detail...",
            "If I may ask...",
            "To confirm your requirements...",
            "Could you provide additional detail...",
            "To narrow the options precisely...",
        ],
        PersonalityType.ENTHUSIASTIC: [
            "Ooh, just one quick thing!",
            "Help me help you!!!",
            "Almost there! Just need...",
            "SO close! One more detail...",
            "Let's nail this down!!!",
            "Just a tiny detail and we're GOLDEN!!!",
            "One more thing and I'll find something AMAZING!!!",
        ],
    },
    TransitionCategory.CONFIRMING: {
        PersonalityType.FRIENDLY: [
            "Got it!",
            "Perfect!",
            "Thanks for that!",
            "Noted!",
            "Awesome, I've got that down!",
            "Right on!",
            "Sweet, all set!",
        ],
        PersonalityType.PROFESSIONAL: [
            "Understood.",
            "Thank you for that information.",
            "Noted.",
            "Confirmed.",
            "I have that recorded.",
            "Thank you. That has been processed.",
            "Acknowledged and recorded.",
        ],
        PersonalityType.ENTHUSIASTIC: [
            "GOT IT!!!",
            "PERFECT!!!",
            "LOVE IT!!!",
            "Awesome!!! Got that down!!!",
            "FANTASTIC!!! Thanks!!!",
            "YES!!! Noted!!!",
            "SUPER!!! All over it!!!",
        ],
    },
    TransitionCategory.ACKNOWLEDGING: {
        PersonalityType.FRIENDLY: [
            "I hear you!",
            "That makes sense!",
            "Absolutely!",
            "Of course!",
            "No worries at all!",
            "I totally get it!",
            "Fair enough!",
        ],
        PersonalityType.PROFESSIONAL: [
            "I understand.",
            "That is clear.",
            "Certainly.",
            "Of course.",
            "That is noted.",
            "I appreciate you sharing that.",
            "That is understood.",
        ],
        PersonalityType.ENTHUSIASTIC: [
            "ABSOLUTELY!!!",
            "I hear you!!!",
            "TOTALLY get it!!!",
            "Makes SO much sense!!!",
            "Of course!!!",
            "COMPLETELY understand!!!",
            "You're SO right!!!",
        ],
    },
    TransitionCategory.TRANSITIONING_TOPICS: {
        PersonalityType.FRIENDLY: [
            "By the way...",
            "While we're at it...",
            "On another note...",
            "Speaking of which...",
            "Here's something you might like...",
            "Oh, thought you'd want to know...",
            "Switching gears for a sec...",
        ],
        PersonalityType.PROFESSIONAL: [
            "On a related note...",
            "Additionally...",
            "In relation to that...",
            "As an aside...",
            "I should also mention...",
            "Furthermore...",
            "Another point to consider...",
        ],
        PersonalityType.ENTHUSIASTIC: [
            "OH! And also...",
            "WAIT! There's more!!!",
            "By the way!!!",
            "OH OH OH! Related thought!!!",
            "And GUESS WHAT else?!!",
            "BUT WAIT, there's more!!!",
            "OH! Here's something else COOL!!!",
        ],
    },
    TransitionCategory.OFFERING_HELP: {
        PersonalityType.FRIENDLY: [
            "Anything else I can help with?",
            "Need help with something else?",
            "What else can I do for you?",
            "I'm here if you need anything else!",
            "Just let me know!",
            "Anything else on your mind?",
            "Feel free to ask away!",
        ],
        PersonalityType.PROFESSIONAL: [
            "Is there anything else I can assist with?",
            "May I help you with anything else?",
            "Do you require any additional assistance?",
            "Please let me know if you need further help.",
            "I am available if you have more questions.",
            "How else may I be of service?",
            "Is there something else I can help you find?",
        ],
        PersonalityType.ENTHUSIASTIC: [
            "Need ANYTHING else?!!!",
            "What else can I help with?!!!",
            "I'm SO here for you!!!",
            "ANYTHING else at all?!!!",
            "Let me know what else you need!!! I'm READY!!!",
            "What else are you looking for?!!!",
            "I'm ON IT!!! What else do you need?!!!",
        ],
    },
}

ECOMMERCE_TRANSITIONS: dict[TransitionCategory, dict[PersonalityType, list[str]]] = {
    TransitionCategory.OFFERING_HELP: {
        PersonalityType.FRIENDLY: [
            "Want to keep shopping?",
            "Ready to check out?",
            "Shall I show you more?",
        ],
        PersonalityType.PROFESSIONAL: [
            "Would you like to continue browsing?",
            "Shall I proceed with checkout?",
            "Would you like to see additional options?",
        ],
        PersonalityType.ENTHUSIASTIC: [
            "Want to keep shopping?!!!",
            "Ready to CHECK OUT?!!!",
            "Let's find MORE awesome stuff!!!",
        ],
    },
    TransitionCategory.TRANSITIONING_TOPICS: {
        PersonalityType.FRIENDLY: [
            "Let's keep shopping!",
            "Back to browsing!",
            "What else catches your eye?",
        ],
        PersonalityType.PROFESSIONAL: [
            "Shall we continue browsing?",
            "Returning to product selection.",
            "Would you like to explore other categories?",
        ],
        PersonalityType.ENTHUSIASTIC: [
            "Let's keep shopping!!!",
            "Back to BROWSING!!!",
            "What ELSE catches your eye?!!!",
        ],
    },
    TransitionCategory.SHOWING_RESULTS: {
        PersonalityType.FRIENDLY: [
            "While you shop...",
            "For your shopping pleasure...",
        ],
        PersonalityType.PROFESSIONAL: [
            "For your convenience...",
            "Available in our selection...",
        ],
        PersonalityType.ENTHUSIASTIC: [
            "While you shop for AWESOME stuff...",
            "For your shopping pleasure!!!",
        ],
    },
}

GENERAL_MODE_TRANSITIONS: dict[TransitionCategory, dict[PersonalityType, list[str]]] = {
    TransitionCategory.OFFERING_HELP: {
        PersonalityType.FRIENDLY: [
            "Need more info on this topic?",
            "Want me to look into something else?",
            "Any other questions?",
        ],
        PersonalityType.PROFESSIONAL: [
            "Do you have additional questions on this topic?",
            "Shall I provide further details?",
            "May I assist with related inquiries?",
        ],
        PersonalityType.ENTHUSIASTIC: [
            "Want to know MORE?!!!",
            "Any other questions?!!! I'm ON IT!!!",
            "Let me tell you MORE about this!!!",
        ],
    },
    TransitionCategory.TRANSITIONING_TOPICS: {
        PersonalityType.FRIENDLY: [
            "Anything else I can help clarify?",
            "Moving on...",
            "What else is on your mind?",
        ],
        PersonalityType.PROFESSIONAL: [
            "Shall we move to another topic?",
            "Proceeding to the next subject.",
            "Is there another area of interest?",
        ],
        PersonalityType.ENTHUSIASTIC: [
            "Anything else I can clarify?!!!",
            "Moving on to MORE cool stuff!!!",
            "What else is on your mind?!!!",
        ],
    },
}

RESPONSE_TYPE_TO_TRANSITION: dict[str, TransitionCategory] = {
    "product_search": TransitionCategory.SHOWING_RESULTS,
    "cart": TransitionCategory.CONFIRMING,
    "checkout": TransitionCategory.CONFIRMING,
    "order_tracking": TransitionCategory.SHOWING_RESULTS,
    "handoff": TransitionCategory.ACKNOWLEDGING,
    "error": TransitionCategory.ACKNOWLEDGING,
    "order_confirmation": TransitionCategory.CONFIRMING,
    "general_mode_fallback": TransitionCategory.ACKNOWLEDGING,
    "proactive_gathering": TransitionCategory.CLARIFYING,
    "summarization": TransitionCategory.CONFIRMING,
    "sentiment_adaptive": TransitionCategory.ACKNOWLEDGING,
    "clarification_natural": TransitionCategory.CLARIFYING,
}

TEMPLATES_WITH_OPENINGS: dict[str, set[str]] = {
    "product_search": {
        "found_single",
        "found_multiple",
        "recommendation_single",
        "recommendation_multiple",
    },
    "cart": {"add_success", "view_items"},
    "checkout": {"ready"},
    "order_tracking": {"found", "found_shipped", "found_delivered", "found_processing"},
    "order_confirmation": {"confirmed"},
    "proactive_gathering": {
        "needs_order_number",
        "needs_product_details",
        "needs_constraints",
        "needs_issue_type",
        "combined_question",
        "best_effort_notice",
    },
    "summarization": {
        "summary_intro",
        "short_conversation",
        "summary_closing",
    },
    "sentiment_adaptive": {
        "pre_empathetic",
        "pre_empathetic_ecommerce",
        "pre_empathetic_general",
        "pre_concise",
        "pre_concise_ecommerce",
        "pre_concise_general",
        "pre_detailed",
        "pre_enthusiastic",
        "post_empathetic",
        "post_empathetic_ecommerce",
        "post_empathetic_general",
        "post_enthusiastic",
        "escalation_message",
    },
    "clarification_natural": {
        "constraint_added_acknowledgment",
        "transition_to_results",
        "transition_to_results_thanks",
        "near_limit_summary",
        "invalid_response_retry",
        "partial_response_acknowledge",
        "combined_question_wrapper",
    },
}


def get_phrases_for_mode(
    category: TransitionCategory,
    personality: PersonalityType,
    mode: str = "ecommerce",
) -> list[str]:
    """Get all available phrases for a given category, personality, and mode.

    Combines base phrases with mode-specific phrases.

    Args:
        category: Transition category
        personality: Personality type
        mode: "ecommerce" or "general"

    Returns:
        List of phrase strings
    """
    base = list(TRANSITION_PHRASES[category].get(personality, []))

    mode_transitions = ECOMMERCE_TRANSITIONS if mode == "ecommerce" else GENERAL_MODE_TRANSITIONS
    mode_phrases = mode_transitions.get(category, {}).get(personality, [])

    return base + mode_phrases
