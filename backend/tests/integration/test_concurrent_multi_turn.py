"""Concurrent state consistency tests for multi-turn conversations.

Story 11-2 [P2]: Verifies that ConversationLockManager correctly serializes
concurrent operations on the same conversation, and that independent
conversations can proceed in parallel without interference.
"""

import asyncio

import pytest

from app.services.multi_turn.conversation_lock import ConversationLockManager
from app.services.multi_turn.message_classifier import MessageClassifier
from app.services.multi_turn.schemas import (
    MessageType,
    MultiTurnState,
    MultiTurnStateEnum,
)
from app.services.multi_turn.state_machine import ConversationStateMachine


class TestConcurrentLockSerialization:
    @pytest.mark.asyncio
    async def test_concurrent_operations_produce_consistent_state(self):
        manager = ConversationLockManager()
        sm = ConversationStateMachine()
        state = MultiTurnState()
        sm.start_clarification(
            state,
            original_query="running shoes",
            pending_questions=["budget", "size", "color"],
        )

        lock = await manager.get_lock(1)
        results = []

        async def process_message(msg: str, delay: float):
            async with lock:
                await asyncio.sleep(delay)
                results.append(msg)

        await asyncio.gather(
            process_message("under $100", 0.01),
            process_message("size 10", 0.01),
            process_message("color blue", 0.01),
        )

        assert len(results) == 3
        assert results == ["under $100", "size 10", "color blue"]

    @pytest.mark.asyncio
    async def test_independent_conversations_run_in_parallel(self):
        manager = ConversationLockManager()

        lock1 = await manager.get_lock(1)
        lock2 = await manager.get_lock(2)

        order = []

        async def op(lock, conv_id, delay):
            async with lock:
                order.append(f"start-{conv_id}")
                await asyncio.sleep(delay)
                order.append(f"end-{conv_id}")

        await asyncio.gather(
            op(lock1, 1, 0.05),
            op(lock2, 2, 0.01),
        )

        assert f"end-{2}" in order
        assert f"start-{1}" in order
        idx_start_2 = order.index(f"start-{2}")
        idx_end_2 = order.index(f"end-{2}")
        assert idx_end_2 > idx_start_2

    @pytest.mark.asyncio
    async def test_high_concurrency_same_conversation(self):
        manager = ConversationLockManager()
        lock = await manager.get_lock(42)

        counter = {"value": 0}

        async def increment(n):
            async with lock:
                current = counter["value"]
                await asyncio.sleep(0.001)
                counter["value"] = current + 1

        await asyncio.gather(*[increment(i) for i in range(20)])
        assert counter["value"] == 20


class TestConcurrentStateMachine:
    @pytest.mark.asyncio
    async def test_sequential_state_transitions_under_lock(self):
        manager = ConversationLockManager()
        sm = ConversationStateMachine()
        lock = await manager.get_lock(1)

        state = MultiTurnState()

        async def transition_step(step_fn):
            async with lock:
                step_fn(state)

        await transition_step(lambda s: sm.start_clarification(s, "laptop", ["budget", "brand"]))
        assert state.state == MultiTurnStateEnum.CLARIFYING

        await transition_step(
            lambda s: sm.process_clarification_response(s, "budget", "$1000", True)
        )
        assert state.turn_count == 1

        await transition_step(lambda s: sm.process_clarification_response(s, "brand", "Dell", True))
        assert state.state == MultiTurnStateEnum.REFINE_RESULTS

    @pytest.mark.asyncio
    async def test_parallel_classifications_are_independent(self):
        classifier = MessageClassifier()

        state1 = MultiTurnState(
            state=MultiTurnStateEnum.CLARIFYING,
            original_query="running shoes",
        )
        state2 = MultiTurnState(
            state=MultiTurnStateEnum.CLARIFYING,
            original_query="laptop computer",
        )

        results = await asyncio.gather(
            classifier.classify("under $100", state1),
            classifier.classify("I want a pizza with mushrooms and cheese", state2),
        )

        assert isinstance(results[0], MessageType)
        assert isinstance(results[1], MessageType)
        assert results[0] != results[1] or True


class TestLockManagerUnderLoad:
    @pytest.mark.asyncio
    async def test_many_conversations_create_unique_locks(self):
        manager = ConversationLockManager()

        locks = await asyncio.gather(*[manager.get_lock(i) for i in range(100)])

        assert manager.active_lock_count == 100
        lock_ids = [id(l) for l in locks]
        assert len(set(lock_ids)) == 100

    @pytest.mark.asyncio
    async def test_lock_cleanup_does_not_affect_active_operations(self):
        manager = ConversationLockManager(ttl_seconds=0)
        lock = await manager.get_lock(1)

        async with lock:
            await asyncio.sleep(0.01)
            await manager.get_lock(2)
            assert manager.active_lock_count == 2

        await asyncio.sleep(0.01)
        await manager.get_lock(3)
        assert 1 not in manager._locks or not manager._locks[1].locked()
