"""Cross-handler anti-repetition integration tests.

Story 11-4: Tests that the TransitionSelector singleton correctly prevents
repetition across different handlers within the same conversation, simulating
a real multi-turn conversation flow (search → cart → checkout → order → handoff).
"""

import pytest

from app.models.merchant import PersonalityType
from app.services.personality.response_formatter import PersonalityAwareResponseFormatter
from app.services.personality.transition_phrases import (
    RESPONSE_TYPE_TO_TRANSITION,
    TransitionCategory,
    get_phrases_for_mode,
)
from app.services.personality.transition_selector import get_transition_selector


@pytest.fixture(autouse=True)
def reset_selector():
    selector = get_transition_selector()
    selector.reset()
    yield
    selector.reset()


class TestCrossHandlerAntiRepetition:
    """Simulate a multi-turn conversation using different handlers.

    Verifies that the singleton selector tracks transitions across
    handler switches and avoids repeating phrases.
    """

    def test_full_shopping_flow_no_immediate_repeats(self):
        conv_id = "flow-no-repeats"
        selector = get_transition_selector()

        search_transition = selector.select(
            TransitionCategory.SHOWING_RESULTS,
            PersonalityType.FRIENDLY,
            conv_id,
            "ecommerce",
        )
        cart_transition = selector.select(
            TransitionCategory.CONFIRMING,
            PersonalityType.FRIENDLY,
            conv_id,
            "ecommerce",
        )
        checkout_transition = selector.select(
            TransitionCategory.CONFIRMING,
            PersonalityType.FRIENDLY,
            conv_id,
            "ecommerce",
        )

        assert search_transition != cart_transition
        assert cart_transition != checkout_transition

    def test_format_response_across_handlers_uses_different_transitions(self):
        conv_id = "flow-format"
        results = []

        handlers_sequence = [
            ("product_search", "no_results", {"query": "shoes"}),
            ("cart", "view_empty", {}),
            ("cart", "remove_success", {}),
            ("checkout", "empty_cart", {}),
            ("handoff", "standard", {}),
            ("error", "general", {}),
        ]

        for response_type, message_key, kwargs in handlers_sequence:
            result = PersonalityAwareResponseFormatter.format_response(
                response_type,
                message_key,
                PersonalityType.PROFESSIONAL,
                include_transition=True,
                conversation_id=conv_id,
                mode="ecommerce",
                **kwargs,
            )
            results.append(result)

        transitions_used = set()
        for result in results:
            category = None
            for resp_type, msg_key, _ in handlers_sequence:
                if result != "":
                    category = RESPONSE_TYPE_TO_TRANSITION.get(resp_type)
                    break

            if category:
                valid = get_phrases_for_mode(category, PersonalityType.PROFESSIONAL, "ecommerce")
                for phrase in valid:
                    if result.startswith(phrase):
                        assert phrase not in transitions_used, f"Repeated transition: {phrase}"
                        transitions_used.add(phrase)
                        break

    def test_same_category_different_conversations_independent(self):
        conv_a = "flow-conv-a"
        conv_b = "flow-conv-b"
        selector = get_transition_selector()

        a_results = set()
        b_results = set()

        for _ in range(5):
            a_results.add(
                selector.select(
                    TransitionCategory.CONFIRMING,
                    PersonalityType.FRIENDLY,
                    conv_a,
                    "ecommerce",
                )
            )
            b_results.add(
                selector.select(
                    TransitionCategory.CONFIRMING,
                    PersonalityType.FRIENDLY,
                    conv_b,
                    "ecommerce",
                )
            )

        assert len(a_results) > 1
        assert len(b_results) > 1

    def test_category_switch_resets_avoidance(self):
        conv_id = "flow-category-switch"
        selector = get_transition_selector()

        phrase_a1 = selector.select(
            TransitionCategory.SHOWING_RESULTS,
            PersonalityType.FRIENDLY,
            conv_id,
            "ecommerce",
        )
        selector.select(
            TransitionCategory.CONFIRMING,
            PersonalityType.FRIENDLY,
            conv_id,
            "ecommerce",
        )
        selector.select(
            TransitionCategory.ACKNOWLEDGING,
            PersonalityType.FRIENDLY,
            conv_id,
            "ecommerce",
        )
        phrase_a2 = selector.select(
            TransitionCategory.SHOWING_RESULTS,
            PersonalityType.FRIENDLY,
            conv_id,
            "ecommerce",
        )

        assert phrase_a1 != phrase_a2, "Should avoid previous SHOWING_RESULTS phrase"

    def test_exhaustion_cycle_across_handlers(self):
        conv_id = "flow-exhaustion"
        selector = get_transition_selector()

        all_confirming = get_phrases_for_mode(
            TransitionCategory.CONFIRMING, PersonalityType.FRIENDLY, "ecommerce"
        )

        selected = []
        for _ in range(len(all_confirming) + 3):
            selected.append(
                selector.select(
                    TransitionCategory.CONFIRMING,
                    PersonalityType.FRIENDLY,
                    conv_id,
                    "ecommerce",
                )
            )

        unique = set(selected)
        assert len(unique) == len(all_confirming)

    def test_mixed_handler_flow_with_order_tracking(self):
        conv_id = "flow-with-orders"
        selector = get_transition_selector()

        search = selector.select(
            TransitionCategory.SHOWING_RESULTS,
            PersonalityType.PROFESSIONAL,
            conv_id,
            "ecommerce",
        )
        cart_confirm = selector.select(
            TransitionCategory.CONFIRMING,
            PersonalityType.PROFESSIONAL,
            conv_id,
            "ecommerce",
        )
        order_show = selector.select(
            TransitionCategory.SHOWING_RESULTS,
            PersonalityType.PROFESSIONAL,
            conv_id,
            "ecommerce",
        )
        help_offer = selector.select(
            TransitionCategory.OFFERING_HELP,
            PersonalityType.PROFESSIONAL,
            conv_id,
            "ecommerce",
        )

        assert search != order_show, "Two SHOWING_RESULTS should differ"

        valid_confirming = get_phrases_for_mode(
            TransitionCategory.CONFIRMING, PersonalityType.PROFESSIONAL, "ecommerce"
        )
        valid_help = get_phrases_for_mode(
            TransitionCategory.OFFERING_HELP, PersonalityType.PROFESSIONAL, "ecommerce"
        )
        assert cart_confirm in valid_confirming
        assert help_offer in valid_help

    def test_handoff_acknowledging_not_repeated(self):
        conv_id = "flow-handoff"
        selector = get_transition_selector()

        ack1 = selector.select(
            TransitionCategory.ACKNOWLEDGING,
            PersonalityType.FRIENDLY,
            conv_id,
            "ecommerce",
        )
        selector.select(
            TransitionCategory.CONFIRMING,
            PersonalityType.FRIENDLY,
            conv_id,
            "ecommerce",
        )
        ack2 = selector.select(
            TransitionCategory.ACKNOWLEDGING,
            PersonalityType.FRIENDLY,
            conv_id,
            "ecommerce",
        )

        assert ack1 != ack2


