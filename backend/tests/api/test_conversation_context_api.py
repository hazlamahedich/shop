"""Unit tests for Conversation Context API endpoints: GET and UPDATE.

Story 11-1: Conversation Context Memory
Tests the API endpoint functions directly (not via HTTP) for
fast, isolated contract testing without database dependencies.

Acceptance Criteria:
- GET context returns data when found, 404 when not
- UPDATE context passes message to service
- CSRF validation enforced on all endpoints
- Merchant authorization verified
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.errors import APIError, ErrorCode
from app.schemas.conversation_context import ContextUpdateResponse, ConversationContextUpdate
from tests.helpers.context_factories import (
    create_mock_ecommerce_context,
    create_mock_general_context,
)

MOCK_CONTEXT = create_mock_ecommerce_context()
MOCK_GENERAL_CONTEXT = create_mock_general_context()

API_MODULE = "app.api.conversation_context"


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


def _mock_context_service(get_return=None, update_return=None):
    service = MagicMock()
    service.get_context = AsyncMock(return_value=get_return)
    service.update_context = AsyncMock(return_value=update_return or MOCK_CONTEXT)
    return service


class TestGetConversationContextEndpoint:
    @pytest.mark.asyncio
    async def test_P0_returns_context_when_found(self):
        """GET returns ecommerce context data when found. [11.1-API-001]"""
        from app.api.conversation_context import get_conversation_context

        # Given: A context service that returns ecommerce context
        mock_service = _mock_context_service(get_return=MOCK_CONTEXT)
        mock_request = _mock_request()
        mock_db = _mock_db()

        with (
            patch(f"{API_MODULE}.get_csrf_protection") as mock_csrf,
            patch(f"{API_MODULE}.get_redis_client") as mock_redis,
            patch(f"{API_MODULE}.ConversationContextService", return_value=mock_service),
        ):
            mock_csrf.return_value.validate_token.return_value = True
            # When: Getting conversation context
            result = await get_conversation_context(
                conversation_id=42, request=mock_request, db=mock_db, x_csrf_token="test"
            )

        # Then: Response contains context data
        assert isinstance(result, ContextUpdateResponse)
        assert result.data.mode == "ecommerce"
        assert result.data.turn_count == 3
        assert result.data.viewed_products == [101, 202]

    @pytest.mark.asyncio
    async def test_P0_raises_404_when_context_not_found(self):
        """GET raises CONTEXT_NOT_FOUND when service returns None. [11.1-API-002]"""
        from app.api.conversation_context import get_conversation_context

        # Given: A context service that returns None
        mock_service = _mock_context_service(get_return=None)
        mock_request = _mock_request()
        mock_db = _mock_db()

        with (
            patch(f"{API_MODULE}.get_csrf_protection") as mock_csrf,
            patch(f"{API_MODULE}.get_redis_client") as mock_redis,
            patch(f"{API_MODULE}.ConversationContextService", return_value=mock_service),
        ):
            mock_csrf.return_value.validate_token.return_value = True
            # When/Then: Getting context raises APIError
            with pytest.raises(APIError) as exc_info:
                await get_conversation_context(
                    conversation_id=42, request=mock_request, db=mock_db, x_csrf_token="test"
                )

        assert exc_info.value.code == ErrorCode.CONTEXT_NOT_FOUND

    @pytest.mark.asyncio
    async def test_P0_rejects_invalid_csrf_token(self):
        """GET rejects requests with invalid CSRF token. [11.1-API-003]"""
        from app.api.conversation_context import get_conversation_context

        # Given: An invalid CSRF token
        mock_request = _mock_request()
        mock_db = _mock_db()

        with patch(f"{API_MODULE}.get_csrf_protection") as mock_csrf:
            mock_csrf.return_value.validate_token.return_value = False
            # When/Then: Request is rejected with VALIDATION_ERROR
            with pytest.raises(APIError) as exc_info:
                await get_conversation_context(
                    conversation_id=42, request=mock_request, db=mock_db, x_csrf_token="invalid"
                )

        assert exc_info.value.code == ErrorCode.VALIDATION_ERROR

    @pytest.mark.asyncio
    async def test_P2_raises_404_for_wrong_merchant(self):
        """GET raises CONVERSATION_NOT_FOUND for unauthorized merchant. [11.1-API-004]"""
        from app.api.conversation_context import get_conversation_context

        # Given: A merchant that doesn't own the conversation
        mock_request = _mock_request(merchant_id=9999)
        mock_db = _mock_db(conversation_found=False)

        with patch(f"{API_MODULE}.get_csrf_protection") as mock_csrf:
            mock_csrf.return_value.validate_token.return_value = True
            # When/Then: Request raises CONVERSATION_NOT_FOUND
            with pytest.raises(APIError) as exc_info:
                await get_conversation_context(
                    conversation_id=42, request=mock_request, db=mock_db, x_csrf_token="test"
                )

        assert exc_info.value.code == ErrorCode.CONVERSATION_NOT_FOUND


class TestUpdateConversationContextEndpoint:
    @pytest.mark.asyncio
    async def test_P0_returns_updated_ecommerce_context(self):
        """UPDATE returns updated ecommerce context with correct fields. [11.1-API-005]"""
        from app.api.conversation_context import update_conversation_context

        # Given: Valid update request for ecommerce mode
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
            # When: Updating context
            result = await update_conversation_context(
                conversation_id=42,
                request=mock_request,
                update=update,
                db=mock_db,
                x_csrf_token="test",
            )

        # Then: Response contains updated ecommerce context
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
        """UPDATE returns updated general context with topics. [11.1-API-006]"""
        from app.api.conversation_context import update_conversation_context

        # Given: Valid update request for general mode
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
            # When: Updating context in general mode
            result = await update_conversation_context(
                conversation_id=42,
                request=mock_request,
                update=update,
                db=mock_db,
                x_csrf_token="test",
            )

        # Then: Response contains general context data
        assert result.data.mode == "general"
        assert result.data.topics_discussed == ["billing", "account"]

    @pytest.mark.asyncio
    async def test_P1_rejects_invalid_csrf(self):
        """UPDATE rejects requests with invalid CSRF token. [11.1-API-008]"""
        from app.api.conversation_context import update_conversation_context

        # Given: An invalid CSRF token
        mock_request = _mock_request()
        mock_db = _mock_db()
        update = ConversationContextUpdate(message="test", mode="ecommerce")

        with patch(f"{API_MODULE}.get_csrf_protection") as mock_csrf:
            mock_csrf.return_value.validate_token.return_value = False
            # When/Then: Request is rejected
            with pytest.raises(APIError) as exc_info:
                await update_conversation_context(
                    conversation_id=42,
                    request=mock_request,
                    update=update,
                    db=mock_db,
                    x_csrf_token="bad",
                )

        assert exc_info.value.code == ErrorCode.VALIDATION_ERROR
