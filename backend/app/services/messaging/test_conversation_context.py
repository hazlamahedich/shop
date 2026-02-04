"""Tests for conversation context manager.

Unit tests for Redis storage, TTL, and context retrieval.
"""

from __future__ import annotations

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.messaging.conversation_context import ConversationContextManager


@pytest.mark.asyncio
async def test_get_context_new_session():
    """Test getting context for new session (no existing data)."""
    with patch("app.services.messaging.conversation_context.redis") as mock_redis:
        mock_redis_client = MagicMock()
        mock_redis_client.get.return_value = None
        mock_redis.from_url.return_value = mock_redis_client

        manager = ConversationContextManager()
        context = await manager.get_context("123456")

        assert context["psid"] == "123456"
        assert context["created_at"] is None
        assert context["last_message_at"] is None
        assert context["message_count"] == 0
        assert context["previous_intents"] == []
        assert context["extracted_entities"] == {}
        assert context["conversation_state"] == "active"


@pytest.mark.asyncio
async def test_get_context_existing_session():
    """Test getting context for existing session."""
    with patch("app.services.messaging.conversation_context.redis") as mock_redis:
        mock_redis_client = MagicMock()
        existing_context = {
            "psid": "123456",
            "created_at": "2024-01-01T00:00:00",
            "last_message_at": "running shoes",
            "message_count": 2,
            "previous_intents": ["product_search", "greeting"],
            "extracted_entities": {"category": "shoes", "budget": 100.0},
            "conversation_state": "active",
        }
        mock_redis_client.get.return_value = json.dumps(existing_context)
        mock_redis.from_url.return_value = mock_redis_client

        manager = ConversationContextManager()
        context = await manager.get_context("123456")

        assert context["psid"] == "123456"
        assert context["created_at"] == "2024-01-01T00:00:00"
        assert context["message_count"] == 2
        assert context["previous_intents"] == ["product_search", "greeting"]
        assert context["extracted_entities"] == {"category": "shoes", "budget": 100.0}


@pytest.mark.asyncio
async def test_update_classification():
    """Test updating context with new classification."""
    with patch("app.services.messaging.conversation_context.redis") as mock_redis:
        mock_redis_client = MagicMock()
        # No existing context
        mock_redis_client.get.return_value = None
        mock_redis.from_url.return_value = mock_redis_client

        manager = ConversationContextManager()

        classification = {
            "intent": "product_search",
            "entities": {"category": "shoes", "budget": 100.0},
            "raw_message": "running shoes under $100",
        }

        await manager.update_classification("123456", classification)

        # Verify setex was called with TTL
        mock_redis_client.setex.assert_called_once()
        call_args = mock_redis_client.setex.call_args
        assert call_args[0][0] == "conversation:123456"  # session key
        assert call_args[0][1] == 86400  # TTL (24 hours)

        # Verify stored context
        stored_context = json.loads(call_args[0][2])
        assert "product_search" in stored_context["previous_intents"]
        assert stored_context["extracted_entities"]["category"] == "shoes"
        assert stored_context["extracted_entities"]["budget"] == 100.0
        assert stored_context["message_count"] == 1


@pytest.mark.asyncio
async def test_update_classification_merge_entities():
    """Test that entities are merged on update."""
    with patch("app.services.messaging.conversation_context.redis") as mock_redis:
        mock_redis_client = MagicMock()
        existing_context = {
            "psid": "123456",
            "created_at": "2024-01-01T00:00:00",
            "last_message_at": "shoes",
            "message_count": 1,
            "previous_intents": ["product_search"],
            "extracted_entities": {"category": "shoes"},
            "conversation_state": "active",
        }
        mock_redis_client.get.return_value = json.dumps(existing_context)
        mock_redis.from_url.return_value = mock_redis_client

        manager = ConversationContextManager()

        # New classification adds budget and size
        classification = {
            "intent": "product_search",
            "entities": {"category": "shoes", "budget": 100.0, "size": "8"},
            "raw_message": "size 8 under $100",
        }

        await manager.update_classification("123456", classification)

        # Verify entities were merged
        call_args = mock_redis_client.setex.call_args
        stored_context = json.loads(call_args[0][2])
        assert stored_context["extracted_entities"]["category"] == "shoes"
        assert stored_context["extracted_entities"]["budget"] == 100.0
        assert stored_context["extracted_entities"]["size"] == "8"
        assert stored_context["message_count"] == 2  # Incremented


@pytest.mark.asyncio
async def test_delete_context():
    """Test deleting conversation context."""
    with patch("app.services.messaging.conversation_context.redis") as mock_redis:
        mock_redis_client = MagicMock()
        mock_redis.from_url.return_value = mock_redis_client

        manager = ConversationContextManager()
        await manager.delete_context("123456")

        mock_redis_client.delete.assert_called_once_with("conversation:123456")


@pytest.mark.asyncio
async def test_get_context_error_handling():
    """Test error handling when Redis fails."""
    with patch("app.services.messaging.conversation_context.redis") as mock_redis:
        mock_redis_client = MagicMock()
        mock_redis_client.get.side_effect = Exception("Redis connection failed")
        mock_redis.from_url.return_value = mock_redis_client

        manager = ConversationContextManager()
        context = await manager.get_context("123456")

        # Should return error context
        assert context["psid"] == "123456"
        assert context["conversation_state"] == "error"


@pytest.mark.asyncio
async def test_session_key_generation():
    """Test session key generation for different PSIDs."""
    manager = ConversationContextManager()

    key1 = manager._get_session_key("123456")
    key2 = manager._get_session_key("789012")

    assert key1 == "conversation:123456"
    assert key2 == "conversation:789012"
    assert key1 != key2


@pytest.mark.asyncio
async def test_update_classification_error_handling():
    """Test error handling when update fails."""
    with patch("app.services.messaging.conversation_context.redis") as mock_redis:
        mock_redis_client = MagicMock()
        mock_redis_client.get.return_value = None
        mock_redis_client.setex.side_effect = Exception("Redis write failed")
        mock_redis.from_url.return_value = mock_redis_client

        manager = ConversationContextManager()

        classification = {
            "intent": "product_search",
            "entities": {"category": "shoes"},
            "raw_message": "shoes",
        }

        # Should not raise exception
        await manager.update_classification("123456", classification)
