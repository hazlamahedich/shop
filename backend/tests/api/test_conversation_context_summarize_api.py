"""Unit tests for Conversation Context API: SUMMARIZE and auth helper.

Story 11-1: Conversation Context Memory
Tests summarization endpoint, merchant verification helper,
and placeholder for future DELETE endpoint.

Acceptance Criteria:
- SUMMARIZE returns summary or 404
- CSRF validation enforced
- Merchant authorization verified via helper
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.errors import APIError, ErrorCode
from app.schemas.conversation_context import ContextSummaryResponse
from tests.helpers.context_factories import (
    create_mock_ecommerce_context,
    create_mock_summary,
)

MOCK_CONTEXT = create_mock_ecommerce_context()
MOCK_SUMMARY = create_mock_summary()

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


def _mock_context_service(get_return=None, summarize_return=None):
    service = MagicMock()
    service.get_context = AsyncMock(return_value=get_return)
    service.summarize_context = AsyncMock(return_value=summarize_return or MOCK_SUMMARY)
    return service


class TestSummarizeConversationContextEndpoint:
    @pytest.mark.asyncio
    async def test_P1_returns_summary_when_context_exists(self):
        """SUMMARIZE returns summary data when context exists. [11.1-API-009]"""
        from app.api.conversation_context import summarize_conversation_context

        # Given: A context service with existing context
        mock_service = _mock_context_service(get_return=MOCK_CONTEXT, summarize_return=MOCK_SUMMARY)
        mock_request = _mock_request()
        mock_db = _mock_db()

        with (
            patch(f"{API_MODULE}.get_csrf_protection") as mock_csrf,
            patch(f"{API_MODULE}.get_redis_client") as mock_redis,
            patch(f"{API_MODULE}.ConversationContextService", return_value=mock_service),
        ):
            mock_csrf.return_value.validate_token.return_value = True
            # When: Summarizing context
            result = await summarize_conversation_context(
                conversation_id=42, request=mock_request, db=mock_db, x_csrf_token="test"
            )

        # Then: Summary response contains expected data
        assert isinstance(result, ContextSummaryResponse)
        assert result.data.summary == "Customer is looking for blue shoes under $50."
        assert len(result.data.key_points) == 2
        assert result.data.original_turns == 3
        mock_service.summarize_context.assert_called_once()

    @pytest.mark.asyncio
    async def test_P1_raises_404_when_no_context(self):
        """SUMMARIZE raises CONTEXT_NOT_FOUND when no context exists. [11.1-API-010]"""
        from app.api.conversation_context import summarize_conversation_context

        # Given: No context for the conversation
        mock_service = _mock_context_service(get_return=None)
        mock_request = _mock_request()
        mock_db = _mock_db()

        with (
            patch(f"{API_MODULE}.get_csrf_protection") as mock_csrf,
            patch(f"{API_MODULE}.get_redis_client") as mock_redis,
            patch(f"{API_MODULE}.ConversationContextService", return_value=mock_service),
        ):
            mock_csrf.return_value.validate_token.return_value = True
            # When/Then: Summarize raises APIError
            with pytest.raises(APIError) as exc_info:
                await summarize_conversation_context(
                    conversation_id=42, request=mock_request, db=mock_db, x_csrf_token="test"
                )

        assert exc_info.value.code == ErrorCode.CONTEXT_NOT_FOUND

    @pytest.mark.asyncio
    async def test_P1_rejects_invalid_csrf(self):
        """SUMMARIZE rejects requests with invalid CSRF token. [11.1-API-011]"""
        from app.api.conversation_context import summarize_conversation_context

        # Given: An invalid CSRF token
        mock_request = _mock_request()
        mock_db = _mock_db()

        with patch(f"{API_MODULE}.get_csrf_protection") as mock_csrf:
            mock_csrf.return_value.validate_token.return_value = False
            # When/Then: Request is rejected
            with pytest.raises(APIError) as exc_info:
                await summarize_conversation_context(
                    conversation_id=42, request=mock_request, db=mock_db, x_csrf_token="bad"
                )

        assert exc_info.value.code == ErrorCode.VALIDATION_ERROR


class TestVerifyConversationBelongsToMerchant:
    @pytest.mark.asyncio
    async def test_P1_raises_404_when_conversation_not_found(self):
        """Helper raises CONVERSATION_NOT_FOUND for missing conversation. [11.1-API-012]"""
        from app.api.conversation_context import _verify_conversation_belongs_to_merchant

        # Given: A conversation that doesn't exist
        mock_db = _mock_db(conversation_found=False)

        # When/Then: Verification raises APIError
        with pytest.raises(APIError) as exc_info:
            await _verify_conversation_belongs_to_merchant(42, 9999, mock_db)

        assert exc_info.value.code == ErrorCode.CONVERSATION_NOT_FOUND

    @pytest.mark.asyncio
    async def test_P1_passes_when_conversation_belongs_to_merchant(self):
        """Helper returns None when conversation belongs to merchant. [11.1-API-013]"""
        from app.api.conversation_context import _verify_conversation_belongs_to_merchant

        # Given: A conversation that belongs to the merchant
        mock_db = _mock_db(conversation_found=True)

        # When: Verifying ownership
        result = await _verify_conversation_belongs_to_merchant(42, 1, mock_db)

        # Then: Returns None (no exception)
        assert result is None


# TODO [11.1-API-014]: Add delete_conversation_context tests once the DELETE endpoint
# is implemented in app.api.conversation_context. Expected tests:
# - test_P1_deletes_context_and_returns_200
# - test_P1_rejects_invalid_csrf_on_delete