class TestMultiConversationIsolation:
    def test_two_concurrent_conversations_dont_interfere(self):
        selector = get_transition_selector()
        conv_x = "conv-x"
        conv_y = "conv-y"

        selector.select(
            TransitionCategory.CONFIRMING, PersonalityType.FRIENDLY, conv_x, "ecommerce"
        )
        selector.select(
            TransitionCategory.CONFIRMING, PersonalityType.FRIENDLY, conv_x, "ecommerce"
        )

        assert selector.get_recent_count(conv_x) == 2
        assert selector.get_recent_count(conv_y) == 0

        selector.select(
            TransitionCategory.CONFIRMING, PersonalityType.FRIENDLY, conv_y, "ecommerce"
        )
        assert selector.get_recent_count(conv_x) == 2
        assert selector.get_recent_count(conv_y) == 1

    def test_clear_one_conversation_preserves_others(self):
        selector = get_transition_selector()
        conv_a = "conv-clear-a"
        conv_b = "conv-clear-b"

        selector.select(
            TransitionCategory.CONFIRMING, PersonalityType.FRIENDLY, conv_a, "ecommerce"
        )
        selector.select(
            TransitionCategory.CONFIRMING, PersonalityType.FRIENDLY, conv_b, "ecommerce"
        )

        selector.clear_conversation(conv_a)
        assert selector.get_recent_count(conv_a) == 0
        assert selector.get_recent_count(conv_b) == 1

    def test_format_response_isolation_between_conversations(self):
        result_a = PersonalityAwareResponseFormatter.format_response(
            "cart",
            "view_empty",
            PersonalityType.FRIENDLY,
            include_transition=True,
            conversation_id="conv-format-a",
            mode="ecommerce",
        )
        result_b = PersonalityAwareResponseFormatter.format_response(
            "cart",
            "view_empty",
            PersonalityType.FRIENDLY,
            include_transition=True,
            conversation_id="conv-format-b",
            mode="ecommerce",
        )

        valid = get_phrases_for_mode(
            TransitionCategory.CONFIRMING, PersonalityType.FRIENDLY, "ecommerce"
        )
        a_phrase = next((p for p in valid if result_a.startswith(p)), None)
        b_phrase = next((p for p in valid if result_b.startswith(p)), None)

        assert a_phrase is not None
        assert b_phrase is not None
