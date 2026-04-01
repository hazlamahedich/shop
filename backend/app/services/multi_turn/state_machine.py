"""Conversation state machine for multi-turn query handling.

Story 11-2: Multi-Turn Query Handling (AC6)
States: IDLE → CLARIFYING → REFINE_RESULTS → COMPLETE
"""

from __future__ import annotations

import structlog

from app.core.errors import ErrorCode
from app.services.multi_turn.schemas import (
    MultiTurnConfig,
    MultiTurnState,
    MultiTurnStateEnum,
)

logger = structlog.get_logger(__name__)

VALID_TRANSITIONS: dict[str, set[str]] = {
    "IDLE": {"CLARIFYING", "IDLE"},
    "CLARIFYING": {"CLARIFYING", "REFINE_RESULTS", "IDLE"},
    "REFINE_RESULTS": {"REFINE_RESULTS", "COMPLETE", "IDLE"},
    "COMPLETE": {"IDLE", "CLARIFYING"},
}


class ConversationStateMachine:
    """State machine for multi-turn conversation flows.

    State Transitions:
    - IDLE + ambiguous_query → CLARIFYING
    - CLARIFYING + clarification_response → CLARIFYING or REFINE_RESULTS
    - CLARIFYING + turn_limit_reached → REFINE_RESULTS (force)
    - REFINE_RESULTS + constraint_addition → REFINE_RESULTS
    - REFINE_RESULTS + sufficient_info → COMPLETE
    - ANY + topic_change → IDLE (reset)
    - COMPLETE + new_query → IDLE (reset)

    Persist state BEFORE making LLM calls to handle failures gracefully.
    """

    def __init__(self, config: MultiTurnConfig | None = None) -> None:
        self.config = config or MultiTurnConfig()
        self.logger = structlog.get_logger(__name__)

    def start_clarification(
        self,
        state: MultiTurnState,
        original_query: str,
        pending_questions: list[str],
        mode: str = "ecommerce",
    ) -> MultiTurnState:
        self._validate_transition(state.state, MultiTurnStateEnum.CLARIFYING)

        state.state = MultiTurnStateEnum.CLARIFYING
        state.original_query = original_query
        state.pending_questions = list(pending_questions)
        state.mode = mode
        state.turn_count = 0
        state.invalid_response_count = 0

        self._log_transition("IDLE", MultiTurnStateEnum.CLARIFYING, "ambiguous_query")
        return state

    def process_clarification_response(
        self,
        state: MultiTurnState,
        constraint_name: str,
        user_response: str,
        is_valid: bool,
    ) -> MultiTurnState:
        self._validate_transition(state.state, MultiTurnStateEnum.CLARIFYING)

        from app.services.multi_turn.schemas import ClarificationTurn

        turn = ClarificationTurn(
            question_asked=state.pending_questions[0]
            if state.pending_questions
            else constraint_name,
            constraint_name=constraint_name,
            user_response=user_response,
            is_valid=is_valid,
        )
        state.clarification_turns.append(turn)

        if is_valid:
            state.invalid_response_count = 0
            if constraint_name in state.questions_asked:
                state.questions_asked.remove(constraint_name)
            state.questions_asked.append(constraint_name)
            if constraint_name in state.pending_questions:
                state.pending_questions.remove(constraint_name)

        state.turn_count += 1

        if self._should_force_results(state):
            return self.transition_to_refine(state, "turn_limit_reached")

        if not state.pending_questions:
            return self.transition_to_refine(state, "all_questions_answered")

        self._log_transition(
            MultiTurnStateEnum.CLARIFYING,
            MultiTurnStateEnum.CLARIFYING,
            f"clarification_response(turn={state.turn_count})",
        )
        return state

    def transition_to_refine(
        self,
        state: MultiTurnState,
        trigger: str = "sufficient_info",
    ) -> MultiTurnState:
        self._validate_transition(state.state, MultiTurnStateEnum.REFINE_RESULTS)

        old_state = state.state
        state.state = MultiTurnStateEnum.REFINE_RESULTS

        self._log_transition(old_state, MultiTurnStateEnum.REFINE_RESULTS, trigger)
        return state

    def complete(self, state: MultiTurnState) -> MultiTurnState:
        self._validate_transition(state.state, MultiTurnStateEnum.COMPLETE)

        old_state = state.state
        state.state = MultiTurnStateEnum.COMPLETE

        self._log_transition(old_state, MultiTurnStateEnum.COMPLETE, "results_shown")
        return state

    def reset(self, state: MultiTurnState) -> MultiTurnState:
        old_state = state.state
        state.state = MultiTurnStateEnum.IDLE
        state.turn_count = 0
        state.invalid_response_count = 0
        state.accumulated_constraints = {}
        state.questions_asked = []
        state.pending_questions = []
        state.original_query = None
        state.clarification_turns = []

        self._log_transition(old_state, MultiTurnStateEnum.IDLE, "reset")
        return state

    def increment_invalid_count(self, state: MultiTurnState) -> MultiTurnState:
        state.invalid_response_count += 1
        self.logger.info(
            "invalid_response_count_incremented",
            count=state.invalid_response_count,
            max=self.config.max_invalid_responses,
        )
        return state

    def should_force_results(self, state: MultiTurnState) -> bool:
        return self._should_force_results(state)

    def is_at_turn_limit(self, state: MultiTurnState) -> bool:
        return state.turn_count >= self.config.max_clarification_turns

    def is_near_turn_limit(self, state: MultiTurnState) -> bool:
        return state.turn_count >= self.config.max_clarification_turns - 1

    def _should_force_results(self, state: MultiTurnState) -> bool:
        if state.turn_count >= self.config.max_clarification_turns:
            return True
        if state.invalid_response_count >= self.config.max_invalid_responses:
            return True
        return False

    def _validate_transition(self, from_state: str, to_state: str) -> None:
        from_val = from_state.value if isinstance(from_state, MultiTurnStateEnum) else from_state
        to_val = to_state.value if isinstance(to_state, MultiTurnStateEnum) else to_state

        allowed = VALID_TRANSITIONS.get(from_val, set())
        if to_val not in allowed:
            logger.error(
                "invalid_state_transition",
                error_code=ErrorCode.MULTI_TURN_STATE_MACHINE_ERROR,
                from_state=from_val,
                to_state=to_val,
                allowed=list(allowed),
            )
            raise ValueError(
                f"Invalid state transition: {from_val} → {to_val}. "
                f"Allowed transitions from {from_val}: {sorted(allowed)}"
            )

    def _log_transition(self, from_state: str, to_state: str, trigger: str) -> None:
        from_val = from_state.value if isinstance(from_state, MultiTurnStateEnum) else from_state
        to_val = to_state.value if isinstance(to_state, MultiTurnStateEnum) else to_state
        self.logger.info(
            "State transition: %s → %s (trigger: %s)",
            from_val,
            to_val,
            trigger,
        )
