"""Unit tests for conversation lock manager.

Story 11-2: Tests TTL cleanup, singleton pattern, active_lock_count,
concurrent access, and lock lifecycle.
"""

import asyncio
import time

import pytest

from app.services.multi_turn.conversation_lock import (
    LOCK_TTL_SECONDS,
    ConversationLockManager,
    get_lock_manager,
)


@pytest.fixture
def lock_manager() -> ConversationLockManager:
    return ConversationLockManager()


class TestGetLock:
    @pytest.mark.asyncio
    async def test_creates_lock_for_new_conversation(self, lock_manager: ConversationLockManager):
        lock = await lock_manager.get_lock(1)
        assert lock is not None
        assert isinstance(lock, asyncio.Lock)

    @pytest.mark.asyncio
    async def test_returns_same_lock_for_same_conversation(
        self, lock_manager: ConversationLockManager
    ):
        lock1 = await lock_manager.get_lock(42)
        lock2 = await lock_manager.get_lock(42)
        assert lock1 is lock2

    @pytest.mark.asyncio
    async def test_different_conversations_get_different_locks(
        self, lock_manager: ConversationLockManager
    ):
        lock1 = await lock_manager.get_lock(1)
        lock2 = await lock_manager.get_lock(2)
        assert lock1 is not lock2


class TestActiveLockCount:
    @pytest.mark.asyncio
    async def test_starts_at_zero(self):
        manager = ConversationLockManager()
        assert manager.active_lock_count == 0

    @pytest.mark.asyncio
    async def test_increases_with_new_conversations(self, lock_manager: ConversationLockManager):
        await lock_manager.get_lock(1)
        assert lock_manager.active_lock_count == 1
        await lock_manager.get_lock(2)
        assert lock_manager.active_lock_count == 2

    @pytest.mark.asyncio
    async def test_same_conversation_does_not_increase_count(
        self, lock_manager: ConversationLockManager
    ):
        await lock_manager.get_lock(1)
        await lock_manager.get_lock(1)
        assert lock_manager.active_lock_count == 1


class TestTTLCleanup:
    @pytest.mark.asyncio
    async def test_expired_locks_are_cleaned_up(self):
        manager = ConversationLockManager(ttl_seconds=0)
        lock = await manager.get_lock(1)
        assert manager.active_lock_count == 1

        await asyncio.sleep(0.01)

        await manager.get_lock(2)
        assert manager.active_lock_count == 1
        assert 1 not in manager._locks

    @pytest.mark.asyncio
    async def test_recently_used_locks_are_not_cleaned(self):
        manager = ConversationLockManager(ttl_seconds=300)
        await manager.get_lock(1)
        await manager.get_lock(2)
        assert manager.active_lock_count == 2

    @pytest.mark.asyncio
    async def test_held_lock_is_not_cleaned_even_if_expired(self):
        manager = ConversationLockManager(ttl_seconds=0)
        lock = await manager.get_lock(1)
        async with lock:
            await asyncio.sleep(0.01)
            await manager.get_lock(2)
            assert manager.active_lock_count == 2

    @pytest.mark.asyncio
    async def test_cleanup_on_next_get_lock_call(self):
        manager = ConversationLockManager(ttl_seconds=0)
        await manager.get_lock(10)
        await manager.get_lock(20)

        await asyncio.sleep(0.01)

        await manager.get_lock(30)
        assert manager.active_lock_count == 1
        assert 10 not in manager._locks
        assert 20 not in manager._locks
        assert 30 in manager._locks


class TestConcurrentAccess:
    @pytest.mark.asyncio
    async def test_lock_serializes_concurrent_operations(
        self, lock_manager: ConversationLockManager
    ):
        lock = await lock_manager.get_lock(1)
        results = []
        order = []

        async def protected_op(value: int):
            async with lock:
                order.append(f"start-{value}")
                results.append(value)
                await asyncio.sleep(0.01)
                order.append(f"end-{value}")

        await asyncio.gather(
            protected_op(1),
            protected_op(2),
            protected_op(3),
        )
        assert sorted(results) == [1, 2, 3]
        assert order.index("start-1") < order.index("end-1")
        assert order.index("start-2") < order.index("end-2")

    @pytest.mark.asyncio
    async def test_concurrent_get_lock_calls_are_safe(self):
        manager = ConversationLockManager()

        results = await asyncio.gather(
            manager.get_lock(1),
            manager.get_lock(1),
            manager.get_lock(1),
        )
        assert results[0] is results[1]
        assert results[1] is results[2]
        assert manager.active_lock_count == 1


class TestSingletonPattern:
    def test_get_lock_manager_returns_same_instance(self):
        import app.services.multi_turn.conversation_lock as mod

        original = mod._lock_manager
        mod._lock_manager = None
        try:
            m1 = get_lock_manager()
            m2 = get_lock_manager()
            assert m1 is m2
        finally:
            mod._lock_manager = original

    def test_default_ttl_is_300_seconds(self):
        manager = ConversationLockManager()
        assert manager._ttl_seconds == LOCK_TTL_SECONDS
        assert manager._ttl_seconds == 300


class TestLastAccess:
    @pytest.mark.asyncio
    async def test_last_access_updated_on_get(self, lock_manager: ConversationLockManager):
        await lock_manager.get_lock(1)
        t1 = lock_manager._last_access[1]
        assert t1 is not None

        await asyncio.sleep(0.01)
        await lock_manager.get_lock(1)
        t2 = lock_manager._last_access[1]
        assert t2 > t1
