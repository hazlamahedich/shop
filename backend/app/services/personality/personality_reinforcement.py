"""Mid-conversation personality reinforcement (Story 11-5, AC3).

Generates personality reminder text for injection into LLM system prompts
when conversations exceed a configurable turn threshold.
"""

from __future__ import annotations

from app.models.merchant import PersonalityType

REINFORCEMENT_TURN_THRESHOLD = 5

_PROFESSIONAL_REINFORCEMENT = (
    "\n\nPERSONALITY CONSISTENCY REMINDER:\n"
    "You are speaking in a PROFESSIONAL tone. Remember:\n"
    "- NO emojis anywhere\n"
    "- Use formal, polite language\n"
    "- No slang or overly casual expressions\n"
    "- Be efficient and clear\n"
    "- Maintain this tone for the rest of the conversation"
)

_FRIENDLY_REINFORCEMENT = (
    "\n\nPERSONALITY CONSISTENCY REMINDER:\n"
    "You are speaking in a FRIENDLY, warm tone. Remember:\n"
    "- Use at most 1-2 emojis per response\n"
    "- Keep it casual and conversational\n"
    "- Use contractions freely (you're, that's, let's)\n"
    "- Be warm and approachable\n"
    "- Maintain this tone for the rest of the conversation"
)

_ENTHUSIASTIC_REINFORCEMENT = (
    "\n\nPERSONALITY CONSISTENCY REMINDER:\n"
    "You are speaking in an ENTHUSIASTIC, energetic tone. Remember:\n"
    "- Use exclamation marks freely!!!\n"
    "- Include energetic emojis (🔥, ✨, 🎉)\n"
    "- Be upbeat and excited about everything\n"
    "- Use words like AMAZING, AWESOME, INCREDIBLE\n"
    "- Maintain this tone for the rest of the conversation"
)

_REINFORCEMENT_MAP = {
    PersonalityType.PROFESSIONAL: _PROFESSIONAL_REINFORCEMENT,
    PersonalityType.FRIENDLY: _FRIENDLY_REINFORCEMENT,
    PersonalityType.ENTHUSIASTIC: _ENTHUSIASTIC_REINFORCEMENT,
}


def get_personality_reinforcement(
    personality: PersonalityType,
    turn_number: int,
    consistency_score: float | None = None,
) -> str | None:
    """Generate a personality reinforcement reminder for LLM system prompt.

    Called by LLM handler when conversation exceeds the turn threshold to
    prevent personality drift in long conversations.

    Args:
        personality: Configured personality type
        turn_number: Current turn number in the conversation
        consistency_score: Optional consistency score for adaptive reinforcement

    Returns:
        Reinforcement text to append to system prompt, or None if not needed
    """
    if turn_number < REINFORCEMENT_TURN_THRESHOLD:
        return None

    base = _REINFORCEMENT_MAP.get(personality, _FRIENDLY_REINFORCEMENT)

    if consistency_score is not None and consistency_score < 0.7:
        base += (
            "\n\nWARNING: Your personality consistency has been declining. "
            "Please pay extra attention to maintaining the correct tone."
        )

    return base
