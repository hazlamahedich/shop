"""Unit tests for Conversation Context API endpoint logic.

Story 11-1: Conversation Context Memory
Tests the API endpoint functions directly (not via HTTP) for
fast, isolated contract testing without database dependencies.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.errors import APIError, ErrorCode
from app.schemas.conversation_context import (
    ContextSummary,
    ContextSummaryResponse,
    ContextUpdateResponse,
    ConversationContextResponse,
    ConversationContextUpdate,
)

MOCK_CONTEXT = {
    "mode": "ecommerce",
    "turn_count": 3,
    "viewed_products": [101, 202],
    "cart_items": [101],
    "constraints": {"budget_max": 50},
    "search_history": ["blue shoes"],
    "preferences": {"currency": "USD"},
    "expires_at": datetime.now(timezone.utc).isoformat(),
    "created_at": datetime.now(timezone.utc).isoformat(),
    "updated_at": datetime.now(timezone.utc).isoformat(),
}

MOCK_GENERAL_CONTEXT = {
    "mode": "general",
    "turn_count": 2,
    "topics_discussed": ["billing", "account"],
    "documents_referenced": [123],
    "support_issues": [{"type": "billing", "status": "pending"}],
    "escalation_status": "low",
    "expires_at": datetime.now(timezone.utc).isoformat(),
    "created_at": datetime.now(timezone.utc).isoformat(),
    "updated_at": datetime.now(timezone.utc).isoformat(),
}

MOCK_SUMMARY = {
    "summary": "Customer is looking for blue shoes under $50.",
    "key_points": ["Interested in blue shoes", "Budget under $50"],
    "active_constraints": {"budget_max": 50, "color": "blue"},
    "original_turns": 3,
    "summarized_at": datetime.now(timezone.utc).isoformat(),
}


def _mock_request(merchant_id=1):
    request = MagicMock()
    request.state.merchant_id = merchant_id
    return request


def _mock_db(conversation_found=True):
    db = AsyncMock()
    mock_conversation = MagicMock()
    mock_conversation.id = 42
    mock_conversation.merchant_id = 1
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_conversation if conversation_found else None
    db.execute = AsyncMock(return_value=mock_result)
    db.commit = AsyncMock()
    return db


def _mock_context_service(get_return=None, update_return=None, summarize_return=None):
    service = MagicMock()
    service.get_context = AsyncMock(return_value=get_return)
    service.update_context = AsyncMock(return_value=update_return or MOCK_CONTEXT)
    service.summarize_context = AsyncMock(return_value=summarize_return or MOCK_SUMMARY)
    return service


API_MODULE = "app.api.conversation_context"


class TestGetConversationContextEndpoint:
    @pytest.mark.asyncio
    async def test_P0_returns_context_when_found(self):
        from app.api.conversation_context import get_conversation_context

        mock_service = _mock_context_service(get_return=MOCK_CONTEXT)
        mock_request = _mock_request()
        mock_db = _mock_db()

        with (
            patch(f"{API_MODULE}.get_csrf_protection") as mock_csrf,
            patch(f"{API_MODULE}.get_redis_client") as mock_redis,
            patch(f"{API_MODULE}.ConversationContextService", return_value=mock_service),
        ):
            mock_csrf.return_value.validate_token.return_value = True
            result = await get_conversation_context(
                conversation_id=42, request=mock_request, db=mock_db, x_csrf_token="test"
            )

        assert isinstance(result, ContextUpdateResponse)
        assert result.data.mode == "ecommerce"
        assert result.data.turn_count == 3
        assert result.data.viewed_products == [101, 202]

    @pytest.mark.asyncio
    async def test_P0_raises_404_when_context_not_found(self):
        from app.api.conversation_context import get_conversation_context

        mock_service = _mock_context_service(get_return=None)
        mock_request = _mock_request()
        mock_db = _mock_db()

        with (
            patch(f"{API_MODULE}.get_csrf_protection") as mock_csrf,
            patch(f"{API_MODULE}.get_redis_client") as mock_redis,
            patch(f"{API_MODULE}.ConversationContextService", return_value=mock_service),
        ):
            mock_csrf.return_value.validate_token.return_value = True
            with pytest.raises(APIError) as exc_info:
                await get_conversation_context(
                    conversation_id=42,
                    request=mock_request,
                    db=mock_db,
                    x_csrf_token="test",
                )

        assert exc_info.value.code == ErrorCode.CONTEXT_NOT_FOUND

    @pytest.mark.asyncio
    async def test_P0_rejects_invalid_csrf_token(self):
        from app.api.conversation_context import get_conversation_context

        mock_request = _mock_request()
        mock_db = _mock_db()

        with patch(f"{API_MODULE}.get_csrf_protection") as mock_csrf:
            mock_csrf.return_value.validate_token.return_value = False
            with pytest.raises(APIError) as exc_info:
                await get_conversation_context(
                    conversation_id=42,
                    request=mock_request,
                    db=mock_db,
                    x_csrf_token="invalid",
                )

        assert exc_info.value.code == ErrorCode.VALIDATION_ERROR

    @pytest.mark.asyncio
    async def test_P2_raises_404_for_wrong_merchant(self):
        from app.api.conversation_context import get_conversation_context

        mock_request = _mock_request(merchant_id=9999)
        mock_db = _mock_db(conversation_found=False)

        with patch(f"{API_MODULE}.get_csrf_protection") as mock_csrf:
            mock_csrf.return_value.validate_token.return_value = True
            with pytest.raises(APIError) as exc_info:
                await get_conversation_context(
                    conversation_id=42,
                    request=mock_request,
                    db=mock_db,
                    x_csrf_token="test",
                )

        assert exc_info.value.code == ErrorCode.CONVERSATION_NOT_FOUND


class TestUpdateConversationContextEndpoint:
    @pytest.mark.asyncio
    async def test_P0_returns_updated_ecommerce_context(self):
        from app.api.conversation_context import update_conversation_context

        mock_service = _mock_context_service(update_return=MOCK_CONTEXT)
        mock_request = _mock_request()
        mock_db = _mock_db()
        update = ConversationContextUpdate(message="I want blue shoes under $100", mode="ecommerce")

        with (
            patch(f"{API_MODULE}.get_csrf_protection") as mock_csrf,
            patch(f"{API_MODULE}.get_redis_client") as mock_redis,
            patch(f"{API_MODULE}.ConversationContextService", return_value=mock_service),
        ):
            mock_csrf.return_value.validate_token.return_value = True
            result = await update_conversation_context(
                conversation_id=42,
                request=mock_request,
                update=update,
                db=mock_db,
                x_csrf_token="test",
            )

        assert isinstance(result, ContextUpdateResponse)
        assert result.data.mode == "ecommerce"
        mock_service.update_context.assert_called_once_with(
            conversation_id=42,
            merchant_id=1,
            message="I want blue shoes under $100",
            mode="ecommerce",
        )

    @pytest.mark.asyncio
    async def test_P0_returns_updated_general_context(self):
        from app.api.conversation_context import update_conversation_context

        mock_service = _mock_context_service(update_return=MOCK_GENERAL_CONTEXT)
        mock_request = _mock_request()
        mock_db = _mock_db()
        update = ConversationContextUpdate(message="I have a billing question", mode="general")

        with (
            patch(f"{API_MODULE}.get_csrf_protection") as mock_csrf,
            patch(f"{API_MODULE}.get_redis_client") as mock_redis,
            patch(f"{API_MODULE}.ConversationContextService", return_value=mock_service),
        ):
            mock_csrf.return_value.validate_token.return_value = True
            result = await update_conversation_context(
                conversation_id=42,
                request=mock_request,
                update=update,
                db=mock_db,
                x_csrf_token="test",
            )

        assert result.data.mode == "general"
        assert result.data.topics_discussed == ["billing", "account"]

    @pytest.mark.asyncio
    async def test_P1_passes_message_to_service(self):
        from app.api.conversation_context import update_conversation_context

        mock_service = _mock_context_service(update_return=MOCK_CONTEXT)
        mock_request = _mock_request()
        mock_db = _mock_db()
        update = ConversationContextUpdate(message="Show me #123", mode="ecommerce")

        with (
            patch(f"{API_MODULE}.get_csrf_protection") as mock_csrf,
            patch(f"{API_MODULE}.get_redis_client") as mock_redis,
            patch(f"{API_MODULE}.ConversationContextService", return_value=mock_service),
        ):
            mock_csrf.return_value.validate_token.return_value = True
            await update_conversation_context(
                conversation_id=42,
                request=mock_request,
                update=update,
                db=mock_db,
                x_csrf_token="test",
            )

        mock_service.update_context.assert_called_once_with(
            conversation_id=42,
            merchant_id=1,
            message="Show me #123",
            mode="ecommerce",
        )

    @pytest.mark.asyncio
    async def test_P1_rejects_invalid_csrf(self):
        from app.api.conversation_context import update_conversation_context

        mock_request = _mock_request()
        mock_db = _mock_db()
        update = ConversationContextUpdate(message="test", mode="ecommerce")

        with patch(f"{API_MODULE}.get_csrf_protection") as mock_csrf:
            mock_csrf.return_value.validate_token.return_value = False
            with pytest.raises(APIError) as exc_info:
                await update_conversation_context(
                    conversation_id=42,
                    request=mock_request,
                    update=update,
                    db=mock_db,
                    x_csrf_token="bad",
                )

        assert exc_info.value.code == ErrorCode.VALIDATION_ERROR


class TestSummarizeConversationContextEndpoint:
    @pytest.mark.asyncio
    async def test_P1_returns_summary_when_context_exists(self):
        from app.api.conversation_context import summarize_conversation_context

        mock_service = _mock_context_service(get_return=MOCK_CONTEXT, summarize_return=MOCK_SUMMARY)
        mock_request = _mock_request()
        mock_db = _mock_db()

        with (
            patch(f"{API_MODULE}.get_csrf_protection") as mock_csrf,
            patch(f"{API_MODULE}.get_redis_client") as mock_redis,
            patch(f"{API_MODULE}.ConversationContextService", return_value=mock_service),
        ):
            mock_csrf.return_value.validate_token.return_value = True
            result = await summarize_conversation_context(
                conversation_id=42,
                request=mock_request,
                db=mock_db,
                x_csrf_token="test",
            )

        assert isinstance(result, ContextSummaryResponse)
        assert result.data.summary == "Customer is looking for blue shoes under $50."
        assert len(result.data.key_points) == 2
        assert result.data.original_turns == 3
        mock_service.summarize_context.assert_called_once()

    @pytest.mark.asyncio
    async def test_P1_raises_404_when_no_context(self):
        from app.api.conversation_context import summarize_conversation_context

        mock_service = _mock_context_service(get_return=None)
        mock_request = _mock_request()
        mock_db = _mock_db()

        with (
            patch(f"{API_MODULE}.get_csrf_protection") as mock_csrf,
            patch(f"{API_MODULE}.get_redis_client") as mock_redis,
            patch(f"{API_MODULE}.ConversationContextService", return_value=mock_service),
        ):
            mock_csrf.return_value.validate_token.return_value = True
            with pytest.raises(APIError) as exc_info:
                await summarize_conversation_context(
                    conversation_id=42,
                    request=mock_request,
                    db=mock_db,
                    x_csrf_token="test",
                )

        assert exc_info.value.code == ErrorCode.CONTEXT_NOT_FOUND

    @pytest.mark.asyncio
    async def test_P1_rejects_invalid_csrf(self):
        from app.api.conversation_context import summarize_conversation_context

        mock_request = _mock_request()
        mock_db = _mock_db()

        with patch(f"{API_MODULE}.get_csrf_protection") as mock_csrf:
            mock_csrf.return_value.validate_token.return_value = False
            with pytest.raises(APIError) as exc_info:
                await summarize_conversation_context(
                    conversation_id=42,
                    request=mock_request,
                    db=mock_db,
                    x_csrf_token="bad",
                )

        assert exc_info.value.code == ErrorCode.VALIDATION_ERROR


class TestVerifyConversationBelongsToMerchant:
    @pytest.mark.asyncio
    async def test_P1_raises_404_when_conversation_not_found(self):
        from app.api.conversation_context import _verify_conversation_belongs_to_merchant

        mock_db = _mock_db(conversation_found=False)

        with pytest.raises(APIError) as exc_info:
            await _verify_conversation_belongs_to_merchant(42, 9999, mock_db)

        assert exc_info.value.code == ErrorCode.CONVERSATION_NOT_FOUND

    @pytest.mark.asyncio
    async def test_P1_passes_when_conversation_belongs_to_merchant(self):
        from app.api.conversation_context import _verify_conversation_belongs_to_merchant

        mock_db = _mock_db(conversation_found=True)

        result = await _verify_conversation_belongs_to_merchant(42, 1, mock_db)

        assert result is None
