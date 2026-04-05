"""Natural clarification question personality templates (Story 11-11).

Personality-aware wrapping templates for clarification questions.
These provide the outer formatting (acknowledgment + question body)
that wraps the raw question from QuestionGenerator.

Registered via PersonalityAwareResponseFormatter.register_response_type().
All 3 personality variants must be defined for each key to prevent KeyError.
"""

from app.models.merchant import PersonalityType
from app.services.personality.response_formatter import PersonalityAwareResponseFormatter

CLARIFICATION_QUESTION_TEMPLATES = {
    PersonalityType.FRIENDLY: {
        "constraint_added_acknowledgment": (
            "Got it! {understanding} Let me refine the results for you."
        ),
        "transition_to_results": "{understanding} Here are the results.",
        "transition_to_results_thanks": "Thanks! {understanding} Here are the results.",
        "near_limit_summary": ("{understanding} Let me show you what I found based on this."),
        "invalid_response_retry": (
            "I didn't quite catch that. Could you try rephrasing? "
            "For example, you could mention a specific price range, size, or brand."
        ),
        "partial_response_acknowledge": (
            "Thanks for that info! I've noted the {accepted_field}. {follow_up_question}"
        ),
        "combined_question_wrapper": (
            "To help me find exactly what you need — {combined_question}"
        ),
    },
    PersonalityType.PROFESSIONAL: {
        "constraint_added_acknowledgment": (
            "Understood. {understanding} I will refine the results accordingly."
        ),
        "transition_to_results": "{understanding} Here are the available results.",
        "transition_to_results_thanks": ("Thank you. {understanding} Here are the results."),
        "near_limit_summary": ("{understanding} Let me present the findings based on this."),
        "invalid_response_retry": (
            "I was unable to process that response. Could you please rephrase? "
            "For instance, specifying a price range, size, or brand would be helpful."
        ),
        "partial_response_acknowledge": (
            "Thank you for providing the {accepted_field}. {follow_up_question}"
        ),
        "combined_question_wrapper": ("To assist you effectively — {combined_question}"),
    },
    PersonalityType.ENTHUSIASTIC: {
        "constraint_added_acknowledgment": (
            "GOT IT! {understanding} Let me find you something AMAZING!"
        ),
        "transition_to_results": ("{understanding} Here are the FABULOUS results!"),
        "transition_to_results_thanks": ("Thanks SO much! {understanding} Here are the results!"),
        "near_limit_summary": ("{understanding} Check out what I found for you!"),
        "invalid_response_retry": (
            "Hmm, I didn't quite get that! Could you try again? "
            "Something like a price range, size, or brand would be SUPER helpful!"
        ),
        "partial_response_acknowledge": ("AWESOME, got the {accepted_field}! {follow_up_question}"),
        "combined_question_wrapper": ("To find you something PERFECT — {combined_question}"),
    },
}


def register_natural_question_templates() -> None:
    """Register natural clarification question templates with the formatter."""
    PersonalityAwareResponseFormatter.register_response_type(
        "clarification_natural", CLARIFICATION_QUESTION_TEMPLATES
    )
