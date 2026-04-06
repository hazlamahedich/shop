"""Unit tests for _write_conversation_turn DB record creation.

Story 11-12a: Conversation Turn Tracking Pipeline

Tests turn record creation with correct fields and IntegrityError propagation.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.conversation_context import ConversationTurn
from app.services.conversation.unified_conversation_service import (
    UnifiedConversationService,
)


class TestGivenTurnDataWhenWriteConversationTurn:
    @pytest.mark.p0
    @pytest.mark.test_id("STORY-11-12a-007")
    @pytest.mark.asyncio
    async def test_given_valid_fields_when_turn_written_then_record_created_correctly(self):
        service = MagicMock(spec=UnifiedConversationService)
        service._write_conversation_turn = (
            UnifiedConversationService._write_conversation_turn.__get__(service)
        )

        db = AsyncMock()
        nested_cm = AsyncMock()
        nested_cm.__aenter__ = AsyncMock(return_value=None)
        nested_cm.__aexit__ = AsyncMock(return_value=None)
        db.begin_nested = MagicMock(return_value=nested_cm)
        db.add = MagicMock()
        db.flush = AsyncMock()

        snapshot = {"confidence": 0.9, "processing_time_ms": 100}

        await service._write_conversation_turn(
            db=db,
            conversation_id=42,
            turn_number=3,
            intent_detected="product_search",
            sentiment="EMPATHETIC",
            context_snapshot=snapshot,
            merchant_id=1,
        )

        db.add.assert_called_once()
        turn_obj = db.add.call_args[0][0]
        assert isinstance(turn_obj, ConversationTurn)
        assert turn_obj.conversation_id == 42
        assert turn_obj.turn_number == 3
        assert turn_obj.intent_detected == "product_search"
        assert turn_obj.sentiment == "EMPATHETIC"
        assert turn_obj.context_snapshot == snapshot
        assert turn_obj.merchant_id == 1

    @pytest.mark.p0
    @pytest.mark.test_id("STORY-11-12a-008")
    @pytest.mark.asyncio
    async def test_given_duplicate_turn_when_turn_written_then_integrity_error_propagates(self):
        service = MagicMock(spec=UnifiedConversationService)
        service._write_conversation_turn = (
            UnifiedConversationService._write_conversation_turn.__get__(service)
        )

        db = AsyncMock()
        nested_cm = AsyncMock()
        nested_cm.__aenter__ = AsyncMock(side_effect=IntegrityError("stmt", "params", "orig"))
        nested_cm.__aexit__ = AsyncMock(return_value=False)
        db.begin_nested = MagicMock(return_value=nested_cm)

        with pytest.raises(IntegrityError):
            await service._write_conversation_turn(
                db=db,
                conversation_id=1,
                turn_number=1,
                intent_detected="greeting",
                sentiment=None,
                context_snapshot={},
                merchant_id=1,
            )
