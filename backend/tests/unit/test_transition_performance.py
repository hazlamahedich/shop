"""Performance benchmark tests for transition phrase selection.

Story 11-4 AC7: Transition selection must complete in <1ms.
Tests single-selection latency, batch throughput, and
anti-repetition lookup performance at scale.
"""

import time

import pytest

from app.models.merchant import PersonalityType
from app.services.personality.transition_phrases import TransitionCategory
from app.services.personality.transition_selector import (
    MAX_RECENT_PER_CONVERSATION,
    TransitionSelector,
    get_transition_selector,
)

MAX_SINGLE_SELECT_MS = 1.0
MAX_BATCH_AVG_MS = 1.0
MAX_BATCH_TOTAL_MS = 100.0
MAX_SCALE_SELECT_MS = 1.0
BATCH_ITERATIONS = 1000
SCALE_ITERATIONS = 200


@pytest.fixture(autouse=True)
def reset_selector():
    selector = get_transition_selector()
    selector.reset()
    yield
    selector.reset()


class TestSingleSelectionPerformance:
    def test_single_select_under_1ms(self):
        selector = get_transition_selector()
        start = time.perf_counter()
        selector.select(
            TransitionCategory.SHOWING_RESULTS,
            PersonalityType.FRIENDLY,
            "perf-single",
            "ecommerce",
        )
        elapsed_ms = (time.perf_counter() - start) * 1000
        assert elapsed_ms < MAX_SINGLE_SELECT_MS, (
            f"Single select took {elapsed_ms:.3f}ms (limit: 1ms)"
        )

    @pytest.mark.parametrize("category", list(TransitionCategory))
    def test_each_category_under_1ms(self, category):
        selector = get_transition_selector()
        start = time.perf_counter()
        selector.select(
            category, PersonalityType.PROFESSIONAL, f"perf-cat-{category.value}", "ecommerce"
        )
        elapsed_ms = (time.perf_counter() - start) * 1000
        assert elapsed_ms < MAX_SINGLE_SELECT_MS, f"{category.value} select took {elapsed_ms:.3f}ms"

    @pytest.mark.parametrize("personality", list(PersonalityType))
    def test_each_personality_under_1ms(self, personality):
        selector = get_transition_selector()
        start = time.perf_counter()
        selector.select(
            TransitionCategory.CONFIRMING,
            personality,
            f"perf-pers-{personality.value}",
            "ecommerce",
        )
        elapsed_ms = (time.perf_counter() - start) * 1000
        assert elapsed_ms < MAX_SINGLE_SELECT_MS, (
            f"{personality.value} select took {elapsed_ms:.3f}ms"
        )


class TestBatchSelectionPerformance:
    def test_1000_selections_average_under_1ms(self):
        selector = get_transition_selector()
        conv_id = "perf-batch"

        start = time.perf_counter()
        for _ in range(BATCH_ITERATIONS):
            selector.select(
                TransitionCategory.SHOWING_RESULTS,
                PersonalityType.FRIENDLY,
                conv_id,
                "ecommerce",
            )
        total_ms = (time.perf_counter() - start) * 1000
        avg_ms = total_ms / BATCH_ITERATIONS

        assert avg_ms < MAX_BATCH_AVG_MS, f"Average select took {avg_ms:.4f}ms (limit: 1ms)"

    def test_1000_selections_total_under_100ms(self):
        selector = get_transition_selector()
        conv_id = "perf-batch-total"

        start = time.perf_counter()
        for _ in range(BATCH_ITERATIONS):
            selector.select(
                TransitionCategory.CONFIRMING,
                PersonalityType.PROFESSIONAL,
                conv_id,
                "ecommerce",
            )
        total_ms = (time.perf_counter() - start) * 1000

        assert total_ms < MAX_BATCH_TOTAL_MS, f"1000 selects took {total_ms:.1f}ms (limit: 100ms)"

    def test_format_response_with_transition_under_1ms(self):
        from app.services.personality.response_formatter import PersonalityAwareResponseFormatter

        start = time.perf_counter()
        PersonalityAwareResponseFormatter.format_response(
            "cart",
            "view_empty",
            PersonalityType.FRIENDLY,
            include_transition=True,
            conversation_id="perf-format",
            mode="ecommerce",
        )
        elapsed_ms = (time.perf_counter() - start) * 1000
        assert elapsed_ms < MAX_SINGLE_SELECT_MS, (
            f"format_response with transition took {elapsed_ms:.3f}ms"
        )


class TestAntiRepetitionScalePerformance:
    def test_lookup_with_50_tracked_phrases(self):
        selector = get_transition_selector()
        conv_id = "perf-scale-50"

        for _ in range(MAX_RECENT_PER_CONVERSATION):
            selector.select(
                TransitionCategory.CONFIRMING,
                PersonalityType.FRIENDLY,
                conv_id,
                "ecommerce",
            )

        start = time.perf_counter()
        selector.select(
            TransitionCategory.CONFIRMING,
            PersonalityType.FRIENDLY,
            conv_id,
            "ecommerce",
        )
        elapsed_ms = (time.perf_counter() - start) * 1000
        assert elapsed_ms < MAX_SCALE_SELECT_MS, f"Select with max recent took {elapsed_ms:.3f}ms"

    def test_100_conversations_performance(self):
        selector = get_transition_selector()

        for i in range(100):
            selector.select(
                TransitionCategory.CONFIRMING,
                PersonalityType.FRIENDLY,
                f"perf-conv-{i}",
                "ecommerce",
            )

        assert selector.active_conversation_count == 100

        start = time.perf_counter()
        selector.select(
            TransitionCategory.CONFIRMING,
            PersonalityType.FRIENDLY,
            "perf-conv-50",
            "ecommerce",
        )
        elapsed_ms = (time.perf_counter() - start) * 1000
        assert elapsed_ms < MAX_SCALE_SELECT_MS, (
            f"Select with 100 active conversations took {elapsed_ms:.3f}ms"
        )

    def test_cleanup_performance_not_degrading(self):
        selector = get_transition_selector()

        for i in range(100):
            selector.select(
                TransitionCategory.CONFIRMING,
                PersonalityType.FRIENDLY,
                f"perf-cleanup-{i}",
                "ecommerce",
            )

        start = time.perf_counter()
        for _ in range(SCALE_ITERATIONS):
            selector.select(
                TransitionCategory.CONFIRMING,
                PersonalityType.FRIENDLY,
                "perf-cleanup-active",
                "ecommerce",
            )
        elapsed_ms = (time.perf_counter() - start) * 1000

        avg_ms = elapsed_ms / SCALE_ITERATIONS
        assert avg_ms < MAX_SCALE_SELECT_MS, (
            f"Degraded performance: {avg_ms:.4f}ms avg with cleanup"
        )
