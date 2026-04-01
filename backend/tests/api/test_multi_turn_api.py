"""API tests for multi-turn debug endpoints.

Story 11-2: Tests GET/POST multi-turn state debug endpoints via direct function calls.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.errors import APIError


def _mock_request(merchant_id=1):
    request = MagicMock()
    request.state.merchant_id = merchant_id
    request.headers = {}
    return request


def _mock_db(conversation_found=True, context=None):
    db = AsyncMock()
    mock_conversation = MagicMock()
    mock_conversation.id = 42
    mock_conversation.merchant_id = 1
    mock_conversation.context = context
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_conversation if conversation_found else None
    db.execute = AsyncMock(return_value=mock_result)
    db.commit = AsyncMock()
    return db, mock_conversation


@pytest.mark.asyncio
class TestGetMultiTurnState:
    async def test_returns_default_state_for_new_conversation(self):
        from app.api.multi_turn import get_multi_turn_state

        mock_request = _mock_request(merchant_id=1)
        mock_db, _ = _mock_db(conversation_found=True, context=None)

        result = await get_multi_turn_state(conversation_id=42, request=mock_request, db=mock_db)

        data = result.data
        assert data["state"] == "IDLE"
        assert data["turn_count"] == 0
        assert data["accumulated_constraints"] == {}
        assert data["conversation_id"] == 42

    async def test_returns_existing_state(self):
        from app.api.multi_turn import get_multi_turn_state

        mock_request = _mock_request(merchant_id=1)
        context = {
            "clarification_state": {
                "multi_turn_state": "COLLECTING",
                "turn_count": 3,
                "accumulated_constraints": {"budget_max": 100},
                "questions_asked": ["What is your budget?"],
                "pending_questions": ["What color?"],
                "original_query": "I want a gift",
                "invalid_response_count": 1,
                "mode": "general",
            }
        }
        mock_db, _ = _mock_db(conversation_found=True, context=context)

        result = await get_multi_turn_state(conversation_id=42, request=mock_request, db=mock_db)

        data = result.data
        assert data["state"] == "COLLECTING"
        assert data["turn_count"] == 3
        assert data["accumulated_constraints"] == {"budget_max": 100}
        assert data["questions_asked"] == ["What is your budget?"]
        assert data["pending_questions"] == ["What color?"]
        assert data["original_query"] == "I want a gift"
        assert data["invalid_response_count"] == 1
        assert data["mode"] == "general"

    async def test_raises_for_wrong_merchant(self):
        from app.api.multi_turn import get_multi_turn_state

        mock_request = _mock_request(merchant_id=999)
        mock_db, _ = _mock_db(conversation_found=False)

        with pytest.raises(APIError) as exc_info:
            await get_multi_turn_state(conversation_id=42, request=mock_request, db=mock_db)
        assert "not found" in str(exc_info.value.message).lower()

    async def test_raises_for_nonexistent_conversation(self):
        from app.api.multi_turn import get_multi_turn_state

        mock_request = _mock_request(merchant_id=1)
        mock_db, _ = _mock_db(conversation_found=False)

        with pytest.raises(APIError):
            await get_multi_turn_state(conversation_id=99999, request=mock_request, db=mock_db)

    async def test_envelope_has_meta(self):
        from app.api.multi_turn import get_multi_turn_state

        mock_request = _mock_request(merchant_id=1)
        mock_db, _ = _mock_db(conversation_found=True, context=None)

        result = await get_multi_turn_state(conversation_id=42, request=mock_request, db=mock_db)

        meta = result.meta
        assert meta.request_id is not None
        assert meta.timestamp is not None


@pytest.mark.asyncio
class TestResetMultiTurnState:
    async def test_reset_returns_previous_state(self):
        from app.api.multi_turn import reset_multi_turn_state

        mock_request = _mock_request(merchant_id=1)
        context = {
            "clarification_state": {
                "multi_turn_state": "COLLECTING",
                "turn_count": 2,
            }
        }
        mock_db, mock_conv = _mock_db(conversation_found=True, context=context)

        result = await reset_multi_turn_state(conversation_id=42, request=mock_request, db=mock_db)

        data = result.data
        assert data["reset"] is True
        assert data["previous_state"] == "COLLECTING"
        assert data["conversation_id"] == 42

    async def test_reset_clears_state(self):
        from app.api.multi_turn import reset_multi_turn_state

        mock_request = _mock_request(merchant_id=1)
        context = {
            "clarification_state": {
                "multi_turn_state": "COLLECTING",
                "turn_count": 5,
            }
        }
        mock_db, mock_conv = _mock_db(conversation_found=True, context=context)

        await reset_multi_turn_state(conversation_id=42, request=mock_request, db=mock_db)

        mock_db.commit.assert_called_once()

    async def test_reset_raises_for_missing_conversation(self):
        from app.api.multi_turn import reset_multi_turn_state

        mock_request = _mock_request(merchant_id=1)
        mock_db, _ = _mock_db(conversation_found=False)

        with pytest.raises(APIError):
            await reset_multi_turn_state(conversation_id=42, request=mock_request, db=mock_db)

    async def test_reset_from_idle_returns_idle(self):
        from app.api.multi_turn import reset_multi_turn_state

        mock_request = _mock_request(merchant_id=1)
        mock_db, _ = _mock_db(conversation_found=True, context=None)

        result = await reset_multi_turn_state(conversation_id=42, request=mock_request, db=mock_db)

        data = result.data
        assert data["previous_state"] == "IDLE"
        assert data["reset"] is True
